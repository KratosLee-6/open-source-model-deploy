"""
结构化显存需求模型 (v1.0.3)

解决的问题
----------
v1.0.2 之前，模型的显存需求只有两种形态：
  1. `assessor.vram_note` —— 一句自然语言字符串，机器无法解析；
  2. `hardware_detect.recommend_models_for_hardware` 里的临时计算 —— 且对 MoE 是错的。

MoE 的关键事实：**所有 expert 权重都必须常驻显存**。稀疏激活只降低计算量（FLOPs），
不降低权重占用的显存。所以显存必须按**总参数**（size_b）算，而不是按激活参数
（activated_b）算。

v1.0.2 的 bug：MoE 分支用 activated_b 乘每参数字节数，导致
  DeepSeek-V3（671B 总参 / 37B 激活）算出 Q4 ≈ 22GB
  → 一张 24GB 的 4090 被判定"可以跑 DeepSeek-V3"，而实际需要 600GB+。

本模块把显存需求变成可序列化、可复用的结构化数据，并修正上述 MoE 误判。
纯标准库，无依赖。
"""
from typing import Any, Dict, List, Optional


# 各量化档位的每参数字节数（含权重元数据开销的经验值）
# GGUF 量化额外带 scale/zero-point 元数据，故 4bit 取 0.6 而非理论 0.5
QUANT_SPECS: Dict[str, float] = {
    "Q4_K_M": 0.6,     # 消费级 4bit 甜点，llama.cpp / Ollama 默认
    "Q5_K_M": 0.7,
    "Q6_K": 0.8,
    "Q8_0": 1.0,      # 8bit，质量优先
    "FP8": 1.0,       # 数据中心推理主流
    "BF16": 2.0,      # 训练/高精度推理
}

# 量化档位从低到高（用于「给定显存找最优档位」）
QUANT_LADDER: List[str] = ["Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0", "FP8", "BF16"]

# 运行时开销系数：KV cache + 激活值 + CUDA context + 显存碎片
# 经验值 1.2；长 context（>32K）需要更大，见 context_scaling_factor
HEADROOM = 1.2

# 官方公布的显存下限（优先于启发式计算）。只收录能从官方渠道确认的数字。
# source 字段会随结构化结果一起输出，便于溯源。
VRAM_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "deepseek-v4.1-flash": {
        "vram_min_gb": 614,
        "source": "official",
        "note": "官方 vram_min 614 GB（GB200 NVL4 / 8×H200 节点）",
    },
    "qwen3.5-397b-a17b": {
        "vram_min_gb": 400,
        "source": "official",
        "note": "官方 vram ≥ 400 GB（H200 / 8×H100 节点）",
    },
}

# 消费级显卡档位（用于「需要几张卡」的反推建议）
GPU_TIERS: List[Dict[str, Any]] = [
    {"name": "RTX 4090 / 3090", "vram_gb": 24},
    {"name": "RTX 4080 / A10", "vram_gb": 16},
    {"name": "RTX 4070 Ti", "vram_gb": 12},
    {"name": "RTX 4060 Ti", "vram_gb": 8},
    {"name": "RTX 3060", "vram_gb": 12},
    {"name": "RTX 4060", "vram_gb": 8},
    {"name": "A100 80G", "vram_gb": 80},
    {"name": "A100 40G", "vram_gb": 40},
    {"name": "H100 / H200", "vram_gb": 80},
]


def is_moe(model_info: Dict[str, Any]) -> bool:
    """判断是否 MoE：存在 activated_b 且明显小于 size_b"""
    size_b = model_info.get("size_b") or 0
    activated_b = model_info.get("activated_b") or 0
    return bool(activated_b) and bool(size_b) and activated_b < size_b


def resident_params_b(model_info: Dict[str, Any]) -> float:
    """权重常驻显存所需的参数量（B）

    无论密集还是 MoE，都返回 **总参数** size_b —— MoE 的 expert 权重同样要常驻。
    这与 activated_b（只影响计算量）的区别是本模块存在的核心原因。
    """
    return float(model_info.get("size_b") or 0)


def context_scaling_factor(context_k: int = 0) -> float:
    """context 长度对 KV cache 的放大系数

    KV cache 与 context 长度成正比。短 context（≤4K）时该项相对权重很小，
    统一用 HEADROOM 覆盖；长 context 需要额外放大。
    """
    if context_k <= 0:
        return 1.0
    if context_k <= 8:
        return 1.0
    if context_k <= 32:
        return 1.15
    if context_k <= 128:
        return 1.4
    return 1.8


def vram_requirement(
    model_info: Dict[str, Any],
    quant: str = "Q4_K_M",
    gpu_count: int = 1,
    context_k: int = 0,
) -> Dict[str, Any]:
    """计算单模型在指定量化 / 卡数下的结构化显存需求

    Args:
        model_info: KNOWN_MODELS 里的单条记录
        quant:      量化档位，见 QUANT_SPECS
        gpu_count:  张量并行卡数（权重按卡均分）
        context_k:  context 长度（千 token），影响 KV cache

    Returns:
        可直接 JSON 序列化的结构化字典。
    """
    size_b = resident_params_b(model_info)
    if size_b <= 0:
        return {"error": "model has no size_b", "model_size_known": False}

    if quant not in QUANT_SPECS:
        raise ValueError(f"unknown quant {quant!r}, expected one of {list(QUANT_SPECS)}")

    gpu_count = max(1, int(gpu_count))
    bytes_per_param = QUANT_SPECS[quant]

    # 权重：全部常驻，按总参数算；按卡均分
    weights_gb_total = size_b * bytes_per_param
    weights_gb_per_gpu = weights_gb_total / gpu_count

    # 运行时开销 = KV cache + 激活 + context
    overhead_factor = HEADROOM * context_scaling_factor(context_k)
    runtime_gb_per_gpu = weights_gb_per_gpu * (overhead_factor - 1.0)

    vram_required = weights_gb_per_gpu * overhead_factor

    moe = is_moe(model_info)
    result: Dict[str, Any] = {
        "quant": quant,
        "bytes_per_param": bytes_per_param,
        "size_b": size_b,
        "activated_b": model_info.get("activated_b"),
        "is_moe": moe,
        "gpu_count": gpu_count,
        "context_k": context_k,
        "weights_gb_total": _round_gb(weights_gb_total),
        "weights_gb_per_gpu": _round_gb(weights_gb_per_gpu),
        "runtime_overhead_gb_per_gpu": _round_gb(runtime_gb_per_gpu),
        "vram_required_gb": _round_gb(vram_required),
        "source": "heuristic",
    }

    if moe:
        # 显式记录修正依据，便于 review 和排查
        result["moe_weight_rule"] = "all-experts-resident"
        result["note"] = (
            "MoE：expert 权重全部常驻显存，显存按总参数算；"
            f"activated_b={model_info.get('activated_b')}B 只影响计算量与 KV cache"
        )

    return result


def min_vram_requirement(
    model_info: Dict[str, Any], context_k: int = 0
) -> Dict[str, Any]:
    """该模型的最小实用显存需求（Q4 量化，单卡）

    优先返回官方公布值（VRAM_OVERRIDES），否则用启发式计算。
    """
    name = model_info.get("_name") or ""
    override = VRAM_OVERRIDES.get(name)
    if override:
        return {
            "vram_min_gb": override["vram_min_gb"],
            "quant": "官方口径",
            "source": "official",
            "note": override.get("note", ""),
        }

    req = vram_requirement(model_info, quant="Q4_K_M", gpu_count=1, context_k=context_k)
    return {
        "vram_min_gb": req["vram_required_gb"],
        "quant": "Q4_K_M",
        "source": "heuristic",
        "note": "按总参数 × 0.6 bytes × 1.2 运行时开销估算",
    }


def _round_gb(value: float) -> float:
    """显存数值取整：小模型（<1GB，如 MiniLM 22M）不能被 round 到 0.0"""
    r = round(value, 1)
    if r == 0.0 and value > 0:
        return round(value, 3)
    return r


def best_quant_for_vram(
    model_info: Dict[str, Any], available_gb: float, context_k: int = 0
) -> Optional[str]:
    """给定可用显存，返回能跑的**最高**量化档位；连 Q4 都跑不了返回 None

    注意是从高到低找：显存富余时应给 Q8/FP8 而不是一律 Q4。
    """
    for quant in reversed(QUANT_LADDER):
        req = vram_requirement(
            model_info, quant=quant, gpu_count=1, context_k=context_k
        )
        if req["vram_required_gb"] <= available_gb:
            return quant
    return None


def suggest_gpu_plan(
    model_info: Dict[str, Any],
    quant: str = "Q4_K_M",
    context_k: int = 0,
) -> Dict[str, Any]:
    """反推部署建议：单卡行不行、要几张卡、推荐什么卡

    这是给「我该买什么 / 这台机器能跑吗」场景用的。
    """
    single = vram_requirement(model_info, quant=quant, gpu_count=1, context_k=context_k)

    if single["vram_required_gb"] <= 24:
        plan = {"tier": "single-consumer", "recommend": f"单张消费级 24GB 卡（{quant}）"}
    elif single["vram_required_gb"] <= 80:
        plan = {"tier": "single-datacenter", "recommend": f"单张 A100 80G / H100（{quant}）"}
    else:
        need = single["vram_required_gb"]
        gpus_80g = -(-need // 80)  # 向上取整
        gpus_24g = -(-need // 24)
        plan = {
            "tier": "multi-gpu",
            "recommend": f"多卡集群：{int(gpus_80g)}×80GB 或 {int(gpus_24g)}×24GB（{quant}）",
            "min_gpus_80gb": int(gpus_80g),
            "min_gpus_24gb": int(gpus_24g),
        }

    plan.update(
        {
            "quant": quant,
            "vram_required_gb": single["vram_required_gb"],
            "is_moe": single["is_moe"],
            "source": single["source"],
        }
    )
    return plan


def fit_verdict(required_gb: float, available_gb: float) -> str:
    """可行性判定：fits / tight / no"""
    if available_gb <= 0:
        return "unknown"
    if required_gb <= available_gb * 0.85:
        return "fits"
    if required_gb <= available_gb:
        return "tight"
    return "no"


def model_vram_profile(
    model_name: str, model_info: Dict[str, Any]
) -> Dict[str, Any]:
    """生成一个模型的完整结构化显存档案（用于导出 JSON / 供插件消费）"""
    info = dict(model_info)
    info["_name"] = model_name

    by_quant = {
        q: vram_requirement(info, quant=q, gpu_count=1)["vram_required_gb"]
        for q in QUANT_LADDER
    }

    return {
        "model": model_name,
        "category": model_info.get("category"),
        "size_b": model_info.get("size_b"),
        "activated_b": model_info.get("activated_b"),
        "is_moe": is_moe(info),
        "hf_repo": model_info.get("hf_repo"),
        "vram_gb_by_quant": by_quant,
        "min_vram": min_vram_requirement(info),
        "plan_q4": suggest_gpu_plan(info, quant="Q4_K_M"),
        "note": model_info.get("note", ""),
    }

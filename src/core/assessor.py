"""
步骤 2-5: 整合器
- 调用 model_resolver 拿动态数据
- 调 hardware_prices 算预算
- 输出标准报告字典
"""
from typing import Dict, Any, List

from .model_resolver import resolve_model
from . import vram_requirements as vram
from ..data_sources import hardware_prices as hw


def full_assessment(model_name: str, force: bool = False) -> Dict[str, Any]:
    """5 步鉴别主入口

    Returns:
        报告字典，可被 CLI / Skill 渲染为 markdown
    """
    resolved = resolve_model(model_name, force=force)

    # 估算参数规模（单位：B = billion）
    # 优先级: HF safetensors 元数据 → KNOWN_MODELS 内置 size_b
    size_b = 0.0
    meta = resolved.get("hf_metadata") or {}
    if "safetensors" in meta and meta["safetensors"].get("total"):
        # HF 返回 safetensors.total 是参数个数（不是字节数）
        size_b = meta["safetensors"]["total"] / 1e9
    elif resolved.get("size_b"):
        size_b = resolved["size_b"]

    # 预算估算
    budget = {}
    if size_b > 0:
        budget = hw.estimate_3tier_budget(size_b)

    # ── 结构化显存需求（v1.0.3）────────────────────────────────────
    # 替换 v1.0.2 那句只给 MoE 看的自然语言 vram_note：现在所有模型都有
    # 6 档量化的显存数值、可行性判定和部署卡数建议，且 JSON 可序列化。
    vram_profile: Dict[str, Any] = {}
    vram_note = ""
    if size_b > 0:
        # 用解析到的 size_b（含 HF 动态值）构造一个临时 info 参与计算
        info = dict(resolved)
        info["size_b"] = size_b
        info["_name"] = model_name
        vram_profile = vram.model_vram_profile(model_name, info)
        min_v = vram_profile["min_vram"]
        vram_note = (
            f"最低显存 {min_v['vram_min_gb']} GB（{min_v['quant']}，"
            f"{min_v['source']}）· Q4 部署建议：{vram_profile['plan_q4']['recommend']}"
        )

    return {
        "model_name": model_name,
        "resolved": resolved,
        "estimated_params_b": size_b,
        "activated_params_b": resolved.get("activated_b"),
        "is_moe": vram.is_moe(resolved),
        "vram_note": vram_note,
        "vram_requirements": vram_profile,
        "budget_estimates": budget,
        "category": resolved.get("category"),
        "note": resolved.get("note"),
        "timestamp": _now(),
    }


def _now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

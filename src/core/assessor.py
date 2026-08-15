"""
步骤 2-5: 整合器
- 调用 model_resolver 拿动态数据
- 调 hardware_prices 算预算
- 输出标准报告字典
"""
from typing import Dict, Any, List

from .model_resolver import resolve_model
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
        # 估算激活参数后的显存（用于 MoE）
        activated_b = resolved.get("activated_b", 0)
        vram_note = ""
        if activated_b:
            vram_fp8 = activated_b * 1.0  # 激活参数 × 1 byte (FP8)
            vram_bf16 = activated_b * 2.0  # 激活参数 × 2 bytes
            vram_4bit = activated_b * 0.5  # 激活参数 × 0.5 bytes
            vram_note = f"激活参数显存: FP8≈{vram_fp8:.0f}GB, BF16≈{vram_bf16:.0f}GB, 4bit≈{vram_4bit:.0f}GB"

    return {
        "model_name": model_name,
        "resolved": resolved,
        "estimated_params_b": size_b,
        "activated_params_b": resolved.get("activated_b"),
        "vram_note": vram_note,
        "budget_estimates": budget,
        "category": resolved.get("category"),
        "note": resolved.get("note"),
        "timestamp": _now(),
    }


def _now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

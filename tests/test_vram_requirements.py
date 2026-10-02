"""
vram_requirements 单元测试 (v1.0.3)

重点回归 v1.0.2 的 MoE 显存误判 bug。
运行：python -m pytest tests/ -v
"""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core import vram_requirements as vram  # noqa: E402
from src.core.model_resolver import KNOWN_MODELS  # noqa: E402


# ===== 量化档位 =====

def test_quant_specs_cover_ladder():
    assert set(vram.QUANT_LADDER) == set(vram.QUANT_SPECS)


def test_quant_bytes_monotonic():
    vals = [vram.QUANT_SPECS[q] for q in vram.QUANT_LADDER]
    assert vals == sorted(vals), "量化档位应按每参数字节数递增"
    assert vram.QUANT_SPECS["Q4_K_M"] < vram.QUANT_SPECS["Q8_0"] < vram.QUANT_SPECS["BF16"]


def test_unknown_quant_raises():
    with pytest.raises(ValueError):
        vram.vram_requirement({"size_b": 7}, quant="Q3_MAGIC")


# ===== 核心：MoE 必须按总参数算 =====

def test_moe_detected():
    assert vram.is_moe(KNOWN_MODELS["deepseek-v3"])
    assert vram.is_moe(KNOWN_MODELS["kimi-k2"])
    assert not vram.is_moe(KNOWN_MODELS["qwen3-32b"])
    assert not vram.is_moe(KNOWN_MODELS["llama-3.2-1b-instruct"])


def test_moe_vram_uses_total_params_not_activated():
    """回归测试：v1.0.2 用 activated_b 算 MoE 显存，把 DeepSeek-V3 说成 24GB 卡能跑。

    v1.0.3 必须按总参 671B 算，Q4 需求约 483GB。
    """
    info = KNOWN_MODELS["deepseek-v3"]
    req = vram.vram_requirement(info, quant="Q4_K_M")

    # 671B × 0.6 bytes × 1.2 headroom = 483.1 GB
    assert req["vram_required_gb"] == pytest.approx(483.1, abs=0.5)
    assert req["weights_gb_total"] == pytest.approx(402.6, abs=0.5)
    assert req["moe_weight_rule"] == "all-experts-resident"

    # 关键：绝不能是 v1.0.2 的 22~27GB 区间
    assert req["vram_required_gb"] > 400
    # 24GB 消费级卡明确跑不动
    assert vram.fit_verdict(req["vram_required_gb"], 24) == "no"


def test_all_large_moe_models_exceed_consumer_cards():
    """大型 MoE（>100B 总参）在 24GB 消费级卡上必须判定为跑不动。

    回归 v1.0.2 的 MoE 误判：它按 activated_b 算显存，于是
      Kimi-K2（1000B 总参 / 32B 激活）→ 23GB → 24GB 卡判 "tight"（可跑）
      Qwen3-235B-A22B（235B / 22B）  → 15.8GB → 16GB 卡判 "fits"（可跑）
    两者实际都需要 170GB+。

    注意：小型 MoE（如 gemma-4-26b-a4b 25.8B、deepseek-coder-v2-lite 16B）
    在 24GB 卡上确实跑得动，不属于误判，故按总参 100B 划线。
    """
    regressions = []
    checked = 0
    for name, info in KNOWN_MODELS.items():
        if not vram.is_moe(info) or info["size_b"] <= 100:
            continue
        checked += 1
        req = vram.vram_requirement(info, quant="Q4_K_M")
        if vram.fit_verdict(req["vram_required_gb"], 24) != "no":
            regressions.append((name, req["vram_required_gb"]))
    assert checked >= 10, f"样本太少（{checked}），测试可能失效"
    assert not regressions, f"以下大型 MoE 被误判为消费级卡可跑: {regressions}"


def test_small_moe_can_fit_consumer_card():
    """反向确认：小型 MoE 仍应被判为消费级卡可跑（避免矫枉过正）。"""
    for name in ("gemma-4-26b-a4b", "deepseek-coder-v2-lite"):
        info = KNOWN_MODELS[name]
        assert vram.is_moe(info)
        req = vram.vram_requirement(info, quant="Q4_K_M")
        assert vram.fit_verdict(req["vram_required_gb"], 24) != "no"


def test_activated_b_affects_compute_not_weights():
    """MoE 的 activated_b 不应进入权重显存计算。"""
    info = dict(KNOWN_MODELS["deepseek-v3"])
    base = vram.vram_requirement(info, quant="Q4_K_M")["weights_gb_total"]

    info["activated_b"] = 999  # 篡改激活参数
    after = vram.vram_requirement(info, quant="Q4_K_M")["weights_gb_total"]
    assert base == after


# ===== 官方 override =====

def test_official_override_takes_priority():
    info = dict(KNOWN_MODELS["deepseek-v4.1-flash"])
    info["_name"] = "deepseek-v4.1-flash"
    mn = vram.min_vram_requirement(info)
    assert mn["source"] == "official"
    assert mn["vram_min_gb"] == 614


def test_heuristic_used_without_override():
    info = dict(KNOWN_MODELS["qwen3-32b"])
    info["_name"] = "qwen3-32b"
    mn = vram.min_vram_requirement(info)
    assert mn["source"] == "heuristic"
    # 32B × 0.6 × 1.2 = 23.04
    assert mn["vram_min_gb"] == pytest.approx(23.0, abs=0.5)


# ===== 多卡均分 =====

def test_gpu_count_splits_weights():
    info = KNOWN_MODELS["deepseek-v3"]
    r1 = vram.vram_requirement(info, "Q4_K_M", gpu_count=1)
    r8 = vram.vram_requirement(info, "Q4_K_M", gpu_count=8)
    # 数值已按 1 位小数取整，用绝对容差比较
    assert r8["weights_gb_per_gpu"] == pytest.approx(r1["weights_gb_per_gpu"] / 8, abs=0.1)
    # 总权重不随卡数变化
    assert r8["weights_gb_total"] == pytest.approx(r1["weights_gb_total"], abs=0.1)
    # 8 卡 × 80GB H200 可行
    assert vram.fit_verdict(r8["vram_required_gb"], 80) in ("fits", "tight")


def test_gpu_count_zero_is_coerced():
    info = KNOWN_MODELS["qwen3-32b"]
    r = vram.vram_requirement(info, "Q4_K_M", gpu_count=0)
    assert r["gpu_count"] == 1


# ===== 上下文长度 =====

def test_long_context_increases_vram():
    info = KNOWN_MODELS["qwen3-32b"]
    short = vram.vram_requirement(info, "Q4_K_M", context_k=4)["vram_required_gb"]
    long = vram.vram_requirement(info, "Q4_K_M", context_k=128)["vram_required_gb"]
    assert long > short


# ===== 档位选择与判定 =====

def test_best_quant_ladder():
    """显存富余时给最高档位，而不是一律 Q4。

    qwen3-32b（32B）：Q4≈23GB, Q8≈38GB, BF16≈77GB
    """
    info = KNOWN_MODELS["qwen3-32b"]
    assert vram.best_quant_for_vram(info, 8) is None      # 连 Q4 都放不下
    assert vram.best_quant_for_vram(info, 24) == "Q4_K_M"
    # Q8_0 与 FP8 同为 1.0 byte/param，显存相同；反向遍历时 FP8 排在 Q8_0 之后
    assert vram.QUANT_SPECS["Q8_0"] == vram.QUANT_SPECS["FP8"]
    assert vram.best_quant_for_vram(info, 40) in ("Q8_0", "FP8")
    assert vram.best_quant_for_vram(info, 80) == "BF16"


def test_best_quant_prefers_higher_over_lower():
    """显式验证方向：24GB→Q4，80GB→BF16，后者必须严格更高。"""
    info = KNOWN_MODELS["qwen3-32b"]
    low = vram.best_quant_for_vram(info, 24)
    high = vram.best_quant_for_vram(info, 80)
    assert vram.QUANT_LADDER.index(high) > vram.QUANT_LADDER.index(low)


def test_fit_verdict_bands():
    assert vram.fit_verdict(10, 24) == "fits"
    assert vram.fit_verdict(23, 24) == "tight"
    assert vram.fit_verdict(30, 24) == "no"
    assert vram.fit_verdict(10, 0) == "unknown"


# ===== 边界 =====

def test_missing_size_returns_error_not_crash():
    out = vram.vram_requirement({"hf_repo": "x/y"})
    assert out.get("model_size_known") is False
    assert "error" in out


def test_suggest_gpu_plan_single_and_multi():
    single = vram.suggest_gpu_plan(KNOWN_MODELS["qwen3-14b"], "Q4_K_M")
    assert single["tier"] == "single-consumer"

    multi = vram.suggest_gpu_plan(KNOWN_MODELS["deepseek-v3"], "Q4_K_M")
    assert multi["tier"] == "multi-gpu"
    assert multi["min_gpus_80gb"] >= 1


# ===== 全量一致性 =====

def test_every_model_produces_profile():
    for name in KNOWN_MODELS:
        p = vram.model_vram_profile(name, KNOWN_MODELS[name])
        assert p["model"] == name
        assert set(p["vram_gb_by_quant"]) == set(vram.QUANT_LADDER)
        assert p["min_vram"]["vram_min_gb"] > 0


def test_no_model_recommended_on_zero_vram():
    """total_vram=0（纯 CPU 无显卡）时不应推荐任何模型为 fits"""
    for name, info in KNOWN_MODELS.items():
        if not info.get("size_b"):
            continue
        req = vram.vram_requirement(info, "Q4_K_M")
        assert vram.fit_verdict(req["vram_required_gb"], 0) == "unknown"

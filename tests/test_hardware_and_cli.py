"""
硬件检测与 CLI 计数的回归测试 (v1.0.3)

锁两个在出 v1.0.3 截图时发现的真 bug：
  1. wmic 在 Win11 24H2+ 被移除 → 内存读出 0GB（本机实测 15.9GB 却显示 0）
  2. CLI 打印「总共 N 个模型可在本机部署」用的 len(recs) 是全库条数
     → 6GB 显卡宣称 136 个可部署，正是 v1.0.3 要消灭的那类误导
"""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.data_sources import hardware_detect as hw  # noqa: E402
from src.core.model_resolver import KNOWN_MODELS  # noqa: E402


# ===== 内存检测 =====

def test_windows_memory_reader_returns_sane_values():
    """_windows_memory_gb 必须返回 (total, avail)，且 total > 0（非 wmic 路径）。"""
    import platform
    if platform.system() != "Windows":
        pytest.skip("仅 Windows 生效")
    total, avail = hw._windows_memory_gb()
    assert total > 0, "内存读取返回 0，说明又退回 wmic 了"
    assert total < 4096, "内存数值不合理"
    assert avail >= 0
    assert avail <= total + 1, "available 不应大于 total"


def test_detect_memory_shape():
    m = hw.detect_memory()
    assert set(m) >= {"total_gb", "available_gb"}
    assert m["total_gb"] >= 0


def test_memory_used_in_detect_shape():
    """detect_memory 走的那条分支要保证 key 存在（供 CPU 兜底判断用）。"""
    m = hw.detect_memory()
    assert "total_gb" in m
    assert isinstance(m["total_gb"], (int, float))


# ===== 计数不得夸大 =====

@pytest.fixture
def tiny_gpu_scan():
    """模拟 6GB 显卡 + 16GB 内存的低配机（接近本机实测环境）"""
    return {
        "platform": "windows",
        "apple_silicon": None,
        "nvidia_gpus": [{"index": 0, "vendor": "nvidia", "name": "GTX 1660 Ti",
                         "vram_total_gb": 6, "vram_free_gb": 5, "driver_version": "595.97"}],
        "amd_gpus": [],
        "cpu": {"physical_cores": 8, "logical_cores": 8},
        "memory": {"total_gb": 16.0, "available_gb": 9.0},
        "disk": {"free_gb": 133.6, "total_gb": 500.0},
        "total_vram_gb": 6,
        "deployable_tier": "cpu_only",
    }


def test_runnable_count_never_exceeds_catalog(tiny_gpu_scan):
    """核心回归：可部署数必须远小于全库条数，不得出现「136/136 可部署」这种谎报。"""
    recs = hw.recommend_models_for_hardware(tiny_gpu_scan, KNOWN_MODELS)
    runnable = [r for r in recs if r.get("deployable_quant") or r.get("deployable_precision")]
    assert runnable, "低配机也该能跑点 embedding 小模型"
    assert len(runnable) < len(recs), "6GB 显卡不可能跑全部模型，计数逻辑有问题"
    # 大型 MoE 必须明确不可跑
    for big in ("deepseek-v3", "kimi-k3", "mimo-v2.6-pro", "glm-5.3"):
        r = next(x for x in recs if x["model"] == big)
        assert not (r.get("deployable_quant") or r.get("deployable_precision")), \
            f"{big} 在 6GB 卡上被判为可部署"


def test_retired_excluded_from_live_count(tiny_gpu_scan):
    recs = hw.recommend_models_for_hardware(tiny_gpu_scan, KNOWN_MODELS)
    live = [r for r in recs if r.get("status") != "retired"]
    retired = [r for r in recs if r.get("status") == "retired"]
    assert len(live) + len(retired) == len(recs)
    assert any(r["model"] == "deepseek-v4-flash" for r in retired)
    assert all(r.get("superseded_by") for r in retired)


def test_cpu_fallback_labelled(tiny_gpu_scan):
    """走 CPU 兜底的推荐必须标出显存缺口，不能只写「能跑」。"""
    recs = hw.recommend_models_for_hardware(tiny_gpu_scan, KNOWN_MODELS)
    cpu_recs = [r for r in recs if "CPU" in (r.get("deployable_quant") or "")]
    for r in cpu_recs:
        assert "显存需" in r["deployable_quant"], \
            f"{r['model']} 的 CPU 兜底标签缺少显存缺口说明: {r['deployable_quant']}"


def test_every_recommendation_carries_vram_fields(tiny_gpu_scan):
    """每条推荐都要带 fit / is_moe / status，供上层直接消费。"""
    recs = hw.recommend_models_for_hardware(tiny_gpu_scan, KNOWN_MODELS)
    for r in recs:
        for k in ("fit", "is_moe", "status", "vram_estimate_4bit_gb"):
            assert k in r, f"{r['model']} 缺字段 {k}"

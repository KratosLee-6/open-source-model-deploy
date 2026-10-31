"""test_cost_model.py · 成本对比的回归测试

这一层的核心承诺是「数字可信」，所以测试重点不是算得对，而是：
  1. 每个价格都带出处和时间（没有出处的数字不许进结果）
  2. 云租给区间而不是单点（同一张卡不同平台/时段价差真实存在）
  3. 回本周期的方向正确（云租越贵 → 本地回本越快 → min < max）
  4. 没有报价就不编（不猜平台价格）
  5. 卡型选择按显存需求，不按参数量拍脑袋
"""
from __future__ import annotations

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core import cost_model as cm  # noqa: E402
from src.core.cost_model import (  # noqa: E402
    CLOUD_GPU,
    CostError,
    LOCAL_GPU,
    compare_cost,
    render_cost,
)


# ---------------------------------------------------------------------------
# 1. 数据表自身的完整性：价格必须有出处
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("gpu", list(LOCAL_GPU.keys()))
def test_every_local_gpu_has_source_and_date(gpu):
    """本地卡价必须带出处和采集时间 —— 没出处的数字就是编的"""
    spec = LOCAL_GPU[gpu]
    assert spec["price_cny"] > 0, f"{gpu}: 价格必须为正"
    assert spec["price_source"], f"{gpu}: 缺 price_source"
    assert spec["price_as_of"], f"{gpu}: 缺 price_as_of"
    assert spec["vram_gb"] > 0, f"{gpu}: 缺显存"
    assert spec["power_w"] > 0, f"{gpu}: 缺功耗（没功耗就算不了电费）"


@pytest.mark.parametrize("platform", list(CLOUD_GPU.keys()))
def test_every_cloud_rate_is_a_range(platform):
    """云租必须是区间：低 ≤ 高，且带出处"""
    for gpu, rate in CLOUD_GPU[platform].items():
        assert rate["spot_low"] > 0
        assert rate["ondemand_high"] >= rate["spot_low"], (
            f"{platform}/{gpu}: 现货价不应高于按需价"
        )
        assert rate["source"], f"{platform}/{gpu}: 缺 source"
        assert rate["as_of"], f"{platform}/{gpu}: 缺 as_of"


# ---------------------------------------------------------------------------
# 2. 卡型选择
# ---------------------------------------------------------------------------
def test_pick_single_consumer_for_small_model():
    """6.4GB 需求 → 单张消费级 24GB"""
    plan = {"vram_required_gb": 6.4, "is_moe": False}
    choices = cm._pick_local_gpu(plan)
    assert choices[0]["gpu"] == "RTX 4090"
    assert choices[0]["count"] == 1


def test_pick_a100_for_30_to_80gb():
    plan = {"vram_required_gb": 55.0, "is_moe": False}
    choices = cm._pick_local_gpu(plan)
    assert choices[0]["gpu"] == "NVIDIA A100 80G"
    assert choices[0]["count"] == 1


def test_pick_multi_24gb_for_100gb():
    """100GB → 5 张 4090（ceil(100/24)=5），不超过 8 张"""
    plan = {"vram_required_gb": 100.0, "is_moe": True}
    choices = cm._pick_local_gpu(plan)
    assert choices[0]["gpu"] == "RTX 4090"
    assert choices[0]["count"] == 5


def test_pick_80gb_when_too_many_24gb():
    """500GB → 24GB 卡要 21 张（超 8 张上限）→ 改用 80GB 卡"""
    plan = {"vram_required_gb": 493.5, "is_moe": True}
    choices = cm._pick_local_gpu(plan)
    assert choices[0]["gpu"] == "NVIDIA A100 80G"
    assert choices[0]["count"] == 7  # ceil(493.5/80)


def test_pick_rejects_zero_vram():
    with pytest.raises(CostError, match="显存需求为 0"):
        cm._pick_local_gpu({"vram_required_gb": 0, "is_moe": False})


# ---------------------------------------------------------------------------
# 3. compare_cost 主流程
# ---------------------------------------------------------------------------
def test_small_model_full_structure():
    info = {"size_b": 8.95, "category": "decision"}
    cost = compare_cost(info)

    assert cost["quant"] == "Q4_K_M"
    assert cost["vram_required_gb"] > 0
    assert cost["local"]["gpu"] == "RTX 4090"
    assert cost["local"]["count"] == 1
    # 整机 = 卡价 × 数量 × 加价率
    assert cost["local"]["rig_price_cny"] == int(
        cost["local"]["gpu_total_cny"] * cm.RIG_MARKUP)
    # 每个价格元素都要有出处
    assert cost["local"]["price_source"]
    assert cost["cloud"], "小模型在 AutoDL 有 4090 报价，不该为空"
    for c in cost["cloud"]:
        assert c["source"] and c["as_of"]


def test_breakeven_direction_is_correct():
    """关键：云租越贵 → 本地回本越快，所以 months_min 应来自贵档"""
    cost = compare_cost({"size_b": 8.95})
    items = cost["breakeven"]["items_24x7"]
    assert items, "应有 24×7 回本数据"
    for it in items:
        assert it["months_min"] <= it["months_max"], (
            f"{it['platform']}: min({it['months_min']}) 不应大于 max({it['months_max']})"
        )
        # 数值上验证：min 应来自云租高的那一档
        rig = cost["local"]["rig_price_cny"]
        assert it["months_min"] == min(
            round(rig / it["cloud_monthly_low_cny"], 1),
            round(rig / it["cloud_monthly_high_cny"], 1),
        )


def test_working_hours_breakeven_longer_than_24x7():
    """8h×22 用云少 → 本地方案回本更慢"""
    cost = compare_cost({"size_b": 8.95})
    a = cost["breakeven"]["items_24x7"][0]["months_min"]
    b = cost["breakeven"]["items_working"][0]["months_min"]
    assert b > a, "间歇使用应比 24×7 回本更慢"


def test_electricity_parameter_takes_effect():
    cheap = compare_cost({"size_b": 8.95}, electricity_cny_per_kwh=0.5)
    pricey = compare_cost({"size_b": 8.95}, electricity_cny_per_kwh=1.2)
    assert (pricey["local"]["electricity_cny_per_month_24x7"]
            > cheap["local"]["electricity_cny_per_month_24x7"])


def test_hours_per_month_single_mode():
    cost = compare_cost({"size_b": 8.95}, hours_per_month=200)
    be = cost["breakeven"]
    assert "items_24x7" not in be
    assert be["hours_per_month"] == 200
    assert be["items"]


def test_moe_uses_total_params():
    """MoE 显存按总参算 —— 493.5GB 需要多卡，不能按激活参给小卡"""
    cost = compare_cost({"size_b": 685.36, "activated_b": 37})
    assert cost["vram_required_gb"] > 400, "MoE 应按总参算显存"
    assert cost["local"]["count"] > 1, "这个规模必须多卡"
    assert cost["is_moe"] is True


def test_caveats_present():
    """必须把没算进去的东西说清楚"""
    cost = compare_cost({"size_b": 8.95})
    assert cost["caveats"], "缺 caveats"
    joined = " ".join(cost["caveats"])
    assert "运维" in joined
    assert "总拥有成本" in joined


def test_no_cloud_quote_does_not_invent():
    """没有云报价的卡，不编价格"""
    # 直接测底层：RTX 5090 / H100 在 CLOUD_GPU 里都没有报价
    for gpu in ("RTX 5090", "NVIDIA H100 80G PCIe", "NVIDIA H200", "华为昇腾 910B"):
        assert gpu in LOCAL_GPU, f"{gpu} 应在本地卡表"
        assert cm._cloud_candidates(gpu, 1) == [], (
            f"{gpu} 没有公开云报价，_cloud_candidates 不该凭空返回价格"
        )


def test_no_cloud_quote_yields_note_not_fake_numbers():
    """整条链路上：选了无云报价的卡时，breakeven 给 note 而不是编一个回本月数"""
    # 构造一个一定会选 5090 的显存需求（25–32GB 区间）
    plan = cm._pick_local_gpu({"vram_required_gb": 28.0, "is_moe": False})
    assert plan[0]["gpu"] == "RTX 5090", "28GB 需求应选 5090（32GB）"

    info = {"size_b": 44.0}  # Q4 约 31.7GB → 落在 5090 的 32GB 内
    cost = compare_cost(info)
    if cost["local"]["gpu"] != "RTX 5090":
        pytest.skip(f"该规模选到了 {cost['local']['gpu']}，前提不成立")

    assert cost["cloud"] == []
    assert "note" in cost["breakeven"]
    assert "无法算回本周期" in cost["breakeven"]["note"]


# ---------------------------------------------------------------------------
# 4. 渲染
# ---------------------------------------------------------------------------
def test_render_cost_contains_key_facts():
    text = render_cost(compare_cost({"size_b": 8.95}))
    assert "本地方案" in text
    assert "云租对比" in text
    assert "回本周期" in text
    assert "价格出处" in text
    assert "AutoDL" in text

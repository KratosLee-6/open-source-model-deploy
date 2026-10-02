"""
模型库状态 + 显存暴露的回归测试 (v1.0.3)
"""
import json
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core.model_resolver import KNOWN_MODELS  # noqa: E402
from src.core import vram_requirements as vram  # noqa: E402
from src.mcp_server import _call_tool  # noqa: E402

# 2026-09 新增的模型（参数取自 HF safetensors 实测，勿随意改动）
NEW_MODELS = {
    "mimo-v2.6-pro":              (1024.2, 42),
    "mimo-v2.6-flash":            (310.8, 15),
    "mimo-v2.6-distill-qwen-9b":  (9.41, None),
    "glm-5.3":                    (753.3, 39),
    "glm-5.3-flash":              (321.3, 14),
    "kimi-k3":                    (2779.9, 119),
    "llama-4-scout-17b":          (108.6, 17),
    "llama-4-maverick-17b":       (401.6, 17),
    "qwen3-coder-480b":           (480.2, 35),
}


# ===== 新增模型 =====

def test_new_models_present():
    for n, (size_b, act) in NEW_MODELS.items():
        assert n in KNOWN_MODELS, f"{n} 缺失"
        assert KNOWN_MODELS[n]["size_b"] == pytest.approx(size_b, abs=0.1)
        assert KNOWN_MODELS[n].get("activated_b") == act


def test_new_models_have_hf_repo():
    for n in NEW_MODELS:
        repo = KNOWN_MODELS[n].get("hf_repo", "")
        assert "/" in repo, f"{n} 缺 hf_repo"
        assert repo.count("/") == 1


def test_new_large_moe_not_runnable_on_consumer_card():
    """新增的万亿/千亿级 MoE 在 24GB 卡上必须判为不可跑。"""
    for n in ("mimo-v2.6-pro", "mimo-v2.6-flash", "kimi-k3", "glm-5.3",
              "qwen3-coder-480b", "llama-4-maverick-17b"):
        info = KNOWN_MODELS[n]
        assert vram.is_moe(info), f"{n} 应识别为 MoE"
        req = vram.vram_requirement(info, "Q4_K_M")
        assert vram.fit_verdict(req["vram_required_gb"], 24) == "no", \
            f"{n} 被误判为 24GB 卡可跑"


def test_mimo_distill_fits_consumer_card():
    """MiMo 蒸馏 9B 是新增模型里唯一该落到消费级显卡的。"""
    info = KNOWN_MODELS["mimo-v2.6-distill-qwen-9b"]
    assert not vram.is_moe(info)          # 密集模型
    req = vram.vram_requirement(info, "Q4_K_M")
    assert 6.0 <= req["vram_required_gb"] <= 8.0
    assert vram.fit_verdict(req["vram_required_gb"], 8) in ("fits", "tight")


# ===== 退役模型 =====

def test_retired_model_flagged():
    info = KNOWN_MODELS["deepseek-v4-flash"]
    assert info["status"] == "retired"
    assert info["superseded_by"] == "deepseek-v4.1-flash"
    assert "退役" in info["note"]


def test_replacement_model_is_active():
    assert KNOWN_MODELS["deepseek-v4.1-flash"].get("status", "active") == "active"


def test_resolve_model_surfaces_status():
    r = json.loads(_call_tool("assess_model", {"model": "deepseek-v4-flash"}))
    assert r["status"] == "retired"
    assert r["superseded_by"] == "deepseek-v4.1-flash"


# ===== list_models 显存暴露 =====

def test_list_models_excludes_retired_by_default():
    names = {m["name"] for m in json.loads(_call_tool("list_models", {}))}
    assert "deepseek-v4-flash" not in names
    assert "deepseek-v4.1-flash" in names


def test_list_models_can_include_retired():
    models = json.loads(_call_tool("list_models", {"include_retired": True}))
    m = next(x for x in models if x["name"] == "deepseek-v4-flash")
    assert m["status"] == "retired"
    assert m["superseded_by"] == "deepseek-v4.1-flash"


def test_list_models_entries_carry_vram_data():
    models = json.loads(_call_tool("list_models", {}))
    m = next(x for x in models if x["name"] == "qwen3-32b")
    assert "vram_gb_by_quant" in m
    assert set(m["vram_gb_by_quant"]) == set(vram.QUANT_LADDER)
    assert m["min_vram"]["vram_min_gb"] > 0
    assert "is_moe" in m and "status" in m


@pytest.mark.parametrize("vram_gb", [8, 12, 16, 24, 80])
def test_list_models_max_vram_filters_and_sorts(vram_gb):
    """核心能力：直接问「我这卡能跑什么」，不用逐个 assess。"""
    got = json.loads(_call_tool("list_models", {"max_vram_gb": vram_gb}))
    assert got, f"{vram_gb}GB 不该一个模型都没有"
    # 不该混进跑不动的
    assert all(m["fit"] != "no" for m in got), f"{vram_gb}GB 混入了跑不动的模型"
    # 升序排列（先看到最容易跑的）
    sizes = [m["min_vram"]["vram_min_gb"] for m in got]
    assert sizes == sorted(sizes)
    # 退役模型不该回来
    assert "deepseek-v4-flash" not in {m["name"] for m in got}


def test_list_models_8gb_excludes_large_moe():
    got = json.loads(_call_tool("list_models", {"max_vram_gb": 8}))
    names = {m["name"] for m in got}
    for big in ("mimo-v2.6-pro", "kimi-k3", "glm-5.3", "deepseek-v3"):
        assert big not in names, f"{big} 不该出现在 8GB 列表"


def test_list_models_8gb_includes_mimo_distill():
    got = json.loads(_call_tool("list_models", {"max_vram_gb": 8}))
    assert "mimo-v2.6-distill-qwen-9b" in {m["name"] for m in got}


def test_list_models_category_filter_still_works():
    got = json.loads(_call_tool("list_models", {"category": "code"}))
    assert got
    assert all(m["category"] == "code" for m in got)


# ===== detect_hardware =====

def test_detect_hardware_separates_retired():
    d = json.loads(_call_tool("detect_hardware", {}))
    assert "excluded_retired" in d
    names = {x["model"] for x in d["excluded_retired"]}
    assert "deepseek-v4-flash" in names
    for x in d["excluded_retired"]:
        assert x["superseded_by"]
    # 推荐列表里的条目带 status
    r = d["top_recommendations"][0]
    assert "status" in r and "fit" in r and "is_moe" in r

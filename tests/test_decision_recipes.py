"""test_decision_recipes.py · System One 决策模型部署配方的回归测试

守住三件事：
  1. 每个 decision 类模型都有配方（不能出现「库里列了但无法部署」的洞）
  2. 配方字段完整（form / endpoint / port / install / run 缺一不可）
  3. deploy 生成器对 decision 类**不套用 chat 模板**（这是 v1.1.1 的真实 bug）
"""
from __future__ import annotations

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core.decision_recipes import (  # noqa: E402
    DECISION_RECIPES,
    ENDPOINT_DECIDE,
    ENDPOINT_SYSTEMONE,
    get_recipe,
    list_covered,
)
from src.core.deployment_generator import generate_deploy_script  # noqa: E402
from src.core.model_resolver import KNOWN_MODELS  # noqa: E402

VALID_FORMS = {"service", "library", "hybrid"}
# /v1/completions 是 JEV 的真实决策入口（2026-10-31 真机验证）
VALID_ENDPOINTS = {ENDPOINT_DECIDE, ENDPOINT_SYSTEMONE, "/v1/completions"}

# 假硬件（不需要真 GPU，只验生成逻辑）
FAKE_HW = {
    "platform": "linux",
    "cpu": {"logical_cores": 8, "arch": "x86_64"},
    "memory_gb": 32,
    "nvidia_gpus": [{"name": "Fake GPU", "vram_gb": 24}],
    "total_vram_gb": 24,
    "apple_silicon": None,
}


def decision_models():
    """KNOWN_MODELS 里 category == decision 的全部条目"""
    return {
        slug: info
        for slug, info in KNOWN_MODELS.items()
        if info.get("category") == "decision"
    }


# ---------------------------------------------------------------------------
# 1. 覆盖率：库里的每个 decision 模型都必须有配方
# ---------------------------------------------------------------------------
def test_every_decision_model_has_recipe():
    """decision 类模型不能有「列出来了但 deploy 不出东西」的洞"""
    missing = [
        f"{slug} ({info.get('hf_repo')})"
        for slug, info in decision_models().items()
        if get_recipe(info.get("hf_repo", "")) is None
    ]
    assert not missing, (
        "以下 decision 模型缺部署配方，用户在 deploy 时会拿到「尚未核实」：\n  "
        + "\n  ".join(missing)
    )


def test_recipe_count_matches_decision_category():
    """配方数与 decision 类模型数应一致（多出来的说明库里有配方但没模型）"""
    n_models = len(decision_models())
    n_recipes = len(DECISION_RECIPES)
    assert n_models == n_recipes, (
        f"decision 模型 {n_models} 个，配方 {n_recipes} 个；"
        f"多出的配方: {sorted(set(DECISION_RECIPES) - {i.get('hf_repo','').lower() for i in decision_models().values()})}"
    )


# ---------------------------------------------------------------------------
# 2. 配方字段完整性
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("hf_repo", list_covered())
def test_recipe_fields_complete(hf_repo):
    """每个配方都要有 form / endpoint / install / run；service 形态还要 port"""
    r = DECISION_RECIPES[hf_repo]

    assert r["display"], f"{hf_repo}: display 缺失"
    assert r["form"] in VALID_FORMS, f"{hf_repo}: form={r['form']!r} 不合法"
    assert r["framework"], f"{hf_repo}: framework 缺失"
    assert r["endpoint"] in VALID_ENDPOINTS, f"{hf_repo}: endpoint={r['endpoint']!r} 不合法"
    assert r["install"], f"{hf_repo}: install 为空"
    assert r["run"], f"{hf_repo}: run 为空"

    if r["form"] in ("service", "hybrid"):
        assert isinstance(r["port"], int) and r["port"] > 0, (
            f"{hf_repo}: form={r['form']} 必须有合法 port，实际 {r['port']!r}"
        )
    if r["form"] == "library":
        assert r["port"] is None, (
            f"{hf_repo}: library 形态不该有 port（进程内调用），实际 {r['port']!r}"
        )


@pytest.mark.parametrize("hf_repo", list_covered())
def test_recipe_example_has_required_keys(hf_repo):
    """每种 body 格式的示例必须带各自必需的键"""
    r = DECISION_RECIPES[hf_repo]
    ex = r.get("example") or {}
    assert ex, f"{hf_repo}: 缺 example（生成的脚本就没有真实请求示例）"

    body_format = r.get("body_format")
    assert body_format in ("decide", "systemone", "vllm_logprobs"), (
        f"{hf_repo}: body_format={body_format!r} 不合法"
    )

    if body_format in ("decide", "vllm_logprobs"):
        assert "kind" in ex, f"{hf_repo}: decide 格式的示例必须带 kind"
        assert "state" in ex, f"{hf_repo}: decide 格式的示例必须带 state"
        assert "question" in ex, f"{hf_repo}: decide 格式的示例必须带 question"
        assert ex["kind"] in ("noul", "choice", "score"), (
            f"{hf_repo}: kind={ex['kind']!r} 不是三原语之一"
        )
    else:
        assert "state" in ex, f"{hf_repo}: systemone 格式的示例必须带 state"
        assert "questions" in ex, f"{hf_repo}: systemone 格式的示例必须带 questions"
        for qname, q in ex["questions"].items():
            assert "type" in q, f"{hf_repo}: 题目 {qname} 缺 type"
            assert q["type"] in ("noul", "choice", "score", "number", "excerpt"), (
                f"{hf_repo}: 题目 {qname} 的 type={q['type']!r} 不认识"
            )


def test_thx01_path_and_body_format_differ():
    """THX-01 是「路径 /v1/decide + body systemone」的反例，必须显式记录"""
    r = DECISION_RECIPES.get("doofz/thx-01")
    assert r is not None
    assert r["endpoint"] == "/v1/decide"
    assert r["body_format"] == "systemone", (
        "THX-01 官方文档写明 POST /v1/decide 是 /v1/systemone 的别名、"
        "body 用多题格式；若这里退回 decide 会把示例 body 生成错"
    )


# ---------------------------------------------------------------------------
# 3. 核心回归：decision 类不能走 chat 模板
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("slug", list(decision_models().keys()))
def test_deploy_decision_does_not_use_chat_template(slug):
    """v1.1.1 的真实 bug：decision 模型被给成 vllm serve（只有 chat 接口）"""
    info = KNOWN_MODELS[slug]
    script = generate_deploy_script(slug, info, FAKE_HW)

    assert script.get("decision") is True, f"{slug}: 未标记为 decision"

    run = script["run_cmd"]
    # chat 模板的标志：直接 vllm serve <hf_repo> 而不带 decision 相关参数
    if "vllm serve" in run:
        assert ("adapter" in run or "shim" in run or "adapter_vllm" in run), (
            f"{slug}: run_cmd 用了裸 vllm serve，但决策模型需要 adapter 或 shim —— "
            f"用户会得到一个只有 chat/completions 的服务\n{run}"
        )

    # 必须告知真实接口，否则用户不知道问什么
    assert script.get("endpoint") in VALID_ENDPOINTS, f"{slug}: 缺 endpoint"
    if script.get("form") != "library":
        assert script.get("example_curl"), f"{slug}: 缺真实请求示例"


def test_deploy_decision_library_form_has_no_server():
    """library 形态不该给服务命令，也不该给 curl"""
    slug = None
    for s, info in decision_models().items():
        r = get_recipe(info.get("hf_repo", ""))
        if r and r["form"] == "library":
            slug = s
            break
    if slug is None:
        pytest.skip("库里没有 library 形态的决策模型")

    script = generate_deploy_script(slug, KNOWN_MODELS[slug], FAKE_HW)
    assert script["form"] == "library"
    assert "example_curl" not in script
    assert "vllm serve" not in script["run_cmd"]


def test_deploy_unknown_decision_model_is_honest():
    """没有配方的决策模型必须明说「未核实」，不能编命令"""
    info = {
        "hf_repo": "someone/brand-new-decision-model",
        "category": "decision",
        "size_b": 3,
    }
    script = generate_deploy_script("fake-model", info, FAKE_HW)
    assert script["framework"] == "unknown-decision"
    assert "未核实" in script["run_cmd"] or "尚未核实" in script["run_cmd"]
    assert "vllm serve" not in script["run_cmd"]


# ---------------------------------------------------------------------------
# 4. 非 decision 模型不受影响
# ---------------------------------------------------------------------------
def test_non_decision_model_unchanged():
    """普通模型仍走原路径，不被打上 decision 标记"""
    script = generate_deploy_script(
        "qwen3-8b",
        KNOWN_MODELS["qwen3-8b"],
        FAKE_HW,
    )
    assert not script.get("decision")
    assert "run_cmd" in script and script["run_cmd"]

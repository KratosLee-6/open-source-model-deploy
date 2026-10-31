"""test_decision_client.py · 决策模型统一客户端的回归测试

守住四件事：
  1. 问题构造正确（noul/choice/score → 统一 spec）
  2. 两种 body 格式分别正确（/v1/decide 单题 vs /v1/systemone 多题）
  3. 两种返回格式都能归一化成同一形状（这是「统一客户端」的核心承诺）
  4. 该报错的场景明确报错（library 形态 / 非决策模型 / 无配方）
"""
from __future__ import annotations

import os
import sys
from unittest import mock

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core import decision_client as dc  # noqa: E402
from src.core.decision_client import (  # noqa: E402
    DecisionError,
    _body_decide,
    _body_systemone,
    _build_questions,
    ask,
    render_answers,
)


# ---------------------------------------------------------------------------
# 1. 问题构造
# ---------------------------------------------------------------------------
def test_build_questions_three_kinds():
    qs = _build_questions(
        ["是否包含自动续约条款"],
        {"风险等级": ["低", "中", "高"]},
        {"严重程度": ["无", "轻微", "严重"]},
    )
    assert len(qs) == 3
    kinds = [q["kind"] for q in qs]
    assert kinds == ["noul", "choice", "score"]
    assert qs[0]["options"] == ["false", "true"]
    assert qs[1]["options"] == ["低", "中", "高"]
    assert qs[2]["options"] == ["无", "轻微", "严重"]


def test_build_questions_score_default_levels():
    qs = _build_questions(None, None, {"严重程度": None})
    assert qs[0]["options"] == dc.DEFAULT_SCORE_LEVELS


def test_build_questions_rejects_empty():
    with pytest.raises(DecisionError, match="至少要问一个问题"):
        _build_questions(None, None, None)


def test_build_questions_rejects_single_option_choice():
    with pytest.raises(DecisionError, match="至少需要 2 个选项"):
        _build_questions(None, {"x": ["only"]}, None)


# ---------------------------------------------------------------------------
# 2. 两种 body 格式
# ---------------------------------------------------------------------------
def test_body_decide_single_question():
    q = {"name": "q0", "kind": "choice", "instructions": "哪个团队?",
         "options": ["计费", "技术"]}
    b = _body_decide("材料", q)
    assert b == {"kind": "choice", "state": "材料",
                 "question": "哪个团队?", "options": ["计费", "技术"]}


def test_body_decide_noul_has_no_options():
    q = {"name": "q0", "kind": "noul", "instructions": "是否紧急", "options": ["false", "true"]}
    b = _body_decide("材料", q)
    assert "options" not in b, "noul 不该带 options"


def test_body_systemone_multi_question():
    qs = _build_questions(
        ["是否紧急"],
        {"负责团队": ["计费", "技术"]},
        {"严重": ["低", "中", "高"]},
    )
    b = _body_systemone("材料", qs)
    assert b["state"] == "材料"
    assert set(b["questions"]) == {"noul_0", "负责团队", "严重"}
    assert b["questions"]["noul_0"]["type"] == "noul"
    assert b["questions"]["负责团队"]["criteria"] == ["计费", "技术"]
    assert b["questions"]["严重"]["criteria"] == ["低", "中", "高"]


# ---------------------------------------------------------------------------
# 3. 归一化：这是统一客户端的核心 —— 两种返回格式产出同一形状
# ---------------------------------------------------------------------------
def test_normalise_decide_choice():
    q = {"name": "q", "kind": "choice", "instructions": "哪个团队?",
         "options": ["billing", "shipping", "technical"]}
    raw = {"options": ["billing", "shipping", "technical"],
           "probabilities": [0.12, 0.08, 0.80]}
    r = dc._normalise_decide(q, raw)
    assert r["value"] == "technical"
    assert r["probability"] == 0.80
    assert r["distribution"]["billing"] == 0.12


def test_normalise_decide_noul():
    q = {"name": "q", "kind": "noul", "instructions": "是否紧急",
         "options": ["false", "true"]}
    r = dc._normalise_decide(q, {"options": ["false", "true"],
                                 "probabilities": [0.07, 0.93]})
    assert r["value"] is True
    assert r["probability"] == 0.93


def test_normalise_decide_score_expected_value():
    q = {"name": "q", "kind": "score", "instructions": "严重程度",
         "options": ["0", "1", "2"]}
    # 期望 = 0*0.1 + 1*0.3 + 2*0.6 = 1.5
    r = dc._normalise_decide(q, {"options": ["0", "1", "2"],
                                 "probabilities": [0.1, 0.3, 0.6]})
    assert r["value"] == 1.5
    assert r["peak"] == "2"


def test_normalise_decide_uses_JEV_choice_index():
    """JEV-27B 会回 choice_index，应优先于 argmax"""
    q = {"name": "q", "kind": "choice", "instructions": "?",
         "options": ["a", "b", "c"]}
    raw = {"options": ["a", "b", "c"], "probabilities": [0.4, 0.35, 0.25],
           "choice_index": 2, "choice": "c"}
    r = dc._normalise_decide(q, raw)
    assert r["value"] == "c", "有 choice_index 时应信任它，而不是 argmax"


def test_normalise_systemone_all_kinds():
    qs = _build_questions(
        ["是否服务宕机"],
        {"负责团队": ["billing", "technical"]},
        {"紧急度": ["可等", "本周", "今天"]},
    )
    raw = {"answers": {
        "noul_0": {"type": "noul", "noul": 0.88, "confidence": 0.88},
        "负责团队": {"type": "choice", "choice": "technical", "confidence": 0.91},
        "紧急度": {"type": "score", "score": 2.1, "confidence": 0.66},
    }}
    r = dc._normalise_systemone(qs, raw)
    assert r["noul_0"]["value"] is True
    assert r["负责团队"]["value"] == "technical"
    assert r["紧急度"]["value"] == 2.1


def test_normalise_systemone_missing_answer_is_reported():
    qs = _build_questions(["是否紧急"], None, None)
    r = dc._normalise_systemone(qs, {"answers": {}})
    assert "error" in r["noul_0"], "缺答案要显式报，不能静默当 False"


def test_both_formats_yield_same_shape():
    """核心承诺：两种接口的返回归一化成同一形状"""
    q = {"name": "q", "kind": "choice", "instructions": "团队?",
         "options": ["billing", "technical"]}

    from_decide = dc._normalise_decide(
        q, {"options": ["billing", "technical"], "probabilities": [0.2, 0.8]})

    from_systemone = dc._normalise_systemone(
        [q], {"answers": {"q": {"type": "choice", "choice": "technical",
                                "confidence": 0.8}}})

    for a in (from_decide, from_systemone["q"]):
        assert a["type"] == "choice"
        assert a["value"] == "technical"
        assert a["probability"] == 0.8


# ---------------------------------------------------------------------------
# 4. ask() 的分流与报错
# ---------------------------------------------------------------------------
def test_ask_jev_splits_into_multiple_requests():
    """JEV 每题一次请求，走 /v1/completions（不是 /v1/decide）

    2026-10-31 真机实测：/v1/decide 在纯 vLLM 上返回 404，那是图像接口。
    """
    r = ask("autotrust-jev-9b", state="x",
            noul=["问题A"], choice={"风险": ["低", "高"]}, dry_run=True)
    assert r["body_format"] == "vllm_logprobs"
    assert len(r["requests"]) == 2
    assert all(req["url"].endswith("/v1/completions") for req in r["requests"])
    # model 必须是 LoRA 名，填基座名会走 System 2 自由生成
    assert all(req["body"]["model"] == "jev-decision" for req in r["requests"])
    # 必须带 allowed_token_ids + logprobs，否则读不到校准概率
    for req in r["requests"]:
        assert req["body"]["logprobs"] >= 2
        assert req["body"]["allowed_token_ids"]
        assert req["body"]["max_tokens"] == 1
        assert req["body"]["add_special_tokens"] is False


def test_ask_clef_single_request():
    """/v1/systemone 一次问多题 -> 只发一次"""
    r = ask("cloudflare-clef-flash-9b", state="x",
            noul=["问题A"], choice={"风险": ["低", "高"]}, dry_run=True)
    assert r["body_format"] == "systemone"
    assert len(r["requests"]) == 1
    assert len(r["requests"][0]["body"]["questions"]) == 2


def test_ask_uses_recipe_port():
    """端口来自配方，不是默认 8000"""
    r = ask("cloudflare-clef-flash-9b", state="x", noul=["a"], dry_run=True)
    assert ":30000" in r["requests"][0]["url"], "Clef 在 30000，不能套 8000"

    r2 = ask("doofz-thx-01", state="x", noul=["a"], dry_run=True)
    assert ":8095" in r2["requests"][0]["url"]


def test_ask_rejects_library_form():
    with pytest.raises(DecisionError, match="library 形态"):
        ask("convai-laya-multilingual", state="x", noul=["a"])


def test_ask_rejects_non_decision_model():
    with pytest.raises(DecisionError, match="不是决策模型"):
        ask("qwen3-8b", state="x", noul=["a"])


def test_ask_rejects_unknown_model():
    with pytest.raises(DecisionError, match="未知模型"):
        ask("no-such-model", state="x", noul=["a"])


def test_ask_accepts_hf_repo_as_model():
    r = ask("autotrust/JEV-9B", state="x", noul=["a"], dry_run=True)
    assert r["model"] == "autotrust-jev-9b"


def test_ask_base_url_override():
    r = ask("autotrust-jev-9b", state="x", noul=["a"],
            base_url="http://10.0.0.5:9999", dry_run=True)
    assert r["requests"][0]["url"].startswith("http://10.0.0.5:9999")


# ---------------------------------------------------------------------------
# 5. 端到端（mock HTTP）
# ---------------------------------------------------------------------------
def test_ask_end_to_end_decide_with_mock():
    """mock 掉 HTTP，验证 JEV 的 logprobs 路径 + 客户端校准

    真实返回形状（2026-10-31 真机抓的，key 是 "token_id:<id>"）：
      choices[0].logprobs.top_logprobs[0] = {"token_id:1802": -0.0368,
                                             "token_id:3721": -3.3200}
    """
    def fake_post(url, body, timeout):
        ids = body["allowed_token_ids"]
        # 让给定 token 中最后一个 logprob 最高 -> 应被判为 true / 高
        top = {}
        for i, tid in enumerate(ids):
            lp = -0.05 if i == len(ids) - 1 else -3.0
            top[f"token_id:{tid}"] = lp
        return {"choices": [{"logprobs": {"top_logprobs": [top]}}]}

    with mock.patch.object(dc, "_post", side_effect=fake_post):
        r = ask("autotrust-jev-9b", state="材料",
                noul=["是否续约"], choice={"风险": ["低", "高"]})

    assert r["ok"] is True
    assert r["requests_made"] == 2
    assert r["answers"]["noul_0"]["value"] is True
    assert r["answers"]["风险"]["value"] == "高"
    assert r["latency_ms"] >= 0


def test_ask_end_to_end_systemone_with_mock():
    def fake_post(url, body, timeout):
        return {"answers": {
            "noul_0": {"type": "noul", "noul": 0.77},
            "风险": {"type": "choice", "choice": "中", "confidence": 0.71},
        }}

    with mock.patch.object(dc, "_post", side_effect=fake_post):
        r = ask("cloudflare-clef-flash-9b", state="材料",
                noul=["是否紧急"], choice={"风险": ["低", "中", "高"]})

    assert r["requests_made"] == 1
    assert r["answers"]["noul_0"]["value"] is True
    assert r["answers"]["风险"]["value"] == "中"


def test_render_answers_output():
    def fake_post(url, body, timeout):
        return {"answers": {"风险": {"type": "choice", "choice": "中",
                                     "confidence": 0.71}}}

    with mock.patch.object(dc, "_post", side_effect=fake_post):
        r = ask("cloudflare-clef-flash-9b", state="x",
                choice={"风险": ["低", "中", "高"]})

    text = render_answers(r)
    assert "风险" in text
    assert "中" in text
    assert "0.710" in text


# ---------------------------------------------------------------------------
# 6. JEV 决策头的硬约束（全部来自 2026-10-31 真机实测）
#    verbalizer 只有 24 个槽：noul 2 + score 6 + choice 16
#    超了服务端会 IndexError，所以必须在这里拦住并说人话
# ---------------------------------------------------------------------------
def test_jev_choice_16_options_ok():
    """16 个选项是上限，刚好能用满（A-P）"""
    opts = [f"选项{i}" for i in range(1, 17)]
    r = ask("autotrust-jev-9b", state="x", choice={"诉求": opts}, dry_run=True)
    body = r["requests"][0]["body"]
    assert body["logprobs"] == 16
    assert body["allowed_token_ids"] == list(range(32, 48))


def test_jev_choice_17_options_rejected():
    """17 个选项超出 verbalizer -> 本地就报错，不发给服务端"""
    opts = [f"选项{i}" for i in range(1, 18)]
    with pytest.raises(dc.DecisionError, match="最多 16"):
        ask("autotrust-jev-9b", state="x", choice={"诉求": opts}, dry_run=True)


def test_jev_score_6_levels_ok():
    """6 档是上限（0-5）"""
    r = ask("autotrust-jev-9b", state="x",
            score={"程度": ["a", "b", "c", "d", "e", "f"]}, dry_run=True)
    body = r["requests"][0]["body"]
    assert body["logprobs"] == 6
    assert body["allowed_token_ids"] == [15, 16, 17, 18, 19, 20]


def test_jev_score_7_levels_rejected():
    """7 档超出 6 个档位槽"""
    with pytest.raises(dc.DecisionError, match="6 个档位槽"):
        ask("autotrust-jev-9b", state="x",
            score={"程度": ["a", "b", "c", "d", "e", "f", "g"]}, dry_run=True)


def test_jev_prompt_uses_bare_v1_template():
    """prompt 必须严格是 bare-v1 模板，choice 选项带字母前缀"""
    r = ask("autotrust-jev-9b", state="合同文本",
            choice={"风险": ["低", "高"]}, dry_run=True)
    prompt = r["requests"][0]["body"]["prompt"]

    assert prompt.startswith("[kind] choice\n")
    assert "\n[state] 合同文本\n" in prompt
    assert "\n[question] 风险\n" in prompt
    assert "\n[options]\nA) 低\nB) 高\n" in prompt
    assert prompt.endswith("\n[decision]:")


def test_jev_noul_uses_false_true_tokens():
    """noul 的选项固定 false/true，槽位 0-1"""
    r = ask("autotrust-jev-9b", state="x", noul=["是否续约"], dry_run=True)
    body = r["requests"][0]["body"]
    assert "false" in body["prompt"] and "true" in body["prompt"]
    assert body["allowed_token_ids"] == [3721, 1802]


def test_jev_score_labels_map_to_model_slots():
    """score 的模型档位是 0..N-1，返回要映射回用户标签"""
    def fake_post(url, body, timeout):
        ids = body["allowed_token_ids"]
        top = {f"token_id:{tid}": (-0.05 if i == len(ids) - 1 else -3.0)
               for i, tid in enumerate(ids)}
        return {"choices": [{"logprobs": {"top_logprobs": [top]}}]}

    with mock.patch.object(dc, "_post", side_effect=fake_post):
        r = ask("autotrust-jev-9b", state="x",
                score={"程度": ["无", "轻微", "中等", "严重"]})

    ans = r["answers"]["程度"]
    # 分布 key 必须是用户标签，不是 "0".."3"
    assert set(ans["distribution"]) == {"无", "轻微", "中等", "严重"}
    assert ans["peak"] == "严重"          # fake 让最后一档最高
    assert ans["peak_index"] == 3


def test_jev_dry_run_shows_served_model():
    """dry-run 要显示真实的 served model（jev-decision），不是基座名"""
    r = ask("autotrust-jev-9b", state="x", noul=["a"], dry_run=True)
    assert r["served_model"] == "jev-decision"
    assert r["endpoint"] == "/v1/completions"
    assert r["requests"][0]["body"]["model"] == "jev-decision"

"""test_verifier.py · verify 的分层判定

这里测的不是「能不能连」，而是**判定逻辑对不对**：
  1. 连通性失败要如实报失败，不能假装通过
  2. library 形态要报「不适用」而不是失败（那是设计，不是 bug）
  3. 结构不对（概率不归一）要拦住
  4. 答案错要报错 —— 这是 verify 存在的理由
  5. 没有 golden set 时 ok=True 但必须明说「答案未验证」，
     不能把「服务能跑」包装成「部署正确」
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core import verifier  # noqa: E402
from src.core.golden_cases import GOLDEN_CASES, list_covered  # noqa: E402
from src.core.verifier import VerifyError, render_verify, verify  # noqa: E402


# ---------------------------------------------------------------------------
# 假服务：按 prompt 里的问句决定哪个 verbalizer 概率高
# ---------------------------------------------------------------------------
class FakeDecisionServer:
    """起一个真的 HTTP 服务，让 verify 走完整链路"""

    def __init__(self, mode: str = "correct"):
        self.mode = mode          # correct | wrong_answer | no_logprobs
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):    # 静音
                pass

            def _json(self, code, payload):
                body = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/v1/models":
                    # 模拟一个「所有决策模型都注册了」的服务，方便不同模型走同一 mock
                    ids = ["jev-decision", "autotrust/JEV-9B", "Cloudflare/clef-flash",
                           "Cloudflare/clef", "convaiinnovations/laya",
                           "doofz/THX-01", "Mapika/decider-2b"]
                    self._json(200, {"object": "list",
                                     "data": [{"id": i, "object": "model"} for i in ids]})
                else:
                    self._json(404, {"detail": "Not Found"})

            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                outer.requests.append(body)

                # ---- /v1/systemone 形态（Clef / Laya / OpenJEV 等）----
                if "questions" in body:
                    answers = {}
                    for name, q in (body.get("questions") or {}).items():
                        if q.get("type") == "noul":
                            answers[name] = {"type": "noul", "noul": 0.91}
                        elif q.get("type") == "choice":
                            crit = q.get("criteria") or {}
                            first = next(iter(crit), "x") if isinstance(crit, dict) \
                                else (crit[0] if crit else "x")
                            answers[name] = {"type": "choice", "choice": first,
                                             "confidence": 0.88}
                        else:
                            answers[name] = {"type": "score", "score": 1,
                                             "confidence": 0.77}
                    self._json(200, {"answers": answers})
                    return

                # ---- /v1/completions 形态（JEV）----
                ids = body.get("allowed_token_ids") or [3721, 1802]
                prompt = body.get("prompt", "")

                # 判断这题期望的答案
                want_true = True
                if "保密" in prompt:
                    want_true = False
                if outer.mode == "wrong_answer":
                    want_true = not want_true

                # ids 前两个是 false/true（noul 槽位 0-1）
                hi, lo = (-0.05, -3.5) if not want_true else (-3.5, -0.05)
                top = {f"token_id:{ids[0]}": hi, f"token_id:{ids[1]}": lo}

                if outer.mode == "no_logprobs":
                    # 真实会遇到的坏情况：服务没带 --logprobs-mode，
                    # 返回里压根没有 logprobs 字段
                    self._json(200, {"choices": [{"text": "false",
                                                  "finish_reason": "length"}]})
                    return

                self._json(200, {"choices": [{
                    "logprobs": {"top_logprobs": [top]}}]})

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"


# ---------------------------------------------------------------------------
# 1. 失败路径
# ---------------------------------------------------------------------------
def test_unreachable_service_reports_l1_failure():
    """端口没人听 -> L1 失败，且不假装通过"""
    r = verify("autotrust-jev-9b", base_url="http://127.0.0.1:1", timeout=2)
    assert r["ok"] is False
    assert r["levels"]["connectivity"]["ok"] is False
    assert r["levels"]["structure"]["ok"] is None
    assert r["levels"]["golden"]["ok"] is None
    assert "服务不可达" in r["conclusion"]


def test_library_form_is_not_a_failure():
    """library 形态没有 HTTP 服务 —— 是设计，不是部署失败"""
    r = verify("convai-laya-multilingual")
    assert r["ok"] is True
    assert r["applicable"] is False
    assert r["levels"]["connectivity"]["ok"] is None
    assert "不是部署问题" in r["conclusion"]


def test_unknown_model_raises():
    with pytest.raises(VerifyError, match="未知模型"):
        verify("no-such-model-xyz")


def test_non_decision_model_raises():
    with pytest.raises(VerifyError, match="不是决策模型"):
        verify("qwen3-8b")


# ---------------------------------------------------------------------------
# 2. 服务在、答案对 -> 三层全过
# ---------------------------------------------------------------------------
def test_full_pass_with_golden_set():
    with FakeDecisionServer("correct") as srv:
        r = verify("autotrust-jev-9b", base_url=srv.url, timeout=10)

    assert r["ok"] is True
    assert r["applicable"] is True
    assert r["levels"]["connectivity"]["ok"] is True
    assert r["levels"]["structure"]["ok"] is True
    assert r["levels"]["golden"]["ok"] is True
    assert "可用" in r["conclusion"]

    # 结构检查 1 次 + golden 3 题 = 至少 4 次请求
    assert len(srv.requests) >= 4
    # 连通性检查认出了 served_model
    assert "jev-decision" in r["levels"]["connectivity"]["available_models"]


# ---------------------------------------------------------------------------
# 3. 答案错 -> 必须报错（verify 存在的理由）
# ---------------------------------------------------------------------------
def test_wrong_answer_fails_l3():
    """服务能跑、结构也对，但答案错 —— 这是 mock 测试永远抓不到的情况"""
    with FakeDecisionServer("wrong_answer") as srv:
        r = verify("autotrust-jev-9b", base_url=srv.url, timeout=10)

    assert r["ok"] is False
    assert r["levels"]["structure"]["ok"] is True     # 结构是好的
    assert r["levels"]["golden"]["ok"] is False        # 但答案错
    assert "答案不对" in r["conclusion"]

    cases = r["levels"]["golden"]["cases"]
    assert len(cases) == 3
    assert not any(c["ok"] for c in cases), "全部答错，不应有通过的题"


# ---------------------------------------------------------------------------
# 4. 结构坏了 -> 拦在 L2
# ---------------------------------------------------------------------------
def test_bad_structure_fails_l2():
    """服务没带 --logprobs-mode -> 返回里没有 top_logprobs，拦在 L2"""
    with FakeDecisionServer("no_logprobs") as srv:
        r = verify("autotrust-jev-9b", base_url=srv.url, timeout=10)

    assert r["ok"] is False
    assert r["levels"]["structure"]["ok"] is False
    assert "请求失败" in r["levels"]["structure"]["detail"]
    assert "logprobs" in r["levels"]["structure"]["detail"]
    # 结构都坏了，golden 不该跑
    assert r["levels"]["golden"]["ok"] is None


# ---------------------------------------------------------------------------
# 5. 没有 golden 的模型：ok=True 但必须说「答案未验证」
# ---------------------------------------------------------------------------
def test_no_golden_says_unverified_explicitly():
    """Clef 没有 golden set -> 通过连通性/结构，但must 明说答案未验证"""
    assert "cloudflare/clef-flash" not in list_covered()

    with FakeDecisionServer("correct") as srv:
        r = verify("cloudflare-clef-flash-9b", base_url=srv.url, timeout=10)

    assert r["ok"] is True
    assert r["levels"]["golden"]["ok"] is None
    assert "未真机实测" in r["levels"]["golden"]["detail"]
    # 结论里必须出现「答案正确性未验证」，不能只说「可用」
    assert "答案正确性未验证" in r["conclusion"]


# ---------------------------------------------------------------------------
# 6. golden set 自身的数据质量
# ---------------------------------------------------------------------------
def test_every_golden_case_has_evidence():
    """每题必须有客观依据（why）和实测概率，不能是凭感觉的题"""
    for repo, block in GOLDEN_CASES.items():
        assert block.get("verified_at"), f"{repo}: 缺 verified_at"
        assert block.get("environment"), f"{repo}: 缺 environment"
        cases = block["cases"]
        assert cases, f"{repo}: 空的 golden set"
        for c in cases:
            assert c.get("why"), f"{repo}/{c['name']}: 缺 why（为什么这是客观答案）"
            assert c["kind"] in ("noul", "choice", "score")
            assert "expect_value" in c
            if c["kind"] == "noul":
                assert isinstance(c["expect_value"], bool)
                assert 0 < c["expect_prob_min"] <= 1


def test_golden_covers_only_decision_models():
    """golden set 不能收录非决策模型"""
    from src.core.model_resolver import KNOWN_MODELS
    repos = {(i.get("hf_repo") or "").lower() for i in KNOWN_MODELS.values()}
    for repo in GOLDEN_CASES:
        assert repo in repos, f"golden set 里的 {repo} 不在 KNOWN_MODELS"


# ---------------------------------------------------------------------------
# 7. 渲染
# ---------------------------------------------------------------------------
def test_render_shows_all_levels():
    with FakeDecisionServer("correct") as srv:
        r = verify("autotrust-jev-9b", base_url=srv.url, timeout=10)
    text = render_verify(r)
    for label in ("L0 配方", "L1 连通性", "L2 结构", "L3 答案"):
        assert label in text
    assert "逐题" in text

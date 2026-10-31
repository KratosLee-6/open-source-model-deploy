"""verifier.py · 自检一个决策模型的部署是否真的可用

为什么需要它
------------
`osm-deploy deploy` 只保证「命令是按 model card 抄对的」。
`osm-deploy ask` 只保证「按这个配方发请求能拿到返回」。
两者都证明不了 **答案对不对**。

2026-10-31 的真机验证就是例子：JEV-9B 的配方在 v1.3.0 里四处全错，
但 25 个 mock 测试全过 —— 因为 mock 永远返回我想让它返回的东西。

verify 分三层，每层能独立给出结论：

    L1 连通性   服务在不在、/v1/models 里有没有预期的 served_model
    L2 结构     发一次最小请求，校验返回字段形状与概率归一
    L3 语义     跑 golden set（已知答案的题），看答案对不对

**诚实原则**：没有 golden set 的模型，L3 会明确标为「未验证」，
不把「服务能跑」包装成「部署正确」。
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .decision_client import (
    KIND_NOUL,
    DecisionError,
    ask,
)
from .decision_recipes import get_recipe
from .golden_cases import get_golden, has_golden
from .model_resolver import KNOWN_MODELS

USER_AGENT = "open-source-model-deploy/verifier"


class VerifyError(RuntimeError):
    """自检过程本身出错（模型不存在、配方缺失等）。"""


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def _http_get(url: str, timeout: float) -> Optional[Dict[str, Any]]:
    """GET 一个 JSON 端点；失败返回 None（verify 里失败是信息不是异常）。"""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, TimeoutError, OSError):
        return None


def _level(ok: Optional[bool], detail: str, **extra) -> Dict[str, Any]:
    node = {"ok": ok, "detail": detail}
    node.update(extra)
    return node


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def verify(
    model: str,
    *,
    base_url: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """自检一个决策模型的部署。

    Args:
        model: KNOWN_MODELS 里的 slug，或 hf_repo
        base_url: 覆盖默认地址（默认 http://localhost:<recipe.port>）
        timeout: 单次请求超时

    Returns:
        {"ok": bool, "levels": {...}, "conclusion": str, ...}
        ok 的语义：服务可用且（有 golden 时）答案正确。
        没有 golden 时 ok=True 但 conclusion 会明确写「答案未验证」。
    """
    # ---- 0) 模型与配方 ----
    slug = model
    info = KNOWN_MODELS.get(slug)
    if info is None:
        for s, i in KNOWN_MODELS.items():
            if (i.get("hf_repo") or "").lower() == model.lower():
                slug, info = s, i
                break
    if info is None:
        raise VerifyError(
            f"未知模型 {model!r}。用 `osm-deploy list --category decision` 看可用的决策模型。"
        )
    if info.get("category") != "decision":
        raise VerifyError(f"{slug} 不是决策模型（category={info.get('category')!r}）。")

    hf_repo = info.get("hf_repo", "")
    recipe = get_recipe(hf_repo)
    if recipe is None:
        raise VerifyError(
            f"{slug} 还没有部署配方，无法自检。参考 references/decision-models.md。"
        )

    form = recipe["form"]
    endpoint = recipe["endpoint"]
    served = recipe.get("served_model") or hf_repo
    root = (base_url or f"http://localhost:{recipe['port'] or 8000}").rstrip("/")

    result: Dict[str, Any] = {
        "ok": False,
        "model": slug,
        "hf_repo": hf_repo,
        "form": form,
        "endpoint": endpoint,
        "served_model": served,
        "service_url": root,
        "levels": {},
    }

    result["levels"]["recipe"] = _level(
        True,
        f"{recipe['display']} · {form} · {endpoint} · model={served}",
    )

    # ---- library 形态：没有 HTTP 服务，verify 不适用（是设计如此，不是失败）----
    if form == "library":
        result["levels"]["connectivity"] = _level(
            None, "library 形态：进程内调用，没有 HTTP 服务，跳过连通性检查"
        )
        result["levels"]["structure"] = _level(None, "library 形态：不适用")
        result["levels"]["golden"] = _level(None, "library 形态：不适用")
        result["ok"] = True
        result["applicable"] = False
        result["conclusion"] = (
            f"ℹ️ {slug} 是 library 形态（进程内 API，不是服务）。"
            f"verify 只适用于有 HTTP 服务的模型 —— 请直接用它的 Python API，见 "
            f"`osm-deploy deploy {slug}` 的 [运行] 段。这不是部署问题。"
        )
        return result

    result["applicable"] = True

    # ---- L1 连通性 ----
    models_resp = _http_get(f"{root}/v1/models", timeout)
    if models_resp is None:
        result["levels"]["connectivity"] = _level(
            False,
            f"连不上 {root}/v1/models —— 服务没起，或端口不对"
            f"（配方端口 {recipe['port']}）",
        )
        result["levels"]["structure"] = _level(None, "未执行（连通性失败）")
        result["levels"]["golden"] = _level(None, "未执行（连通性失败）")
        result["conclusion"] = (
            f"❌ 服务不可达。先按 `osm-deploy deploy {slug}` 的 [运行] 段起服务：\n"
            f"   {root}/v1/models 无响应"
        )
        return result

    served_ids = [d.get("id") for d in (models_resp.get("data") or []) if isinstance(d, dict)]
    if served in served_ids:
        result["levels"]["connectivity"] = _level(
            True, f"服务在线，{served!r} 已注册", available_models=served_ids
        )
    else:
        result["levels"]["connectivity"] = _level(
            None,
            f"服务在线，但没看到 {served!r}。当前可用: {served_ids}。"
            f"如果你用别的 name 起的服务，请用 --base-url 并确认 model 名。",
            available_models=served_ids,
        )

    # ---- L2 结构 ----
    probe_state = "本合同自双方签字之日起生效。"
    try:
        probe = ask(slug, state=probe_state, noul=["这是否是一句话"],
                    base_url=root, timeout=timeout)
    except DecisionError as e:
        result["levels"]["structure"] = _level(False, f"请求失败: {e}")
        result["levels"]["golden"] = _level(None, "未执行（结构检查失败）")
        result["conclusion"] = (
            f"❌ 服务能连上但请求失败：{e}\n"
            f"   常见原因：model 名不对、服务没带 --logprobs-mode、tokenizer 缺失。"
        )
        return result

    structural: List[str] = []
    answers = probe.get("answers") or {}
    first = next(iter(answers.values()), None)
    if not isinstance(first, dict):
        structural.append("返回里没有 answers")
    elif first.get("error"):
        structural.append(f"答案解析出错: {first['error']}")
    else:
        # 两种接口形态对「概率」的载体不同：
        #   vllm_logprobs（JEV）一定有 distribution（客户端 softmax 出来的）
        #   systemone（Clef/Laya/…）可能只给 confidence 或 noul 标量
        has_dist = isinstance(first.get("distribution"), dict) and first["distribution"]
        has_scalar = any(k in first for k in ("value", "probability", "noul",
                                              "confidence"))
        if not (has_dist or has_scalar):
            structural.append(
                f"答案里既没有 distribution 也没有 value/probability，"
                f"字段: {list(first.keys())}"
            )
        if has_dist:
            dist = first["distribution"]
            if set(dist.keys()) != {"false", "true"}:
                structural.append(
                    f"noul 的分布应正好是 false/true，实际 {list(dist.keys())}"
                )
            bad = [k for k, v in dist.items() if not (0.0 <= float(v) <= 1.0)]
            if bad:
                structural.append(f"概率不在 [0,1]: {bad}")
        if first.get("type") != KIND_NOUL:
            structural.append(f"type 应为 noul，实际 {first.get('type')!r}")

    if structural:
        result["levels"]["structure"] = _level(False, "；".join(structural))
        result["levels"]["golden"] = _level(None, "未执行（结构检查失败）")
        result["conclusion"] = f"❌ 返回结构不对：{'；'.join(structural)}"
        return result

    result["levels"]["structure"] = _level(
        True,
        f"返回字段完整 · {probe['requests_made']} 请求 · {probe['latency_ms']:.0f} ms",
        body_format=probe.get("body_format"),
        latency_ms=probe["latency_ms"],
    )

    # ---- L3 语义（golden set）----
    if not has_golden(hf_repo):
        result["levels"]["golden"] = _level(
            None,
            "该模型没有 golden set（未真机实测过答案），只验证了连通性与结构",
        )
        result["ok"] = True
        result["conclusion"] = (
            f"✅ 服务可用（连通性 + 结构通过）。\n"
            f"⚠️ 但 {slug} 的**答案正确性未验证** —— 它还没有 golden set。"
            f"配方是按 model card 抄的，真机上是否正确未知。\n"
            f"   参考教训：JEV-9B 的配方在实测前有 4 处错误，mock 测试全过却完全不能用。"
        )
        return result

    golden = get_golden(hf_repo)
    cases_out: List[Dict[str, Any]] = []
    passed = 0
    for case in golden["cases"]:
        try:
            if case["kind"] == KIND_NOUL:
                r = ask(slug, state=case["state"], noul=[case["question"]],
                        base_url=root, timeout=timeout)
                ans = next(iter(r["answers"].values()))
                got_value = ans.get("value")
                got_prob = ans.get("probability")
            else:
                cases_out.append({"name": case["name"], "ok": None,
                                  "detail": f"暂不支持 kind={case['kind']}"})
                continue
        except DecisionError as e:
            cases_out.append({"name": case["name"], "ok": False, "detail": f"请求失败: {e}"})
            continue

        value_ok = (got_value == case["expect_value"])
        # noul 的 probability 语义是 p_true。expect 为 False 时要取 1-p，
        # 否则「答对了但置信度被判成 0.03」—— 逻辑反了。
        if got_prob is None:
            conf = None
        elif case["expect_value"]:
            conf = got_prob
        else:
            conf = 1.0 - got_prob
        prob_ok = (conf is not None and conf >= case["expect_prob_min"])
        ok = bool(value_ok and prob_ok)
        if ok:
            passed += 1

        detail_parts = [f"预期 {case['expect_value']} 实际 {got_value}"]
        if got_prob is not None:
            detail_parts.append(f"p(true)={got_prob:.3f}")
            if conf != got_prob:
                detail_parts.append(f"取 1-p 得 {conf:.3f}")
            if not prob_ok:
                detail_parts.append(f"低于阈值 {case['expect_prob_min']}")
        if not value_ok:
            detail_parts.append("❌ 答案错")
        elif not prob_ok:
            detail_parts.append("⚠️ 答案对但置信度偏低")

        cases_out.append({
            "name": case["name"],
            "ok": ok,
            "detail": " · ".join(detail_parts),
            "why": case.get("why"),
            "measured_prob": case.get("measured_prob"),
        })

    total = len([c for c in cases_out if c["ok"] is not None])
    all_ok = passed == total and total > 0

    result["levels"]["golden"] = _level(
        all_ok,
        f"{passed}/{total} 通过（环境: {golden.get('environment', '未记录')}）",
        cases=cases_out,
        verified_at=golden.get("verified_at"),
    )

    if all_ok:
        result["ok"] = True
        result["conclusion"] = (
            f"✅ 配方在这台机器上可用 —— 连通性、结构、答案正确性全部通过（{passed}/{total}）。"
        )
    else:
        failed_names = [c["name"] for c in cases_out if c["ok"] is False]
        result["conclusion"] = (
            f"❌ 服务能跑，但答案不对：{', '.join(failed_names)}。\n"
            f"   可能原因：模型/量化档位不同、tokenizer 不匹配、"
            f"或配方里的接口假设不适用于这个版本。"
        )

    return result


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------
_MARK = {True: "✅", False: "❌", None: "➖"}


def render_verify(r: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("=" * 72)
    lines.append(f"【自检】{r['model']}   ({r['hf_repo']})")
    lines.append("=" * 72)
    lines.append(f"  形态     : {r['form']}")
    lines.append(f"  接口     : {r['endpoint']}   model={r['served_model']}")
    lines.append(f"  服务地址 : {r['service_url']}")
    lines.append("")

    labels = {
        "recipe": "L0 配方",
        "connectivity": "L1 连通性",
        "structure": "L2 结构  ",
        "golden": "L3 答案  ",
    }
    for key in ("recipe", "connectivity", "structure", "golden"):
        node = r["levels"].get(key)
        if not node:
            continue
        lines.append(f"  {_MARK.get(node['ok'], '?')} {labels[key]}  {node['detail']}")

    cases = (r["levels"].get("golden") or {}).get("cases") or []
    if cases:
        lines.append("")
        lines.append("  逐题：")
        for c in cases:
            mark = _MARK.get(c["ok"], "?")
            lines.append(f"    {mark} {c['name']}")
            lines.append(f"       {c['detail']}")
            if c.get("why"):
                lines.append(f"       （{c['why']}）")

    lines.append("")
    lines.append("-" * 72)
    for ln in str(r["conclusion"]).split("\n"):
        lines.append("  " + ln)
    lines.append("=" * 72)
    return "\n".join(lines)

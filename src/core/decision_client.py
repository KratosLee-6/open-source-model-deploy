"""decision_client.py · System One 决策模型的统一客户端

为什么需要这一层
----------------
12 个决策模型对外有三种形态、两种接口、五个不同端口：

  形态 : service（HTTP 服务）/ library（进程内）/ hybrid（两者都有）
  接口 : /v1/decide（单题一问）/ /v1/systemone（一次问多题）
  端口 : 8000 / 3000 / 8095 / 30000 / 30002

`osm-deploy deploy` 已经能给出各自的正确启动命令（v1.2.0），但用户仍然要
按模型记两套请求格式。这一层把差异吃掉：**同一套调用，同一套返回**。

    from src.core.decision_client import ask

    result = ask(
        "autotrust-jev-9b",
        state="甲方应在合同到期前 30 日书面通知乙方……",
        noul=["是否包含自动续约条款", "是否约定违约金"],
        choice={"风险等级": ["低", "中", "高"]},
        score={"严重程度": ["无", "轻微", "中等", "严重", "极严重"]},
    )
    print(result["answers"]["风险等级"]["value"])   # -> 中

设计约束
--------
1. **零依赖**：项目 pyproject 不声明任何运行依赖，这里只用标准库 urllib。
2. **不做隐式猜模型**：模型没在 KNOWN_MODELS 里、或没有部署配方，直接报错，
   不退回通用模板（那是 v1.1.1 之前的 bug）。
3. **一次一题 vs 一次多题**：`/v1/decide` 只能问一题，所以多题会被拆成
   多次请求；`/v1/systemone` 一次问完。返回里带 `requests_made` 让你知道
   实际打了几次。
4. **library 形态不假装能连**：Laya 多语言版是进程内模型，没有端口。
   这里明确报错并给进程内调用示例，而不是编一个 HTTP 地址。
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from .decision_recipes import get_recipe
from .model_resolver import KNOWN_MODELS

USER_AGENT = "open-source-model-deploy/decision-client"

# 题型
KIND_NOUL = "noul"
KIND_CHOICE = "choice"
KIND_SCORE = "score"

# score 在 /v1/decide 下的默认档位（JEV 系约定 0-5）
DEFAULT_SCORE_LEVELS = ["0", "1", "2", "3", "4", "5"]


class DecisionError(RuntimeError):
    """决策模型调用失败（模型不存在 / 无配方 / 形态不支持 / 请求失败）。"""


# ---------------------------------------------------------------------------
# 问题规格
# ---------------------------------------------------------------------------
def _build_questions(
    noul: Optional[List[str]],
    choice: Optional[Dict[str, List[str]]],
    score: Optional[Dict[str, List[str]]],
) -> List[Dict[str, Any]]:
    """把三种入参归一化成问题列表。

    每个问题：
        {"name": str, "kind": "noul"|"choice"|"score",
         "instructions": str, "options": list[str]}
    """
    out: List[Dict[str, Any]] = []

    for i, q in enumerate(noul or []):
        if not isinstance(q, str) or not q.strip():
            raise DecisionError(f"noul[{i}] 必须是非空字符串")
        out.append({
            "name": f"noul_{i}",
            "kind": KIND_NOUL,
            "instructions": q.strip(),
            "options": ["false", "true"],
        })

    for name, options in (choice or {}).items():
        if not isinstance(options, (list, tuple)) or len(options) < 2:
            raise DecisionError(f"choice[{name!r}] 至少需要 2 个选项")
        out.append({
            "name": str(name),
            "kind": KIND_CHOICE,
            "instructions": str(name),
            "options": [str(o) for o in options],
        })

    for name, levels in (score or {}).items():
        opts = [str(l) for l in levels] if levels else list(DEFAULT_SCORE_LEVELS)
        if len(opts) < 2:
            raise DecisionError(f"score[{name!r}] 至少需要 2 个档位")
        out.append({
            "name": str(name),
            "kind": KIND_SCORE,
            "instructions": str(name),
            "options": opts,
        })

    if not out:
        raise DecisionError("至少要问一个问题（noul / choice / score 任一）")
    return out


# ---------------------------------------------------------------------------
# 请求构造（两种 body 格式）
# ---------------------------------------------------------------------------
def _body_decide(state: Any, q: Dict[str, Any]) -> Dict[str, Any]:
    """/v1/decide：单题一问"""
    body: Dict[str, Any] = {
        "kind": q["kind"],
        "state": state,
        "question": q["instructions"],
    }
    if q["kind"] in (KIND_CHOICE, KIND_SCORE):
        body["options"] = q["options"]
    return body


def _body_systemone(state: Any, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """/v1/systemone：一次多题，每题带 type + instructions + criteria"""
    qs: Dict[str, Any] = {}
    for q in questions:
        item: Dict[str, Any] = {"type": q["kind"], "instructions": q["instructions"]}
        if q["kind"] == KIND_NOUL:
            item["criteria"] = {"true": "yes", "false": "no"}
        else:
            # score 的 criteria 是有序列表；choice 用列表即可（各模型接受）
            item["criteria"] = q["options"]
        qs[q["name"]] = item
    return {"state": state, "questions": qs}


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _post(url: str, body: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise DecisionError(f"HTTP {e.code} from {url}: {detail}") from e
    except urllib.error.URLError as e:
        raise DecisionError(
            f"连不上 {url}（{e.reason}）。服务起来了吗？"
            f"先跑 `osm-deploy deploy <model>` 看正确启动命令。"
        ) from e
    except TimeoutError:
        raise DecisionError(f"{url} 超时（>{timeout}s）")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise DecisionError(f"{url} 返回的不是 JSON：{raw[:200]}")


# ---------------------------------------------------------------------------
# 响应归一化（各模型字段不完全一致，这里做宽松解析）
# ---------------------------------------------------------------------------
def _pick(d: Dict[str, Any], *keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _normalise_decide(q: Dict[str, Any], r: Dict[str, Any]) -> Dict[str, Any]:
    """解析 /v1/decide 的单题返回"""
    options = _pick(r, "options", default=q["options"])
    probs = _pick(r, "probabilities", default=None)

    base: Dict[str, Any] = {"type": q["kind"], "question": q["instructions"]}

    if not isinstance(probs, (list, tuple)) or not probs:
        # 有些实现只回单个标量
        for key in ("probability", "confidence", "score", "noul"):
            if key in r:
                base["value"] = r[key]
                base["probability"] = r[key]
                return base
        raise DecisionError(f"/v1/decide 返回里找不到 probabilities：{list(r)[:8]}")

    dist = {str(o): float(p) for o, p in zip(options, probs)}

    if q["kind"] == KIND_NOUL:
        # options 通常是 ["false","true"]
        p_true = dist.get("true", dist.get("True", 0.0))
        base.update({"value": p_true >= 0.5, "probability": p_true})
    elif q["kind"] == KIND_CHOICE:
        best = max(dist, key=lambda k: dist[k])
        idx = _pick(r, "choice_index", default=None)
        if idx is not None and isinstance(idx, int) and 0 <= idx < len(options):
            best = str(options[idx])
        base.update({"value": best, "probability": dist[best]})
    else:  # score
        try:
            # 期望值 = Σ(档位值 × 概率)，档位按字符串解析成数字
            expected = sum(float(k) * v for k, v in dist.items())
            best = max(dist, key=lambda k: dist[k])
            base.update({"value": round(expected, 3), "peak": best,
                         "probability": dist[best]})
        except ValueError:
            best = max(dist, key=lambda k: dist[k])
            base.update({"value": best, "probability": dist[best]})

    base["distribution"] = dist
    return base


def _normalise_systemone(
    questions: List[Dict[str, Any]], r: Dict[str, Any]
) -> Dict[str, Any]:
    """解析 /v1/systemone 的多题返回，逐个问题对齐"""
    answers_src = _pick(r, "answers", "results", default=None)
    if not isinstance(answers_src, dict):
        raise DecisionError(f"/v1/systemone 返回里找不到 answers：{list(r)[:8]}")

    out: Dict[str, Any] = {}
    for q in questions:
        node = answers_src.get(q["name"])
        if not isinstance(node, dict):
            out[q["name"]] = {"type": q["kind"], "question": q["instructions"],
                              "error": "答案缺失"}
            continue

        base: Dict[str, Any] = {"type": q["kind"], "question": q["instructions"]}
        kind = q["kind"]

        if kind == KIND_NOUL:
            p = _pick(node, "noul", "probability", "confidence", default=None)
            if p is None:
                base["error"] = "无法解析 noul"
            else:
                p = float(p)
                base.update({"value": p >= 0.5, "probability": p})
        elif kind == KIND_CHOICE:
            val = _pick(node, "choice", "value", default=None)
            p = _pick(node, "confidence", "probability", default=None)
            base.update({"value": val,
                         "probability": float(p) if p is not None else None})
        else:  # score
            val = _pick(node, "score", "value", default=None)
            p = _pick(node, "confidence", "probability", default=None)
            base.update({"value": val,
                         "probability": float(p) if p is not None else None})

        dist = _pick(node, "distribution", "probabilities", default=None)
        if isinstance(dist, dict):
            base["distribution"] = {str(k): float(v) for k, v in dist.items()}
        out[q["name"]] = base

    return out


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------
def ask(
    model: str,
    state: Any,
    *,
    noul: Optional[List[str]] = None,
    choice: Optional[Dict[str, List[str]]] = None,
    score: Optional[Dict[str, List[str]]] = None,
    base_url: Optional[str] = None,
    timeout: float = 60.0,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """向一个 System One 决策模型提问，返回归一化的答案。

    Args:
        model: KNOWN_MODELS 里的 slug（如 "autotrust-jev-9b"）或 hf_repo
        state: 待判断的材料（文本，或模型支持的结构化 dict）
        noul: 是非题列表，如 ["是否包含自动续约条款"]
        choice: 选择题，{问题名: [选项1, 选项2, ...]}
        score: 打题题，{问题名: [档位1, 档位2, ...]}（有序）
        base_url: 覆盖默认地址（默认 http://localhost:<recipe.port>）
        timeout: 单次请求超时（秒）
        dry_run: True 时只返回将要发送的请求，不真的发

    Returns:
        {
          "ok": bool, "model": str, "hf_repo": str, "endpoint": str,
          "form": str, "requests_made": int, "latency_ms": float,
          "answers": {name: {"type", "value", "probability", "distribution"}},
          "raw": [...], "requests": [...] (dry_run),
        }
    """
    # 1) 解析模型
    slug = model
    info = KNOWN_MODELS.get(slug)
    if info is None:
        # 允许直接传 hf_repo
        for s, i in KNOWN_MODELS.items():
            if (i.get("hf_repo") or "").lower() == model.lower():
                slug, info = s, i
                break
    if info is None:
        raise DecisionError(
            f"未知模型 {model!r}。用 `osm-deploy list --category decision` 看可用的 12 个。"
        )
    if info.get("category") != "decision":
        raise DecisionError(
            f"{slug} 属于 {info.get('category')!r}，不是决策模型。"
            f"决策模型用 `osm-deploy list --category decision` 查。"
        )

    hf_repo = info.get("hf_repo", "")
    recipe = get_recipe(hf_repo)
    if recipe is None:
        raise DecisionError(
            f"{slug} 还没有部署配方（v1.2.0 只覆盖了 12 个已核实的模型）。"
            f"参考 references/decision-models.md。"
        )

    form = recipe["form"]
    if form == "library":
        raise DecisionError(
            f"{slug} 是 library 形态（进程内调用，没有 HTTP 服务）。"
            f"请直接用它的 Python API：{recipe['display']} —— 见 "
            f"`osm-deploy deploy {slug}` 里的 [运行] 段。"
        )

    # 2) 组装问题
    questions = _build_questions(noul, choice, score)
    endpoint = recipe["endpoint"]
    port = recipe["port"] or 8000
    root = (base_url or f"http://localhost:{port}").rstrip("/")
    url = f"{root}{endpoint}"
    body_format = recipe.get("body_format") or (
        "decide" if endpoint == "/v1/decide" else "systemone"
    )

    # 3) 构造请求列表
    if body_format == "systemone":
        reqs: List[Tuple[str, Dict[str, Any], Optional[str]]] = [
            (url, _body_systemone(state, questions), None)
        ]
    else:
        # /v1/decide 一次只问一题 -> 拆成多次
        reqs = [(url, _body_decide(state, q), q["name"]) for q in questions]

    result: Dict[str, Any] = {
        "ok": True,
        "model": slug,
        "hf_repo": hf_repo,
        "endpoint": endpoint,
        "form": form,
        "body_format": body_format,
        "requests_made": 0,
        "latency_ms": 0.0,
        "answers": {},
        "raw": [],
    }

    if dry_run:
        result["requests"] = [{"url": u, "body": b} for u, b, _ in reqs]
        result["ok"] = False
        result["note"] = "dry_run：未发送"
        return result

    # 4) 发送
    t0 = time.time()
    raw_all: List[Any] = []
    for u, b, qname in reqs:
        raw = _post(u, b, timeout)
        raw_all.append(raw)
        result["requests_made"] += 1

    result["latency_ms"] = round((time.time() - t0) * 1000, 1)
    result["raw"] = raw_all

    # 5) 归一化
    if body_format == "systemone":
        result["answers"] = _normalise_systemone(questions, raw_all[0])
    else:
        by_name = {q["name"]: q for q in questions}
        for qname, raw in zip([n for _, _, n in reqs], raw_all):
            result["answers"][qname] = _normalise_decide(by_name[qname], raw)

    return result


def render_answers(result: Dict[str, Any]) -> str:
    """把 ask() 的结果渲染成人类可读的一段（CLI 用）。"""
    lines: List[str] = []
    lines.append(f"模型     : {result['model']}  ({result['hf_repo']})")
    lines.append(f"接口     : {result['endpoint']}  请求 {result['requests_made']} 次"
                 f"  耗时 {result['latency_ms']} ms")

    for name, a in (result.get("answers") or {}).items():
        kind = a.get("type", "?")
        if "error" in a:
            lines.append(f"  {name:24} [{kind}]  ❌ {a['error']}")
            continue
        val = a.get("value")
        prob = a.get("probability")
        p_txt = f"{prob:.3f}" if isinstance(prob, (int, float)) else "-"
        if kind == KIND_SCORE:
            lines.append(f"  {name:24} [score]  期望 {val}  (峰值 {a.get('peak','-')}, p={p_txt})")
        elif kind == KIND_NOUL:
            lines.append(f"  {name:24} [noul]   {val}  (p={p_txt})")
        else:
            lines.append(f"  {name:24} [choice] {val}  (p={p_txt})")

        dist = a.get("distribution")
        if isinstance(dist, dict) and dist:
            top = sorted(dist.items(), key=lambda kv: -kv[1])[:4]
            lines.append("  " + " " * 24 + " 分布: " +
                         "  ".join(f"{k}={v:.3f}" for k, v in top))
    return "\n".join(lines)

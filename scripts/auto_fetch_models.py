#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_fetch_models.py · 自动从 HuggingFace + GitHub 拉取主流开源模型
                    生成可粘贴到 model_resolver.py 的 KNOWN_MODELS patch

Usage:
    python3 scripts/auto_fetch_models.py --mode=diff      # 对比现有 KNOWN_MODELS 与 HF top
    python3 scripts/auto_fetch_models.py --mode=patch     # 打印可直接插入的字典条目
    python3 scripts/auto_fetch_models.py --mode=stats     # 仅输出统计

数据源（HuggingFace API + HF 文件 size_b 探测）：
    - /api/models?pipeline_tag=text-generation&sort=downloads
    - /api/models?pipeline_tag=image-text-to-text&sort=downloads
    - /api/models?pipeline_tag=sentence-similarity&sort=downloads
    - /api/models?pipeline_tag=text-to-image&sort=downloads

过滤规则：
    1. 只接受权威 namespace（Qwen / deepseek-ai / meta-llama / google / mistralai / THUDM /
       moonshotai / openai / nvidia / microsoft / baai / BAAI / sentence-transformers /
       intfloat / OpenGVLab / CohereLabs / apple / stabilityai / Alibaba-NLP / EleutherAI /
       MiniMaxAI / inclusionAI / tencent / Hunyuan）
    2. 排除明显量化/微调衍生：-GGUF/-AWQ/-GPTQ/-NVFP4/-QAT/-abliterated/-heretic/-uncensored/...
    3. 排除 LoRA/adapter/merge tag
    4. downloads < 50_000 跳过（默认）
    5. 与现有 KNOWN_MODELS hf_repo 对比，输出 missing
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.request
from typing import Dict, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOLVER_PATH = os.path.join(REPO_ROOT, "src", "core", "model_resolver.py")

# 8 大类（与现有 KNOWN_MODELS 一致；JEV 类不进，参见 references/jev-integration.md）
CATEGORY_BY_TAG = {
    "text-generation": "domestic-general",   # 默认；后面用 namespace + size 区分
    "image-text-to-text": "vision",
    "sentence-similarity": "embedding",
    "text-to-image": "image-generation",     # 新类（若需）
}

AUTHORITATIVE_NS = {
    "Qwen", "deepseek-ai", "meta-llama", "google", "mistralai", "THUDM",
    "moonshotai", "openai", "nvidia", "microsoft", "baai", "BAAI",
    "sentence-transformers", "intfloat", "OpenGVLab", "CohereLabs",
    "apple", "stabilityai", "Alibaba-NLP", "NousResearch", "EleutherAI",
    "MiniMaxAI", "inclusionAI", "tencent", "Hunyuan",
}

FORBIDDEN_SUFFIX = [
    "-GGUF", "-gguf", "-AWQ", "-GPTQ", "-BNB", "-NF4",
    "-abliterated", "-heretic", "-uncensored",
    "-NVFP4", "-QAT", "-imatrix", "-IMatrix", "-MTP",
    # FP8/FP4 等官方预量化权重：参数量与基座模型完全相同，入库只是制造重复条目
    # （Qwen3.6-35B-A3B-FP8 与已在库的 qwen3.6-35b-a3b 是同一个模型）
    "-FP8", "-fp8", "-INT8", "-int8", "-W8A8", "-w8a8",
]
BAD_TAGS = {"adapter", "lora", "merge"}

PIPELINE_TAGS = [
    "text-generation",
    "image-text-to-text",
    "sentence-similarity",
    "text-to-image",
]


def http_get_json(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "osm-deploy-fetcher/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


# HF 参数量查询缓存（一次进程内每个 repo 只打一次 API）
# patch 模式会对同一候选既做 lint 探测又生成条目，没有缓存就是双倍网络请求
_PARAMS_CACHE: Dict[str, dict | None] = {}


def fetch_model_params(repo_id: str) -> dict | None:
    """从 HF API 取 safetensors 参数量（权威口径，取代名称正则猜测）

    /api/models/{repo}?expand[]=safetensors 返回的 safetensors.total 是**权重元素
    个数**，即真实总参数量，与权重存储 dtype 无关。

    动机（v1.0.3）：原来的 guess_size_b() 纯正则抠模型名，对
    - MiMo-V2.6-Pro-RL / GLM-5.3 / Kimi-K3 这类新命名 → size_b=0（数据全丢）
    - Llama-4-Scout-17B-16E                     → 抠到 17B（激活参）当总参，
      显存低估 6.4 倍，与 v1.0.2 那个 MoE bug 同源

    Returns: {"total_b": float, "params_by_dtype": {...}} 或 None
    """
    if repo_id in _PARAMS_CACHE:
        return _PARAMS_CACHE[repo_id]

    url = f"https://huggingface.co/api/models/{repo_id}?expand[]=safetensors"
    result = None
    try:
        data = http_get_json(url, timeout=25)
        st = data.get("safetensors") or {}
        total = st.get("total")
        if total:
            result = {
                "total_b": round(total / 1e9, 2),
                "params_by_dtype": st.get("parameters") or {},
            }
    except Exception as e:
        sys.stderr.write(f"[warn] params {repo_id} fail: {e}\n")

    _PARAMS_CACHE[repo_id] = result
    return result


def guess_activated_b(model_id: str) -> str | None:
    """从模型名里推 activated_b（仅当命名形态明确时）

    识别 Qwen 系的 '<总参>B-A<激活>B' 形态（qwen3-30b-a3b / qwen3-coder-480b-a35b）。

    注意：这是**推断**，不是实测。Meta 的 '<激活>B-<专家>E' 形态（Llama-4-Scout-17B-16E）
    故意不处理——那种命名里的 B 就是激活参，套用反而会引入与 guess_size_b 同类的错误。
    真正的激活参只能从模型卡或 config.json 取，故本函数返回的值一律标注为待核。
    """
    base = model_id.split("/", 1)[1]
    m = re.search(r"[-_]a(\d+(?:\.\d+)?)[bB]\b", base, re.I)
    if m:
        return m.group(1)
    return None


def fetch_top(tag: str, limit: int = 300, sort: str = "downloads") -> List[dict]:
    url = f"https://huggingface.co/api/models?pipeline_tag={tag}&sort={sort}&direction=-1&limit={limit}"
    try:
        return http_get_json(url)
    except Exception as e:
        sys.stderr.write(f"[warn] fetch {tag} fail: {e}\n")
        return []


def is_authoritative(model_id: str) -> bool:
    author = model_id.split("/")[0]
    return author in AUTHORITATIVE_NS


def is_clean(model_id: str, tags: list[str]) -> bool:
    base = model_id.split("/", 1)[1]
    for kw in FORBIDDEN_SUFFIX:
        if kw in base:
            return False
    if any(t in BAD_TAGS for t in (tags or [])):
        return False
    return True


def get_existing_repos() -> set[str]:
    if not os.path.exists(RESOLVER_PATH):
        return set()
    s = open(RESOLVER_PATH, encoding="utf-8").read()
    return set(re.findall(r'"hf_repo"\s*:\s*"([^"]+)"', s))


def guess_category(model_id: str, pipeline_tag: str) -> str:
    """映射到 8 大类。基于 namespace + base name 启发式。"""
    base = model_id.split("/", 1)[1].lower()
    if pipeline_tag == "sentence-similarity" or "embed" in base or "gte-" in base:
        return "embedding"
    if pipeline_tag == "image-text-to-text" or "-vl" in base or "-vision" in base or "-ocr" in base:
        return "vision"
    if "coder" in base or "code" in base or "starcoder" in base:
        return "code"
    if "deepseek-r1" in base or "qwq" in base or "deepseek-v4" in base or "r1" in base.split("-")[-1]:
        return "domestic-reasoning" if any(c in model_id for c in ("Qwen", "deepseek", "THUDM", "moonshotai")) else "domestic-reasoning"
    if any(t in model_id for t in ("Qwen", "deepseek-ai", "THUDM", "moonshotai", "MiniMaxAI", "inclusionAI", "tencent", "Hunyuan", "01-ai", "zhipuai")):
        return "domestic-general"
    if any(t in model_id for t in ("meta-llama", "google", "mistralai", "microsoft", "EleutherAI", "apple", "CohereLabs", "NousResearch")):
        return "international-edge" if re.search(r"(\d+(\.\d+)?)[bB]\b", base) and float(re.search(r"(\d+(\.\d+)?)[bB]\b", base).group(1)) < 20 else "international-dense"
    if pipeline_tag == "text-to-image":
        return "image-generation"
    return "domestic-general"


def guess_size_b(model_id: str) -> str:
    """从 base name 抓 size（粗略，无 API 验证时标 None 占位）"""
    base = model_id.split("/", 1)[1]
    # 形如 qwen3-8b / gemma-3-9b / llama-3.1-70b
    m = re.search(r"[-_](?:(\d+)\.?\d*)\s*([bBmM])", base)
    if m:
        size = m.group(1)
        unit = m.group(2).lower()
        if unit == "m":
            return f"{int(size) / 1000:.2f}"  # millions → B
        return size  # B
    # 形如 Qwen3-VL-Embedding-8B
    m = re.search(r"(\d+)([bBmM])", base)
    if m:
        size, unit = int(m.group(1)), m.group(2).lower()
        if unit == "m":
            return f"{size / 1000:.2f}"
        return str(size)
    return "0"


def build_patch_entry(
    model_id: str,
    downloads: int,
    pipeline_tag: str,
    liked: int = 0,
    verify_params: bool = True,
) -> str:
    """生成一条 KNOWN_MODELS 字典条目

    size_b 优先取 HF safetensors 实测值；取不到才退回名称正则，并在
    _param_source 里标出来源，便于人工判断可信度。
    """
    repo_id = model_id
    slug = repo_id.lower().replace("/", "-").replace("_", "-").replace(".", "-")
    cat = guess_category(model_id, pipeline_tag)
    org, repo = repo_id.split("/", 1)

    # ---- size_b：优先实测 ----
    params = fetch_model_params(repo_id) if verify_params else None
    if params:
        size = f"{params['total_b']}"
        param_source = "hf-safetensors"
    else:
        size = guess_size_b(model_id)
        param_source = "name-regex-unverified" if size != "0" else "name-regex-miss"

    # ---- activated_b：仅在 MoE 命名形态明确时给，且标注为推断 ----
    act = guess_activated_b(model_id)
    act_line = f'        "activated_b": {act},\n' if act else ""

    note = f"Auto-fetched · {downloads / 1e6:.2f}M DLs · {liked} likes"
    if pipeline_tag == "sentence-similarity":
        note = f"Auto-fetched embedding · {downloads / 1e6:.2f}M DLs"
    elif pipeline_tag == "image-text-to-text":
        note = f"Auto-fetched vision · {downloads / 1e6:.2f}M DLs"
    elif pipeline_tag == "text-to-image":
        note = f"Auto-fetched image gen · {downloads / 1e6:.2f}M DLs"

    # 数据来源与待核提示直接写进条目，避免未经复核的数据混进主库
    caveat = ""
    if param_source != "hf-safetensors":
        caveat = "【待核】size_b 未能从 HF 取得，系按名称推断"
    if act:
        caveat += "；activated_b 由命名形态推断，需人工核对"
    if caveat:
        note += f"（{caveat.lstrip('；')}）"

    return (
        f'    "{slug}": {{\n'
        f'        "hf_repo": "{repo_id}",\n'
        f'        "github": "{org}/{repo}",\n'
        f'        "category": "{cat}",\n'
        f'        "size_b": {size},\n'
        f'{act_line}'
        f'        "_auto_fetched": {{\n'
        f'            "downloads": {downloads},\n'
        f'            "likes": {liked},\n'
        f'            "pipeline": "{pipeline_tag}",\n'
        f'            "param_source": "{param_source}",\n'
        f'            "fetched_at": "<ISO_TIMESTAMP>",\n'
        f'        }},\n'
        f'        "note": "{note}",\n'
        f'    }},'
    )


def main():
    ap = argparse.ArgumentParser(description="auto-fetch HF models")
    ap.add_argument("--mode", choices=["diff", "patch", "stats"], default="diff")
    ap.add_argument("--limit", type=int, default=300, help="每 tag 拉多少")
    ap.add_argument("--min-downloads", type=int, default=50_000)
    ap.add_argument(
        "--no-verify", dest="verify_params", action="store_false",
        help="跳过 HF safetensors 实测（快，但 size_b 只能靠名称正则，不可靠）",
    )
    ap.set_defaults(verify_params=True)
    args = ap.parse_args()

    existing = get_existing_repos()

    # 收集所有候选
    pool: Dict[str, dict] = {}
    for tag in PIPELINE_TAGS:
        for m in fetch_top(tag, limit=args.limit):
            if m.get("downloads", 0) < args.min_downloads:
                continue
            mid = m["id"]
            if mid in existing:
                continue
            if not is_authoritative(mid):
                continue
            if not is_clean(mid, m.get("tags", [])):
                continue
            if mid in pool and pool[mid].get("downloads", 0) >= m.get("downloads", 0):
                continue
            pool[mid] = {
                "downloads": m.get("downloads", 0),
                "likes": m.get("likes", 0),
                "pipeline": tag,
                "tags": m.get("tags", []),
            }

    candidates = sorted(pool.items(), key=lambda kv: -kv[1]["downloads"])

    if args.mode == "stats":
        by_cat = {}
        for mid, info in candidates:
            cat = guess_category(mid, info["pipeline"])
            by_cat[cat] = by_cat.get(cat, 0) + 1
        print(f"\n=== 候选总计 {len(candidates)} 个（>={args.min_downloads} DLs · 权威 ns · 非衍生）===\n")
        print("按 8 大类分布（启发式）：")
        for c, n in sorted(by_cat.items(), key=lambda x: -x[1]):
            print(f"  {c:<22}  {n:>3}")
        print(f"\nTop 30:")
        for i, (mid, info) in enumerate(candidates[:30], 1):
            print(f"  {i:>3}. {info['downloads']:>9}  {mid:55} [{info['pipeline']}]")
        return

    if args.mode == "diff":
        print(f"\n=== diff: 当前 KNOWN_MODELS {len(existing)} 个 vs HF 权威候选池 {len(candidates)} 个 ===\n")
        print("missing 详情（按 downloads 排序，仅显示前 50）：")
        for i, (mid, info) in enumerate(candidates[:50], 1):
            cat = guess_category(mid, info["pipeline"])
            print(f"  {i:>3}. [{info['downloads']/1e6:5.2f}M] {mid:55} → {cat}")
        return

    if args.mode == "patch":
        # ── 生成前先体检（v1.0.3）─────────────────────────────────
        # 把候选当成已入库条目跑一遍 lint，ERROR 的直接拦下不输出，
        # 避免把 size_b=0 / 把激活参当总参这类脏数据贴进 model_resolver.py。
        sys.path.insert(0, REPO_ROOT)
        from src.core.model_lint import lint_entry, ERROR as LINT_ERROR

        entries = []
        blocked = []
        for mid, info in candidates:
            slug = mid.lower().replace("/", "-").replace("_", "-").replace(".", "-")
            act = guess_activated_b(mid)
            probe = {
                "hf_repo": mid,
                "size_b": guess_size_b(mid),
                "activated_b": act,
                "note": "Auto-fetched",
            }
            if args.verify_params:
                p = fetch_model_params(mid)
                if p:
                    probe["size_b"] = f"{p['total_b']}"
            issues = lint_entry(slug, probe)
            errs = [i for i in issues if i["severity"] == LINT_ERROR]
            if errs:
                blocked.append((mid, errs))
            else:
                entries.append((mid, info))

        print(f"# === auto_fetch_models.py patch · 候选 {len(candidates)} 个 ===")
        if blocked:
            print(f"#\n# ⚠️ 以下 {len(blocked)} 个候选未通过体检，已拦下（需人工处理后再入库）")
            for mid, errs in blocked:
                print(f"#   ✗ {mid}")
                for e in errs:
                    print(f"#       [{e['code']}] {e['message']}")
            print("#")
        print(f"# 复制下列 {len(entries)} 条到 src/core/model_resolver.py 的 KNOWN_MODELS 字典末尾")
        if not args.verify_params:
            print("# ⚠️ --no-verify 模式：size_b 全部来自名称正则，不可信，仅供快速浏览")
        print("#")
        for mid, info in entries:
            print(build_patch_entry(
                mid, info["downloads"], info["pipeline"], info["likes"],
                verify_params=args.verify_params,
            ))
            print()
        return


if __name__ == "__main__":
    main()

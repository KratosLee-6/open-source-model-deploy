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

# 9 大类（与现有 KNOWN_MODELS 一致；JEV 类不进，参见 references/jev-integration.md）
#
# VALID_CATEGORIES 是**白名单**：分类名必须落在这里。
# 之前 CATEGORY_BY_TAG 里写了一个 "image-generation"，但 KNOWN_MODELS 里根本没有这一类
# —— 于是 guess_category 能返回它，生成出来的条目 lint 抓不到（lint 没做白名单校验），
# 只能等到人工 review 才发现。把白名单显式化 + 让 lint 校验，才能挡住同类错误。
VALID_CATEGORIES = {
    "domestic-general",
    "domestic-reasoning",
    "international-dense",
    "international-edge",
    "code",
    "vision",
    "embedding",
    "reranker",
    "decision",
}

CATEGORY_BY_TAG = {
    "text-generation": "domestic-general",   # 默认；后面用 namespace + size 区分
    "image-text-to-text": "vision",
    "sentence-similarity": "embedding",
    "text-to-image": "vision",               # 文生图没有独立类，按多模态归 vision
    "text-ranking": "reranker",
    "text-to-speech": "domestic-general",    # TTS 不在工具覆盖范围，先不收
    "automatic-speech-recognition": "domestic-general",
}

# 国内 namespace（Qwen 系 / DeepSeek / GLM / Kimi / MiniMax / 腾讯 / 混元 …）
DOMESTIC_NS = (
    "Qwen", "deepseek-ai", "THUDM", "moonshotai", "MiniMaxAI", "inclusionAI",
    "tencent", "Hunyuan", "01-ai", "zhipuai", "baai", "BAAI", "Alibaba-NLP",
)
# 国际 namespace
INTERNATIONAL_NS = (
    "meta-llama", "google", "mistralai", "microsoft", "EleutherAI", "apple",
    "CohereLabs", "NousResearch", "nvidia", "OpenGVLab", "sentence-transformers",
    "intfloat", "stabilityai", "openai", "openbmb", "lmms-lab", "microsoft",
    "THUDM",  # GLM 是国内，放国内；此行仅防误读，实际见 DOMESTIC_NS
)
INTERNATIONAL_NS = tuple(ns for ns in INTERNATIONAL_NS if ns not in DOMESTIC_NS)

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


def _param_b_from_name(base: str) -> float | None:
    """从模型名里抠参数量（B）。只用于分类判定（edge/dense 分界），不写进条目。

    与 guess_size_b 同源，但返回 float 便于比较；抠不到返回 None。
    """
    m = re.search(r"[-_](\d+(?:\.\d+)?)\s*([bBmM])\b", base)
    if not m:
        return None
    size, unit = float(m.group(1)), m.group(2).lower()
    return size / 1000 if unit == "m" else size


def _effective_b_for_tier(base: str) -> float | None:
    """MoE 用激活参、密集模型用总参 —— 决定 edge/dense 归属。

    "Nemotron-3-Nano-30B-A3B" 总参 31.58B 但激活 3B：按总参会误判成 dense
    （需要大机器），按激活参才是 edge（边缘设备友好）。与显存估算口径一致。
    """
    m = _MOE_ACTIVATED_RE.search(base)
    if m:
        return float(m.group(1))
    m4 = _MOE_LLAMA4_RE.search(base)
    if m4:
        return float(m4.group(1))
    return _param_b_from_name(base)


# edge / dense 的分界参数量（B）。低于此算边缘设备模型。
#
# 依据现有 KNOWN_MODELS 的真实分布（size_b 为总参）：
#   edge  : 1.0 / 1.0 / 3.0 / 3.8 / 3.97 / 4.0 / 7.0 / 8.03 / 9.0 / 14.0 / 20.91 / 31.58(MoE 激活 3B)
#   dense : 22.0 / 27.0 / 31.27 / 70.0 / 108.6 / 116.83 / 123.0 / 123.61 / 401.6 / 405.0 / 560.52
# 分界落在 20.91（edge）与 22.0（dense）之间 → 取 21.0。
#
# MoE 例外：Nemotron-Nano-30B-A3B 总参 31.58B 但激活仅 3B → 归 edge。
# 所以 MoE 按**激活参**判定（与显存估算口径一致，见 vram_requirements 的 moe_weight_rule）。
EDGE_MAX_B = 21.0

# 人工有意与通用规则不同的存量条目（repo → 分类）。
#
# 这些是 review 时按「家族定位」而不是「参数量」定的，启发式推不出来：
#   Llama-4-Maverick/Scout  → 旗舰模型（激活 17B 但总参 400B+）归 dense
#   Mistral-Large / Small-3  → 名字里没有参数量，抠不到，按家族定位归 dense
#   Nemotron-3-Super-120B    → 总参 123B 归 dense（虽然激活仅 12B）
#   gemma-2-9b-it            → 早期按 gemma-2 家族整体归 dense（gemma-3-9b 是 edge）
#
# 加进来是为了让「存量数据 = 人工结论」这件事有据可查，而不是靠启发式碰运气。
CATEGORY_OVERRIDES = {
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct": "international-dense",
    "meta-llama/Llama-4-Scout-17B-16E-Instruct": "international-dense",
    "mistralai/Mistral-Large-Instruct-2407": "international-dense",
    "mistralai/Mistral-Small-3": "international-dense",
    "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16": "international-dense",
    "google/gemma-2-9b-it": "international-dense",
}

# MoE 命名形态里的激活参：
#   -A3B / -A12B / -A55B   （Qwen3 / Nemotron / DeepSeek 风格）
#   -17B-128E              （Llama 4 风格：激活参 + 专家数）
_MOE_ACTIVATED_RE = re.compile(r"-A(\d+(?:\.\d+)?)B\b", re.IGNORECASE)
_MOE_LLAMA4_RE = re.compile(r"-(\d+(?:\.\d+)?)B-\d+E\b", re.IGNORECASE)


def guess_category(model_id: str, pipeline_tag: str) -> str:
    """映射到 9 大类。基于 namespace + 命名 + pipeline_tag 启发式。

    顺序有讲究：**先判功能类（embedding/reranker/code/vision），再判推理类，
    最后才按 namespace 分国内/国际**。反过来的话 embedding 模型会因为名字里
    带 "embed" 但 namespace 是 BAAI（国内）而被误判成通用模型。

    返回值保证落在 VALID_CATEGORIES 内 —— 见 VALID_CATEGORIES 的说明。
    """
    org = model_id.split("/", 1)[0]
    base = model_id.split("/", 1)[1].lower()
    name = model_id.lower()

    # 人工有意为之的例外优先于启发式
    override = CATEGORY_OVERRIDES.get(model_id)
    if override:
        return override

    # ---- 1. 功能类：靠命名（比 pipeline_tag 更可靠，HF 的 tag 常缺失）----
    if pipeline_tag == "sentence-similarity" or pipeline_tag == "text-ranking":
        return "reranker" if pipeline_tag == "text-ranking" else "embedding"
    if "reranker" in base or "rerank" in base:
        return "reranker"
    if "embed" in base or "gte-" in base or "-e5-" in base or "e5-" in base:
        return "embedding"
    # sentence-transformers 整库都是向量模型（名字里不一定带 embed）
    if org == "sentence-transformers":
        return "embedding"
    # bge-* 是 BAAI 的向量模型系列，但名字里没有 "embed"（bge-m3 / bge-base-zh-v1.5）
    if base.startswith("bge-") or base.startswith("bge_"):
        return "embedding"
    if pipeline_tag == "image-text-to-text" or any(
        k in base for k in ("-vl", "-vision", "-ocr", "-vlm")
    ):
        return "vision"
    # 视觉模型的名字不一定带 -vl：InternVL / MiniCPM-V / llava / Florence / Cosmos
    # / diffusiongemma / idefics / paligemma / pixtral / mllama
    if any(k in base for k in (
        "internvl", "minicpm-v", "llava", "florence", "cosmos", "diffusiongemma",
        "idefics", "paligemma", "pixtral", "mllama", "got-ocr", "qwen2-vl", "qwen2.5-vl",
        "hunyuanocr", "hunyuan-ocr", "gemma-4-26b", "gemma-4b",
    )):
        return "vision"
    if "coder" in base or "code" in base or "starcoder" in base:
        return "code"

    # ---- 2. 推理类（国内厂商的 reasoning 模型）----
    reasoning_markers = (
        "deepseek-r1", "qwq", "glm-z1", "magistral", "hunyuan-a13b",
    )
    if any(k in name for k in reasoning_markers):
        return "domestic-reasoning"
    # "-r1" 结尾或 "-reasoning" 结尾
    if re.search(r"[-_]r1\b", base) or "reasoning" in base:
        return "domestic-reasoning" if org in DOMESTIC_NS else "international-dense"

    # ---- 3. 按 namespace 分国内 / 国际 ----
    if org in DOMESTIC_NS:
        return "domestic-general"
    if org in INTERNATIONAL_NS:
        # 参数量决定 edge / dense；抠不到参数量（Embedding 之外的冷门模型）
        # 一律按 edge（更保守：不会把跑不动的模型标成 dense）
        size = _effective_b_for_tier(base)
        if size is None:
            return "international-edge"
        return "international-edge" if size < EDGE_MAX_B else "international-dense"

    # ---- 4. 未知 namespace：按 pipeline_tag 兜底，绝不返回表外分类 ----
    fallback = CATEGORY_BY_TAG.get(pipeline_tag, "domestic-general")
    return fallback if fallback in VALID_CATEGORIES else "domestic-general"


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

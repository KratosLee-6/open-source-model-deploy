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


def build_patch_entry(model_id: str, downloads: int, pipeline_tag: str, liked: int = 0) -> str:
    repo_id = model_id
    slug = repo_id.lower().replace("/", "-").replace("_", "-").replace(".", "-")
    cat = guess_category(model_id, pipeline_tag)
    size = guess_size_b(model_id)
    org, repo = repo_id.split("/", 1)
    note = f"Auto-fetched · {downloads / 1e6:.2f}M DLs · {liked} likes"
    if pipeline_tag == "sentence-similarity":
        note = f"Auto-fetched embedding · {downloads / 1e6:.2f}M DLs"
    elif pipeline_tag == "image-text-to-text":
        note = f"Auto-fetched vision · {downloads / 1e6:.2f}M DLs"
    elif pipeline_tag == "text-to-image":
        note = f"Auto-fetched image gen · {downloads / 1e6:.2f}M DLs"
    return (
        f'    "{slug}": {{\n'
        f'        "hf_repo": "{repo_id}",\n'
        f'        "github": "{org}/{repo}",\n'
        f'        "category": "{cat}",\n'
        f'        "size_b": {size},\n'
        f'        "_auto_fetched": {{\n'
        f'            "downloads": {downloads},\n'
        f'            "likes": {liked},\n'
        f'            "pipeline": "{pipeline_tag}",\n'
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
        print(f"# === auto_fetch_models.py patch · {len(candidates)} 条候选 ===")
        print("# 复制下列 { ... } 块到 src/core/model_resolver.py 的 KNOWN_MODELS 字典末尾")
        print("# 建议配合 --top=N 控制数量\n")
        for mid, info in candidates:
            print(build_patch_entry(mid, info["downloads"], info["pipeline"], info["likes"]))
            print()
        return


if __name__ == "__main__":
    main()

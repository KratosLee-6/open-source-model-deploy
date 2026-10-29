#!/usr/bin/env python3
"""
verify_decision_endpoints.py
逐个拉 12 个决策模型的 HF model card，提取「怎么起服务 / 接口路径 / 请求格式」。
只输出去重后的关键行，避免刷屏。
"""
import json
import re
import urllib.request

MODELS = [
    ("autotrust-jev-9b", "autotrust/JEV-9B"),
    ("autotrust-jev-27b", "autotrust/JEV-27B"),
    ("autotrust-jev-35b", "autotrust/JEV-35B"),
    ("cloudflare-clef-27b", "Cloudflare/clef"),
    ("cloudflare-clef-flash-9b", "Cloudflare/clef-flash"),
    ("convai-laya", "convaiinnovations/laya"),
    ("convai-laya-multilingual", "convaiinnovations/laya-multilingual"),
    ("openjev-openjev-27b", "openjev/openjev"),
    ("juspay-xor-35b", "juspay/xor"),
    ("doofz-thx-01", "doofz/THX-01"),
    ("mapika-decider-2b", "Mapika/decider-2b"),
    ("strands-decider-2b", "StrandsAgents/strands-decider-2B-hobson-v19"),
]

# 关键信号：接口路径 / 启动命令 / 客户端库
SIG = re.compile(
    r"/v1/(decide|systemone|chat|completions)|serve|ollama|sglang|vllm|pip install|"
    r"from_pretrained|JevClient|import |curl |requests\.(post|get)|localhost:|"
    r'noul|"kind"|probabilities|MCP|mcp',
    re.I,
)


def fetch(repo):
    url = f"https://huggingface.co/{repo}/raw/main/README.md"
    req = urllib.request.Request(url, headers={"User-Agent": "osm/4.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return f"__ERR__ {type(e).__name__}: {e}"


def extract(card):
    """提取代码块 + 含接口特征的行"""
    out = []
    # 1) 代码块（最能说明调用方式）
    blocks = re.findall(r"```(\w*)\n(.*?)```", card, re.S)
    for lang, body in blocks:
        b = body.strip()
        if not b:
            continue
        if SIG.search(b):
            # 只取前 14 行
            lines = b.split("\n")[:14]
            out.append(("code:" + (lang or "?"), "\n".join(lines)))
    # 2) 正文里明确写接口路径的行
    for line in card.split("\n"):
        s = line.strip()
        if not s or s.startswith("```"):
            continue
        if re.search(r"/v1/(decide|systemone)", s) or re.search(r"\bollama run\b|\bsglang\b.*serve", s, re.I):
            out.append(("prose", s[:200]))
    # 去重保序
    seen, uniq = set(), []
    for k, v in out:
        key = v[:120]
        if key in seen:
            continue
        seen.add(key)
        uniq.append((k, v))
    return uniq[:6]


results = {}
for slug, repo in MODELS:
    card = fetch(repo)
    print("=" * 78)
    print(f"{slug}   ({repo})")
    print("-" * 78)
    if card.startswith("__ERR__"):
        print(f"  ❌ {card[:120]}")
        results[slug] = {"repo": repo, "error": card[:120]}
        continue
    items = extract(card)
    if not items:
        print("  ⚠️ 没提取到接口信号（可能 card 太简或只有图表）")
        results[slug] = {"repo": repo, "items": []}
    for kind, body in items:
        print(f"  [{kind}]")
        for ln in body.split("\n"):
            print(f"    {ln[:150]}")
        print()
    results[slug] = {"repo": repo, "items": items}

with open(r"C:\Users\Admin\AppData\Local\Temp\decision_endpoints.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\n✅ 已存 decision_endpoints.json")

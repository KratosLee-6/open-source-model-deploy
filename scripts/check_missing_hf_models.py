"""对比 HF 主流开源模型 vs 当前 KNOWN_MODELS，找出 missing"""
import urllib.request, json

# 当前 48 个 KNOWN_MODELS（从 model_resolver.py）
known_hf_repos = {
    # 国内通用
    "deepseek-ai/DeepSeek-V3",
    "deepseek-ai/DeepSeek-V4.1-Flash",
    "deepseek-ai/DeepSeek-V2.5",
    "deepseek-ai/DeepSeek-R1",
    "THUDM/glm-4-9b-chat",
    "THUDM/glm-4-32b-0414",
    "moonshotai/Kimi-K2-Instruct",
    "Qwen/Qwen3-235B-A22B-Instruct-2507",
    "Qwen/Qwen3-32B",
    "Qwen/Qwen3-14B",
    "Qwen/Qwen3-8B",
    # 国内推理
    "THUDM/glm-z1-32b-0414",
    "Qwen/QwQ-32B-Preview",
    "Qwen/QwQ-32B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    # 代码
    "deepseek-ai/DeepSeek-Coder-V2-Instruct",
    "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
    "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "mistralai/Codestral-22B-v0.1",
    # 视觉
    "Qwen/Qwen2.5-VL-72B-Instruct",
    "Qwen/Qwen2.5-VL-7B-Instruct",
    "OpenGVLab/InternVL3-78B",
    "OpenGVLab/InternVL3-8B",
    "lmms-lab/llava-onevision-qwen2-7b-ov",
    # 国际密集
    "meta-llama/Llama-3.1-405B",
    "meta-llama/Llama-3.1-70B",
    "mistralai/Mistral-Large-2",
    "mistralai/Mistral-Small-3",
    "google/gemma-3-27b-it",
    # 国际边缘
    "meta-llama/Llama-3.2-1B",
    "meta-llama/Llama-3.2-3B",
    "google/gemma-3-9b-it",
    "google/gemma-3-4b-it",
    "microsoft/phi-4",
    "microsoft/Phi-4-mini-instruct",
    "microsoft/Phi-3.5-mini-instruct",
    # Embedding + Reranker
    "BAAI/bge-m3",
    "BAAI/bge-large-zh-v1.5",
    "Qwen/Qwen3-Embedding-8B",
    "Alibaba-NLP/gte-Qwen2-7B-instruct",
    "BAAI/bge-reranker-v2-m3",
}

# HF 主流候选
queries = [
    ("text-generation", 30),
    ("image-text-to-text", 20),
    ("sentence-similarity", 10),
    ("feature-extraction", 10),
]

candidates = []
for task, limit in queries:
    url = f"https://hf-mirror.com/api/models?pipeline_tag={task}&sort=downloads&direction=-1&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        for m in data:
            candidates.append((m["id"], task, m.get("downloads", 0), m.get("likes", 0)))
    except Exception as e:
        print(f"✗ {task}: {e}")

# Qwen 3.5/3.6/3.8 搜
for q in ["Qwen3.8", "Qwen3.6", "Qwen3.5"]:
    url = f"https://hf-mirror.com/api/models?search={q}&sort=downloads&direction=-1&limit=8"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        for m in data:
            if m["id"].startswith("Qwen/"):
                candidates.append((m["id"], f"qwen-3.{q[-1]}", m.get("downloads", 0), m.get("likes", 0)))
    except Exception as e:
        print(f"✗ {q}: {e}")

# 去重
seen = set(); uniq = []
for cid, tag, dl, lk in candidates:
    if cid not in seen and dl >= 100000:
        seen.add(cid); uniq.append((cid, tag, dl, lk))

# 对比 known：找 missing
missing = []
for cid, tag, dl, lk in uniq:
    # 检查是否在 known_hf_repos（不区分大小写）
    cid_lower = cid.lower()
    in_known = False
    for k in known_hf_repos:
        if k.lower() == cid_lower:
            in_known = True; break
    if not in_known:
        missing.append((cid, tag, dl, lk))

missing.sort(key=lambda x: -x[2])

print(f"\n{'='*95}")
print(f"当前 KNOWN_MODELS: {len(known_hf_repos)} 个")
print(f"HF 候选 (downloads>100K): {len(uniq)} 个")
print(f"**未覆盖主流模型: {len(missing)} 个**")
print(f"{'='*95}\n")

print(f"{'#':<3} {'HF Repo':<55} {'DLs':>10} {'Likes':>5}  类别")
print("-" * 95)
for i, (cid, tag, dl, lk) in enumerate(missing[:60], 1):
    print(f"{i:<3} {cid:<55} {dl:>10,} {lk:>5}  {tag}")

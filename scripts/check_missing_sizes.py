"""查剩余 missing 模型的精确 size_b + 类别"""
import urllib.request, json

QUERIES = [
    # Embedding 工业标准（缺）
    ("sentence-transformers/all-MiniLM-L6-v2", "embedding"),
    ("sentence-transformers/all-mpnet-base-v2", "embedding"),
    ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "embedding"),
    ("nomic-ai/nomic-embed-text-v1.5", "embedding"),
    ("intfloat/multilingual-e5-small", "embedding"),
    ("intfloat/multilingual-e5-base", "embedding"),
    ("intfloat/multilingual-e5-large", "embedding"),
    ("BAAI/bge-small-en-v1.5", "embedding"),
    ("BAAI/bge-base-en-v1.5", "embedding"),
    ("BAAI/bge-large-en-v1.5", "embedding"),
    ("BAAI/bge-small-zh-v1.5", "embedding"),
    ("BAAI/bge-base-zh-v1.5", "embedding"),
    # Reranker
    ("BAAI/bge-reranker-large", "reranker"),
    # OpenAI 开源
    ("openai/gpt-oss-20b", "international-edge"),
    ("openai/gpt-oss-120b", "international-dense"),
    # Google Gemma-4
    ("google/gemma-4-26B-A4B-it", "vision"),
    ("google/gemma-4-31B-it", "international-dense"),
    # Meta
    ("meta-llama/Llama-3.1-8B-Instruct", "international-edge"),
    # NVIDIA
    ("nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16", "international-edge"),
    # Qwen3-Embedding-0.6B (新)
    ("Qwen/Qwen3-Embedding-0.6B", "embedding"),
]

results = []
for hf_repo, category in QUERIES:
    url = f"https://hf-mirror.com/api/models/{hf_repo}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        st = data.get("safetensors", {})
        total_params = st.get("total", 0) if isinstance(st, dict) else 0
        size_b = round(total_params / 1e9, 2) if total_params else 0

        if size_b == 0:
            siblings = data.get("siblings", [])
            total = sum(s.get("size", 0) or 0 for s in siblings if s.get("rfilename", "").endswith((".safetensors", ".bin")))
            size_b = round(total / 1e9, 2)

        tags = data.get("tags", [])
        size_from_tag = 0
        for t in tags:
            if t.startswith("size:"):
                try: size_from_tag = float(t.split(":")[1].rstrip("B"))
                except: pass

        dls = data.get("downloads", 0)
        lks = data.get("likes", 0)
        lic = ""
        for t in tags:
            if t.startswith("license:"):
                lic = t.replace("license:", ""); break

        # 推断 activated_b（已知映射）
        activated_b = None
        if "A3B" in hf_repo: activated_b = 3
        elif "A4B" in hf_repo: activated_b = 4
        elif "A10B" in hf_repo: activated_b = 10
        elif "A17B" in hf_repo: activated_b = 17
        elif "A22B" in hf_repo: activated_b = 22

        final_size = size_b if size_b else size_from_tag
        results.append({
            "hf_repo": hf_repo,
            "size_b": final_size,
            "activated_b": activated_b,
            "category": category,
            "downloads": dls,
            "likes": lks,
            "license": lic,
        })
        print(f"✓ {hf_repo:<55} size={final_size}B activated={activated_b or '-'}B DLs={dls:,} lic={lic}")
    except Exception as e:
        print(f"✗ {hf_repo}: {e}")

out_path = "E:/工作/【汐构科技】/客户跟进/开源模型部署检测工具/open-source-model-deploy-clone/docs/missing-models.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n已写入 {out_path}: {len(results)} 条")

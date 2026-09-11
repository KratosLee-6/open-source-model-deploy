"""查 Qwen3.5/3.6/3.7/3.8 全家每个模型的精确 size_b + 官方类别"""
import urllib.request, json

QUERIES = [
    # (hf_repo, 期望类别)
    ("Qwen/Qwen3.5-0.8B", "domestic-general"),
    ("Qwen/Qwen3.5-2B", "domestic-general"),
    ("Qwen/Qwen3.5-4B", "domestic-general"),
    ("Qwen/Qwen3.5-9B", "domestic-general"),
    ("Qwen/Qwen3.5-27B", "domestic-general"),
    ("Qwen/Qwen3.5-35B-A3B", "domestic-general"),
    ("Qwen/Qwen3.5-122B-A10B", "domestic-general"),
    ("Qwen/Qwen3.5-397B-A17B", "domestic-general"),
    ("Qwen/Qwen3.6-27B", "domestic-general"),
    ("Qwen/Qwen3.6-35B-A3B", "domestic-general"),
    ("Qwen/Qwen3.7", "domestic-general"),
    ("Qwen/Qwen3.8-27B", "domestic-general"),
    ("Qwen/Qwen3-0.6B", "domestic-general"),
    ("Qwen/Qwen3-1.7B", "domestic-general"),
    ("Qwen/Qwen3-4B", "domestic-general"),
    ("Qwen/Qwen3-VL-2B-Instruct", "vision"),
    ("Qwen/Qwen3-VL-4B-Instruct", "vision"),
    ("Qwen/Qwen3-VL-8B-Instruct", "vision"),
    ("Qwen/Qwen3-VL-32B-Instruct", "vision"),
]

results = []
for hf_repo, category in QUERIES:
    url = f"https://hf-mirror.com/api/models/{hf_repo}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        # 抓 size: safetensors total / library / siblings 数
        st = data.get("safetensors", {})
        total_params = st.get("total", 0) if isinstance(st, dict) else 0
        size_b = round(total_params / 1e9, 2) if total_params else 0

        # 从 siblings 推断（如果 safetensors 没 total）
        if size_b == 0:
            siblings = data.get("siblings", [])
            total = sum(s.get("size", 0) or 0 for s in siblings if s.get("rfilename", "").endswith((".safetensors", ".bin")))
            size_b = round(total / 1e9, 2)

        # 从 tags 推断
        tags = data.get("tags", [])
        # 找 size tag
        size_from_tag = 0
        for t in tags:
            if t.startswith("size:"):
                # e.g., "size:4B" → 4
                try: size_from_tag = float(t.split(":")[1].rstrip("B"))
                except: pass

        dls = data.get("downloads", 0)
        lks = data.get("likes", 0)
        lm = data.get("lastModified", "")
        lic = ""
        for t in tags:
            if t.startswith("license:"):
                lic = t.replace("license:", ""); break

        # 推断 activated_b（MoE 标签或 sibling 中 .json 含 expert）
        is_moe = any("A" in hf_repo.split("-")[-1] and hf_repo.split("-")[-1].endswith("B") for _ in [1])
        # 更准：tags 含 moe
        is_moe = "moe" in tags

        # 推断 activated_b（已知映射：Qwen3.5-35B-A3B = 35B/3B 激活; 122B-A10B = 122B/10B; 397B-A17B = 397B/17B）
        activated_b = None
        if "A3B" in hf_repo: activated_b = 3
        elif "A10B" in hf_repo: activated_b = 10
        elif "A17B" in hf_repo: activated_b = 17
        elif "A22B" in hf_repo: activated_b = 22
        elif "A4B" in hf_repo: activated_b = 4

        # 决定最终 size_b（safetensors 优先）
        final_size = size_b if size_b else size_from_tag

        results.append({
            "hf_repo": hf_repo,
            "size_b": final_size,
            "activated_b": activated_b,
            "is_moe": is_moe,
            "category": category,
            "downloads": dls,
            "likes": lks,
            "license": lic,
            "last_modified": lm[:10] if lm else "",
            "note": data.get("cardData", {}).get("description", "")[:120],
        })
        print(f"✓ {hf_repo:<40} size={final_size}B activated={activated_b or '-'}B DLs={dls:,}")
    except Exception as e:
        print(f"✗ {hf_repo}: {e}")

# 写到 CSV
out_path = "E:/工作/【汐构科技】/客户跟进/开源模型部署检测工具/open-source-model-deploy-clone/docs/qwen3-models.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n已写入 {out_path}")

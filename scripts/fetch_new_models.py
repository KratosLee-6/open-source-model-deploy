#!/usr/bin/env python3
"""
fetch_new_models.py
为 v1.1.1 补充 2026-10 最新权威开源模型：拉 HF API 精确 size_b + 生成 KNOWN_MODELS 字典条目
"""
import json
import re
import urllib.request

# 目标模型（2026-08 之后发布 / 或高价值且仓库尚缺）
TARGETS = [
    # slug, hf_repo, github, category, note
    ("deepseek-v3.2", "deepseek-ai/DeepSeek-V3.2", "deepseek-ai/DeepSeek-V3.2", "domestic-general",
     "DeepSeek V3.2 正式版，HF 610 万下载，MoE 685B/37B 激活，对标前沿闭源"),
    ("qwen3.8-flash-next", "Qwen/Qwen3.8-Flash-Next", "QwenLM/Qwen3", "domestic-general",
     "Qwen3.8 Flash Next 新旗舰，HF 385 万下载，多模态 Flash 家族"),
    ("nemotron-3.5-lightning-30b-a3b", "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16",
     "nvidia/Nemotron", "domestic-general", "NVIDIA Nemotron 3.5 Lightning 30B MoE / 3B 激活"),
    ("nemotron-3-nano-30b-a3b", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
     "nvidia/Nemotron", "international-edge", "NVIDIA Nemotron 3 Nano 30B MoE / 3B 激活，边缘友好"),
    ("nemotron-3-ultra-550b", "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16",
     "nvidia/Nemotron", "international-dense", "NVIDIA Nemotron 3 Ultra 550B MoE / 55B 激活"),
    ("nemotron-3-super-120b", "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
     "nvidia/Nemotron", "international-dense", "NVIDIA Nemotron 3 Super 120B MoE / 12B 激活"),
    ("minicpm-v-4.7-35b-a3b", "openbmb/MiniCPM-V-4.7-35B-A3B", "OpenBMB/MiniCPM-V",
     "vision", "MiniCPM-V 4.7 35B MoE 多模态，国产视觉旗舰"),
    ("minicpm-v-4.7-1b", "openbmb/MiniCPM-V-4.7-1B", "OpenBMB/MiniCPM-V",
     "vision", "MiniCPM-V 4.7 1B 轻量多模态，6GB 卡可跑"),
    ("qwen3-vl-embedding-8b", "Qwen/Qwen3-VL-Embedding-8B", "QwenLM/Qwen3",
     "embedding", "Qwen3-VL Embedding 8B，多模态向量化新形态"),
    ("qwen3-vl-embedding-2b", "Qwen/Qwen3-VL-Embedding-2B", "QwenLM/Qwen3",
     "embedding", "Qwen3-VL Embedding 2B，多模态向量化轻量版"),
    ("deepseek-ocr", "deepseek-ai/DeepSeek-OCR", "deepseek-ai/DeepSeek-OCR",
     "vision", "DeepSeek-OCR 文档解析，HF 208 万下载"),
    ("hunyuan-ocr", "tencent/HunyuanOCR", "Tencent-Hunyuan/HunyuanOCR",
     "vision", "腾讯混元 OCR，文档版面解析"),
    ("diffusiongemma-26b-a4b", "google/diffusiongemma-26B-A4B-it", "google-deepmind/gemma",
     "vision", "Google DiffusionGemma 26B MoE / 4B 激活，扩散式多模态"),
    ("cosmos-reason2-2b", "nvidia/Cosmos-Reason2-2B", "nvidia/Cosmos-Reason2",
     "vision", "NVIDIA Cosmos Reason2 2B，物理世界推理小模型"),
    ("labse", "sentence-transformers/LaBSE", "UKPLab/sentence-transformers",
     "embedding", "LaBSE 跨语言句子对齐，82 语种，检索基础设施"),
    ("distiluse-base-multilingual-cased-v1", "sentence-transformers/distiluse-base-multilingual-cased-v1",
     "UKPLab/sentence-transformers", "embedding", "distilUSE 多语言 cased v1，15 语种基线"),
    ("qwen3-30b-a3b-instruct-2507", "Qwen/Qwen3-30B-A3B-Instruct-2507", "QwenLM/Qwen3",
     "domestic-general", "Qwen3 30B-A3B Instruct-2507，MoE / 3B 激活，109 万下载"),
    ("qwen2-vl-2b-instruct", "Qwen/Qwen2-VL-2B-Instruct", "QwenLM/Qwen2-VL",
     "vision", "Qwen2-VL 2B Instruct，前代多模态小尺寸"),
    ("minimax-m2.5", "MiniMaxAI/MiniMax-M2.5", "MiniMax-AI/MiniMax-M2",
     "domestic-general", "MiniMax M2.5，国产大模型旗舰"),
    ("hy3", "tencent/Hy3", "Tencent-Hunyuan/Hy3", "domestic-general",
     "腾讯混元 Hy3，通用大模型"),
]


# 已知 MoE 激活参数（模型名/README 权威，比 config 靠谱）
ACTIVATED = {
    "deepseek-ai/DeepSeek-V3.2": 37,
    "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16": 3,
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16": 3,
    "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16": 55,
    "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16": 12,
    "openbmb/MiniCPM-V-4.7-35B-A3B": 3,
    "google/diffusiongemma-26B-A4B-it": 4,
    "Qwen/Qwen3-30B-A3B-Instruct-2507": 3,
}


def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "osm-deploy-fetcher/4.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def params_from_safetensors(repo):
    """HF safetensors API 给出 total 参数量（最准）"""
    try:
        d = api(f"https://huggingface.co/api/models/{repo}?expand[]=safetensors")
        st = d.get("safetensors") or {}
        total = st.get("total")
        if total:
            return round(total / 1e9, 2), st.get("parameters", {})
    except Exception:
        pass
    return None, {}


def hf_info(repo):
    """拿 HF 上真实的参数规模（safetensors 索引优先，回落 tags）"""
    d = api(f"https://huggingface.co/api/models/{repo}")
    out = {
        "downloads": d.get("downloads", 0),
        "likes": d.get("likes", 0),
        "created": (d.get("createdAt") or "")[:10],
        "modified": (d.get("lastModified") or "")[:10],
        "tags": d.get("tags", []),
        "size_b": None,
        "activated_b": ACTIVATED.get(repo),
        "params": None,
    }
    size_b, _ = params_from_safetensors(repo)
    if size_b:
        out["size_b"] = size_b
        out["params"] = size_b
    else:
        # 从 tags 找参数规模
        for t in out["tags"]:
            m = re.match(r"^(\d+(?:\.\d+)?)B$", t)
            if m:
                out["params"] = float(m.group(1))
                out["size_b"] = float(m.group(1))
                break
    return out


print("=== 拉 HF 真实元数据 ===\n")
entries = []
for slug, repo, gh, cat, note in TARGETS:
    try:
        info = hf_info(repo)
    except Exception as e:
        print(f"  ❌ {repo}: {e}")
        continue
    print(f"  {repo}")
    print(f"      size_b={info['size_b']}  activated={info['activated_b']}  DL={info['downloads']:,}  "
          f"♥={info['likes']:,}  created={info['created']}")
    entries.append((slug, repo, gh, cat, note, info))

print(f"\n\n=== 生成 KNOWN_MODELS 条目（{len(entries)} 个）===\n")
blocks = []
for slug, repo, gh, cat, note, info in entries:
    size = info.get("size_b") or 0
    act = info.get("activated_b")
    lines = [
        f'    "{slug}": {{',
        f'        "hf_repo": "{repo}",',
        f'        "github": "{gh}",',
        f'        "category": "{cat}",',
        f'        "size_b": {size},',
    ]
    if act:
        lines.append(f'        "activated_b": {act},')
    lines.append(f'        "note": "{note}（HF {info["downloads"]/1e6:.1f}M DLs · {info["created"][:7]}）",')
    lines.append("    },")
    blocks.append("\n".join(lines))

out = "\n".join(blocks)
print(out)
with open(r"C:\Users\Admin\AppData\Local\Temp\kx-check\new_models_block.txt", "w", encoding="utf-8") as f:
    f.write(out)
print(f"\n✅ 已存 {len(blocks)} 条到 new_models_block.txt")

"""
自动扩充 KNOWN_MODELS 的脚本

用途：
1. 列出当前 47 模型清单 (基于 SKILL.md)
2. 对比 model_resolver.py 中的 KNOWN_MODELS，输出差异
3. 自动通过 HF API 拉取缺失模型的元数据，生成 model_resolver.py 的补丁
4. 输出本地部署建议报告

运行：python3 auto_expand_models.py [--mode=check|patch|recommend]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

# ============================================================
# 配置：47 个期望模型 + HF 路径 + GitHub 路径
# ============================================================
EXPECTED_MODELS = [
    # 国内通用（9）
    {"name": "deepseek-v3", "hf_repo": "deepseek-ai/DeepSeek-V3", "github": "deepseek-ai/DeepSeek-V3",
     "category": "domestic-general", "size_b": 685, "note": "MoE 685B/37B，对话旗舰"},
    {"name": "deepseek-v2.5", "hf_repo": "deepseek-ai/DeepSeek-V2.5", "github": "deepseek-ai/DeepSeek-V2.5",
     "category": "domestic-general", "size_b": 236, "note": "MoE 236B/21B"},
    {"name": "deepseek-r1", "hf_repo": "deepseek-ai/DeepSeek-R1", "github": "deepseek-ai/DeepSeek-R1",
     "category": "domestic-general", "size_b": 671, "note": "推理增强 R1"},
    {"name": "glm-4.5", "hf_repo": "THUDM/GLM-4-9B-chat" if False else "THUDM/glm-4-9b-chat",
     "github": "THUDM/GLM-4", "category": "domestic-general", "size_b": 9, "note": "智谱 GLM-4.5"},
    {"name": "glm-4-32b", "hf_repo": "THUDM/glm-4-32b-0414", "github": "THUDM/GLM-4",
     "category": "domestic-general", "size_b": 32, "note": "智谱 GLM-4 32B"},
    {"name": "kimi-k2", "hf_repo": "moonshotai/Kimi-K2-Instruct", "github": "moonshotai/Kimi-K2",
     "category": "domestic-general", "size_b": 1040, "note": "Moonshot 1T MoE"},
    {"name": "qwen3-235b-a22b", "hf_repo": "Qwen/Qwen3-235B-A22B-Instruct-2507",
     "github": "QwenLM/Qwen3", "category": "domestic-general", "size_b": 235, "note": "通义千问 3 235B MoE"},
    {"name": "qwen3-32b", "hf_repo": "Qwen/Qwen3-32B", "github": "QwenLM/Qwen3",
     "category": "domestic-general", "size_b": 32, "note": "通义千问 3 32B 密集"},
    {"name": "qwen3-14b", "hf_repo": "Qwen/Qwen3-14B", "github": "QwenLM/Qwen3",
     "category": "domestic-general", "size_b": 14, "note": "通义千问 3 14B"},
    {"name": "qwen3-8b", "hf_repo": "Qwen/Qwen3-8B", "github": "QwenLM/Qwen3",
     "category": "domestic-general", "size_b": 8, "note": "通义千问 3 8B 轻量"},

    # 国内推理（10）
    {"name": "glm-z1-32b", "hf_repo": "THUDM/glm-z1-32b-0414", "github": "THUDM/GLM-Z1",
     "category": "domestic-reasoning", "size_b": 32, "note": "智谱 Z1 推理"},
    {"name": "qwq-32b-preview", "hf_repo": "Qwen/QwQ-32B-Preview", "github": "QwenLM/QwQ",
     "category": "domestic-reasoning", "size_b": 32, "note": "通义千问 QwQ 预览"},
    {"name": "qwq-32b", "hf_repo": "Qwen/QwQ-32B", "github": "QwenLM/QwQ",
     "category": "domestic-reasoning", "size_b": 32, "note": "通义千问 QwQ 正式"},
    {"name": "deepseek-r1-distill-qwen-32b", "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
     "github": "deepseek-ai/DeepSeek-R1", "category": "domestic-reasoning", "size_b": 32,
     "note": "R1 蒸馏 Qwen 32B"},
    {"name": "deepseek-r1-distill-llama-70b", "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
     "github": "deepseek-ai/DeepSeek-R1", "category": "domestic-reasoning", "size_b": 70,
     "note": "R1 蒸馏 Llama 70B"},
    {"name": "deepseek-r1-distill-qwen-14b", "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
     "github": "deepseek-ai/DeepSeek-R1", "category": "domestic-reasoning", "size_b": 14,
     "note": "R1 蒸馏 Qwen 14B"},
    {"name": "deepseek-r1-distill-qwen-7b", "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
     "github": "deepseek-ai/DeepSeek-R1", "category": "domestic-reasoning", "size_b": 7,
     "note": "R1 蒸馏 Qwen 7B"},
    {"name": "deepseek-r1-distill-llama-8b", "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
     "github": "deepseek-ai/DeepSeek-R1", "category": "domestic-reasoning", "size_b": 8,
     "note": "R1 蒸馏 Llama 8B"},
    {"name": "deepseek-r1-distill-qwen-1.5b", "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
     "github": "deepseek-ai/DeepSeek-R1", "category": "domestic-reasoning", "size_b": 2,
     "note": "R1 蒸馏 Qwen 1.5B 极轻量"},

    # 代码专用（6）
    {"name": "deepseek-coder-v2", "hf_repo": "deepseek-ai/DeepSeek-Coder-V2-Instruct",
     "github": "deepseek-ai/DeepSeek-Coder-V2", "category": "code", "size_b": 236,
     "note": "MoE 236B/21B，代码专用"},
    {"name": "deepseek-coder-v2-lite", "hf_repo": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
     "github": "deepseek-ai/DeepSeek-Coder-V2", "category": "code", "size_b": 16,
     "note": "MoE 16B/2.4B，代码轻量"},
    {"name": "qwen3-coder-30b", "hf_repo": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
     "github": "QwenLM/Qwen3-Coder", "category": "code", "size_b": 30,
     "note": "通义千问 3 代码 30B"},
    {"name": "qwen2.5-coder-32b", "hf_repo": "Qwen/Qwen2.5-Coder-32B-Instruct",
     "github": "QwenLM/Qwen2.5-Coder", "category": "code", "size_b": 32,
     "note": "通义千问 2.5 代码 32B"},
    {"name": "qwen2.5-coder-7b", "hf_repo": "Qwen/Qwen2.5-Coder-7B-Instruct",
     "github": "QwenLM/Qwen2.5-Coder", "category": "code", "size_b": 7,
     "note": "通义千问 2.5 代码 7B"},
    {"name": "codestral-22b", "hf_repo": "mistralai/Codestral-22B-v0.1",
     "github": "mistralai/codestral", "category": "code", "size_b": 22,
     "note": "Mistral 代码 22B"},

    # 视觉多模态（5）
    {"name": "qwen2.5-vl-72b", "hf_repo": "Qwen/Qwen2.5-VL-72B-Instruct",
     "github": "QwenLM/Qwen2.5-VL", "category": "vision", "size_b": 72,
     "note": "通义千问 2.5 视觉 72B"},
    {"name": "qwen2.5-vl-7b", "hf_repo": "Qwen/Qwen2.5-VL-7B-Instruct",
     "github": "QwenLM/Qwen2.5-VL", "category": "vision", "size_b": 7,
     "note": "通义千问 2.5 视觉 7B"},
    {"name": "internvl3-78b", "hf_repo": "OpenGVLab/InternVL3-78B",
     "github": "OpenGVLab/InternVL", "category": "vision", "size_b": 78,
     "note": "书生·万象 78B"},
    {"name": "internvl3-8b", "hf_repo": "OpenGVLab/InternVL3-8B",
     "github": "OpenGVLab/InternVL", "category": "vision", "size_b": 8,
     "note": "书生·万象 8B"},
    {"name": "llava-onevision-qwen2-7b", "hf_repo": "lmms-lab/llava-onevision-qwen2-7b-ov",
     "github": "lmms-lab/LLaVA-OneVision", "category": "vision", "size_b": 7,
     "note": "LLaVA OneVision 7B"},

    # 国际密集（5）
    {"name": "llama-3.1-405b", "hf_repo": "meta-llama/Llama-3.1-405B-Instruct",
     "github": "meta-llama/llama-models", "category": "international-dense", "size_b": 405,
     "note": "Meta Llama 3.1 405B"},
    {"name": "llama-3.1-70b", "hf_repo": "meta-llama/Llama-3.1-70B-Instruct",
     "github": "meta-llama/llama-models", "category": "international-dense", "size_b": 70,
     "note": "Meta Llama 3.1 70B"},
    {"name": "mistral-large-2", "hf_repo": "mistralai/Mistral-Large-Instruct-2407",
     "github": "mistralai/mistral-finetune", "category": "international-dense", "size_b": 123,
     "note": "Mistral Large 2 123B"},
    {"name": "mistral-small-3", "hf_repo": "mistralai/Mistral-Small-24B-Instruct-2501",
     "github": "mistralai/mistral-finetune", "category": "international-dense", "size_b": 24,
     "note": "Mistral Small 3 24B"},
    {"name": "gemma-3-27b", "hf_repo": "google/gemma-3-27b-it",
     "github": "google-deepmind/gemma", "category": "international-dense", "size_b": 27,
     "note": "Google Gemma 3 27B"},

    # 国际边缘（7）
    {"name": "llama-3.2-1b", "hf_repo": "meta-llama/Llama-3.2-1B-Instruct",
     "github": "meta-llama/llama-models", "category": "international-edge", "size_b": 1,
     "note": "Meta Llama 3.2 1B 极轻量"},
    {"name": "llama-3.2-3b", "hf_repo": "meta-llama/Llama-3.2-3B-Instruct",
     "github": "meta-llama/llama-models", "category": "international-edge", "size_b": 3,
     "note": "Meta Llama 3.2 3B 轻量"},
    {"name": "gemma-3-9b", "hf_repo": "google/gemma-3-9b-it",
     "github": "google-deepmind/gemma", "category": "international-edge", "size_b": 9,
     "note": "Google Gemma 3 9B"},
    {"name": "gemma-3-4b", "hf_repo": "google/gemma-3-4b-it",
     "github": "google-deepmind/gemma", "category": "international-edge", "size_b": 4,
     "note": "Google Gemma 3 4B"},
    {"name": "phi-4", "hf_repo": "microsoft/phi-4",
     "github": "microsoft/PhiCookBook", "category": "international-edge", "size_b": 14,
     "note": "Microsoft Phi-4 14B"},
    {"name": "phi-4-mini", "hf_repo": "microsoft/Phi-4-mini-instruct",
     "github": "microsoft/PhiCookBook", "category": "international-edge", "size_b": 4,
     "note": "Microsoft Phi-4 mini 3.8B"},
    {"name": "phi-3.5-mini", "hf_repo": "microsoft/Phi-3.5-mini-instruct",
     "github": "microsoft/PhiCookBook", "category": "international-edge", "size_b": 2,
     "note": "Microsoft Phi-3.5 mini 2.7B"},

    # Embedding（4）
    {"name": "bge-m3", "hf_repo": "BAAI/bge-m3",
     "github": "FlagOpen/FlagEmbedding", "category": "embedding", "size_b": 0.6,
     "note": "BGE 多语言 Embedding"},
    {"name": "bge-large-zh-v1.5", "hf_repo": "BAAI/bge-large-zh-v1.5",
     "github": "FlagOpen/FlagEmbedding", "category": "embedding", "size_b": 0.3,
     "note": "BGE 中文 Embedding v1.5"},
    {"name": "qwen3-embedding-8b", "hf_repo": "Qwen/Qwen3-Embedding-8B",
     "github": "QwenLM/Qwen3-Embedding", "category": "embedding", "size_b": 8,
     "note": "Qwen3 Embedding 8B"},
    {"name": "gte-qwen2-7b-instruct", "hf_repo": "Alibaba-NLP/gte-Qwen2-7B-instruct",
     "github": "Alibaba-NLP/gte", "category": "embedding", "size_b": 7,
     "note": "阿里 GTE Qwen2 7B Embedding"},

    # Reranker（1）
    {"name": "bge-reranker-v2-m3", "hf_repo": "BAAI/bge-reranker-v2-m3",
     "github": "FlagOpen/FlagEmbedding", "category": "reranker", "size_b": 0.6,
     "note": "BGE 多语言 Reranker"},
]

HF_API_BASE = "https://huggingface.co/api"
HF_MIRROR = "https://hf-mirror.com/api"
TIMEOUT = 15


def http_get_json(url: str, timeout: int = TIMEOUT) -> Optional[Any]:
    """带镜像 fallback 的 GET 请求"""
    bases = [url, url.replace(HF_API_BASE, HF_MIRROR)]
    last_err = None
    for try_url in bases:
        req = urllib.request.Request(try_url, headers={"User-Agent": "auto-expand/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
            last_err = e
            continue
    return None


def fetch_hf_metadata(repo_id: str) -> Optional[Dict[str, Any]]:
    """拉取 HF 模型元数据"""
    return http_get_json(f"{HF_API_BASE}/models/{repo_id}")


def fetch_gguf_files(repo_id: str) -> Optional[List[Dict[str, Any]]]:
    """列出 GGUF 文件清单"""
    files = http_get_json(f"{HF_API_BASE}/models/{repo_id}/tree/main?recursive=true")
    if not files:
        return None
    return [f for f in files if isinstance(f, dict)
            and f.get("type") == "file" and f["path"].endswith(".gguf")
            and not f["path"].startswith("mmproj")]


def extract_size_b_from_metadata(meta: Dict[str, Any]) -> Optional[float]:
    """从 HF metadata 估算参数规模"""
    # HF 的 safetensors.index.json 里有 metadata.size，但不能直接通过 API 拿
    # 简化策略：从 tags 推断
    tags = meta.get("tags", [])
    # 例如 "8B", "70B" 在 tags 末尾
    for t in tags:
        m = re.match(r"^(\d+(?:\.\d+)?)[BM]$", t)
        if m:
            return float(m.group(1))
    return None


# ============================================================
# mode = check  ：只对比，不改文件
# mode = patch  ：生成补丁到 stdout，可重定向覆盖 model_resolver.py
# mode = recommend：对每模型生成部署建议
# ============================================================

def parse_resolver(resolver_path: str) -> Dict[str, Dict[str, Any]]:
    """提取当前 KNOWN_MODELS 字典

    实现：找到 KNOWN_MODELS = { ... } 块，逐行扫描 "name": { 起
    的键，提取后续 4 个字段 (hf_repo, github, category, size_b, note)，
    直到遇到下一个 "  "xxxx": { 或字典结束。
    """
    with open(resolver_path, encoding="utf-8") as f:
        content = f.read()
    # 兼容多种写法：KNOWN_MODELS = { ... } 或 KNOWN_MODELS: Dict[...] = { ... }
    m = re.search(r"KNOWN_MODELS[^=]*=\s*\{(.+?)\n\}\n", content, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    result = {}
    # 找 "name": { 入口
    entry_starts = list(re.finditer(r'^\s*"([^"]+)":\s*\{', block, re.MULTILINE))
    for i, em in enumerate(entry_starts):
        name = em.group(1)
        # 跳过分类标题（不含 hf_repo）
        # 看从这个 name 开始到下一个 name 或文件结束的块
        next_start = entry_starts[i + 1].start() if i + 1 < len(entry_starts) else len(block)
        chunk = block[em.end():next_start]
        # 从 chunk 提取 hf_repo/github/category/size_b/note
        m_hf = re.search(r'"hf_repo":\s*"([^"]+)"', chunk)
        m_gh = re.search(r'"github":\s*"([^"]+)"', chunk)
        m_cat = re.search(r'"category":\s*"([^"]+)"', chunk)
        m_sz = re.search(r'"size_b":\s*([\d.]+)', chunk)
        m_note = re.search(r'"note":\s*"([^"]+)"', chunk)
        if m_hf:
            result[name] = {
                "hf_repo": m_hf.group(1),
                "github": m_gh.group(1) if m_gh else "",
                "category": m_cat.group(1) if m_cat else "",
                "size_b": float(m_sz.group(1)) if m_sz else 0,
                "note": m_note.group(1) if m_note else "",
            }
    return result


def mode_check(resolver_path: str):
    """对比当前 model_resolver.py 与期望清单"""
    current = parse_resolver(resolver_path)
    expected_names = {m["name"] for m in EXPECTED_MODELS}

    print(f"=== KNOWN_MODELS 完整性检查 ===\n")
    print(f"当前 model_resolver.py: {len(current)} 个")
    print(f"期望清单: {len(EXPECTED_MODELS)} 个 (SKILL.md 声称 47)\n")

    cur_names = set(current.keys())
    missing = expected_names - cur_names
    extra = cur_names - expected_names

    if missing:
        print(f"[缺失 {len(missing)} 个]")
        for m in EXPECTED_MODELS:
            if m["name"] in missing:
                print(f"  - {m['name']:<35} {m['category']:<22} {m['note']}")
    else:
        print("✓ 无缺失")

    if extra:
        print(f"\n[多余 {len(extra)} 个]")
        for n in sorted(extra):
            print(f"  - {n}")

    print(f"\n=== 建议 ===")
    if missing:
        print("→ 运行 `python3 auto_expand_models.py --mode=patch` 生成补丁")
    else:
        print("✓ KNOWN_MODELS 已完整")


def mode_patch(resolver_path: str):
    """为缺失模型生成补丁"""
    current = parse_resolver(resolver_path)
    expected_names = {m["name"] for m in EXPECTED_MODELS}
    cur_names = set(current.keys())
    missing = [m for m in EXPECTED_MODELS if m["name"] not in cur_names]

    if not missing:
        print("# 无缺失模型，跳过补丁生成")
        return

    print(f"# 自动补丁：缺失 {len(missing)} 个模型")
    print(f"# 追加位置：model_resolver.py 的 KNOWN_MODELS 字典内")
    print(f"# 格式：python3 auto_expand_models.py --mode=patch > patch.py\n")

    for m in missing:
        print(f'''    "{m['name']}": {{
        "hf_repo": "{m['hf_repo']}",
        "github": "{m['github']}",
        "category": "{m['category']}",
        "size_b": {m['size_b']},
        "note": "{m['note']}",
    }},''')


def mode_recommend(target_user: str = "default"):
    """生成部署建议"""
    print(f"=== 本地部署建议（target={target_user}）===\n")
    scenarios = {
        "default": "常规笔记本 16GB / 无独显",
        "consumer-gpu": "RTX 4090 (24GB)",
        "studio": "2× RTX 4090 / A100 80G",
        "cloud": "云租按量（H100/A100）",
    }
    print(f"适用场景: {scenarios.get(target_user, target_user)}\n")

    for cat in ["domestic-general", "domestic-reasoning", "code", "vision",
                "international-dense", "international-edge", "embedding", "reranker"]:
        print(f"\n[{cat}]")
        for m in EXPECTED_MODELS:
            if m["category"] != cat:
                continue
            sb = m["size_b"]
            # 内存预估：fp16 = 2B/param × size_b × 1e9 = 2*size_b GB；Q4 量化约 0.5B/param
            fp16_gb = round(2 * sb, 1)
            q4_gb = round(0.5 * sb, 1)
            # 推荐档位
            if target_user == "default":
                if sb <= 3:
                    tier = "✓ CPU 即可"
                    frame = "llama.cpp / Ollama"
                elif sb <= 8:
                    tier = "⚠ Q4 量化 4-8GB"
                    frame = "llama.cpp Q4 / Ollama"
                else:
                    tier = "❌ 需 GPU"
                    frame = "vLLM / 云租"
            elif target_user == "consumer-gpu":
                if sb <= 30:
                    tier = f"✓ FP16 量化 {fp16_gb}GB (1× 4090)"
                    frame = "vLLM / llama.cpp"
                elif sb <= 70:
                    tier = f"⚠ Q4 量化 {q4_gb}GB (1× 4090)"
                    frame = "vLLM"
                else:
                    tier = "❌ 需云租"
                    frame = "云租 H100"
            else:
                tier = "需要详细评估"
                frame = "vLLM"

            print(f"  {m['name']:<35} size={sb}B  fp16≈{fp16_gb}GB  q4≈{q4_gb}GB  {tier}  [{frame}]")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["check", "patch", "recommend"], default="check")
    parser.add_argument("--resolver", default="E:/工作/【汐构科技】/客户跟进/开源模型部署检测工具/red-skill-upload-clean/src/core/model_resolver.py")
    parser.add_argument("--target", default="default",
                        choices=["default", "consumer-gpu", "studio", "cloud"])
    args = parser.parse_args()

    if args.mode == "check":
        mode_check(args.resolver)
    elif args.mode == "patch":
        mode_patch(args.resolver)
    elif args.mode == "recommend":
        mode_recommend(args.target)


if __name__ == "__main__":
    main()
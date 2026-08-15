"""
步骤 1: 锁定模型
- 接收模型标识（HF repo 或模型名）
- 拉取 HF 元数据 + 官方 README + arXiv 论文
- 输出标准化的模型身份字典
"""
import re
from typing import Dict, Any, Optional

from ..data_sources import huggingface as hf
from ..data_sources import github_raw as gh
from ..data_sources import arxiv as arx


# 内置主流模型识别表（org/repo + GitHub org/repo + arxiv_id）
# 持续扩展中 - 欢迎 PR 添加新模型
KNOWN_MODELS: Dict[str, Dict[str, str]] = {
    # ===== DeepSeek 系列 =====
    "deepseek-v3": {
        "hf_repo": "deepseek-ai/DeepSeek-V3",
        "github": "deepseek-ai/DeepSeek-V3",
        "arxiv_id": "2412.19437",
        "category": "domestic-general",
        "size_b": 671,
        "activated_b": 37,
        "note": "MoE 671B，激活 37B，对标 GPT-4o",
    },
    "deepseek-r1": {
        "hf_repo": "deepseek-ai/DeepSeek-R1",
        "github": "deepseek-ai/DeepSeek-R1",
        "arxiv_id": "2501.12948",
        "category": "domestic-reasoning",
        "size_b": 671,
        "activated_b": 37,
        "note": "推理强化版，对标 OpenAI-o1",
    },
    "deepseek-v2.5": {
        "hf_repo": "deepseek-ai/DeepSeek-V2.5",
        "github": "deepseek-ai/DeepSeek-V2.5",
        "category": "domestic-general",
        "size_b": 236,
        "activated_b": 21,
        "note": "上一代 MoE，硬件门槛较低",
    },
    # ===== Qwen 系列（阿里）=====
    "qwen3-235b-a22b": {
        "hf_repo": "Qwen/Qwen3-235B-A22B",
        "github": "QwenLM/Qwen3",
        "category": "domestic-general",
        "size_b": 235,
        "activated_b": 22,
        "note": "MoE 235B/22B，Qwen3 旗舰",
    },
    "qwen3-32b": {
        "hf_repo": "Qwen/Qwen3-32B",
        "github": "QwenLM/Qwen3",
        "category": "domestic-general",
        "size_b": 32,
        "note": "32B 密集模型，性价比首选",
    },
    "qwen3-14b": {
        "hf_repo": "Qwen/Qwen3-14B",
        "github": "QwenLM/Qwen3",
        "category": "domestic-general",
        "size_b": 14,
        "note": "中等规模",
    },
    "qwen3-8b": {
        "hf_repo": "Qwen/Qwen3-8B",
        "github": "QwenLM/Qwen3",
        "category": "domestic-general",
        "size_b": 8,
        "note": "单卡 4090 友好",
    },
    "qwq-32b-preview": {
        "hf_repo": "Qwen/QwQ-32B-Preview",
        "github": "QwenLM/QwQ",
        "category": "domestic-reasoning",
        "size_b": 32,
        "note": "32B 推理预览版",
    },
    # ===== GLM 系列（智谱）=====
    "glm-4.5": {
        "hf_repo": "THUDM/GLM-4.5",
        "github": "THUDM/GLM-4",
        "category": "domestic-general",
        "size_b": 355,  # 估计值
        "activated_b": 32,  # 估计值
        "note": "智谱新一代旗舰",
    },
    "glm-4-32b": {
        "hf_repo": "THUDM/glm-4-32b-0414",
        "github": "THUDM/GLM-4",
        "category": "domestic-general",
        "size_b": 32,
        "note": "32B 上一代主力",
    },
    "glm-z1-32b": {
        "hf_repo": "THUDM/GLM-Z1-32B-0414",
        "github": "THUDM/GLM-4",
        "category": "domestic-reasoning",
        "size_b": 32,
        "note": "智谱推理模型",
    },
    # ===== Kimi（月之暗面）=====
    "kimi-k2": {
        "hf_repo": "moonshotai/Kimi-K2-Instruct",
        "github": "MoonshotAI/Kimi-K2",
        "category": "domestic-general",
        "size_b": 1000,  # MoE 1T
        "activated_b": 32,  # 估计值
        "note": "MoE 1T 超大规模",
    },
    # ===== 国际开源：Meta Llama =====
    "llama-3.1-405b": {
        "hf_repo": "meta-llama/Llama-3.1-405B",
        "github": "meta-llama/llama-models",
        "arxiv_id": "2407.21783",
        "category": "international-dense",
        "size_b": 405,
        "note": "Llama 3.1 旗舰，密集模型",
    },
    "llama-3.1-70b": {
        "hf_repo": "meta-llama/Llama-3.1-70B",
        "github": "meta-llama/llama-models",
        "category": "international-dense",
        "size_b": 70,
        "note": "70B 中大规模",
    },
    "llama-3.2-3b": {
        "hf_repo": "meta-llama/Llama-3.2-3B",
        "github": "meta-llama/llama-models",
        "category": "international-edge",
        "size_b": 3,
        "note": "边缘部署友好",
    },
    "llama-3.2-1b": {
        "hf_repo": "meta-llama/Llama-3.2-1B",
        "github": "meta-llama/llama-models",
        "category": "international-edge",
        "size_b": 1,
        "note": "极致轻量",
    },
    # ===== Mistral =====
    "mistral-large-2": {
        "hf_repo": "mistralai/Mistral-Large-Instruct-2407",
        "github": "mistralai/mistral-finetune",
        "category": "international-dense",
        "size_b": 123,
        "note": "Mistral 旗舰",
    },
    "mistral-small-3": {
        "hf_repo": "mistralai/Mistral-Small-3",
        "github": "mistralai/mistral-finetune",
        "category": "international-dense",
        "size_b": 22,
        "note": "Mistral 中等规模",
    },
    # ===== Gemma（Google）=====
    "gemma-3-27b": {
        "hf_repo": "google/gemma-3-27b-it",
        "github": "google-deepmind/gemma",
        "category": "international-dense",
        "size_b": 27,
        "note": "Gemma 3 中等规模",
    },
    "gemma-3-9b": {
        "hf_repo": "google/gemma-3-9b-it",
        "github": "google-deepmind/gemma",
        "category": "international-edge",
        "size_b": 9,
        "note": "Gemma 3 轻量",
    },
    "gemma-3-4b": {
        "hf_repo": "google/gemma-3-4b-it",
        "github": "google-deepmind/gemma",
        "category": "international-edge",
        "size_b": 4,
        "note": "边缘/移动友好",
    },
    # ===== Phi（Microsoft）=====
    "phi-4": {
        "hf_repo": "microsoft/phi-4",
        "github": "microsoft/PhiCookBook",
        "arxiv_id": "2412.08905",
        "category": "international-edge",
        "size_b": 14,
        "note": "Microsoft 14B 强推理",
    },
    "phi-4-mini": {
        "hf_repo": "microsoft/Phi-4-mini-instruct",
        "github": "microsoft/PhiCookBook",
        "category": "international-edge",
        "size_b": 3.8,
        "note": "3.8B 极致轻量",
    },
    "phi-3.5-mini": {
        "hf_repo": "microsoft/Phi-3.5-mini-instruct",
        "github": "microsoft/PhiCookBook",
        "category": "international-edge",
        "size_b": 3.8,
        "note": "上一代 3.8B",
    },

    # ===== 代码专用模型 =====
    "deepseek-coder-v2": {
        "hf_repo": "deepseek-ai/DeepSeek-Coder-V2-Instruct",
        "github": "deepseek-ai/DeepSeek-Coder-V2",
        "arxiv_id": "2406.11931",
        "category": "code",
        "size_b": 236,
        "activated_b": 21,
        "note": "MoE 236B/21B，代码专用旗舰",
    },
    "deepseek-coder-v2-lite": {
        "hf_repo": "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        "github": "deepseek-ai/DeepSeek-Coder-V2",
        "category": "code",
        "size_b": 16,
        "activated_b": 2.4,
        "note": "MoE 16B/2.4B，轻量代码模型",
    },
    "qwen3-coder-30b": {
        "hf_repo": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "github": "QwenLM/Qwen3-Coder",
        "category": "code",
        "size_b": 30,
        "activated_b": 3,
        "note": "MoE 30B/3B，Qwen3 代码版",
    },
    "qwen2.5-coder-32b": {
        "hf_repo": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "github": "QwenLM/Qwen2.5-Coder",
        "category": "code",
        "size_b": 32,
        "note": "32B 上一代代码模型",
    },
    "qwen2.5-coder-7b": {
        "hf_repo": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "github": "QwenLM/Qwen2.5-Coder",
        "category": "code",
        "size_b": 7,
        "note": "7B 单卡 4090 友好",
    },
    "codestral-22b": {
        "hf_repo": "mistralai/Codestral-22B-v0.1",
        "github": "mistralai/codestral",
        "category": "code",
        "size_b": 22,
        "note": "Mistral 代码模型",
    },

    # ===== 多模态模型（视觉/语音）=====
    "qwen2.5-vl-72b": {
        "hf_repo": "Qwen/Qwen2.5-VL-72B-Instruct",
        "github": "QwenLM/Qwen2.5-VL",
        "category": "vision",
        "size_b": 72,
        "note": "Qwen2.5 视觉旗舰",
    },
    "qwen2.5-vl-7b": {
        "hf_repo": "Qwen/Qwen2.5-VL-7B-Instruct",
        "github": "QwenLM/Qwen2.5-VL",
        "category": "vision",
        "size_b": 7,
        "note": "Qwen2.5 视觉轻量",
    },
    "internvl3-78b": {
        "hf_repo": "OpenGVLab/InternVL3-78B",
        "github": "OpenGVLab/InternVL",
        "category": "vision",
        "size_b": 78,
        "note": "InternVL3 旗舰",
    },
    "internvl3-8b": {
        "hf_repo": "OpenGVLab/InternVL3-8B",
        "github": "OpenGVLab/InternVL",
        "category": "vision",
        "size_b": 8,
        "note": "InternVL3 轻量",
    },
    "llava-onevision-qwen2-7b": {
        "hf_repo": "lmms-lab/llava-onevision-qwen2-7b-ov",
        "github": "lmms-lab/LLaVA-OneVision",
        "category": "vision",
        "size_b": 7,
        "note": "LLaVA-OneVision 视觉",
    },

    # ===== Embedding / Reranker 模型 =====
    "bge-m3": {
        "hf_repo": "BAAI/bge-m3",
        "github": "FlagOpen/FlagEmbedding",
        "category": "embedding",
        "size_b": 0.6,  # 568M
        "note": "BGE 多语言 Embedding",
    },
    "bge-large-zh-v1.5": {
        "hf_repo": "BAAI/bge-large-zh-v1.5",
        "github": "FlagOpen/FlagEmbedding",
        "category": "embedding",
        "size_b": 0.3,  # 326M
        "note": "BGE 中文 Embedding",
    },
    "bge-reranker-v2-m3": {
        "hf_repo": "BAAI/bge-reranker-v2-m3",
        "github": "FlagOpen/FlagEmbedding",
        "category": "reranker",
        "size_b": 0.6,  # 568M
        "note": "BGE 多语言 Reranker",
    },
    "qwen3-embedding-8b": {
        "hf_repo": "Qwen/Qwen3-Embedding-8B",
        "github": "QwenLM/Qwen3-Embedding",
        "category": "embedding",
        "size_b": 8,
        "note": "Qwen3 Embedding 8B",
    },
    "gte-qwen2-7b-instruct": {
        "hf_repo": "Alibaba-NLP/gte-Qwen2-7B-instruct",
        "github": "Alibaba-NLP/gte-Qwen",
        "category": "embedding",
        "size_b": 7,
        "note": "阿里 GTE Embedding",
    },

    # ===== 推理专项模型（OpenAI-o1 类）=====
    "qwq-32b": {
        "hf_repo": "Qwen/QwQ-32B",
        "github": "QwenLM/QwQ",
        "category": "domestic-reasoning",
        "size_b": 32,
        "note": "Qwen 32B 推理模型（正式版）",
    },
    "deepseek-r1-distill-qwen-32b": {
        "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "github": "deepseek-ai/DeepSeek-R1",
        "category": "domestic-reasoning",
        "size_b": 32,
        "note": "DeepSeek R1 蒸馏到 Qwen-32B，性价比首选",
    },
    "deepseek-r1-distill-llama-70b": {
        "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "github": "deepseek-ai/DeepSeek-R1",
        "category": "domestic-reasoning",
        "size_b": 70,
        "note": "DeepSeek R1 蒸馏到 Llama-70B",
    },
    "deepseek-r1-distill-qwen-14b": {
        "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        "github": "deepseek-ai/DeepSeek-R1",
        "category": "domestic-reasoning",
        "size_b": 14,
        "note": "DeepSeek R1 蒸馏到 Qwen-14B",
    },
    "deepseek-r1-distill-qwen-7b": {
        "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "github": "deepseek-ai/DeepSeek-R1",
        "category": "domestic-reasoning",
        "size_b": 7,
        "note": "DeepSeek R1 蒸馏到 Qwen-7B，单卡 4090 友好",
    },
    "deepseek-r1-distill-llama-8b": {
        "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        "github": "deepseek-ai/DeepSeek-R1",
        "category": "domestic-reasoning",
        "size_b": 8,
        "note": "DeepSeek R1 蒸馏到 Llama-8B",
    },
    "deepseek-r1-distill-qwen-1.5b": {
        "hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        "github": "deepseek-ai/DeepSeek-R1",
        "category": "domestic-reasoning",
        "size_b": 1.5,
        "note": "DeepSeek R1 蒸馏到 Qwen-1.5B，CPU 也能跑",
    },
}


def resolve_model(model_name: str, force: bool = False) -> Dict[str, Any]:
    """主入口：解析模型标识，返回完整身份信息

    Args:
        model_name: 模型名（支持别名如 "deepseek-v3"、"DeepSeek-V3"、"deepseek-ai/DeepSeek-V3"）

    Returns:
        {
          "input": "deepseek-v3",
          "hf_repo": "deepseek-ai/DeepSeek-V3",
          "github_org": "deepseek-ai",
          "github_repo": "DeepSeek-V3",
          "arxiv_id": "2412.19437",
          "hf_metadata": {...},  # 动态拉取
          "readme": "...",      # 动态拉取
          "arxiv_paper": {...}, # 动态拉取
        }
    """
    key = model_name.lower().strip()
    info = KNOWN_MODELS.get(key, {})

    # 如果不在内置表，尝试当作 HF repo 直接处理
    if not info and "/" in model_name:
        info = {
            "hf_repo": model_name,
            "github_org": model_name.split("/")[0],
            "github_repo": model_name.split("/")[1],
        }

    if not info or "hf_repo" not in info:
        raise ValueError(
            f"Unknown model: {model_name}. "
            f"Add it to KNOWN_MODELS in src/core/model_resolver.py "
            f"or pass as 'org/repo' (HF format)."
        )

    result = {
        "input": model_name,
        "hf_repo": info["hf_repo"],
        "github_org": info.get("github_org", info["hf_repo"].split("/")[0]),
        "github_repo": info.get("github_repo", info["hf_repo"].split("/")[1]),
        "arxiv_id": info.get("arxiv_id"),
        "category": info.get("category"),
        "size_b": info.get("size_b"),
        "activated_b": info.get("activated_b"),
        "note": info.get("note"),
    }

    # 动态拉取
    try:
        result["hf_metadata"] = hf.fetch_model_metadata(info["hf_repo"], force=force)
    except Exception as e:
        result["hf_metadata_error"] = str(e)

    try:
        result["readme"] = hf.fetch_model_readme(info["hf_repo"], force=force)
    except Exception as e:
        result["readme_error"] = str(e)

    if result["arxiv_id"]:
        try:
            result["arxiv_paper"] = arx.fetch_by_id(result["arxiv_id"], force=force)
        except Exception as e:
            result["arxiv_error"] = str(e)

    # 顺手抓 GGUF 文件（如果有 GGUF 仓库）
    gguf_repo = _detect_gguf_repo(info["hf_repo"])
    if gguf_repo:
        try:
            result["gguf_files"] = hf.fetch_gguf_files(gguf_repo, force=force)
            result["gguf_repo"] = gguf_repo
        except Exception as e:
            result["gguf_error"] = str(e)

    return result


def _detect_gguf_repo(hf_repo: str) -> Optional[str]:
    """检测社区 GGUF 仓库（bartowski、unsloth 等通常会量化）

    规则: 在基础名后追加 -GGUF，常见量化者前缀列表
    """
    quantizers = ["bartowski", "unsloth", "TheBloke", "mradermacher", "lmstudio-community"]
    base_name = hf_repo.split("/")[-1] + "-GGUF"
    # 简化：直接返回可能的 GGUF 仓库（实际使用时可多次探测）
    for q in quantizers:
        candidate = f"{q}/{base_name}"
        # 这里只返回第一个候选，由调用方 try/except 处理
        return candidate
    return None


def extract_params_from_readme(readme: str) -> Dict[str, Any]:
    """从 README 抽取关键参数（参数、上下文、量化等）"""
    info = {}
    if not readme:
        return info

    # 参数规模
    m = re.search(r"(\d+(?:\.\d+)?)\s*[Bb](?:\s+(?:total|activated))?", readme)
    if m:
        info["size_b_hint"] = float(m.group(1))

    # 上下文
    m = re.search(r"(\d+)[Kk]\s*(?:context|tokens?)?", readme)
    if m:
        info["context_k_hint"] = int(m.group(1))

    # 协议
    for lic in ["MIT", "Apache 2.0", "Apache-2.0", "Llama 3 Community License", "DeepSeek License"]:
        if lic.lower() in readme.lower():
            info["license_hint"] = lic
            break

    return info

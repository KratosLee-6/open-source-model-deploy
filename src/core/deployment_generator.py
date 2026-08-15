"""
部署脚本生成器 - 按硬件 + 模型生成一键启动命令
支持：vLLM / SGLang / Ollama / llama.cpp / Transformers
"""
from typing import Dict, List, Any


def generate_deploy_script(
    model_name: str,
    model_info: Dict[str, Any],
    hw_scan: Dict[str, Any],
    framework: str = "auto",
) -> Dict[str, Any]:
    """生成部署脚本

    Args:
        model_name: 模型名（如 "qwen3-32b"）
        model_info: KNOWN_MODELS 中的 info
        hw_scan: full_hardware_scan() 输出
        framework: 强制指定框架（vllm/sglang/ollama/llama.cpp/auto）

    Returns:
        {
          "framework": "vllm",
          "install_cmd": "pip install vllm",
          "run_cmd": "vllm serve Qwen/Qwen3-32B --gpu-memory-utilization 0.9",
          "docker_cmd": "docker run ...",  # 可选
          "notes": ["需要 CUDA 12.0+", "..."]
        }
    """
    hf_repo = model_info.get("hf_repo", "")
    size_b = model_info.get("size_b", 0)
    category = model_info.get("category", "")
    is_apple = hw_scan.get("apple_silicon") is not None
    has_cuda = len(hw_scan.get("nvidia_gpus", [])) > 0
    total_vram = hw_scan.get("total_vram_gb", 0)

    # 自动选择框架
    if framework == "auto":
        if is_apple:
            framework = "ollama"  # Apple Silicon Ollama 最方便
        elif category in ("embedding", "reranker"):
            framework = "transformers"  # Embedding 通常用 Transformers
        elif has_cuda and size_b >= 70:
            framework = "vllm"  # 大模型用 vLLM
        elif has_cuda:
            framework = "vllm"
        else:
            framework = "llama.cpp"

    notes = []
    result = {"framework": framework, "model": model_name, "hf_repo": hf_repo}

    if framework == "vllm":
        result["install_cmd"] = "pip install vllm"
        gpu_util = 0.9 if total_vram >= 80 else 0.85
        ctx = 8192  # 默认上下文
        result["run_cmd"] = (
            f"vllm serve {hf_repo} \\\n"
            f"    --host 0.0.0.0 \\\n"
            f"    --port 8000 \\\n"
            f"    --gpu-memory-utilization {gpu_util} \\\n"
            f"    --max-model-len {ctx}"
        )
        result["docker_cmd"] = (
            f"docker run --gpus all -p 8000:8000 \\\n"
            f"    -v ~/.cache/huggingface:/root/.cache/huggingface \\\n"
            f"    vllm/vllm-openai:latest \\\n"
            f"    --model {hf_repo}"
        )
        notes.append("需要 CUDA 12.0+")
        notes.append(f"预估显存：{size_b * 2}GB（FP16）/ {size_b * 0.6:.1f}GB（4bit）")

    elif framework == "sglang":
        result["install_cmd"] = "pip install sglang[all]"
        result["run_cmd"] = (
            f"python -m sglang.launch_server \\\n"
            f"    --model-path {hf_repo} \\\n"
            f"    --host 0.0.0.0 \\\n"
            f"    --port 8000"
        )
        notes.append("SGLang 对 MoE 模型优化更好")
        notes.append("需要 CUDA 12.0+")

    elif framework == "ollama":
        # Ollama 优先找 GGUF
        notes.append("Ollama 需要 GGUF 格式，社区量化版通常在 bartowski 或 unsloth")
        notes.append("如果模型不在 Ollama 库，需手动拉 GGUF 后用 Modelfile 导入")
        result["install_cmd"] = (
            "# macOS\nbrew install ollama\n\n"
            "# Linux\ncurl -fsSL https://ollama.com/install.sh | sh"
        )
        # 简化：直接给个示例
        result["run_cmd"] = (
            f"# 1. 创建 Modelfile\necho 'FROM {hf_repo}' > Modelfile\n\n"
            f"# 2. 创建模型\nollama create {model_name} -f Modelfile\n\n"
            f"# 3. 启动服务\nollama serve"
        )

    elif framework == "llama.cpp":
        result["install_cmd"] = (
            "# macOS\nbrew install llama.cpp\n\n"
            "# Windows\nwinget install llama.cpp\n\n"
            "# Linux\ngit clone https://github.com/ggml-org/llama.cpp\n"
            "cmake -B build && cmake --build build --config Release"
        )
        # 找 GGUF 仓库（bartowski 优先）
        gguf_repo = f"bartowski/{hf_repo.split('/')[-1]}-GGUF"
        result["run_cmd"] = (
            f"# 直接从 HF 启动（推荐）\n"
            f"llama-server -hf {gguf_repo}:Q4_K_M -c 8192\n\n"
            f"# 或指定具体 GGUF 文件\n"
            f"llama-server --hf-repo {gguf_repo} --hf-file *Q4_K_M.gguf -c 8192"
        )
        notes.append("llama.cpp 支持 CPU / CUDA / Metal / ROCm 全平台")
        notes.append("Q4_K_M 是性价比首选精度")

    elif framework == "transformers":
        result["install_cmd"] = "pip install transformers torch accelerate"
        result["run_cmd"] = (
            f"python -c \"\n"
            f"from transformers import AutoModel, AutoTokenizer\n"
            f"model = AutoModel.from_pretrained('{hf_repo}', device_map='auto')\n"
            f"tokenizer = AutoTokenizer.from_pretrained('{hf_repo}')\n"
            f"\""
        )
        notes.append("Transformers 适合研究和 Embedding 场景")
        notes.append("生产环境推荐 vLLM/SGLang")

    result["notes"] = notes
    result["estimated_vram_gb"] = size_b * 2  # FP16
    result["recommended_quant"] = "Q4_K_M" if total_vram < size_b * 2 else "FP16"

    return result

"""
部署脚本生成器 - 按硬件 + 模型生成一键启动命令
支持：vLLM / SGLang / Ollama / llama.cpp / Transformers
      以及 decision（System One 决策模型）的专用配方 —— 见 decision_recipes.py
"""
import json
from typing import Dict, List, Any

from .decision_recipes import get_recipe, ENDPOINT_NOTES


def _build_decision_example(recipe: Dict[str, Any], endpoint: str) -> Dict[str, str]:
    """按 body 格式生成真实的 curl / python 请求示例。

    两种 body 形状不同，不能混用：
      decide     -> {kind, state, question, options?}
      systemone  -> {model?, state, questions: {name: {type, instructions, criteria}}}

    ⚠️ body 形状由 recipe['body_format'] 决定，不由 URL 路径决定 ——
    THX-01 的路径是 /v1/decide，但 body 是 systemone 格式。
    """
    port = recipe.get("port") or 8000
    example = recipe.get("example") or {}
    body_format = recipe.get("body_format") or (
        "decide" if endpoint == "/v1/decide" else "systemone"
    )

    body = dict(example)
    if body_format == "decide":
        py_tail = "print(dict(zip(r['options'], r['probabilities'])))"
    else:
        py_tail = "print(r['answers'])"

    curl = (
        f"curl -s http://localhost:{port}{endpoint} \\\n"
        f"  -H 'Content-Type: application/json' \\\n"
        f"  -d '{json.dumps(body, ensure_ascii=False)}'"
    )
    py = (
        "import requests\n"
        f"r = requests.post('http://localhost:{port}{endpoint}', "
        f"json={json.dumps(body, ensure_ascii=False)}).json()\n"
        f"{py_tail}"
    )

    return {"curl": curl, "python": py}


def _deploy_decision(model_name: str, model_info: Dict[str, Any]) -> Dict[str, Any]:
    """decision 类模型的部署脚本（不走通用 vllm/sglang 模板）。"""
    hf_repo = model_info.get("hf_repo", "")
    recipe = get_recipe(hf_repo)

    if recipe is None:
        # 没有配方时，至少不要把 chat 模板当成能用 —— 明确告知缺口
        return {
            "framework": "unknown-decision",
            "install_cmd": "# 未核实的决策模型，暂无配方",
            "run_cmd": (
                f"# ⚠️ 未核实：{hf_repo} 是 System One 决策模型，不能用通用 chat 模板部署。\n"
                f"# 它的接口不是 /v1/chat/completions，而是类型化决策接口（/v1/decide 或 /v1/systemone），\n"
                f"# 且通常需要 adapter / shim / 专用 serve 脚本。请先查 model card 确认：\n"
                f"#   启动入口 / 接口路径 / 端口 / 是否需要额外 adapter\n"
                f"# 参考 references/decision-models.md，或跑 scripts/verify_decision_endpoints.py 补配方。"
            ),
            "notes": [
                "该模型尚未核实部署方式 —— 工具不提供猜测出来的命令。",
                f"hf_repo: {hf_repo}",
                "补配方：跑 scripts/verify_decision_endpoints.py 核对 model card，"
                "再把真实命令加进 src/core/decision_recipes.py",
            ],
            "decision": True,
            "form": "unknown",
            "endpoint": None,
            "port": None,
        }

    endpoint = recipe["endpoint"]
    form = recipe["form"]
    port = recipe["port"]

    install_cmd = "\n".join(recipe["install"]) if recipe["install"] else "# 无需额外安装"
    download = recipe["download"] or []
    run_lines = recipe["run"] or []
    run_cmd = "\n".join(run_lines)

    # 下载步骤并进 run（用户复制整段就能执行）
    if download:
        run_cmd = "\n".join(download) + "\n\n" + run_cmd

    notes: List[str] = []
    notes.append(f"形态：{form}" + ("（进程内调用，无需起服务）" if form == "library" else ""))
    if endpoint:
        notes.append(f"接口：{endpoint}" + (f"  端口：{port}" if port else ""))
        notes.append(ENDPOINT_NOTES.get(endpoint, ""))
    if recipe.get("vram_note"):
        notes.append(f"显存：{recipe['vram_note']}")
    notes.extend(recipe["notes"])

    result: Dict[str, Any] = {
        "framework": recipe["framework"],
        "install_cmd": install_cmd,
        "run_cmd": run_cmd,
        "notes": [n for n in notes if n],
        "decision": True,
        "form": form,
        "endpoint": endpoint,
        "port": port,
        "display": recipe["display"],
    }

    # 有服务形态才给请求示例和健康检查
    if form != "library" and port:
        ex = _build_decision_example(recipe, endpoint)
        result["example_curl"] = ex["curl"]
        result["example_python"] = ex["python"]
        if recipe.get("health"):
            result["health_cmd"] = recipe["health"]

    return result


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
          "notes": ["需要 CUDA 12.0+", "..."],
          # decision 类额外带：
          "decision": True, "form": "service", "endpoint": "/v1/decide",
          "port": 8000, "example_curl": "...", "example_python": "...", "health_cmd": "..."
        }
    """
    hf_repo = model_info.get("hf_repo", "")
    size_b = model_info.get("size_b", 0)
    category = model_info.get("category", "")

    # System One 决策模型：接口不是 chat/completions，通用模板会误导用户
    if category == "decision":
        return _deploy_decision(model_name, model_info)

    is_apple = hw_scan.get("apple_silicon") is not None
    has_cuda = len(hw_scan.get("nvidia_gpus", [])) > 0
    total_vram = hw_scan.get("total_vram_gb", 0)

    # 自动选择框架
    if framework == "auto":
        if is_apple:
            framework = "ollama"  # Apple Silicon Ollama 最方便
        elif category in ("embedding", "reranker"):
            framework = "transformers"  # Embedding 通常用 Transformers
        elif category == "decision":
            # System One 决策模型：vLLM / SGLang 走 OpenAI 兼容 server，
            # 再用 /v1/systemone 风格的客户端问 noul/choice/score
            framework = "vllm" if has_cuda else "llama.cpp"
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

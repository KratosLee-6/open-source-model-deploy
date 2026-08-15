# 安装与部署指南

> 零基础也能上手的完整教程

## 目录

1. [快速开始（5 分钟上手）](#1-快速开始5-分钟上手)
2. [三种部署方式详细说明](#2-三种部署方式详细说明)
3. [MCP 客户端配置（Claude Desktop / Codex / Hermes）](#3-mcp-客户端配置)
4. [HTTP API 完整端点](#4-http-api-完整端点)
5. [Python API（开发者）](#5-python-api开发者)
6. [常见问题 FAQ](#6-常见问题-faq)
7. [故障排除](#7-故障排除)

---

## 1. 快速开始（5 分钟上手）

### 前置条件

- **Python 3.8+**（大多数系统已自带）
- 网络能访问 HuggingFace（或国内镜像自动 fallback）
- 操作系统：macOS / Windows / Linux 全支持

### 安装

```bash
# 基础安装（CLI + 核心）
pip install open-source-model-deploy

# 完整安装（CLI + MCP + HTTP API）
pip install open-source-model-deploy[all]

# 或从源码安装（开发者模式）
git clone https://github.com/KratosLee-6/open-source-model-deploy
cd open-source-model-deploy
pip install -e .[all]
```

### 第一步：查看支持的模型

```bash
osm-deploy list
```

你应该看到 47 个模型，分 8 类。

### 第二步：自动检测你的硬件

```bash
osm-deploy detect
```

输出示例（Windows + 16 核 + 15.2GB 内存，无独显）：
```
本机硬件扫描：
  平台:     windows
  CPU:      AMD64 (16 核)
  内存:     15.2GB
  硬盘剩余: 176.2GB
  NVIDIA:   0 张
  AMD:      0 张
  总可用显存: 0GB
  部署档位: cpu_only

推荐 47 个模型：
  - bge-large-zh-v1.5  0.3B  Q4_K_M（CPU 慢速）
  - llama-3.2-1b        1B    Q4_K_M（CPU 慢速）
  - phi-4-mini          3.8B  Q4_K_M（CPU 慢速）
  ...
```

### 第三步：评估某个模型

```bash
osm-deploy assess qwen3-32b
```

### 第四步：生成部署脚本

```bash
# 自动选择框架
osm-deploy deploy qwen3-32b

# 强制指定
osm-deploy deploy qwen3-32b --framework vllm
osm-deploy deploy qwen3-32b --framework ollama
osm-deploy deploy qwen3-32b --framework llama.cpp
```

---

## 2. 三种部署方式详细说明

本工具提供 **3 种独立但功能等价的部署方式**，你可以根据使用场景任选其一或多个同时使用：

### 方式 A：CLI（命令行）

**适合**：开发者调试、个人学习、CI/CD 脚本

**启动**：
```bash
osm-deploy --help
osm-deploy assess deepseek-v3
```

**优势**：零依赖（纯标准库）、脚本友好

### 方式 B：MCP Server（Model Context Protocol）

**适合**：Claude Desktop / Codex / Hermes 等 AI Agent 自动调用

**启动**：
```bash
# 前台运行（一般配合 MCP 客户端后台拉起）
osm-mcp

# 或作为模块启动
python -m src.mcp_server
```

**MCP 工具列表**（Agent 可调用）：

| 工具 | 参数 | 返回 |
|------|------|------|
| `assess_model` | `model`, `force_refresh?` | 5 步鉴别 JSON |
| `list_models` | `category?` | 模型清单 |
| `detect_hardware` | （无） | 硬件+推荐 |
| `generate_deploy_script` | `model`, `framework?` | 部署脚本 |
| `clear_cache` | `key?` | 清空确认 |

**优势**：Agent 原生协议、零配置自动发现

### 方式 C：HTTP API（FastAPI）

**适合**：跨语言调用、远程部署、Web/移动端集成

**启动**：
```bash
# 安装 HTTP 依赖
pip install open-source-model-deploy[http]

# 启动（默认 0.0.0.0:8765）
osm-http

# 或指定端口
python -m src.http_server --port 9000
```

**端点**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务自检 |
| POST | `/assess` | 5 步鉴别 |
| GET | `/list` | 列出模型（`?category=code`） |
| GET | `/detect` | 硬件检测 |
| POST | `/deploy` | 生成部署脚本 |
| POST | `/cache-clear` | 清缓存 |

**示例调用**：
```bash
# 列出代码类模型
curl http://localhost:8765/list?category=code

# 评估模型
curl -X POST http://localhost:8765/assess \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-v3"}'

# 生成 vLLM 部署脚本
curl -X POST http://localhost:8765/deploy \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-32b", "framework": "vllm"}'
```

**优势**：跨语言、远程部署、可观测性强

---

## 3. MCP 客户端配置

### Claude Desktop（官方）

配置文件位置：
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "osm-deploy": {
      "command": "osm-mcp",
      "args": []
    }
  }
}
```

### Hermes Agent

在 Hermes 配置文件中添加：

```yaml
mcp_servers:
  osm-deploy:
    command: osm-mcp
```

或编程方式（`~/.config/hermes/mcp.json`）：
```json
{
  "mcpServers": {
    "osm-deploy": {
      "command": "osm-mcp"
    }
  }
}
```

### Codex / Continue.dev / Cline 等

参照各客户端的 MCP 配置格式，命令均为 `osm-mcp`。

### 验证 MCP 连接

启动客户端后，问 AI：
> "用 osm-deploy 工具检测一下我电脑能跑什么模型"

如果返回硬件信息和模型推荐，说明 MCP 接入成功。

---

## 4. HTTP API 完整端点

启动 HTTP server 后，访问 `http://localhost:8765/docs` 查看自动生成的 OpenAPI 文档。

### `POST /assess`

**请求**：
```json
{
  "model": "deepseek-v3",
  "force_refresh": false
}
```

**响应**（节选）：
```json
{
  "model_name": "deepseek-v3",
  "resolved": {
    "hf_repo": "deepseek-ai/DeepSeek-V3",
    "github": "deepseek-ai/DeepSeek-V3",
    "arxiv_id": "2412.19437",
    "category": "domestic-general",
    "size_b": 671,
    "activated_b": 37
  },
  "estimated_params_b": 671,
  "activated_params_b": 37,
  "vram_note": "激活参数显存: FP8≈37GB, BF16≈74GB, 4bit≈19GB",
  "budget_estimates": {
    "entry": 36400,
    "standard": 208000,
    "high": 2600000
  },
  "timestamp": "2026-08-15 12:00:00"
}
```

### `GET /list`

**请求**：`GET /list?category=code`

**响应**：
```json
[
  {"name": "qwen2.5-coder-7b", "size_b": 7, "category": "code", ...},
  {"name": "deepseek-coder-v2-lite", "size_b": 16, ...},
  ...
]
```

### `GET /detect`

自动检测本机硬件并返回推荐模型。

### `POST /deploy`

**请求**：
```json
{
  "model": "qwen3-32b",
  "framework": "vllm"
}
```

**响应**：
```json
{
  "framework": "vllm",
  "model": "qwen3-32b",
  "hf_repo": "Qwen/Qwen3-32B",
  "install_cmd": "pip install vllm",
  "run_cmd": "vllm serve Qwen/Qwen3-32B --gpu-memory-utilization 0.9 --max-model-len 8192",
  "docker_cmd": "...",
  "notes": ["需要 CUDA 12.0+", "..."]
}
```

---

## 5. Python API（开发者）

### 5 步鉴别

```python
from src.core.assessor import full_assessment

report = full_assessment("deepseek-v3")
print(report["budget_estimates"])
```

### 硬件检测

```python
from src.data_sources.hardware_detect import (
    full_hardware_scan,
    recommend_models_for_hardware,
)
from src.core.model_resolver import KNOWN_MODELS

hw = full_hardware_scan()
print(f"总显存: {hw['total_vram_gb']}GB")
print(f"档位: {hw['deployable_tier']}")

recs = recommend_models_for_hardware(hw, KNOWN_MODELS)
for r in recs[:5]:
    print(f"  {r['model']}: {r['size_b']}B - {r['deployable_quant'] or r['deployable_precision']}")
```

### 部署脚本生成

```python
from src.core.deployment_generator import generate_deploy_script
from src.data_sources.hardware_detect import full_hardware_scan
from src.core.model_resolver import KNOWN_MODELS

hw = full_hardware_scan()
info = KNOWN_MODELS["qwen3-32b"]
script = generate_deploy_script("qwen3-32b", info, hw, framework="auto")

print("安装:", script["install_cmd"])
print("运行:", script["run_cmd"])
```

### 直接拉取 HF 数据

```python
from src.data_sources.huggingface import (
    fetch_model_metadata,
    fetch_gguf_files,
    get_local_app_url,
)

meta = fetch_model_metadata("Qwen/Qwen3-32B")
gguf_files = fetch_gguf_files("bartowski/Qwen3-32B-GGUF")
print(f"GGUF 文件数: {len(gguf_files)}")
```

---

## 6. 常见问题 FAQ

### Q1: 国内访问 HuggingFace 超时？

工具会自动 fallback 到 `hf-mirror.com` 镜像。如果还慢：

```bash
# 手动设置镜像环境变量
export HF_ENDPOINT=https://hf-mirror.com
osm-deploy assess deepseek-v3
```

### Q2: 缓存会不会导致数据过期？

缓存 TTL=24h。强制刷新：

```bash
osm-deploy assess deepseek-v3 --force-refresh
# 或
osm-deploy cache-clear
```

### Q3: 支持自定义模型吗？

支持。编辑 `src/core/model_resolver.py` 的 `KNOWN_MODELS`：

```python
"my-model": {
    "hf_repo": "my-org/my-model",
    "github": "my-org/my-model",
    "category": "domestic-general",
    "size_b": 7,
    "note": "我的自定义模型",
},
```

### Q4: 硬件检测不到 GPU？

- NVIDIA：确保安装了 [NVIDIA 驱动](https://www.nvidia.com/drivers) 和 `nvidia-smi`
- AMD：安装 [ROCm](https://rocm.docs.amd.com/) 并确保 `rocm-smi` 在 PATH
- Apple Silicon：自动通过 `system_profiler` 检测

### Q5: 如何部署到服务器给团队用？

```bash
# 在服务器上启动 HTTP API
osm-http --host 0.0.0.0 --port 8765

# 团队其他机器调用
curl http://server-ip:8765/detect
```

### Q6: 数据准确度如何？

- 模型规格：100% 来自 HuggingFace 官方 API 和 arXiv 论文
- 硬件报价：每月手动刷新基准表（建议参考京东/阿里云实时价）
- 显存估算：基于参数 × 精度系数（MoE 用激活参数）

---

## 7. 故障排除

### `osm-deploy` 命令找不到

```bash
# 检查是否安装成功
pip show open-source-model-deploy

# 如果用源码安装
pip install -e .

# 检查 PATH
which osm-deploy  # macOS/Linux
where osm-deploy  # Windows
```

### `mcp` 模块未找到

```bash
pip install mcp
```

### `fastapi` 模块未找到（用 HTTP API 时）

```bash
pip install fastapi uvicorn
# 或
pip install open-source-model-deploy[http]
```

### HTTP server 端口被占用

```bash
osm-http --port 9000  # 换端口
```

### 缓存目录权限问题

缓存目录：`~/.cache/open-source-model-deploy/`

```bash
# 手动清空
rm -rf ~/.cache/open-source-model-deploy/

# 或用命令
osm-deploy cache-clear
```

---

## 8. 进阶使用

### 集成到 CI/CD

```yaml
# GitHub Actions 示例
- name: 评估模型部署
  run: |
    pip install open-source-model-deploy
    osm-deploy assess deepseek-v3 > report.json
```

### 作为 Python 库嵌入

```python
# my_app.py
from open_source_model_deploy import assess, detect_hardware

hw = detect_hardware()
report = assess("qwen3-32b")
# 在你的应用里使用
```

---

如果还有问题，欢迎提 Issue 或在 Discussions 讨论！

如果觉得项目不错，欢迎[请作者喝杯咖啡 ☕](assets/coffee-qr.jpg) 鼓励持续更新！

---
name: open-source-model-deploy
description: 开源大模型部署可行性鉴别（v1.0 首发）。通过 MCP/HTTP 协议，Agent 可直接调用 5 步鉴别 + 硬件自动检测 + 一键部署脚本生成。客户咨询"本地部署 AI/私有化部署大模型/开源模型鉴别"时使用。
version: 1.0.0
updated: 2026-08-15
type: project-skill
project: 汐构信息-开源模型部署检测小工具（开源项目）
covers: 47 个模型 / 8 分类 / MCP+HTTP 双协议
---

# 开源大模型部署可行性鉴别工具（v1.0）

## v1.0 首发版本

首个稳定版本，包含：
- 47 个开源模型（分 8 类）
- 三种部署方式（CLI / MCP Server / HTTP API）
- 硬件自动检测 + 智能推荐
- 一键部署脚本生成（vLLM / SGLang / Ollama / llama.cpp）
- 智能 24h 缓存 + 国内镜像 fallback

## 何时使用

客户提问触发：
- "我想本地跑个 AI 模型"
- "我们公司要私有化部署大模型"
- "这模型值不值得部署"
- "我的电脑能跑什么模型"
- "怎么部署 DeepSeek/Qwen/Llama"
- 任何"开源模型 + 部署"相关的鉴别需求

## 三种部署方式（用户零安装）

### 方式 1：MCP Server（推荐 - Agent 原生协议）

```bash
# 安装
pip install open-source-model-deploy
osm-mcp  # 启动 MCP stdio server

# 客户端配置（Claude Desktop / Codex 等）
{
  "mcpServers": {
    "osm-deploy": {
      "command": "osm-mcp"
    }
  }
}
```

Agent 调用 5 个工具：
- `assess_model(model)` - 5 步鉴别
- `list_models(category?)` - 列出所有模型
- `detect_hardware()` - **自动检测本机硬件 + 推荐**
- `generate_deploy_script(model, framework?)` - **一键部署脚本**
- `clear_cache(key?)` - 清缓存

### 方式 2：HTTP API（任何语言/平台都能调）

```bash
osm-http  # 启动 HTTP server，默认 8765

# 调用
curl http://localhost:8765/detect
curl http://localhost:8765/list?category=code
curl -X POST http://localhost:8765/assess -d '{"model":"deepseek-v3"}'
curl -X POST http://localhost:8765/deploy -d '{"model":"qwen3-32b","framework":"vllm"}'
```

### 方式 3：Python CLI（开发调试用）

```bash
osm-deploy list
osm-deploy assess deepseek-v3
osm-deploy detect
osm-deploy deploy qwen3-32b --framework vllm
```

## 5 步鉴别流程（Agent 按此组织报告）

### 步骤 1 - 锁定模型 → `assess_model(model)`

动态拉取：HF 元数据 + GitHub README + arXiv 论文

### 步骤 2 - 配置需求

从 README 抽取：
- 架构 / 总参数 / 激活参数
- 上下文窗口 / 模态
- 官方支持的推理框架

### 步骤 3 - 部署方式

3 档适配：
| 档位 | 适用 | 硬件 |
|------|------|------|
| 入门 | ≤ 13B 量化 | RTX 4090 × 1-2 |
| 标准 | 14B-70B 量化 | 双 4090 / A100 80G |
| 高性能 | 满血全精度 | 4-8× H100 |

### 步骤 4 - 预算测算 → `detect_hardware()` 自动算

### 步骤 5 - 一键部署 → `generate_deploy_script(model, framework)`

支持：vLLM / SGLang / Ollama / llama.cpp / Transformers

## 硬件自动检测能力

`detect_hardware()` 自动识别：
- **平台**：macOS / Windows / Linux
- **GPU**：NVIDIA（nvidia-smi）/ AMD（rocm-smi）/ Apple Silicon（统一内存）
- **CPU**：型号 / 核数
- **内存 / 硬盘**：总量 + 可用
- **自动推荐**：47 个模型按本机适配度排序

实测示例（本机 Windows + 16 核 + 15.2GB 内存，无独显）：
```
档位：cpu_only
推荐 47 个模型（小到大）：
  - bge-large-zh-v1.5  0.3B  Q4_K_M（CPU 慢速）
  - llama-3.2-1b        1B    Q4_K_M（CPU 慢速）
  - phi-4-mini          3.8B  Q4_K_M（CPU 慢速）
  - qwen3-8b            8B    Q4_K_M（CPU 慢速）
```

## 当前支持的模型池（45 个，分 8 类）

**国内通用 9 个**：DeepSeek-V3/V2.5、GLM-4.5/4-32B、Kimi-K2、Qwen3-235B/32B/14B/8B
**国内推理 10 个**：DeepSeek-R1、GLM-Z1-32B、QwQ-32B(+preview)、DeepSeek-R1-Distill 全系（70B/32B/14B/8B/7B/1.5B）
**代码专用 6 个**：DeepSeek-Coder-V2/V2-Lite、Qwen3-Coder-30B、Qwen2.5-Coder-32B/7B、Codestral-22B
**视觉多模态 5 个**：Qwen2.5-VL-72B/7B、InternVL3-78B/8B、LLaVA-OneVision-Qwen2-7B
**国际密集 5 个**：Llama-3.1-405B/70B、Mistral-Large-2/Small-3、Gemma-3-27B
**国际边缘 7 个**：Llama-3.2-1B/3B、Gemma-3-9B/4B、Phi-4/mini/3.5-mini
**Embedding 4 个**：BGE-m3、bge-large-zh-v1.5、Qwen3-Embedding-8B、GTE-Qwen2-7B
**Reranker 1 个**：BGE-Reranker-v2-m3

```bash
osm-deploy list                # 列出所有
osm-deploy list --category X   # 按分类过滤
```

## 关键优势

1. **零用户安装**：通过 MCP/HTTP 协议，Agent 直接调用
2. **硬件自适应**：自动检测本机，反推可部署模型
3. **一键部署**：自动生成 vLLM/Ollama/llama.cpp 启动脚本
4. **数据永远新鲜**：每次调用都拉取当下最新（缓存 TTL=24h）
5. **镜像 fallback**：自动尝试 hf-mirror.com，国内可用
6. **零依赖核心**：纯标准库，可选 fastapi/mcp

## 工作区位置

源码：`D:\工作\方案\汐构信息\客户跟进\开源模型部署检测小工具\`

## 安装与部署（详见 INSTALL.md）

| 方式 | 安装 | 启动 | 适用 |
|------|------|------|------|
| CLI | `pip install open-source-model-deploy` | `osm-deploy list` | 开发者 |
| MCP Server | `pip install open-source-model-deploy` | `osm-mcp` | AI Agent |
| HTTP API | `pip install open-source-model-deploy[http]` | `osm-http`（端口 8765） | 跨语言 |

完整教程：[INSTALL.md](INSTALL.md)

## 常见问题

**Q: 用户不想装 Python 怎么办？**
A: 用 HTTP API 模式部署在服务器，Agent 通过 HTTP 调；或用 MCP 模式让 Agent 自动管

**Q: 缓存会不会导致数据过期？**
A: 缓存 24h 过期。可调 `clear_cache` 强制刷新

**Q: 国内访问 HF 超时？**
A: 代码已自动 fallback 到 `hf-mirror.com` 镜像

**Q: 如何添加新模型？**
A: 编辑 `src/core/model_resolver.py` 的 `KNOWN_MODELS` 字典

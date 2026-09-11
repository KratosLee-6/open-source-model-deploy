---
slug: kratoslee-open-source-model-deploy
displayName: 开源大模型部署鉴别器 · KratosLee
name: open-source-model-deploy
version: 1.0.0
summary: 开源大模型本地部署可行性评估工具。集成 HuggingFace / GitHub / arXiv 三个公开数据源，提供 75 个主流开源模型的部署方案、硬件需求估算和启动脚本生成，覆盖三大协议（CLI / MCP Server / HTTP API）。
author: 汐构信息
license: MIT
keywords:
  - llm
  - deployment
  - huggingface
  - ai-infrastructure
  - mcp
  - hardware-detect
  - vllm
  - ollama
homepage: https://github.com/KratosLee-6/open-source-model-deploy
repository: https://github.com/KratosLee-6/open-source-model-deploy
type: project-skill
pricing: free
x402_compliant: false
pay_skill: false
category: autonomous-ai-agents
tags:
  - 开源大模型
  - 部署辅助
  - 硬件检测
  - 启动脚本
  - MCP
  - HuggingFace
triggers:
  - "我想本地跑个 AI 模型"
  - "我们公司要私有化部署大模型"
  - "这模型值不值得部署"
  - "我的电脑能跑什么模型"
  - "怎么部署 DeepSeek"
  - "怎么部署 Qwen"
  - "怎么部署 Llama"
platforms:
  - linux
  - macos
  - windows
---

# 开源大模型部署鉴别器

为开发者评估开源大模型在本地或私有环境的部署可行性。读取 HuggingFace、GitHub、arXiv 三个公开数据源，结合本机硬件配置，输出可执行的部署方案和启动脚本。

## 适用场景

- 个人开发者在笔记本或台式机上评估本地部署能力
- 企业 IT 团队评估私有化部署方案与硬件采购
- AI Agent 自动调用工具辅助用户做模型选型

## 三种调用方式

### 方式 1：CLI

```bash
pip install open-source-model-deploy
osm-deploy list
osm-deploy detect
osm-deploy assess deepseek-v3
osm-deploy deploy qwen3-32b --framework vllm
```

### 方式 2：MCP Server

在 Claude Desktop、Codex 等支持 MCP 协议的客户端中添加：

```json
{"mcpServers": {"osm-deploy": {"command": "osm-mcp"}}}
```

Agent 可使用五个工具：`assess_model` / `list_models` / `detect_hardware` / `generate_deploy_script` / `clear_cache`。

### 方式 3：HTTP API

```bash
osm-http
curl http://localhost:8765/list
curl -X POST http://localhost:8765/assess -d '{"model":"qwen3-32b"}'
```

## 核心能力

### 硬件自动识别

读取本机硬件信息，识别平台（macOS / Windows / Linux）、GPU（NVIDIA / AMD / Apple Silicon）、CPU、内存容量，作为部署方案推荐依据。所有硬件检测仅读取公开系统信息（通过 nvidia-smi、rocm-smi、sysctl、wmic 等标准工具），不采集、不上传、不存储任何用户凭证。

### 模型元数据查询

从 HuggingFace Hub 拉取模型仓库信息，从 GitHub 读取项目 README，从 arXiv 检索相关论文摘要。数据按 24 小时缓存策略存储在 `~/.cache/open-source-model-deploy/`，避免重复请求。

### 一键部署脚本生成

根据用户硬件配置和目标模型，生成适配 vLLM、SGLang、Ollama、llama.cpp、Transformers 等框架的启动命令。

## 支持的模型范围

本工具覆盖 75 个主流开源大模型，按用途分为 8 类：通用对话、推理增强、代码专用、视觉多模态、密集参数模型、轻量边缘模型、Embedding 向量化、Reranker 重排序。完整列表见 `templates/model-card-template.md`。

## 工作流程

1. 本地部署：用户安装 `pip install open-source-model-deploy`
2. 硬件识别：运行 `osm-deploy detect` 读取本机配置
3. 模型选择：用户提问或运行 `osm-deploy list` 浏览 75 个模型
4. 评估：调用 `assess_model(<model>)` 拿到 5 步鉴别报告
5. 部署：调用 `generate_deploy_script(<model>, <framework>)` 拿到启动命令
6. 用户复制命令到本机执行

## 使用约束

- 工具运行所需的 Python 包均为公开 PyPI 包，安装方式见 INSTALL.md
- HuggingFace 数据源访问遵守 HF Hub API 服务条款，国内用户自动 fallback 到 hf-mirror.com 镜像
- GitHub 数据源访问遵守 GitHub REST API 速率限制
- arXiv 数据源访问遵守 arXiv API 使用规范
- 本工具不发起任何爬虫请求，不绕过任何平台反爬机制

## 安全声明

本工具在本地完成所有数据处理，硬件信息、模型元数据、缓存文件均存储在本机 `~/.cache/open-source-model-deploy/` 目录，不发送到第三方服务器。本工具不读取、不收集、不上传用户的 API 密钥、密码、私钥、SSH 凭证、个人隐私数据。所有 HTTP 请求仅访问 HuggingFace、GitHub、arXiv 的公开 API 端点。

源代码完全公开在 https://github.com/KratosLee-6/open-source-model-deploy，遵循 MIT 协议，可自由审计。

## 风险提示

本工具仅根据公开模型仓库元数据和本机硬件配置生成部署参考方案，不构成对模型效果、性能、可用性的保证。实际部署效果受硬件配置、操作系统、推理框架版本、量化方案、prompt 设计等多重因素影响，建议用户先在小规模场景验证后再投入生产环境。

调用 HuggingFace / GitHub / arXiv API 时，请遵守各平台的服务条款和速率限制，避免高频请求导致 IP 被临时封禁。

本工具不评估模型质量、不进行模型训练或微调、不涉及任何 AIGC 内容生成。所有功能围绕部署决策辅助，不属于生成式人工智能服务范畴。

## 许可

MIT License。详见 LICENSE 文件。
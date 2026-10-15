---
slug: kratoslee-open-source-model-deploy
displayName: 开源大模型部署鉴别器 · KratosLee
name: open-source-model-deploy
description: 开源大模型部署可行性鉴别器。集成 HuggingFace / GitHub / arXiv 三个公开数据源，提供 137 个主流开源模型（DeepSeek / Qwen3 / GLM / Kimi / Llama / Mistral / Gemma / Phi 全系 + 代码/视觉/Embedding/Reranker + EmbeddingGemma 2 多模态 + Strands Decider 决策模型）的部署方案、硬件需求估算和启动脚本生成（vLLM / SGLang / Ollama / llama.cpp），覆盖 CLI / MCP Server / HTTP API 三协议。含 auto_fetch_models.py 自动拉取工具，每周从 HF API 补模型。当客户咨询"本地部署 AI / 私有化部署大模型 / 开源模型鉴别 / EmbeddingGemma / Jev 能不能本地跑"时使用。
version: 1.1.0
updated: 2026-10-15
summary: 开源大模型本地部署可行性评估工具。集成 HuggingFace / GitHub / arXiv 三个公开数据源，提供 137 个主流开源模型的部署方案、硬件需求估算和启动脚本生成，覆盖三大协议（CLI / MCP Server / HTTP API），并提供 auto_fetch_models 自动拉取工具。
type: project-skill
project: 汐构信息-开源模型部署检测小工具（开源项目）
license: MIT
covers: 137 个模型 / 8 分类 / CLI+MCP+HTTP 三协议 / 6 档量化显存 / 自动每周边补
keywords:
  - llm
  - deployment
  - huggingface
  - ai-infrastructure
  - mcp
  - vllm
  - ollama
  - embedding
homepage: https://github.com/KratosLee-6/open-source-model-deploy
repository: https://github.com/KratosLee-6/open-source-model-deploy
---

# 开源大模型部署可行性鉴别工具（v1.1.0）

## v1.1.0 增量

- **模型库 135 → 137**：
  - **EmbeddingGemma 2**（Google DeepMind，2026-10-06，Apache-2.0）—— 740M 原生多模态 embedding，
    文本/图像/视频/音频统一 768 维空间，MRL 可截断 128/256/512，8K context。
    纯文本场景只加载 270M 文本骨干（视觉 170M / 音频 300M 按需加载）
  - **Strands Decider 2B**（AWS Strands Labs，2026-10-01，Apache-2.0）—— System One 决策模型，
    不生成文本，返回 `noul`/`choice`/`score` 与校准置信度；1.9B，RTX 3090 中位 115ms
- **新增「闭源模型」鉴别范式**：Jev（TypeSafe AI）权重未公开、API-only，
  **不进 `KNOWN_MODELS`**（否则 `list`/`detect` 会告诉客户"能下载下来跑"）。
  详见 `references/jev-integration.md`；模型库里放能真跑的开源对应物 Strands Decider 2B
- **修掉三处「截图会说谎」**：不再编造 nvidia-smi 输出 / 不再调到别的环境安装的旧版 CLI /
  联网失败时保留原图而不是覆盖成空图
- **README 事实校验扩到「截图不能是空图」**（`check_readme_facts.py` 新增高度阈值断言）

详细见主仓 README.md 与 `docs/releases/v1.1.0.md`。

## 版本沿革

| 版本 | 日期 | 模型数 | 重点 |
| --- | --- | ---: | --- |
| **v1.1.0** | 2026-10-15 | **137** | EmbeddingGemma 2 · Strands Decider 2B · JEV 闭源鉴别 · 截图不再说谎 |
| v1.0.3 | 2026-10-03 | 135 | 修正 MoE 显存误判（按总参算）· 显存结构化 · 模型库体检 CI 卡口 |
| v1.0.2 | 2026-09-26 | 127 | auto_fetch_models.py · GH Actions 周日自动开 PR |
| v1.0.1 | 2026-09-10 | 94 | 每周自动刷新元数据 + GPU 价格 |
| v1.0.0 | 2026-08-15 | 47 | 首个版本 · 真实硬件推理实测 |

三种部署方式（CLI / MCP Server / HTTP API）+ 硬件自动检测 + 一键部署脚本生成
（vLLM / SGLang / Ollama / llama.cpp）+ 智能 24h 缓存 + 国内镜像 fallback。

## 何时使用

客户提问触发：
- "我想本地跑个 AI 模型"
- "我们公司要私有化部署大模型"
- "这模型值不值得部署"
- "我的电脑能跑什么模型"
- "怎么部署 DeepSeek/Qwen/Llama"
- "Jev / 某热榜模型能不能本地部署"（→ 先查是否闭源）
- 任何"开源模型 + 部署"相关的鉴别需求

## 三种部署方式（用户零安装）

### 方式 1：MCP Server（推荐 - Agent 原生协议）

```bash
# 安装
pip install open-source-model-deploy
osm-mcp  # 启动 MCP stdio server

# 客户端配置（Claude Desktop / Codex / Hermes）
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
- `list_models(category?, max_vram_gb?)` - 列出所有模型 / 按显存反查
- `detect_hardware()` - **自动检测本机硬件 + 推荐**
- `generate_deploy_script(model, framework?)` - **一键部署脚本**
- `clear_cache(key?)` - 清缓存

### 方式 2：HTTP API（任何语言/平台都能调）

```bash
osm-http  # 启动 HTTP server，默认 8765

# 调用
curl http://localhost:8765/detect
curl http://localhost:8765/list?category=embedding
curl "http://localhost:8765/list?max_vram_gb=24"
curl -X POST http://localhost:8765/assess -d '{"model":"embeddinggemma-2"}'
curl -X POST http://localhost:8765/deploy -d '{"model":"qwen3-32b","framework":"vllm"}'
```

### 方式 3：Python CLI（开发调试用）

```bash
osm-deploy list
osm-deploy assess strands-decider-2b
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
- **自动推荐**：`KNOWN_MODELS` 全部（v1.1.0 = 137 个）按本机适配度排序

实测示例（本机：Windows 11 · AMD Ryzen 7 7840HS 16 核 · Radeon 780M 集显 · 15.2GB 内存）：
```
档位：cpu_only
本机可部署 85 / 137 个在架模型
每行标注「Q4_K_M（CPU 慢速·显存需 X GB 不足）」
```

> ⚠️ 无独显时工具会如实给出 `cpu_only` 档位，并把「能跑但只能 CPU 慢速」
> 和「显存不够跑不了」分开说清楚，不会宣称"137 个全能跑"。

## 当前支持的模型池（v1.1.0 = 137 个，分 8 类）

**国内通用 44 个**：DeepSeek-V3 / V2.5 / V3-0324 / V4-Flash-0731 / V4.1-Flash、GLM-4.5 / 4-32B / GLM-5.3 / 5.3-Flash、Kimi-K2 / K3、MiMo-V2.6 全系、Qwen3-235B/32B/14B/8B、Qwen2.5 全系
**国内推理 10 个**：DeepSeek-R1、GLM-Z1-32B、QwQ-32B、DeepSeek-R1-Distill 全系（70B/32B/14B/8B/7B/1.5B）
**代码专用 9 个**：DeepSeek-Coder-V2 / V2-Lite、Qwen3-Coder-480B-A35B / 30B、Qwen2.5-Coder-32B/14B/7B、Codestral-22B
**视觉多模态 17 个**：Qwen2.5-VL-72B/7B、Qwen3-VL-32B、InternVL3-78B/8B、LLaVA-OneVision、Florence-2-base
**国际密集 11 个**：Llama-4-Maverick / Scout、Llama-3.3-70B、Mistral-Large-2、Gemma-4-31B
**国际边缘 15 个**：Llama-3.2-1B/3B、Gemma-3-9B/4B、Phi-4 / mini、Mistral-7B、**Strands Decider 2B**
**Embedding 29 个**：BGE 全家桶、E5 全家桶、GTE 系列、Nomic、**EmbeddingGemma 2 / 300M**
**Reranker 2 个**：BGE-Reranker-large / v2-m3

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
7. **数据可信度有卡口**：模型库体检 + README 事实校验（含「截图不能是空图」）

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
A: 代码已自动 fallback 到 `hf-mirror.com` 镜像；若脚本仍超时，可给进程加
`HTTPS_PROXY` 环境变量走本地代理

**Q: 某个热榜模型能不能本地部署？**
A: 先查它有没有公开权重。API-only 的闭源模型（如 TypeSafe 的 Jev）进不了模型库，
会在 `assess` 时查不到——这不是 bug，是刻意的：把闭源模型列进"可部署清单"会让客户买错硬件。
参见 `references/jev-integration.md`

**Q: 如何添加新模型？**
A: 编辑 `src/core/model_resolver.py` 的 `KNOWN_MODELS` 字典，`size_b` 取 HF
`safetensors.total` 实测值；完成后跑 `lint_models.py` + `check_readme_facts.py`

# 开源大模型部署可行性鉴别工具

> 把"模型规格 / 硬件报价 / 部署方式"做成**实时拉取**的动态数据层，让 Agent 每次询问都拿到当下最准确的信息，而不是过期快照。

## 🌟 核心亮点

- **🧠 47 个开源模型覆盖**：DeepSeek / Qwen3 / GLM / Kimi / Llama / Mistral / Gemma / Phi 全系 + 代码 / 视觉 / Embedding / Reranker 专用模型
- **🔌 三种部署方式**：CLI / MCP Server（Agent 原生协议）/ HTTP API（FastAPI）
- **🖥️ 硬件自动检测**：跨平台识别 NVIDIA / AMD / Apple Silicon，自动推荐可部署模型
- **🚀 一键部署脚本**：自动生成 vLLM / SGLang / Ollama / llama.cpp / Transformers 启动命令
- **🌐 国内友好**：自动 fallback 到 `hf-mirror.com` 镜像
- **💾 智能缓存**：TTL=24h，零额外依赖（纯 Python 标准库）

## 📦 一分钟上手

```bash
pip install open-source-model-deploy

# 看支持的模型
osm-deploy list

# 自动检测你的硬件 + 推荐可部署模型
osm-deploy detect

# 5 步评估某个模型
osm-deploy assess deepseek-v3

# 一键生成部署脚本
osm-deploy deploy qwen3-32b
```

## 🏆 真实实测案例（2026-08-15）

**环境**：Windows 11 / AMD64 16 核 / 15.2GB 内存 / 无独显
**模型**：Llama-3.2-1B-Instruct Q4_K_M（770MB）
**引擎**：llama.cpp b10424（CPU 版）

| 指标 | 实测结果 |
|------|---------|
| 模型加载 | ~3 秒 |
| **推理速度** | **35.85 tokens/秒** |
| 响应质量 | 准确生成结构化英文描述 |

**结论**：无独显笔记本也能本地跑 1B 模型，速度远超预期。对比云租 AutoDL 4090 月租 ¥2,500，本机部署**节省 100% 成本 + 数据不出本地**。

详细实测：[examples/real_world_test_windows_no_gpu.md](examples/real_world_test_windows_no_gpu.md)

## 🎯 解决什么问题？

部署开源大模型最怕「拿着过期文档做判断」：

- **模型迭代快**：3 个月前推荐的硬件，今天可能已被新模型超越
- **硬件价波动**：GPU 一年跌 30%+，3 个月前的报价严重过时
- **量化版本涌现**：昨天还没有的 GGUF，今天突然有人发布
- **手动调研累**：每个模型都要查 HF / GitHub / arXiv / 京东，时间成本极高

**本工具 = 47 个模型的"实时专家顾问"**，每次调用都重新拉数据，给你当下最准确的部署决策。

## 🏗️ 架构

```
用户/Agent
  ↓
[CLI / MCP Server / HTTP API]  ← 三种入口，按场景选
  ↓
[5 步鉴别 + 硬件检测 + 部署脚本]
  ↓
[动态数据源层]（智能缓存 24h）
  ├─ HuggingFace Hub API（模型元数据、GGUF 文件）
  ├─ GitHub raw（官方 README、LICENSE）
  ├─ arXiv API（论文标题、摘要）
  └─ 硬件基准表（每月刷新）+ 本机硬件扫描
```

## 🛠️ 三种使用方式

### 1️⃣ CLI（开发者）

```bash
osm-deploy list
osm-deploy assess deepseek-v3
osm-deploy detect
osm-deploy deploy qwen3-32b --framework vllm
```

### 2️⃣ MCP Server（AI Agent 推荐）

```bash
osm-mcp  # 启动 stdio server
```

客户端配置（Claude Desktop / Codex / Hermes）：
```json
{"mcpServers": {"osm-deploy": {"command": "osm-mcp"}}}
```

Agent 可调用 5 个工具：`assess_model` / `list_models` / `detect_hardware` / `generate_deploy_script` / `clear_cache`

### 3️⃣ HTTP API（跨语言/远程）

```bash
osm-http  # 启动 FastAPI（端口 8765）

curl http://localhost:8765/detect
curl -X POST http://localhost:8765/assess -d '{"model":"deepseek-v3"}'
curl -X POST http://localhost:8765/deploy -d '{"model":"qwen3-32b","framework":"vllm"}'
```

## 📊 已覆盖的 47 个模型（分 8 类）

| 分类 | 模型示例 |
|------|---------|
| **国内通用** (9) | DeepSeek-V3 / V2.5、GLM-4.5 / 4-32B、Kimi-K2、Qwen3-235B / 32B / 14B / 8B |
| **国内推理** (10) | DeepSeek-R1、GLM-Z1-32B、QwQ-32B、DeepSeek-R1-Distill 全系 |
| **代码专用** (6) | DeepSeek-Coder-V2 / V2-Lite、Qwen3-Coder-30B、Qwen2.5-Coder-32B / 7B、Codestral-22B |
| **视觉多模态** (5) | Qwen2.5-VL-72B / 7B、InternVL3-78B / 8B、LLaVA-OneVision |
| **国际密集** (5) | Llama-3.1-405B / 70B、Mistral-Large-2 / Small-3、Gemma-3-27B |
| **国际边缘** (7) | Llama-3.2-1B / 3B、Gemma-3-9B / 4B、Phi-4 / mini / 3.5-mini |
| **Embedding** (4) | BGE-m3、bge-large-zh-v1.5、Qwen3-Embedding-8B、GTE-Qwen2-7B |
| **Reranker** (1) | BGE-Reranker-v2-m3 |

## 💡 典型使用场景

**场景 1：客户问"本地跑 AI 要多少钱"**
```
Agent → detect_hardware() → 47 个推荐 → 客户决策
```

**场景 2：技术选型对比 DeepSeek vs Qwen3**
```
Agent → assess_model("deepseek-v3") + assess_model("qwen3-32b")
     → 输出对比表 → 客户选型
```

**场景 3：私有化部署验收**
```
Agent → generate_deploy_script("llama-3.1-70b", "vllm")
     → 一键启动命令 → 部署上线
```

## � 安装

```bash
# 基础（CLI）
pip install open-source-model-deploy

# 完整（CLI + MCP + HTTP）
pip install open-source-model-deploy[all]

# 从源码
git clone https://github.com/KratosLee-6/open-source-model-deploy
cd open-source-model-deploy
pip install -e .[all]
```

详见 [INSTALL.md](INSTALL.md)。

## 🤝 贡献

欢迎 PR 添加新模型！只需在 `src/core/model_resolver.py` 的 `KNOWN_MODELS` 中加一行：

```python
"my-model": {
    "hf_repo": "org/Repo-Name",
    "github": "org/repo",
    "category": "domestic-general",
    "size_b": 7,
    "note": "一句话定位",
},
```

## 📜 License

MIT

---

## ☕ 请作者喝杯咖啡

如果觉得项目不错，对你有帮助，欢迎请作者喝杯咖啡 ☕，鼓励持续更新！

<div align="center">
  <img src="assets/coffee-qr.jpg" alt="请作者喝咖啡" width="300" />
</div>

**其他支持方式**：
- ⭐ Star 这个项目让更多人看到
- � 提 Issue 报告 Bug 或建议新功能
- 🔀 提 PR 贡献代码或新模型
- 📢 分享给你的朋友和同事

你的支持是这个项目持续迭代的最大动力 ✨

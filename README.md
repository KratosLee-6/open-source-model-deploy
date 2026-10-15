# 开源大模型部署可行性鉴别工具

> 把「模型规格 / 硬件报价 / 部署方式」做成**实时拉取**的动态数据层，让 Agent 每次询问都拿到当下最准确的信息，而不是过期快照。

[![version](https://img.shields.io/badge/version-v1.1.0-002FA7)](docs/releases/v1.1.0.md) [![models](https://img.shields.io/badge/models-137%20%E5%9C%A8%E6%9E%B6-002FA7)](references/vram-requirements.md) [![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![python](https://img.shields.io/badge/python-3.8%2B-blue)](pyproject.toml)

**v1.1.0**（2026-10-15 发布）· 137 个在架模型 · 8 大分类 · CLI / MCP Server / HTTP API 三通道

---

## ⚠️ 如果你只用 v1.0.2 的结论买过硬件，请先看这段

v1.0.2 对 MoE 模型的显存是**按激活参数算的**，这是错的：

> MoE 的 expert 权重**全部常驻显存**，稀疏激活只降低计算量（FLOPs），不降低权重占用。

实测后果（24GB RTX 4090 场景）：

| 模型 | 总参 / 激活 | v1.0.2 算出的显存 | 当时的判定 | 实际 Q4 需求 |
| --- | --- | ---: | --- | ---: |
| Kimi-K2 | 1000B / 32B | 23.0 GB | `tight` → **建议能跑** | **720 GB** |
| Qwen3-235B-A22B | 235B / 22B | 15.8 GB | `fits` → **建议能跑** | **169 GB** |
| GLM-4.5 | 355B / 32B | 23.0 GB | `tight` → **建议能跑** | **256 GB** |

v1.0.3 已修正为按总参计算。**完整复盘见 [`docs/moe-vram-pitfall.md`](docs/moe-vram-pitfall.md)**，
它同时也是一份可迁移的判据清单（如果你也在做「模型 × 硬件」匹配，那篇能直接用）。

---

## 🌟 核心亮点

- **🧠 137 个在架模型 · 8 大分类**（另 1 个已退役标注，共 138 条记录）——
  DeepSeek / Qwen3 / MiMo / GLM / Kimi / Llama-4 / Mistral / Gemma / Phi 全系，
  加代码 / 视觉 / Embedding / Reranker 专用模型
- **🧮 结构化显存需求**——每个模型 × 6 档量化都有显存数值和可行性判定，
  `list_models?max_vram_gb=24` 一次就能筛出消费级显卡跑得动的清单
- **🔌 三通道**——CLI（开发者）/ MCP Server（Agent 原生）/ HTTP API（跨语言远程）
- **🖥️ 硬件自动检测**——跨平台识别 NVIDIA / AMD / Apple Silicon，推荐可部署模型
- **🚀 一键部署脚本**——自动生成 vLLM / SGLang / Ollama / llama.cpp / Transformers 启动命令
- **🩺 数据可信度有卡口**——模型库体检（`lint_models.py`）+ README 事实校验
  （`check_readme_facts.py`）作为 CI 卡口，挡住「总参 / 激活参」这类会导致错误采购建议的数据错误
- **🌐 国内友好**——自动 fallback 到 `hf-mirror.com` 镜像
- **💾 智能缓存**——TTL=24h，零额外依赖（纯 Python 标准库）

---

## 📦 一分钟上手

```bash
pip install open-source-model-deploy

# 看支持的模型（137 个在架）
osm-deploy list

# 自动检测硬件 + 推荐可部署模型
osm-deploy detect

# 5 步评估某个模型
osm-deploy assess deepseek-v3

# 一键生成部署脚本
osm-deploy deploy qwen3-32b
```

---

## 🆕 v1.1.0 新增：两个模型 + 一份「闭源模型」鉴别

### 1. EmbeddingGemma 2（Google DeepMind，2026-10-06）

**原生多模态 embedding**，四模态进同一个 768 维空间 —— 这是本项目补上的
「多模态检索」这块拼图。

| 维度 | 数值 |
| --- | --- |
| 总参 | **740M**（HF `safetensors.total` 实测 744,371,512） |
| 结构 | 270M 文本骨干（130M transformer + 140M embedder）+ **170M 视觉** + **300M 音频** 编码器 |
| 输出维度 | 768，**MRL 可截断到 512 / 256 / 128**（存储最高省 6×） |
| 上下文 | 8,192 tokens（可容纳数分钟音频 / 视频） |
| 语言 | 100+ 语言；代码任务较一代 **+14%**（MTEB code 68.76 → 78.68） |
| 许可 | Apache-2.0 |
| 本机实测显存 | Q4_K_M **0.5 GB** · BF16 **1.8 GB** |

> 💡 **纯文本场景只加载 270M 文本骨干**（视觉/音频编码器可选加载），
> 所以它虽然标 740M，实际检索场景的占用比参数看起来小得多。
> MRL 截断到 256 维时质量几乎不掉（MTEB 多语 61.36 → 60.41），
> 向量库存储直接省 3 倍。

### 2. Strands Decider 2B（AWS Strands Labs，2026-10-01）

**System One 决策模型** —— 不生成文本，输入状态 + 类型化问题，
一次前向返回 `noul`（是/否概率）/ `choice` / `score`，每个答案自带校准置信度。

| 维度 | 数值 |
| --- | --- |
| 规模 | 1.9B（`Qwen/Qwen3.5-2B-Base` + LoRA + 读出头） |
| 延迟 | RTX 3090 中位 **115 ms**；可 CPU / Apple Silicon |
| 许可 | Apache-2.0（含训练数据与脚本） |
| 本机实测显存 | Q4_K_M **1.4 GB** · BF16 **4.6 GB** |
| ⚠️ 注意 | HF 仓库只含 **91.5MB LoRA adapter**，部署需另配 base 模型 |

用途是 agent 工作流里那些「不值得调用 LLM」的判断：模型路由、工具选择、
参数校验、分诊、护栏、评估。

### 3. 顺手做了一次「闭源模型的鉴别」

Jev（TypeSafe AI，2026-09-15）是 System One 类别的开创者，社区热度极高
（发布一周 1,865 个新仓库 / 43,750 star）。但它**权重未公开、API-only**：

| 判据 | Jev 的实际情况 | 能否进模型库 |
| --- | --- | --- |
| 有开源权重（HF repo） | 无，官方从未发布 | ❌ |
| 可算显存 / 本地推理 | 无权重 ⇒ 无从计算 | ❌ |
| 可生成部署脚本 | 只能生成 API 调用代码 | ❌ |

**结论**：Jev 进不了 `KNOWN_MODELS`，把塞进去会让 `list` / `detect` 说谎 ——
客户会以为它像 Qwen3 一样能下载下来跑。本工具的处理方式：
Jev 记录在 [`references/jev-integration.md`](references/jev-integration.md)（含 env 模板、
成本测算、设备适配），而模型库里放**能真跑**的开源对应物 Strands Decider 2B。

> 完整鉴别（含 Jev 的定价 $0.042/MTok、70–500 ms 延迟、开源替代品清单、
> 以及为什么「闭源 ≠ 不能推荐」）见
> [`references/jev-integration.md`](references/jev-integration.md)。

---

## 🧮 显存需求

每个模型给出 6 档量化的显存数值（Q4_K_M / Q5_K_M / Q6_K / Q8_0 / FP8 / BF16），
并给出单卡 / 多卡的可行性判定。完整 137 行对照表见
[`references/vram-requirements.md`](references/vram-requirements.md)（自动生成，与代码同步），
机器可读版本见 [`data/models-knowledge.json`](data/models-knowledge.json)。

**按显存反查能跑什么**（MCP / HTTP 均可用）：

| 查询 | 返回 |
| --- | ---: |
| `list_models?max_vram_gb=8` | 79 个 |
| `list_models?max_vram_gb=16` | 88 个 |
| `list_models?max_vram_gb=24` | 106 个 |
| `list_models?max_vram_gb=80` | 115 个 |

**几个真实判定示例**（Q4_K_M 单卡）：

| 模型 | 规模 | Q4 显存 | 24GB 4090 能跑吗 |
| --- | --- | ---: | --- |
| `embeddinggemma-2` | 0.74B 多模态 embedding | 0.5 GB | ✅ 轻松 |
| `strands-decider-2b` | 1.9B 决策模型 | 1.4 GB | ✅ 轻松 |
| `mimo-v2.6-distill-qwen-9b` | 9.4B 密集 | 6.8 GB | ✅ 轻松 |
| `qwen3-32b` | 32B 密集 | 23.0 GB | ✅ 刚好 |
| `llama-4-scout-17b` | 108.6B MoE / 17B 激活 | 78.2 GB | ❌ 差 3 倍 |
| `kimi-k3` | 2779.9B MoE / 119B 激活 | 2001.5 GB | ❌ 集群级 |

> 💡 注意 MoE 那两行：`Llama-4-Scout-17B-16E` 模型名里的 **17B 是激活参不是总参**，
> 真实总参 108.6B。这类命名很容易踩坑，本工具的 `size_b` 一律取自
> HuggingFace `safetensors.total` 实测值。

---

## 📊 已覆盖的 137 个模型（8 类 · 2026-10-15）

| 分类 | 模型数 | v1.1.0 新增代表 |
| --- | ---: | --- |
| **国内通用** | 44 | （无新增） |
| **Embedding** | 29 | **EmbeddingGemma 2**（740M 原生多模态，四模态统一 768 维） |
| **视觉多模态** | 17 | （无新增） |
| **国际边缘** | 15 | **Strands Decider 2B**（AWS System One 决策模型，Apache-2.0） |
| **国际密集** | 11 | （无新增） |
| **国内推理** | 10 | （无新增） |
| **代码专用** | 9 | （无新增） |
| **Reranker** | 2 | （无新增） |
| **总计** | **137** | 较 v1.0.3 的 135 **+2**；另 1 个已退役标注（DeepSeek-V4-Flash → V4.1-Flash）不计入 |

各类代表模型速览：

| 分类 | 模型示例 |
| --- | --- |
| **国内通用** (44) | DeepSeek-V3 / V4.1-Flash / V2.5 · GLM-5.3 / 4.5 · Kimi-K3 / K2 · MiMo-V2.6 全系 · Qwen3-235B / 32B / 14B |
| **国内推理** (10) | DeepSeek-R1 全系（含 Distill）· GLM-Z1-32B · QwQ-32B |
| **代码专用** (9) | Qwen3-Coder-480B / 30B · Qwen2.5-Coder-32B / 14B / 7B · DeepSeek-Coder-V2 · Codestral-22B |
| **视觉多模态** (17) | Qwen2.5-VL-72B / 7B · Qwen3-VL-32B · InternVL3-78B / 8B · LLaVA-OneVision · Florence-2-base |
| **国际密集** (11) | Llama-4-Maverick / Scout · Llama-3.3-70B · Mistral-Large-2 · Gemma-4-31B |
| **国际边缘** (15) | Llama-3.2-1B / 3B · Gemma-3-9B / 4B · Phi-4 / mini · **Strands Decider 2B** |
| **Embedding** (29) | BGE 全家桶（M3 / large / base / small 中英）· E5 large/base/small · GTE multilingual / large-en · Nomic · **EmbeddingGemma 2 / 300M** |
| **Reranker** (2) | BGE-Reranker-large · BGE-Reranker-v2-m3 |

---

## 🛠️ 三种使用方式

### 1️⃣ CLI

```bash
osm-deploy list                              # 137 个在架模型
osm-deploy list --category code              # 只看代码模型
osm-deploy list --all                        # 含已退役模型
osm-deploy assess embeddinggemma-2           # 5 步评估（返回结构化 JSON）
osm-deploy detect                            # 扫硬件 + 推荐
osm-deploy deploy qwen3-32b --framework vllm # 生成启动脚本
```

### 2️⃣ MCP Server（AI Agent 推荐）

```bash
osm-mcp    # stdio server
```

客户端配置（Claude Desktop / Codex / Hermes）：

```json
{"mcpServers": {"osm-deploy": {"command": "osm-mcp"}}}
```

5 个工具：`assess_model` / `list_models` / `detect_hardware` / `generate_deploy_script` / `clear_cache`

`list_models` 支持按显存筛选——这是给 Agent 用的核心能力，一次调用即可拿到
「这台机器跑得动的全部模型」，不必逐个 `assess`：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `max_vram_gb` | number | 只返回该显存下放得下的模型，按显存升序 |
| `quant` | string | 判定档位，默认 `Q4_K_M` |
| `category` | string | 按分类过滤 |
| `include_retired` | boolean | 是否含已退役模型，默认 false |

### 3️⃣ HTTP API

```bash
osm-http    # FastAPI，端口 8765

curl http://localhost:8765/detect
curl "http://localhost:8765/list?max_vram_gb=24"
curl -X POST http://localhost:8765/assess -d '{"model":"embeddinggemma-2"}'
curl -X POST http://localhost:8765/deploy -d '{"model":"qwen3-32b","framework":"vllm"}'
```

---

## 🏆 真实实测（v1.1.0 · 2026-10-15）

**环境**：Windows 11 / **AMD Ryzen 7 7840HS**（16 核）/ **Radeon 780M 集显（无独立显卡）** / **15.2GB 内存**

> 本节全部截图由 `python scripts/regen_screenshots.py` 在**本机真实运行**后生成，
> 不是手工拼图。装好之后跑一遍就能复现全部数字。
> 历史版本（v1.0.0 - v1.0.3）的实测记录见 [`docs/releases/archive.md`](docs/releases/archive.md)。

### 实测 1：硬件扫描 + 可部署判定

![本机硬件扫描](docs/screenshots/06-实测截图-硬件扫描.png)

无独显的机器上，工具会如实给出 `cpu_only` 档位，而不是含糊其辞：

| 项目 | 本机实测输出 |
| --- | --- |
| 部署档位 | `cpu_only` |
| 可部署判定 | **137 个在架模型中 85 个可跑** |
| 提示口径 | 每个模型后标注 `Q4_K_M（CPU 慢速·显存需 X GB 不足）` |

一个连集显都算不上的推理环境，如果宣称「137 个模型全能跑」同样是谎报 ——
正确的做法是把「能跑，但只能 CPU 慢速」和「显存不够，跑不了」分开说清楚。

### 实测 2：137 模型分类清单

![137 模型分类](docs/screenshots/07-实测截图-137模型分类.png)

### 实测 3：本机 GPU 实测

![本机 GPU 实测](docs/screenshots/08-实测截图-nvidia-smi.png)

> 🔧 **v1.1.0 修掉的一处「截图会说谎」**：截图脚本原先在 `nvidia-smi` 不存在时，
> 会**硬编码编造**一段 `NVIDIA GeForce GTX 1660 Ti / 6144MiB / driver 595.97` 的输出。
> 等于在截图里凭空造出一张机器上根本没有的显卡。现在改为如实读本机 GPU：
> 没有 NVIDIA 卡就写「本机无 NVIDIA GPU」并列出真实的显卡信息。

### 实测 4：按本机硬件的部署建议

![可部署模型推荐](docs/screenshots/09-实测截图-推荐结果.png)

### 实测 5：EmbeddingGemma 2 评估（v1.1.0 新增）

![EmbeddingGemma 2 实测](docs/screenshots/15-实测截图-EmbeddingGemma2.png)

HF 实测 `safetensors.total = 744,371,512`，与官方模型卡声明的 740M 一致；
许可 `apache-2.0`，`lastModified 2026-10-06`。

### 实测 6：Strands Decider 2B 评估（v1.1.0 新增）

![Strands Decider 2B 实测](docs/screenshots/16-实测截图-strands-decider.png)

这个仓库的 `safetensors.total` 返回 `None` —— 因为它是 **LoRA adapter** 而非完整权重，
HF 元数据里没有标准参数字段。工具如实显示 `None`，`size_b` 取人工核对的 1.9B，
而不是拿一个看起来漂亮的假数字充数。

### 实测 7：模型库统计 + 体检（v1.1.0 新增）

![模型库统计](docs/screenshots/17-实测截图-模型库统计.png)

```bash
$ python scripts/lint_models.py --strict
模型库体检：138 个模型 · ERROR 0 · WARN 0 · INFO 0
✓ 全部通过
```

> 体检口径是**库内全部 138 条记录**（含 1 个已退役标注），
> 与 `list` 命令显示的 137 个在架模型是不同口径，不是矛盾。

### 实测 8：`auto_fetch_models.py --mode=stats`

![auto_fetch stats](docs/screenshots/13-实测截图-auto-fetch-stats.png)

### 实测 9：`auto_fetch_models.py --mode=patch`

![auto_fetch patch](docs/screenshots/14-实测截图-auto-fetch-patch.png)

每条生成条目带 `param_source: hf-safetensors`（总参来自 HF API 实测，
不再靠正则猜模型名），且 patch 输出前会先跑 `model_lint` 闸门，ERROR 的候选直接拦下列出原因。

---

## 🎯 解决什么问题？

部署开源大模型最怕「拿着过期文档做判断」：

- **模型迭代快**——3 个月前推荐的硬件，今天可能已被新模型超越
- **硬件价波动**——GPU 一年跌 30%+，3 个月前的报价严重过时
- **量化版本涌现**——昨天还没有的 GGUF，今天突然有人发布
- **手动调研累**——每个模型都要查 HF / GitHub / arXiv / 电商，时间成本极高
- **显存算错代价高**——把 MoE 的激活参当总参，会让你以为小显卡能跑大模型
- **闭源模型混进清单**——API-only 的模型被列成「可部署」，客户按清单买完硬件才发现跑不了

---

## 🏗️ 架构

```
用户 / Agent
  ↓
[CLI / MCP Server / HTTP API]          ← 三种入口，按场景选
  ↓
[5 步鉴别 + 硬件检测 + 部署脚本]
  ↓
[结构化显存层]（可序列化契约）
  └─ 6 档量化 × 多卡均分 × context 影响 × fits/tight/no 判定
  ↓
[动态数据源层]（智能缓存 24h）
  ├─ HuggingFace Hub API（模型元数据、safetensors 参数量、GGUF 文件）
  ├─ GitHub raw（官方 README、LICENSE）
  ├─ arXiv API（论文标题、摘要）
  └─ 硬件基准表（定期刷新）+ 本机硬件扫描
```

**交互式架构图**（archify-diagrams 生成，自包含 SVG，支持缩放 / 暗亮主题 / 演示模式）：
[`docs/archify/architecture.html`](docs/archify/architecture.html)

![架构图预览](docs/screenshots/12-archify-architecture.png)

---

## 💡 典型使用场景

**场景 1：客户问「本地跑 AI 要多少钱 / 我这台机器行不行」**
```
Agent → detect_hardware() → 137 个在架模型 → 85 个可跑 + 显存判定 → 客户决策
```

**场景 2：技术选型对比 DeepSeek vs Qwen3**
```
Agent → assess_model("deepseek-v3") + assess_model("qwen3-32b")
     → 含 6 档量化显存的结构化对比 → 选型
```

**场景 3：按显卡预算反查能跑的模型**
```
Agent → list_models(max_vram_gb=12) → 候选清单（按显存升序）→ 选型 + 部署脚本
```

**场景 4：客户问「我们能不能本地跑 Jev / 某个热榜模型」**
```
Agent → 查 KNOWN_MODELS → 不在库里
     → 查 references/jev-integration.md → 闭源 SaaS，只能 API 调
     → 给出可本地部署的开源对应物（Strands Decider 2B）+ assess 显存
```

---

## 📥 安装

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

详见 [`INSTALL.md`](INSTALL.md)。

---

## 🤝 贡献

### 添加新模型

在 `src/core/model_resolver.py` 的 `KNOWN_MODELS` 里加一条：

```python
"my-model": {
    "hf_repo": "org/Repo-Name",
    "github": "org/repo",
    "category": "domestic-general",
    "size_b": 7,
    "note": "一句话定位",
},
```

**请务必遵守**：

- `size_b` 取 **HuggingFace `safetensors.total` 实测值**（约 `total / 1e9`），
  **不要从模型名里正则抠**。`Llama-4-Scout-17B-16E` 里的 `17B` 是激活参不是总参
- MoE 模型**必须填 `activated_b`**，从模型卡或 `config.json`
  （`n_routed_experts` / `num_experts_per_token`）取
- 只有 LoRA/adapter 仓库时（`safetensors.total` 会是 `None`），
  `size_b` 按 base + adapter 的总量填，并在 `note` 里写明
- 填完跑一次体检，ERROR 必须清零：

```bash
python scripts/lint_models.py --strict
python scripts/check_readme_facts.py          # README 数字必须与代码一致
python -m pytest tests/ -q
python scripts/export_models_knowledge.py     # 同步知识库
python scripts/regen_screenshots.py           # 重拍实测截图
```

想省事的话，`auto_fetch_models.py --mode=patch` 会自动从 HF API 取实测总参
并过一遍 lint 闸门，但 `activated_b` 仍需人工核对。

---

## 📖 版本历史

| 版本 | 日期 | 模型数 | 重点 |
| --- | --- | ---: | --- |
| **v1.1.0** | 2026-10-15 | 137 | EmbeddingGemma 2（多模态 embedding）· Strands Decider 2B（System One 决策模型）· JEV 闭源鉴别 · 截图不再编造 nvidia-smi |
| v1.0.3 | 2026-10-03 | 135 | 修正 MoE 显存误判 · 显存需求结构化 · 模型库体检 CI 卡口 |
| v1.0.2 | 2026-09-26 | 127 | `auto_fetch_models.py` · 周日自动开 PR |
| v1.0.1 | 2026-09-10 | 94 | 每周自动刷新元数据 + GPU 价格 |
| v1.0.0 | 2026-08-15 | 47 | 首个版本 · 真实硬件推理实测 |

- Release notes：[`docs/releases/`](docs/releases/)
- 历史实测记录：[`docs/releases/archive.md`](docs/releases/archive.md)
- v1.1.0 完整说明：[`docs/releases/v1.1.0.md`](docs/releases/v1.1.0.md)
- MoE 踩坑复盘：[`docs/moe-vram-pitfall.md`](docs/moe-vram-pitfall.md)

---

## 📜 License

MIT © 汐构信息

## ☕ 支持这个项目

如果觉得有用，欢迎请作者喝杯咖啡 ☕

<div align="center">
  <img src="assets/coffee-qr.jpg" alt="请作者喝咖啡" width="300" />
</div>

**其他支持方式**：

- ⭐ Star 这个项目让更多人看到
- 🐛 提 Issue 报告 Bug 或建议新功能
- 🔀 提 PR 贡献代码或新模型
- 📢 分享给你的朋友和同事

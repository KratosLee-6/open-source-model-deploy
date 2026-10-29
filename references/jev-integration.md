---
slug: kratoslee-open-source-model-deploy-jev
displayName: Open Source Model Deploy · JEV / System One 决策模型
name: open-source-model-deploy-jev-integration
version: 2.1.0
updated: 2026-10-29
summary: TypeSafe Jev（闭源 SaaS，2026-09-15 发布）与 System One 决策模型的完整鉴别：为什么它进不了 KNOWN_MODELS、有哪些开源可本地部署的对应物（v1.1.1 起 12 个，单列第 9 类）、以及本工具库内的实测部署建议。
author: 汐构信息
license: MIT
keywords:
  - jev
  - typesafe
  - system-one
  - decision-model
  - strands-decider
  - browser-agent
  - external-saas
---

# 🔌 JEV / System One 决策模型鉴别

> **一句话结论**：Jev 是 TypeSafe AI 的**闭源 SaaS**（2026-09-15 发布，权重未公开），
> **不具备本地部署可能性**，因此**不进 `KNOWN_MODELS`**。
> 但它的开源可本地部署对应物（AWS Strands Decider 2B）已纳入本工具模型库，
> 可以真正跑 `assess` / `deploy`。

---

## 1. Jev 是什么（2026-10 最新核实）

| 维度 | 事实 | 来源 |
|---|---|---|
| 发布 | **2026-09-15**，early access | TypeSafe AI 官方博客 |
| 开发者 | TypeSafe AI（创始人 Diogo Almeida，前 OpenAI，参与 ChatGPT 背后的指令遵循研究） | 官方博客 |
| 模型类别 | **System One Model** —— 不生成文本，输出类型安全的结构化决策 | 官方博客 |
| 训练方法 | RLCD（Reinforcement Learning for Calibrated Decisions），并行采样（非自回归） | 官方博客 |
| 输出原语 | `Noul`（是/否概率）· `Choice`（N 选一）· `Score`（有序标尺打分） | 官方文档 |
| 延迟 | **70–500 ms**（对比 LLM 端到端 3–329 秒） | 官方博客 |
| 价格 | 输入 **$0.042 / MTok**，输出**免费** | 官方博客 |
| 上下文 | ~64k tokens（state + 全部问题） | 官方文档 |
| 接口 | `POST https://api.typesafe.ai/v1/systemone` · `model: jev-latest` → `jev-1.13.0` | 官方文档 |
| 开放度 | **闭源**：权重未发布、训练配方未公开、API-only | 官方博客 + 第三方核实 |
| 命名 | 取自 William Stanley Jevons（杰文斯悖论） | 官方博客 |

### 1.1 为什么它进不了 `KNOWN_MODELS`

本工具的 `KNOWN_MODELS` 语义是「**可本地部署的开源权重模型**」，每条记录都要能拉 HF 元数据、
算显存、生成 vLLM/Ollama 启动脚本。Jev 三条全部不满足：

| 判据 | Jev 的实际情况 | 结果 |
|---|---|---|
| 有开源权重（HF repo） | 无，官方从未发布权重 | ❌ |
| 可算显存 / 本地推理 | 无权重 ⇒ 无从计算 | ❌ |
| 可生成部署脚本 | 只能生成 API 调用代码，不是部署 | ❌ |
| ✅ **正确形态** | 作为**外部 SaaS** 在 `references/` + `templates/` 记录 | → 本文档 |

> 把 Jev 塞进模型库会让 `list` / `detect` 说谎 —— 用户会以为它像 Qwen3 一样能下载下来跑。
> v1.0.3 刚修掉「MoE 按激活参算显存」那类误导，这里沿用同一条原则：**不让工具输出超出事实的结论。**

### 1.2 生态实测（发布后第一周）

| 指标 | 数值 |
|---|---:|
| 新建 GitHub 仓库 | 1,865 个（另 305 个既有仓库接入） |
| 累计 star | 43,750 |
| 第三方基准 | Jevals（独立 Jev benchmark）、JevBench |

---

## 2. 开源可本地部署的对应物（✅ 本工具覆盖，v1.1.1 起共 12 个）

Jev 关上了权重，社区在两周内补上了可下载的同类模型。
**v1.1.1 起这些模型单列为第 9 类「决策模型 / System One」**（`category: "decision"`），
可以用 `osm-deploy list --category decision` 单独列出。

| 模型 | 规模 | 许可 | 本工具状态 | 说明 |
|---|---|---:|---|---|
| **AutoTrust JEV-9B** | 8.95B | Apache-2.0 | ✅ `autotrust-jev-9b` | Jev 1.13 蒸馏学生（Qwen3.5-9B + LoRA + 24 槽决策头），noul AUROC 0.996，29,955 题留出集上与教师选项一致率 87.5% |
| **AutoTrust JEV-27B** | 26.9B | Apache-2.0 | ✅ `autotrust-jev-27b` | Qwen3.8-27B 底座，6 基准平均 **84.07%**，反超闭源教师 Jev 1.13（83.85%），4/6 基准胜出，单张 B200 约 140ms |
| **AutoTrust JEV-35B** | 35.95B / 3B | Apache-2.0 | ✅ `autotrust-jev-35b` | Qwen3.5-35B-A3B MoE，HF **147 万下载**，已在生产环境跑实时新闻推荐 |
| **Cloudflare Clef 27B** | 27.36B | Apache-2.0 | ✅ `cloudflare-clef-27b` | Qwen3.8-27B 底座 + **图像输入**（state 可带图），Ollama 0.35.1 起原生支持 `/v1/systemone` |
| **Cloudflare Clef Flash 9B** | 9.41B | Apache-2.0 | ✅ `cloudflare-clef-flash-9b` | Qwen3.5-9B 底座轻量版，3090 + Ollama 实测 12.8GB 占用、约 220ms |
| **Laya 0.4B** | 0.42B | Apache-2.0 | ✅ `convai-laya` | 最受欢迎（5,852 likes），RLCD 训练，约 **33ms**，pip 可装且自带 MCP extra |
| **Laya 多语言版** | 0.32B | Apache-2.0 | ✅ `convai-laya-multilingual` | 100+ 语言，上下文 8k tokens |
| **OpenJEV 27B** | 27.36B | CC BY-NC 4.0 | ✅ `openjev-openjev-27b` | 开放权重复刻 `/v1/systemone` 请求形状，文本/网页/截图三态，最多 52 选项 ⚠️ **非商用许可** |
| **Juspay XOR 35B** | 35.11B | Apache-2.0 | ✅ `juspay-xor-35b` | 工业级变体，Qwen3.6-35B-A3B 后训练，最多 255 候选，SGLang 部署 |
| **THX-01** | 0.32B | Apache-2.0 | ✅ `doofz-thx-01` | 非自回归 mmBERT（约 322M），单次决策约 **10ms**，多语言（az/en/ru/tr/de），最小可用决策模型 |
| **Mapika Decider 2B** | 1.88B | Apache-2.0 | ✅ `mapika-decider-2b` | System One 模型类的明确开源复刻，本波使用最广 |
| **AWS Strands Decider 2B** | 1.9B | Apache-2.0 | ✅ `strands-decider-2b` | v1.1.0 已收，Qwen3.5-2B-Base + LoRA + 读出头，RTX 3090 中位 115ms，可 CPU / Apple Silicon。⚠️ HF 仓库只存 91.5MB adapter，需另配 base 模型 |

**v1.1.0 时的结论**（2026-10-15 核实）：这一波里「只有 Strands Decider 2B 能真跑」。
**v1.1.1 复核**（2026-10-29）：社区产出速度远超预期 ——
**AutoTrust JEV-27B 已经反超闭源教师**，且出现了 0.32B 的 10ms 级模型，
这一类不再是「只有一个勉强能跑的」。

### 2.1 设备可用性（v1.1.1 补齐）

| 档位 | 能跑的决策模型 | 延迟参考 |
|---|---|---|
| **CPU / 6GB 显卡** | THX-01 (0.32B) · Laya 多语言版 (0.32B) · Laya (0.42B) · Decider 2B (1.88B) · Strands Decider 2B (1.9B) | THX-01 ~10ms · Laya ~33ms · Strands Decider ~115ms(3090) |
| **8–12GB 显卡** | + Clef Flash 9B · JEV-9B | Clef Flash 3090 实测 ~220ms |
| **16–24GB 显卡** | + Clef 27B · JEV-27B · XOR 35B（Q4 量化） | JEV-27B B200 ~140ms |
| **多卡 / 服务器** | JEV-35B · OpenJEV 27B | — |
| **纯云 API（无本地算力）** | TypeSafe Jev 1.13 / 1.14 | $0.042/MTok 输入，输出免费 |

**部署形态**：`decision` 分类的 `osm-deploy deploy <model>` 自动选
vLLM（CUDA）/ llama.cpp（CPU），起 OpenAI 兼容 server 后用
`/v1/systemone` 风格的客户端问 `noul` / `choice` / `score`。

---

## 3. 如果确实要用 Jev：env 模板

文件：`templates/jev-env.example`（复制为 `.env` 填值）

```bash
# ============ TypeSafe SaaS（判定模型）============
TYPESAFE_API_KEY=tsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TYPESAFE_MODEL=jev-latest          # 默认 latest；可锁 jev-1.13.0 / jev-1.12.0
TYPESAFE_BASE_URL=https://api.typesafe.ai/v1/systemone

# ============ 文本生成（OpenAI-compatible）============
# Jev 不生成文本，字段填充仍需一个 LLM
TEXT_MODEL_API_KEY=«redacted:sk-…»
TEXT_MODEL_BASE_URL=https://api.deepseek.com/v1
TEXT_MODEL=deepseek-chat
TEXT_MODEL_REASONING=none          # none / low / medium / high

# ============ 框架开关 ============
JEV_TEXT_HELPER_BUDGET_TOKENS=1024
JEV_REQUEST_BUDGET=50              # 浏览器操作预算
JEV_DECISION_TIMEOUT_MS=25000
```

**成本量级**：Jev 输入 $0.042/MTok、输出免费；真正花钱的是同一个任务里的文本模型
（填字段/写文案），所以选对 `TEXT_MODEL` 才是降本关键 —— 这正是本工具 `assess` 能帮上忙的地方。

---

## 4. 浏览器 Agent 框架（jev-ultrafast）

| 维度 | 事实 |
|---|---|
| 仓库 | [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) · MIT |
| 核心循环 | `agent.py` · 浏览器观察 → TypeSafe API 判定 → 浏览器执行 → 循环 |
| 判定模型 | TypeSafe Jev（**闭源 SaaS**） |
| 文本生成 | OpenAI-compatible，默认 DeepSeek Chat |
| 操作空间 | `CLICK / TYPE_TEXT / SELECT / SCROLL_UP/DOWN / WAIT / DONE / BLOCKED` |
| 安装脚本 | `scripts/jev_ultrafast_install.sh` / `.ps1`（本仓库已交付） |

> ⚠️ 与本仓库**无隶属关系**，仅做工具层面推荐。商用前确认
> [typesafe.ai](https://docs.typesafe.ai/introduction) 条款。

---

## 5. 设备适配（整链路需求）

> Jev 本体不耗本地算力 —— TypeSafe 在云。真正吃硬件的是**浏览器 + Chromium**
> 以及可选的**本地文本模型**。

| 设备 | 跑 Jev 链路 | 本地文本模型建议 | 本地决策模型（可替代 Jev） |
|---|---|---|---|
| 笔记本 6GB 显卡 | ✅ Chromium + API | Qwen3-4B / 8B Q4 | Strands Decider 2B（1.4 GB） |
| RTX 3060 12GB | ✅ | Qwen3-8B BF16 本地 | Strands Decider 2B 全本地 |
| RTX 4090 24GB | ✅ | Qwen3-32B BF16 全本地 | 全栈本地化 |
| Apple M 系列 | ✅ | Ollama + Qwen3-8B | Strands Decider 2B（CPU/MPS 可跑） |

---

## 6. 关键洞察

1. **闭源 ≠ 不能推荐**：Jev 代表一类新形态（System One 决策模型），
   它的价值是「把 LLM 的自由度换成可嵌入代码的确定性」，这对 agent 工作流是刚需。
2. **但工具必须诚实**：它没有权重，就不能出现在「可部署模型清单」里。
   我们把它放在 `references/`，并在模型库里放**能真跑**的 Strands Decider 2B。
3. **降本点在文本模型**：Jev 输出免费、输入极便宜，整条链路的主要成本是配合它的 LLM。
   用 `osm-deploy detect` 选出本机能跑的文本模型，才是省钱的正确姿势。

---

## 7. 免责

1. **TypeSafe Jev 是闭源 SaaS**：本仓库推荐它但不托管它，权重从未发布。
2. 价格 / 延迟 / 版本号以官方为准，本文档核实时点：**2026-10-15**。
3. `browser-use/jev-ultrafast` 为第三方项目，与本仓库无隶属关系。
4. 开源替代模型（Strands Decider 2B 等）的参数、许可、显存均来自 HF 实测或官方模型卡。

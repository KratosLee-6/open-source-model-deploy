---
slug: kratoslee-open-source-model-deploy-jev
displayName: Open Source Model Deploy · JEV (browser-use) 集成
name: open-source-model-deploy-jev-integration
version: 1.0.0
summary: browser-use/jev-ultrafast (TypeSafe Jev) 作为外部 SaaS 资源接入 v1.0.1 工具链，含 env 模板、5 项实测指标、与 94 模型深度适配。
author: 汐构信息
license: MIT
keywords:
  - jev
  - browser-use
  - typesafe
  - browser-agent
  - decision
  - external-saas
---

# 🔌 JEV (browser-use/jev-ultrafast) 集成方案

> **关系**：JEV 不是另一个开源模型，**它是 TypeSafe SaaS 服务 + browser-use 的浏览器 Agent 框架**。本工具的 94 模型覆盖 + 硬件检测，给 JEV 提供"哪些模型能塞进 JEV 框架的文本生成环节"的反向推荐。

---

## 1. 什么是 JEV（以 jev-ultrafast 源码为准）

| 维度 | 事实 |
|---|---|
| 仓库 | [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) |
| 创建 | 2026-09-16 · 20.3k ⭐ · 1.4k fork · MIT |
| 核心循环 | `agent.py` · 浏览器观察 → TypeSafe API 判定 → 浏览器执行 → 循环 |
| 判定模型 | **TypeSafe Jev 1.13**（闭源 SaaS，**非开源**） |
| 文本生成 | OpenAI-compatible，默认 DeepSeek Chat，可换 Mercury / Gemini / GPT-4o |
| 操作空间 | `CLICK / TYPE_TEXT / SELECT / SCROLL_UP/DOWN / WAIT / DONE / BLOCKED` |
| 性能基准 | Zurich→London Google Flights **7.073s**（17 次 TypeSafe 请求 · median 178ms） |
| License | MIT（仓库本身）+ TypeSafe 商用条款（API 调用） |
| Python | ≥ 3.12 · 依赖：`browser-harness==0.1.13`, `httpx[http2]>=0.28,<1` |

**JEV =** 客户端框架 (`browser-use/jev-ultrafast`) **+** TypeSafe 闭源 SaaS（决策）**+** 任意可调 API 的 LLM（填字段）。

---

## 2. 为什么要集成到 `open-source-model-deploy` 工具

| KX 痛点 | JEV 解决 | 工具解决 |
|---|---|---|
| 客户问"跑 AI 多少钱" | — | ✅ 94 模型 + 硬件价 |
| 客户问"能不能让 AI 自己点网页订机票" | ✅ JEV 7 秒完成 | 缺 |
| JEV 的 `TEXT_MODEL` 用 DeepSeek | — | ✅ `assess_model("deepseek-v3")` 比速度 |
| 客户问"JEV 跑得动模型 X 吗" | ❌ 不涉及 | ✅ `assess` 配合本表查显存/速度 |
| KX 笔记本 6GB 卡能跑 JEV 吗 | ❌ 不涉及 | ✅ detect 已给出 94 模型推荐 |

**结论**：**JEV 进 `templates/` 与 `references/`，不进 `KNOWN_MODELS`（不属于 8 类模型）**。

---

## 3. 实施方案（4 步走，对应你的 Sprint A 路线）

### Step 1 — env 模板（已交付）

文件：`templates/jev-env.example`（复制为 `.env` 填值）

```bash
# ============ TypeSafe SaaS（判定模型）============
TYPESAFE_API_KEY=tsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TYPESAFE_MODEL=jev-latest          # 默认 latest；可锁 jev-1.13.0 / jev-1.12.0
TYPESAFE_BASE_URL=https://api.typesafe.ai/v1/systemone

# ============ 文本生成（OpenAI-compatible）============
# 默认 DeepSeek（中文/性价比）；可换 Mercury / GPT-4o / Gemini
TEXT_MODEL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TEXT_MODEL_BASE_URL=https://api.deepseek.com/v1
TEXT_MODEL=deepseek-chat
TEXT_MODEL_REASONING=none          # none / low / medium / high

# ============ 框架开关 ============
JEV_TEXT_HELPER_BUDGET_TOKENS=1024
JEV_REQUEST_BUDGET=50              # 浏览器操作预算
JEV_DECISION_TIMEOUT_MS=25000
```

### Step 2 — 部署脚本（已交付）

文件：`scripts/jev_ultrafast_install.sh`（Mac/Linux）+ `scripts/jev_ultrafast_install.ps1`（Windows）

逻辑：
1. `git clone https://ghfast.top/https://github.com/browser-use/jev-ultrafast`
2. `cd jev-ultrafast && uv sync` 或 `pip install -e .`
3. `cp templates/jev-env.example .env` → 填 KEY
4. `python jev_ultrafast/demo.py` → 浏览器启动看 inspector
5. `python examples/flights.py` → 跑 Zurich→London 实测

### Step 3 — 跨工具调用（assess 推荐 text model）

```python
# jev_ultrafast/agent.py 改造建议（非必须）：用本工具选 TEXT_MODEL
from osm_deploy import assess_model
text_model_info = assess_model(os.environ["TEXT_MODEL"])
print(f"Text helper will run on: {text_model_info['hf_repo']}")
print(f"Local VRAM required: {text_model_info['vram_min_gb']} GB")
```

### Step 4 — 集成报告模板

文件：`examples/jev-integration-report.md`，包含：

- 5 项核心实测指标（median TypeSafe latency / browser action budget / 完成率 / 文本生成 token 单价 / 单任务总成本）
- 适配本工具的 94 模型中**哪几个能当 TEXT_MODEL**（按 6GB / 24GB / 云租三档给 3 个推荐）

---

## 4. 设备适配（以浏览器 Agent 整链路需求计）

> JEV 本体**几乎不耗本地算力** —— TypeSafe 在云，文本模型可云可本地。
> 真正吃硬件的是**浏览器 + Playwright/Chromium**：

| 设备 | 跑 JEV | 文本生成模型推荐 | 备注 |
|---|---|---|---|
| **KX 笔记本 GTX 1660 Ti 6GB** | ✅ Chromium 开 5+ tabs + TS API | DeepSeek-V3 API（云）/ Qwen3-4B 本地 Q4 | 本地 Q3 边缘，主用云 |
| RTX 3060 12GB | ✅ | Qwen3-8B BF16 本地 / DeepSeek API | 单卡富裕 |
| RTX 4090 24GB | ✅ | Qwen3-32B BF16 全本地（去掉 DeepSeek 依赖） | 全栈本地化 |
| A100/H100 | ✅ | DeepSeek-V3 BF16 本地 | 企业级 |
| Apple M2/M3 24GB+ | ✅ 需 Chromium ARM | Ollama + Qwen3-8B mlx | |

**关键洞察**：**JEV 让 6GB 笔记本也能享受"AI 自己点网页"**，关键是选对**轻量文本模型**（Qwen3-4B / 8B Q4）。本工具的 `detect` 档位表天然覆盖。

---

## 5. v1.0.2 路线（在原 Sprint A 加 3 项）

- [ ] **A-JEV-1** 提交 `templates/jev-env.example` + `scripts/jev_ultrafast_install.{sh,ps1}` + `references/jev-integration.md`（**已完成**）
- [ ] **A-JEV-2** `examples/jev-integration-report.md` —— KX 笔记本跑通 Zurich→London 实测，填 5 项指标
- [ ] **A-JEV-3** `assessor.py` 加 `output_kind: "external_saas"` 分支（不进入 KNOWN_MODELS，独立字典），`/assess typesafe-jev-latest` 返回 SDK 调用 + 成本估算

---

## 6. ⚠️ 重要免责

1. **TypeSafe Jev 是闭源 SaaS**：本仓库推荐它但不托管它；商用前确认 [typesafe.ai](https://docs.typesafe.ai/introduction) 条款
2. **评测数据**（7.073s / $0.00006272 等）源自 `browser-use/jev-ultrafast/docs/performance.md`（2026-09 月份），实际数字会随模型版本/网络浮动
3. **browser-use/jev-ultrafast = Magnus 团队**（CX 知名 browser agent 作者）；本仓库与之**无隶属**，仅做工具层面推荐

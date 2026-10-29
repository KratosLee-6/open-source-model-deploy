---
slug: kratoslee-open-source-model-deploy-decision
displayName: Open Source Model Deploy · 决策模型部署手册
name: open-source-model-deploy-decision-models
version: 1.0.0
updated: 2026-10-29
summary: System One 决策模型（noul/choice/score 三原语）的部署与调用手册：两种接口标准、三种部署形态、12 个模型各自的真实启动命令与端口、以及它们和聊天模型的本质区别。
author: 汐构信息
license: MIT
keywords:
  - decision-model
  - system-one
  - jev
  - noul
  - choice
  - score
  - calibration
---

# 🧠 决策模型部署手册（System One）

> **一句话**：决策模型不是聊天模型。它**不生成文本**，输入「状态 + 类型化问题」，
> 一次前向返回**校准概率**。所以它的部署方式、接口、甚至返回值都和 `vllm serve` 那套不一样。

本文覆盖 `category: "decision"` 的 12 个模型。所有命令来自各模型 HF model card 的代码块
（2026-10-29 逐个核对），不是推测。

---

## 1. 三原语：noul / choice / score

| 原语 | 含义 | 输入 | 输出 |
|---|---|---|---|
| **noul** | 是非判断 | 一个问题 | `true` / `false` 的概率 |
| **choice** | N 选一 | 问题 + 2–255 个选项 | 每个选项的概率分布 |
| **score** | 有序打分 | 问题 + **有序**档位列表 | 落在某档的概率 / 期望分 |

**为什么校准很重要**：输出的是概率，不是文本 —— 值钱的地方在于可以写进代码判断：

```python
if p_billing > 0.90:
    auto_route("billing")      # 高置信度自动处理
else:
    human_review(ticket)       # 低置信度转人工
```

> ⚠️ 阈值不能凭感觉定。概率是模型估计，**必须在你的业务分布上校准或监控**
> （这也是本工具后续要做「阈值建议」的原因）。

---

## 2. 两种接口标准（关键：别混用）

### `/v1/decide` —— 单题一问

```json
{
  "kind": "choice",
  "state": "Customer message: my card was charged twice.",
  "question": "Which team should handle this ticket?",
  "options": ["billing", "shipping", "technical support"]
}
```

返回 `{"options": [...], "probabilities": [...]}`，27B 还会带 `choice_index` / `choice`。

**用在**：AutoTrust JEV-9B / 27B / 35B、THX-01（路径）

### `/v1/systemone` —— 一次问多题

```json
{
  "state": "Our checkout started returning errors and orders are blocked.",
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which team should handle the message?",
      "criteria": {"billing": "Payments or invoices", "technical": "Bugs or outages"}
    },
    "urgency": {"type": "score", "criteria": ["Can wait", "This week", "Today"]},
    "outage": {"type": "noul", "instructions": "Is a service down?"}
  }
}
```

返回 `{"answers": {"department": {"choice": "billing", "confidence": 0.94}, ...}}`。

**用在**：Cloudflare Clef / Clef Flash、Laya 系、OpenJEV、Juspay XOR、Decider 2B、Strands Decider

### ⚠️ 反例：THX-01 是「路径 `/v1/decide` + body `systemone`」

官方原话：`POST /v1/decide`（**别名** `POST /v1/systemone`，TypeSafe-compatible）
takes `{"state": ..., "questions": {...}}`。

也就是说 **URL 路径和 body 格式是两件事**。本工具在
`src/core/decision_recipes.py` 里用 `endpoint`（路径）和 `body_format`（body 形状）
两个字段分开记录，就是为了避免这种错配。

---

## 3. 三种部署形态

| 形态 | 含义 | 例子 |
|---|---|---|
| **service** | 起一个 REST 服务 | JEV 系、Clef 系、OpenJEV、XOR |
| **library** | pip 装完 import 就能用，**没有服务** | Laya 多语言版 |
| **hybrid** | 两种都提供 | Laya、THX-01、Decider 2B、Strands Decider |

> **别对 library 形态找端口** —— 它压根没有服务。`osm-deploy deploy` 会明确标出
> 「进程内调用（无 REST 服务）」并给 Python 代码而不是 curl。

---

## 4. 12 个模型对照表

| 模型 | 形态 | 框架 | 接口 | 端口 | 启动入口 |
|---|---|---|---|---|---|
| **AutoTrust JEV-9B** | service | vLLM + LoRA | `/v1/decide` | 8000 | `vllm serve JEV-9B --enable-lora --lora-modules jev-decision=.../adapter_vllm` |
| **AutoTrust JEV-27B** | service | vLLM + LoRA | `/v1/decide` | 8000 | `python3 JEV-27B/serve_decide.py` |
| **AutoTrust JEV-35B** | service | vLLM | `/v1/decide` | 8000 | `bash JEV-35B/serve.sh` |
| **Cloudflare Clef 27B** | service | SGLang | `/v1/systemone` | **30000** | `sglang serve --model-path Cloudflare/clef` |
| **Cloudflare Clef Flash 9B** | service | SGLang | `/v1/systemone` | **30000** | 同上，换 model-path |
| **Convai Laya 0.4B** | hybrid | pip `laya` | `/v1/systemone` | 8000 | `from laya import Router` 或 `laya-serve` |
| **Convai Laya 多语言 0.3B** | library | pip `laya` | `/v1/systemone` | — | `laya.load(".../laya-multilingual")` |
| **OpenJEV 27B** | service | vLLM + shim | `/v1/systemone` | **3000** | 两步：vLLM(:8000) → `shim.py`(:3000) |
| **Juspay XOR 35B** | service | SGLang | `/v1/systemone` | **30002** | `./run.sh`（自带 checksum 校验） |
| **THX-01 0.32B** | hybrid | pip `thx01` | `/v1/decide`¹ | **8095** | `python -m thx01.server --port 8095` |
| **Mapika Decider 2B** | hybrid | pip `decider-ai` | `/v1/systemone` | 8000 | `uvicorn decider.serve:app` |
| **AWS Strands Decider 2B** | hybrid | pip `strands-decider` | `/v1/systemone` | 8000 | `strands-decider serve ... --port 8000` |

¹ THX-01 路径是 `/v1/decide` 但 body 用 `systemone` 格式，见 §2 反例。

**端口不统一是真实情况** —— 3000 / 8000 / 8095 / 30000 / 30002 都有。
套用默认 8000 会连不上。

---

## 5. 设备能用性

| 档位 | 能跑的决策模型 | 延迟参考 |
|---|---|---|
| **CPU / 6GB 显卡** | THX-01 (0.32B) · Laya 多语言 (0.32B) · Laya (0.42B) · Decider 2B (1.88B) · Strands Decider 2B (1.9B) | THX-01 ~10ms · Laya ~33ms · Strands Decider ~115ms(3090) |
| **8–12GB** | + Clef Flash 9B (9.41B) · JEV-9B (8.95B) | Clef Flash 3090 约 220ms/3 题 |
| **16–24GB** | + Clef 27B · JEV-27B（Q4） · XOR 35B（Q4） | JEV-27B B200 ~140ms |
| **80GB 单卡** | JEV-35B · JEV-27B（BF16） · OpenJEV 27B | — |
| **纯云 API** | TypeSafe Jev 1.13 / 1.14（闭源） | $0.042/MTok 输入，输出免费 |

> MoE 模型（JEV-35B 35.95B/3B、XOR 35B）**显存按总参算**，不是按激活参。
> 稀疏激活只降 FLOPs，不降权重占用 —— 这是 v1.0.3 修过的坑，见
> [`docs/moe-vram-pitfall.md`](../docs/moe-vram-pitfall.md)。

---

## 6. 怎么用

```bash
# 看接口 + 启动命令 + 真实请求示例（一次给全）
osm-deploy deploy autotrust-jev-9b

# 只看这一类的全部模型
osm-deploy list --category decision

# 算显存 / 可行性
osm-deploy assess autotrust-jev-9b
```

`deploy` 对决策模型输出六段：**接口 → 安装 → 运行 → 健康检查 → 真实请求(curl + Python) → 注意**。
其中「真实请求」是能直接跑的，不是示意。

---

## 7. 常见坑（都是实测踩到的）

| 坑 | 后果 | 正解 |
|---|---|---|
| 用 `vllm serve <repo>` 直接起 JEV | 起的是纯 Qwen，**没有决策头** | 必须 `--enable-lora --lora-modules jev-decision=<repo>/adapter_vllm` |
| 缺 `--logprobs-mode processed_logprobs` | 读不到校准概率 | JEV 系必加 |
| 套默认端口 8000 | Clef 在 30000、OpenJEV 在 3000、XOR 在 30002 | 按模型表来 |
| 只起 OpenJEV 的 vLLM | 拿不到 `/v1/systemone` | 要再起 `shim.py`（:3000），对外只暴露它 |
| 对 library 形态找端口 | 它没有服务 | `laya.load()` 进程内调用 |
| Strands Decider 直接部署 | HF 仓库只有 91.5MB adapter | 必须另配 `Qwen/Qwen3.5-2B-Base` |
| 把 `decide` 的三原语当聊天问 | 拿不到概率 | 三原语有固定 schema，见 §1 |
| OpenJEV 用于商用 | 许可 **CC BY-NC 4.0** | 非商用；商用换模型或单独授权 |

---

## 8. 许可

| 许可 | 模型 |
|---|---|
| **Apache-2.0** | JEV 系（9B/27B/35B）· Clef 系 · Laya 系 · XOR · THX-01 · Decider 2B · Strands Decider |
| **CC BY-NC 4.0** ⚠️ | **OpenJEV 27B —— 非商用** |

商用部署前请核对当前许可（以 HF model card 为准）。

---

## 9. 维护方式

模型配方固化在 `src/core/decision_recipes.py`，每条都标了数据来源。新增决策模型时：

```bash
# 1. 拉 model card，提取真实启动命令 / 接口 / 端口
python scripts/verify_decision_endpoints.py

# 2. 把命令抄进 decision_recipes.py（endpoint 和 body_format 分开填）

# 3. 测试会强制检查：配方是否覆盖全部 decision 模型、字段是否完整、
#    示例 body 是否符合对应 body_format
python -m pytest tests/test_decision_recipes.py -q
```

**不确定就不写** —— 没有配方的模型会明确输出「⚠️ 未核实」，而不是编一条看起来合理的命令。

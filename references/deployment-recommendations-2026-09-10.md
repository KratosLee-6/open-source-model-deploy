# 47 个开源模型部署建议 · 2026-09-10 14:34 自动生成

> **目标场景**: 云租按量（H100/A100）
> **HF 元数据快照**: 2026-09-10T14:34:15
> **GPU 价格快照**: 2026-09-10T14:34:41
> **生成方式**: GitHub Actions 每周自动跑 (`scripts/render_report.py`)
> **手动重生成**: `python3 scripts/render_report.py --target=cloud`

---

## 内存估算公式

- **fp16** = `2 × size_b` GB
- **Q4 量化** ≈ `0.5 × size_b` GB
- **MoE**: fp16 按 total size 算，推理激活 `activated_b`

---


## 🟢 国内通用 (9 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen3-8b | `Qwen/Qwen3-8B` | 8.0B | 12,883,281 | ✓ 云租 (16GB fp16) | vLLM |
| qwen3-14b | `Qwen/Qwen3-14B` | 14.0B | 1,676,957 | ✓ 云租 (28GB fp16) | vLLM |
| qwen3-32b | `Qwen/Qwen3-32B` | 32.0B | 5,212,359 | ✓ 云租 (64GB fp16) | vLLM |
| glm-4-32b | `THUDM/glm-4-32b-0414` | 32.0B | N/A | ✓ 云租 (64GB fp16) | vLLM |
| qwen3-235b-a22b | `Qwen/Qwen3-235B-A22B` | 235.0B | 346,243 | ✓ 云租 (470GB fp16) | vLLM |
| deepseek-v2.5 | `deepseek-ai/DeepSeek-V2.5` | 236.0B | 5,831 | ✓ 云租 (472GB fp16) | vLLM |
| glm-4.5 | `THUDM/GLM-4.5` | 355.0B | N/A | ✓ 云租 (710GB fp16) | vLLM |
| deepseek-v3 | `deepseek-ai/DeepSeek-V3` | 671.0B | 1,065,138 | ✓ 云租 (1342GB fp16) | vLLM |
| kimi-k2 | `moonshotai/Kimi-K2-Instruct` | 1000.0B | 169,441 | ✓ 云租 (2000GB fp16) | vLLM |

## 🧠 国内推理 (10 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| deepseek-r1-distill-qwen-1.5b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 1.5B | 416,880 | ✓ 云租 (3GB fp16) | vLLM |
| deepseek-r1-distill-qwen-7b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 7.0B | 359,985 | ✓ 云租 (14GB fp16) | vLLM |
| deepseek-r1-distill-llama-8b | `deepseek-ai/DeepSeek-R1-Distill-Llama-8B` | 8.0B | 334,184 | ✓ 云租 (16GB fp16) | vLLM |
| deepseek-r1-distill-qwen-14b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 14.0B | 347,879 | ✓ 云租 (28GB fp16) | vLLM |
| qwq-32b-preview | `Qwen/QwQ-32B-Preview` | 32.0B | 10,160 | ✓ 云租 (64GB fp16) | vLLM |
| glm-z1-32b | `THUDM/GLM-Z1-32B-0414` | 32.0B | 50,606 | ✓ 云租 (64GB fp16) | vLLM |
| qwq-32b | `Qwen/QwQ-32B` | 32.0B | 75,026 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-r1-distill-qwen-32b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | 32.0B | 522,681 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-r1-distill-llama-70b | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | 70.0B | 76,970 | ✓ 云租 (140GB fp16) | vLLM |
| deepseek-r1 | `deepseek-ai/DeepSeek-R1` | 671.0B | 709,327 | ✓ 云租 (1342GB fp16) | vLLM |

## 💻 代码专用 (6 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen2.5-coder-7b | `Qwen/Qwen2.5-Coder-7B-Instruct` | 7.0B | 2,712,497 | ✓ 云租 (14GB fp16) | vLLM |
| deepseek-coder-v2-lite | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | 16.0B | 754,668 | ✓ 云租 (32GB fp16) | vLLM |
| codestral-22b | `mistralai/Codestral-22B-v0.1` | 22.0B | 5,899 | ✓ 云租 (44GB fp16) | vLLM |
| qwen3-coder-30b | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 30.0B | 692,826 | ✓ 云租 (60GB fp16) | vLLM |
| qwen2.5-coder-32b | `Qwen/Qwen2.5-Coder-32B-Instruct` | 32.0B | 1,547,400 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-coder-v2 | `deepseek-ai/DeepSeek-Coder-V2-Instruct` | 236.0B | 10,491 | ✓ 云租 (472GB fp16) | vLLM |

## 👁️ 视觉多模态 (5 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen2.5-vl-7b | `Qwen/Qwen2.5-VL-7B-Instruct` | 7.0B | 7,682,009 | ✓ 云租 (14GB fp16) | vLLM |
| llava-onevision-qwen2-7b | `lmms-lab/llava-onevision-qwen2-7b-ov` | 7.0B | 34,873 | ✓ 云租 (14GB fp16) | vLLM |
| internvl3-8b | `OpenGVLab/InternVL3-8B` | 8.0B | 100,771 | ✓ 云租 (16GB fp16) | vLLM |
| qwen2.5-vl-72b | `Qwen/Qwen2.5-VL-72B-Instruct` | 72.0B | 157,221 | ✓ 云租 (144GB fp16) | vLLM |
| internvl3-78b | `OpenGVLab/InternVL3-78B` | 78.0B | 14,269 | ✓ 云租 (156GB fp16) | vLLM |

## 🌍 国际密集 (5 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| mistral-small-3 | `mistralai/Mistral-Small-3` | 22.0B | N/A | ✓ 云租 (44GB fp16) | vLLM |
| gemma-3-27b | `google/gemma-3-27b-it` | 27.0B | 360,496 | ✓ 云租 (54GB fp16) | vLLM |
| llama-3.1-70b | `meta-llama/Llama-3.1-70B` | 70.0B | 42,776 | ✓ 云租 (140GB fp16) | vLLM |
| mistral-large-2 | `mistralai/Mistral-Large-Instruct-2407` | 123.0B | 4,929 | ✓ 云租 (246GB fp16) | vLLM |
| llama-3.1-405b | `meta-llama/Llama-3.1-405B` | 405.0B | 131,924 | ✓ 云租 (810GB fp16) | vLLM |

## ⚡ 国际边缘 (7 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| llama-3.2-1b | `meta-llama/Llama-3.2-1B` | 1.0B | 1,246,103 | ✓ 云租 (2GB fp16) | vLLM |
| llama-3.2-3b | `meta-llama/Llama-3.2-3B` | 3.0B | 355,044 | ✓ 云租 (6GB fp16) | vLLM |
| phi-4-mini | `microsoft/Phi-4-mini-instruct` | 3.8B | 457,692 | ✓ 云租 (8GB fp16) | vLLM |
| phi-3.5-mini | `microsoft/Phi-3.5-mini-instruct` | 3.8B | 356,127 | ✓ 云租 (8GB fp16) | vLLM |
| gemma-3-4b | `google/gemma-3-4b-it` | 4.0B | 1,668,779 | ✓ 云租 (8GB fp16) | vLLM |
| gemma-3-9b | `google/gemma-3-9b-it` | 9.0B | N/A | ✓ 云租 (18GB fp16) | vLLM |
| phi-4 | `microsoft/phi-4` | 14.0B | 711,395 | ✓ 云租 (28GB fp16) | vLLM |

## 🔢 Embedding (4 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| bge-large-zh-v1.5 | `BAAI/bge-large-zh-v1.5` | 0.3B | 1,181,768 | ✓ 云租 (1GB fp16) | vLLM |
| bge-m3 | `BAAI/bge-m3` | 0.6B | 37,891,167 | ✓ 云租 (1GB fp16) | vLLM |
| gte-qwen2-7b-instruct | `Alibaba-NLP/gte-Qwen2-7B-instruct` | 7.0B | 111,229 | ✓ 云租 (14GB fp16) | vLLM |
| qwen3-embedding-8b | `Qwen/Qwen3-Embedding-8B` | 8.0B | 2,253,605 | ✓ 云租 (16GB fp16) | vLLM |

## 📊 Reranker (1 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| bge-reranker-v2-m3 | `BAAI/bge-reranker-v2-m3` | 0.6B | 18,212,308 | ✓ 云租 (1GB fp16) | vLLM |

---

## 🎯 实战推荐组合（按预算）

| 预算 | 推荐方案 |
|---|---|
| **0 元**（笔记本）| deepseek-r1-distill-qwen-1.5b + bge-m3 + bge-reranker-v2-m3 |
| **$500-800** | RTX 5060 Ti 16GB（一次性）+ qwen3-8b + deepseek-r1-distill-qwen-14b |
| **$1000-1500** | RTX 5080 16GB（一次性）+ qwen3-32b + qwen2.5-vl-7b |
| **$2000-2500** | RTX 5090 32GB（一次性）+ qwen3-32b FP16 + qwen3-235b Q4 |
| **$150-500/月** | AutoDL RTX 4090 单卡按需 |
| **$3000-7000/月** | AutoDL/A100 80GB 包月 |
| **$7000-30000/月** | 阿里云 GPU gn7/gn8（8× A100/H100）|

---

**快照时间**: 2026-09-10 14:34
**下次更新**: 下周一北京时间 8:00

**数据源**:
- HF 模型元数据：`data/hf-metadata-snapshot.json`
- GPU 价格：`data/gpu-prices-snapshot.json`
- 模型清单：`src/core/model_resolver.py`

**自动化工作流**: `.github/workflows/refresh-models.yml`
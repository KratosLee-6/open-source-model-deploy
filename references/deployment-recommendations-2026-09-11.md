# 47 个开源模型部署建议 · 2026-09-11 01:40 自动生成

> **目标场景**: 常规笔记本 16GB / 无独显
> **HF 元数据快照**: 2026-09-11T01:34:17
> **GPU 价格快照**: 2026-09-10T14:34:41
> **生成方式**: GitHub Actions 每周自动跑 (`scripts/render_report.py`)
> **手动重生成**: `python3 scripts/render_report.py --target=default`

---

## 内存估算公式

- **fp16** = `2 × size_b` GB
- **Q4 量化** ≈ `0.5 × size_b` GB
- **MoE**: fp16 按 total size 算，推理激活 `activated_b`

---


## 🟢 国内通用 (10 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen3-8b | `Qwen/Qwen3-8B` | 8.0B | 12,883,281 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| qwen3-14b | `Qwen/Qwen3-14B` | 14.0B | 1,676,957 | ❌ 需 GPU | vLLM / 云租 |
| qwen3-32b | `Qwen/Qwen3-32B` | 32.0B | 5,212,359 | ❌ 需 GPU | vLLM / 云租 |
| glm-4-32b | `THUDM/glm-4-32b-0414` | 32.0B | N/A | ❌ 需 GPU | vLLM / 云租 |
| qwen3-235b-a22b | `Qwen/Qwen3-235B-A22B` | 235.0B | 346,243 | ❌ 需 GPU | vLLM / 云租 |
| deepseek-v2.5 | `deepseek-ai/DeepSeek-V2.5` | 236.0B | 5,831 | ❌ 需 GPU | vLLM / 云租 |
| glm-4.5 | `THUDM/GLM-4.5` | 355.0B | N/A | ❌ 需 GPU | vLLM / 云租 |
| deepseek-v4.1-flash | `deepseek-ai/DeepSeek-V4.1-Flash` | 522.0B | 6 | ❌ 需 GPU | vLLM / 云租 |
| deepseek-v3 | `deepseek-ai/DeepSeek-V3` | 671.0B | 1,065,138 | ❌ 需 GPU | vLLM / 云租 |
| kimi-k2 | `moonshotai/Kimi-K2-Instruct` | 1000.0B | 169,441 | ❌ 需 GPU | vLLM / 云租 |

## 🧠 国内推理 (10 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| deepseek-r1-distill-qwen-1.5b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 1.5B | 416,880 | ✓ CPU 即可 | llama.cpp / Ollama |
| deepseek-r1-distill-qwen-7b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 7.0B | 359,985 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| deepseek-r1-distill-llama-8b | `deepseek-ai/DeepSeek-R1-Distill-Llama-8B` | 8.0B | 334,184 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| deepseek-r1-distill-qwen-14b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 14.0B | 347,879 | ❌ 需 GPU | vLLM / 云租 |
| qwq-32b-preview | `Qwen/QwQ-32B-Preview` | 32.0B | 10,160 | ❌ 需 GPU | vLLM / 云租 |
| glm-z1-32b | `THUDM/GLM-Z1-32B-0414` | 32.0B | 50,606 | ❌ 需 GPU | vLLM / 云租 |
| qwq-32b | `Qwen/QwQ-32B` | 32.0B | 75,026 | ❌ 需 GPU | vLLM / 云租 |
| deepseek-r1-distill-qwen-32b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | 32.0B | 522,681 | ❌ 需 GPU | vLLM / 云租 |
| deepseek-r1-distill-llama-70b | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | 70.0B | 76,970 | ❌ 需 GPU | vLLM / 云租 |
| deepseek-r1 | `deepseek-ai/DeepSeek-R1` | 671.0B | 709,327 | ❌ 需 GPU | vLLM / 云租 |

## 💻 代码专用 (6 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen2.5-coder-7b | `Qwen/Qwen2.5-Coder-7B-Instruct` | 7.0B | 2,712,497 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| deepseek-coder-v2-lite | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | 16.0B | 754,668 | ❌ 需 GPU | vLLM / 云租 |
| codestral-22b | `mistralai/Codestral-22B-v0.1` | 22.0B | 5,899 | ❌ 需 GPU | vLLM / 云租 |
| qwen3-coder-30b | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 30.0B | 692,826 | ❌ 需 GPU | vLLM / 云租 |
| qwen2.5-coder-32b | `Qwen/Qwen2.5-Coder-32B-Instruct` | 32.0B | 1,547,400 | ❌ 需 GPU | vLLM / 云租 |
| deepseek-coder-v2 | `deepseek-ai/DeepSeek-Coder-V2-Instruct` | 236.0B | 10,491 | ❌ 需 GPU | vLLM / 云租 |

## 👁️ 视觉多模态 (5 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen2.5-vl-7b | `Qwen/Qwen2.5-VL-7B-Instruct` | 7.0B | 7,682,009 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| llava-onevision-qwen2-7b | `lmms-lab/llava-onevision-qwen2-7b-ov` | 7.0B | 34,873 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| internvl3-8b | `OpenGVLab/InternVL3-8B` | 8.0B | 100,771 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| qwen2.5-vl-72b | `Qwen/Qwen2.5-VL-72B-Instruct` | 72.0B | 157,221 | ❌ 需 GPU | vLLM / 云租 |
| internvl3-78b | `OpenGVLab/InternVL3-78B` | 78.0B | 14,269 | ❌ 需 GPU | vLLM / 云租 |

## 🌍 国际密集 (5 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| mistral-small-3 | `mistralai/Mistral-Small-3` | 22.0B | N/A | ❌ 需 GPU | vLLM / 云租 |
| gemma-3-27b | `google/gemma-3-27b-it` | 27.0B | 360,496 | ❌ 需 GPU | vLLM / 云租 |
| llama-3.1-70b | `meta-llama/Llama-3.1-70B` | 70.0B | 42,776 | ❌ 需 GPU | vLLM / 云租 |
| mistral-large-2 | `mistralai/Mistral-Large-Instruct-2407` | 123.0B | 4,929 | ❌ 需 GPU | vLLM / 云租 |
| llama-3.1-405b | `meta-llama/Llama-3.1-405B` | 405.0B | 131,924 | ❌ 需 GPU | vLLM / 云租 |

## ⚡ 国际边缘 (7 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| llama-3.2-1b | `meta-llama/Llama-3.2-1B` | 1.0B | 1,246,103 | ✓ CPU 即可 | llama.cpp / Ollama |
| llama-3.2-3b | `meta-llama/Llama-3.2-3B` | 3.0B | 355,044 | ✓ CPU 即可 | llama.cpp / Ollama |
| phi-4-mini | `microsoft/Phi-4-mini-instruct` | 3.8B | 457,692 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| phi-3.5-mini | `microsoft/Phi-3.5-mini-instruct` | 3.8B | 356,127 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| gemma-3-4b | `google/gemma-3-4b-it` | 4.0B | 1,668,779 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| gemma-3-9b | `google/gemma-3-9b-it` | 9.0B | N/A | ❌ 需 GPU | vLLM / 云租 |
| phi-4 | `microsoft/phi-4` | 14.0B | 711,395 | ❌ 需 GPU | vLLM / 云租 |

## 🔢 Embedding (4 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| bge-large-zh-v1.5 | `BAAI/bge-large-zh-v1.5` | 0.3B | 1,181,768 | ✓ CPU 即可 | llama.cpp / Ollama |
| bge-m3 | `BAAI/bge-m3` | 0.6B | 37,891,167 | ✓ CPU 即可 | llama.cpp / Ollama |
| gte-qwen2-7b-instruct | `Alibaba-NLP/gte-Qwen2-7B-instruct` | 7.0B | 111,229 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |
| qwen3-embedding-8b | `Qwen/Qwen3-Embedding-8B` | 8.0B | 2,253,605 | ⚠ Q4 量化（4-8GB） | llama.cpp / Ollama |

## 📊 Reranker (1 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| bge-reranker-v2-m3 | `BAAI/bge-reranker-v2-m3` | 0.6B | 18,212,308 | ✓ CPU 即可 | llama.cpp / Ollama |

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

**快照时间**: 2026-09-11 01:40
**下次更新**: 下周一北京时间 8:00

**数据源**:
- HF 模型元数据：`data/hf-metadata-snapshot.json`
- GPU 价格：`data/gpu-prices-snapshot.json`
- 模型清单：`src/core/model_resolver.py`

**自动化工作流**: `.github/workflows/refresh-models.yml`
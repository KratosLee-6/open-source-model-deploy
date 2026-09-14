# 47 个开源模型部署建议 · 2026-09-14 03:40 自动生成

> **目标场景**: 云租按量（H100/A100）
> **HF 元数据快照**: 2026-09-14T03:39:15
> **GPU 价格快照**: 2026-09-14T03:40:33
> **生成方式**: GitHub Actions 每周自动跑 (`scripts/render_report.py`)
> **手动重生成**: `python3 scripts/render_report.py --target=cloud`

---

## 内存估算公式

- **fp16** = `2 × size_b` GB
- **Q4 量化** ≈ `0.5 × size_b` GB
- **MoE**: fp16 按 total size 算，推理激活 `activated_b`

---


## 🟢 国内通用 (33 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen2.5-0.5b-instruct | `Qwen/Qwen2.5-0.5B-Instruct` | 0.5B | 7,637,171 | ✓ 云租 (1GB fp16) | vLLM |
| qwen3-0.6b | `Qwen/Qwen3-0.6B` | 0.75B | 20,036,436 | ✓ 云租 (2GB fp16) | vLLM |
| qwen3.5-0.8b | `Qwen/Qwen3.5-0.8B` | 0.87B | 2,403,580 | ✓ 云租 (2GB fp16) | vLLM |
| qwen2.5-1.5b-instruct | `Qwen/Qwen2.5-1.5B-Instruct` | 1.5B | 7,148,070 | ✓ 云租 (3GB fp16) | vLLM |
| qwen3-1.7b | `Qwen/Qwen3-1.7B` | 2.03B | 3,515,746 | ✓ 云租 (4GB fp16) | vLLM |
| qwen3.5-2b | `Qwen/Qwen3.5-2B` | 2.27B | 4,015,734 | ✓ 云租 (5GB fp16) | vLLM |
| qwen2.5-3b-instruct | `Qwen/Qwen2.5-3B-Instruct` | 3.0B | 5,354,250 | ✓ 云租 (6GB fp16) | vLLM |
| qwen3-4b | `Qwen/Qwen3-4B` | 4.02B | 6,182,042 | ✓ 云租 (8GB fp16) | vLLM |
| qwen3-4b-instruct-2507 | `Qwen/Qwen3-4B-Instruct-2507` | 4.02B | 3,591,350 | ✓ 云租 (8GB fp16) | vLLM |
| qwen3.5-4b | `Qwen/Qwen3.5-4B` | 4.66B | 7,012,107 | ✓ 云租 (9GB fp16) | vLLM |
| qwen2.5-7b-instruct | `Qwen/Qwen2.5-7B-Instruct` | 7.0B | 9,990,722 | ✓ 云租 (14GB fp16) | vLLM |
| qwen3-8b | `Qwen/Qwen3-8B` | 8.0B | 12,799,189 | ✓ 云租 (16GB fp16) | vLLM |
| qwen3.5-9b | `Qwen/Qwen3.5-9B` | 9.65B | 9,986,315 | ✓ 云租 (19GB fp16) | vLLM |
| qwen3-14b | `Qwen/Qwen3-14B` | 14.0B | 1,614,278 | ✓ 云租 (28GB fp16) | vLLM |
| qwen2.5-14b-instruct | `Qwen/Qwen2.5-14B-Instruct` | 14.0B | 2,505,562 | ✓ 云租 (28GB fp16) | vLLM |
| qwen3.5-27b | `Qwen/Qwen3.5-27B` | 27.78B | 2,074,257 | ✓ 云租 (56GB fp16) | vLLM |
| qwen3.6-27b | `Qwen/Qwen3.6-27B` | 27.78B | 4,145,148 | ✓ 云租 (56GB fp16) | vLLM |
| qwen3.8-27b | `Qwen/Qwen3.8-27B` | 27.78B | 7,768,964 | ✓ 云租 (56GB fp16) | vLLM |
| qwen3-32b | `Qwen/Qwen3-32B` | 32.0B | 4,859,248 | ✓ 云租 (64GB fp16) | vLLM |
| qwen2.5-32b-instruct | `Qwen/Qwen2.5-32B-Instruct` | 32.0B | 2,248,757 | ✓ 云租 (64GB fp16) | vLLM |
| glm-4-32b | `THUDM/glm-4-32b-0414` | 32.0B | N/A | ✓ 云租 (64GB fp16) | vLLM |
| qwen3.5-35b-a3b | `Qwen/Qwen3.5-35B-A3B` | 35.95B | 2,080,213 | ✓ 云租 (72GB fp16) | vLLM |
| qwen3.6-35b-a3b | `Qwen/Qwen3.6-35B-A3B` | 35.95B | 3,747,719 | ✓ 云租 (72GB fp16) | vLLM |
| qwen-72b | `Qwen/Qwen-72B` | 72.0B | 3,704,811 | ✓ 云租 (144GB fp16) | vLLM |
| qwen3.5-122b-a10b | `Qwen/Qwen3.5-122B-A10B` | 125.09B | 566,520 | ✓ 云租 (250GB fp16) | vLLM |
| qwen3-235b-a22b | `Qwen/Qwen3-235B-A22B` | 235.0B | 340,336 | ✓ 云租 (470GB fp16) | vLLM |
| deepseek-v2.5 | `deepseek-ai/DeepSeek-V2.5` | 236.0B | 5,651 | ✓ 云租 (472GB fp16) | vLLM |
| deepseek-v4-flash-0731 | `deepseek-ai/DeepSeek-V4-Flash-0731` | 284.0B | 4,384,168 | ✓ 云租 (568GB fp16) | vLLM |
| glm-4.5 | `THUDM/GLM-4.5` | 355.0B | N/A | ✓ 云租 (710GB fp16) | vLLM |
| qwen3.5-397b-a17b | `Qwen/Qwen3.5-397B-A17B` | 403.4B | 191,511 | ✓ 云租 (807GB fp16) | vLLM |
| deepseek-v4.1-flash | `deepseek-ai/DeepSeek-V4.1-Flash` | 522.0B | 244,457 | ✓ 云租 (1044GB fp16) | vLLM |
| deepseek-v3 | `deepseek-ai/DeepSeek-V3` | 671.0B | 985,991 | ✓ 云租 (1342GB fp16) | vLLM |
| kimi-k2 | `moonshotai/Kimi-K2-Instruct` | 1000.0B | 184,090 | ✓ 云租 (2000GB fp16) | vLLM |

## 🧠 国内推理 (10 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| deepseek-r1-distill-qwen-1.5b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 1.5B | 397,843 | ✓ 云租 (3GB fp16) | vLLM |
| deepseek-r1-distill-qwen-7b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 7.0B | 361,684 | ✓ 云租 (14GB fp16) | vLLM |
| deepseek-r1-distill-llama-8b | `deepseek-ai/DeepSeek-R1-Distill-Llama-8B` | 8.0B | 307,058 | ✓ 云租 (16GB fp16) | vLLM |
| deepseek-r1-distill-qwen-14b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 14.0B | 341,430 | ✓ 云租 (28GB fp16) | vLLM |
| qwq-32b-preview | `Qwen/QwQ-32B-Preview` | 32.0B | 9,895 | ✓ 云租 (64GB fp16) | vLLM |
| glm-z1-32b | `THUDM/GLM-Z1-32B-0414` | 32.0B | 50,439 | ✓ 云租 (64GB fp16) | vLLM |
| qwq-32b | `Qwen/QwQ-32B` | 32.0B | 76,944 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-r1-distill-qwen-32b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | 32.0B | 504,706 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-r1-distill-llama-70b | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | 70.0B | 77,142 | ✓ 云租 (140GB fp16) | vLLM |
| deepseek-r1 | `deepseek-ai/DeepSeek-R1` | 671.0B | 648,837 | ✓ 云租 (1342GB fp16) | vLLM |

## 💻 代码专用 (6 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen2.5-coder-7b | `Qwen/Qwen2.5-Coder-7B-Instruct` | 7.0B | 2,755,951 | ✓ 云租 (14GB fp16) | vLLM |
| deepseek-coder-v2-lite | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | 16.0B | 783,125 | ✓ 云租 (32GB fp16) | vLLM |
| codestral-22b | `mistralai/Codestral-22B-v0.1` | 22.0B | 4,849 | ✓ 云租 (44GB fp16) | vLLM |
| qwen3-coder-30b | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 30.0B | 649,793 | ✓ 云租 (60GB fp16) | vLLM |
| qwen2.5-coder-32b | `Qwen/Qwen2.5-Coder-32B-Instruct` | 32.0B | 1,507,778 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-coder-v2 | `deepseek-ai/DeepSeek-Coder-V2-Instruct` | 236.0B | 10,423 | ✓ 云租 (472GB fp16) | vLLM |

## 👁️ 视觉多模态 (10 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen3-vl-2b-instruct | `Qwen/Qwen3-VL-2B-Instruct` | 2.13B | 3,024,947 | ✓ 云租 (4GB fp16) | vLLM |
| qwen3-vl-4b-instruct | `Qwen/Qwen3-VL-4B-Instruct` | 4.44B | 4,052,439 | ✓ 云租 (9GB fp16) | vLLM |
| qwen2.5-vl-7b | `Qwen/Qwen2.5-VL-7B-Instruct` | 7.0B | 7,320,610 | ✓ 云租 (14GB fp16) | vLLM |
| llava-onevision-qwen2-7b | `lmms-lab/llava-onevision-qwen2-7b-ov` | 7.0B | 35,370 | ✓ 云租 (14GB fp16) | vLLM |
| internvl3-8b | `OpenGVLab/InternVL3-8B` | 8.0B | 94,877 | ✓ 云租 (16GB fp16) | vLLM |
| qwen3-vl-8b-instruct | `Qwen/Qwen3-VL-8B-Instruct` | 8.77B | 16,859,084 | ✓ 云租 (18GB fp16) | vLLM |
| gemma-4-26b-a4b | `google/gemma-4-26B-A4B-it` | 25.81B | 9,072,850 | ✓ 云租 (52GB fp16) | vLLM |
| qwen3-vl-32b-instruct | `Qwen/Qwen3-VL-32B-Instruct` | 33.36B | 319,877 | ✓ 云租 (67GB fp16) | vLLM |
| qwen2.5-vl-72b | `Qwen/Qwen2.5-VL-72B-Instruct` | 72.0B | 125,397 | ✓ 云租 (144GB fp16) | vLLM |
| internvl3-78b | `OpenGVLab/InternVL3-78B` | 78.0B | 13,988 | ✓ 云租 (156GB fp16) | vLLM |

## 🌍 国际密集 (7 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| mistral-small-3 | `mistralai/Mistral-Small-3` | 22.0B | N/A | ✓ 云租 (44GB fp16) | vLLM |
| gemma-3-27b | `google/gemma-3-27b-it` | 27.0B | 353,534 | ✓ 云租 (54GB fp16) | vLLM |
| gemma-4-31b | `google/gemma-4-31B-it` | 31.27B | 8,755,607 | ✓ 云租 (63GB fp16) | vLLM |
| llama-3.1-70b | `meta-llama/Llama-3.1-70B` | 70.0B | 39,228 | ✓ 云租 (140GB fp16) | vLLM |
| openai-gpt-oss-120b | `openai/gpt-oss-120b` | 116.83B | 5,415,732 | ✓ 云租 (234GB fp16) | vLLM |
| mistral-large-2 | `mistralai/Mistral-Large-Instruct-2407` | 123.0B | 2,544 | ✓ 云租 (246GB fp16) | vLLM |
| llama-3.1-405b | `meta-llama/Llama-3.1-405B` | 405.0B | 104,577 | ✓ 云租 (810GB fp16) | vLLM |

## ⚡ 国际边缘 (10 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| llama-3.2-1b | `meta-llama/Llama-3.2-1B` | 1.0B | 1,123,659 | ✓ 云租 (2GB fp16) | vLLM |
| llama-3.2-3b | `meta-llama/Llama-3.2-3B` | 3.0B | 356,173 | ✓ 云租 (6GB fp16) | vLLM |
| phi-4-mini | `microsoft/Phi-4-mini-instruct` | 3.8B | 421,951 | ✓ 云租 (8GB fp16) | vLLM |
| phi-3.5-mini | `microsoft/Phi-3.5-mini-instruct` | 3.8B | 350,389 | ✓ 云租 (8GB fp16) | vLLM |
| nvidia-nemotron-3-nano-4b | `nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16` | 3.97B | 3,439,747 | ✓ 云租 (8GB fp16) | vLLM |
| gemma-3-4b | `google/gemma-3-4b-it` | 4.0B | 1,700,192 | ✓ 云租 (8GB fp16) | vLLM |
| llama-3.1-8b-instruct | `meta-llama/Llama-3.1-8B-Instruct` | 8.03B | 5,574,752 | ✓ 云租 (16GB fp16) | vLLM |
| gemma-3-9b | `google/gemma-3-9b-it` | 9.0B | N/A | ✓ 云租 (18GB fp16) | vLLM |
| phi-4 | `microsoft/phi-4` | 14.0B | 696,921 | ✓ 云租 (28GB fp16) | vLLM |
| openai-gpt-oss-20b | `openai/gpt-oss-20b` | 20.91B | 6,582,044 | ✓ 云租 (42GB fp16) | vLLM |

## 🔢 Embedding (16 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 | `sentence-transformers/all-MiniLM-L6-v2` | 0.02B | 252,928,721 | ✓ 云租 (0GB fp16) | vLLM |
| bge-small-zh-v1.5 | `BAAI/bge-small-zh-v1.5` | 0.02B | 4,973,124 | ✓ 云租 (0GB fp16) | vLLM |
| bge-small-en-v1.5 | `BAAI/bge-small-en-v1.5` | 0.03B | 64,028,390 | ✓ 云租 (0GB fp16) | vLLM |
| bge-base-zh-v1.5 | `BAAI/bge-base-zh-v1.5` | 0.1B | 792,739 | ✓ 云租 (0GB fp16) | vLLM |
| all-mpnet-base-v2 | `sentence-transformers/all-mpnet-base-v2` | 0.11B | 23,712,269 | ✓ 云租 (0GB fp16) | vLLM |
| bge-base-en-v1.5 | `BAAI/bge-base-en-v1.5` | 0.11B | 10,496,040 | ✓ 云租 (0GB fp16) | vLLM |
| paraphrase-multilingual-MiniLM-L12-v2 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 0.12B | 45,734,237 | ✓ 云租 (0GB fp16) | vLLM |
| multilingual-e5-small | `intfloat/multilingual-e5-small` | 0.12B | 12,183,092 | ✓ 云租 (0GB fp16) | vLLM |
| nomic-embed-text-v1.5 | `nomic-ai/nomic-embed-text-v1.5` | 0.14B | 15,683,965 | ✓ 云租 (0GB fp16) | vLLM |
| multilingual-e5-base | `intfloat/multilingual-e5-base` | 0.28B | 7,315,679 | ✓ 云租 (1GB fp16) | vLLM |
| bge-large-zh-v1.5 | `BAAI/bge-large-zh-v1.5` | 0.3B | 1,205,462 | ✓ 云租 (1GB fp16) | vLLM |
| multilingual-e5-large | `intfloat/multilingual-e5-large` | 0.56B | 6,951,190 | ✓ 云租 (1GB fp16) | vLLM |
| bge-m3 | `BAAI/bge-m3` | 0.6B | 37,590,799 | ✓ 云租 (1GB fp16) | vLLM |
| qwen3-embedding-0.6b | `Qwen/Qwen3-Embedding-0.6B` | 0.6B | 8,349,661 | ✓ 云租 (1GB fp16) | vLLM |
| gte-qwen2-7b-instruct | `Alibaba-NLP/gte-Qwen2-7B-instruct` | 7.0B | 107,102 | ✓ 云租 (14GB fp16) | vLLM |
| qwen3-embedding-8b | `Qwen/Qwen3-Embedding-8B` | 8.0B | 2,415,467 | ✓ 云租 (16GB fp16) | vLLM |

## 📊 Reranker (2 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| bge-reranker-large | `BAAI/bge-reranker-large` | 0.56B | 2,718,962 | ✓ 云租 (1GB fp16) | vLLM |
| bge-reranker-v2-m3 | `BAAI/bge-reranker-v2-m3` | 0.6B | 18,093,771 | ✓ 云租 (1GB fp16) | vLLM |

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

**快照时间**: 2026-09-14 03:40
**下次更新**: 下周一北京时间 8:00

**数据源**:
- HF 模型元数据：`data/hf-metadata-snapshot.json`
- GPU 价格：`data/gpu-prices-snapshot.json`
- 模型清单：`src/core/model_resolver.py`

**自动化工作流**: `.github/workflows/refresh-models.yml`
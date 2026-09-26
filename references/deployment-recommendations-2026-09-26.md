# 47 个开源模型部署建议 · 2026-09-26 12:30 自动生成

> **目标场景**: 云租按量（H100/A100）
> **HF 元数据快照**: 2026-09-26T12:28:30
> **GPU 价格快照**: 2026-09-26T12:30:15
> **生成方式**: GitHub Actions 每周自动跑 (`scripts/render_report.py`)
> **手动重生成**: `python3 scripts/render_report.py --target=cloud`

---

## 内存估算公式

- **fp16** = `2 × size_b` GB
- **Q4 量化** ≈ `0.5 × size_b` GB
- **MoE**: fp16 按 total size 算，推理激活 `activated_b`

---


## 🟢 国内通用 (39 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen2.5-0.5b-instruct | `Qwen/Qwen2.5-0.5B-Instruct` | 0.5B | 8,652,021 | ✓ 云租 (1GB fp16) | vLLM |
| qwen2.5-0.5b | `Qwen/Qwen2.5-0.5B` | 0.5B | 1,543,648 | ✓ 云租 (1GB fp16) | vLLM |
| qwen3-0.6b | `Qwen/Qwen3-0.6B` | 0.75B | 29,342,532 | ✓ 云租 (2GB fp16) | vLLM |
| qwen3.5-0.8b | `Qwen/Qwen3.5-0.8B` | 0.87B | 2,439,006 | ✓ 云租 (2GB fp16) | vLLM |
| qwen2.5-1.5b-instruct | `Qwen/Qwen2.5-1.5B-Instruct` | 1.5B | 7,783,247 | ✓ 云租 (3GB fp16) | vLLM |
| qwen2.5-1.5b | `Qwen/Qwen2.5-1.5B` | 1.5B | 777,064 | ✓ 云租 (3GB fp16) | vLLM |
| qwen3-1.7b-base | `Qwen/Qwen3-1.7B-Base` | 1.7B | 1,405,245 | ✓ 云租 (3GB fp16) | vLLM |
| qwen3-1.7b | `Qwen/Qwen3-1.7B` | 2.03B | 3,447,962 | ✓ 云租 (4GB fp16) | vLLM |
| qwen3.5-2b | `Qwen/Qwen3.5-2B` | 2.27B | 4,832,123 | ✓ 云租 (5GB fp16) | vLLM |
| qwen2.5-3b-instruct | `Qwen/Qwen2.5-3B-Instruct` | 3.0B | 4,246,927 | ✓ 云租 (6GB fp16) | vLLM |
| qwen3-4b | `Qwen/Qwen3-4B` | 4.02B | 6,488,517 | ✓ 云租 (8GB fp16) | vLLM |
| qwen3-4b-instruct-2507 | `Qwen/Qwen3-4B-Instruct-2507` | 4.02B | 3,964,449 | ✓ 云租 (8GB fp16) | vLLM |
| qwen3.5-4b | `Qwen/Qwen3.5-4B` | 4.66B | 7,117,867 | ✓ 云租 (9GB fp16) | vLLM |
| qwen2.5-7b-instruct | `Qwen/Qwen2.5-7B-Instruct` | 7.0B | 9,971,153 | ✓ 云租 (14GB fp16) | vLLM |
| qwen3-8b | `Qwen/Qwen3-8B` | 8.0B | 12,384,555 | ✓ 云租 (16GB fp16) | vLLM |
| qwen3.5-9b | `Qwen/Qwen3.5-9B` | 9.65B | 9,958,288 | ✓ 云租 (19GB fp16) | vLLM |
| qwen3-14b | `Qwen/Qwen3-14B` | 14.0B | 2,142,591 | ✓ 云租 (28GB fp16) | vLLM |
| qwen2.5-14b-instruct | `Qwen/Qwen2.5-14B-Instruct` | 14.0B | 1,929,663 | ✓ 云租 (28GB fp16) | vLLM |
| qwen3.5-27b | `Qwen/Qwen3.5-27B` | 27.78B | 1,833,098 | ✓ 云租 (56GB fp16) | vLLM |
| qwen3.6-27b | `Qwen/Qwen3.6-27B` | 27.78B | 2,788,233 | ✓ 云租 (56GB fp16) | vLLM |
| qwen3.8-27b | `Qwen/Qwen3.8-27B` | 27.78B | 6,652,309 | ✓ 云租 (56GB fp16) | vLLM |
| qwen3-30b-a3b | `Qwen/Qwen3-30B-A3B` | 30.0B | 1,620,719 | ✓ 云租 (60GB fp16) | vLLM |
| qwen3-32b | `Qwen/Qwen3-32B` | 32.0B | 4,075,440 | ✓ 云租 (64GB fp16) | vLLM |
| qwen2.5-32b-instruct | `Qwen/Qwen2.5-32B-Instruct` | 32.0B | 2,052,845 | ✓ 云租 (64GB fp16) | vLLM |
| glm-4-32b | `THUDM/glm-4-32b-0414` | 32.0B | N/A | ✓ 云租 (64GB fp16) | vLLM |
| qwen3.5-35b-a3b | `Qwen/Qwen3.5-35B-A3B` | 35.95B | 1,699,859 | ✓ 云租 (72GB fp16) | vLLM |
| qwen3.6-35b-a3b | `Qwen/Qwen3.6-35B-A3B` | 35.95B | 3,193,359 | ✓ 云租 (72GB fp16) | vLLM |
| qwen-72b | `Qwen/Qwen-72B` | 72.0B | 3,831,221 | ✓ 云租 (144GB fp16) | vLLM |
| qwen3.5-122b-a10b | `Qwen/Qwen3.5-122B-A10B` | 125.09B | 375,945 | ✓ 云租 (250GB fp16) | vLLM |
| qwen3-235b-a22b | `Qwen/Qwen3-235B-A22B` | 235.0B | 372,111 | ✓ 云租 (470GB fp16) | vLLM |
| deepseek-v2.5 | `deepseek-ai/DeepSeek-V2.5` | 236.0B | 7,036 | ✓ 云租 (472GB fp16) | vLLM |
| deepseek-v4-flash-0731 | `deepseek-ai/DeepSeek-V4-Flash-0731` | 284.0B | 3,824,182 | ✓ 云租 (568GB fp16) | vLLM |
| deepseek-v4-flash | `deepseek-ai/DeepSeek-V4-Flash` | 284.0B | 1,307,475 | ✓ 云租 (568GB fp16) | vLLM |
| glm-4.5 | `THUDM/GLM-4.5` | 355.0B | N/A | ✓ 云租 (710GB fp16) | vLLM |
| qwen3.5-397b-a17b | `Qwen/Qwen3.5-397B-A17B` | 403.4B | 257,428 | ✓ 云租 (807GB fp16) | vLLM |
| deepseek-v4.1-flash | `deepseek-ai/DeepSeek-V4.1-Flash` | 522.0B | 640,577 | ✓ 云租 (1044GB fp16) | vLLM |
| deepseek-v3 | `deepseek-ai/DeepSeek-V3` | 671.0B | 1,111,843 | ✓ 云租 (1342GB fp16) | vLLM |
| deepseek-v3-0324 | `deepseek-ai/DeepSeek-V3-0324` | 671.0B | 1,312,304 | ✓ 云租 (1342GB fp16) | vLLM |
| kimi-k2 | `moonshotai/Kimi-K2-Instruct` | 1000.0B | 270,831 | ✓ 云租 (2000GB fp16) | vLLM |

## 🧠 国内推理 (10 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| deepseek-r1-distill-qwen-1.5b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 1.5B | 470,297 | ✓ 云租 (3GB fp16) | vLLM |
| deepseek-r1-distill-qwen-7b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 7.0B | 294,027 | ✓ 云租 (14GB fp16) | vLLM |
| deepseek-r1-distill-llama-8b | `deepseek-ai/DeepSeek-R1-Distill-Llama-8B` | 8.0B | 188,909 | ✓ 云租 (16GB fp16) | vLLM |
| deepseek-r1-distill-qwen-14b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 14.0B | 342,407 | ✓ 云租 (28GB fp16) | vLLM |
| qwq-32b-preview | `Qwen/QwQ-32B-Preview` | 32.0B | 12,460 | ✓ 云租 (64GB fp16) | vLLM |
| glm-z1-32b | `THUDM/GLM-Z1-32B-0414` | 32.0B | 34,853 | ✓ 云租 (64GB fp16) | vLLM |
| qwq-32b | `Qwen/QwQ-32B` | 32.0B | 71,442 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-r1-distill-qwen-32b | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | 32.0B | 468,238 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-r1-distill-llama-70b | `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` | 70.0B | 75,351 | ✓ 云租 (140GB fp16) | vLLM |
| deepseek-r1 | `deepseek-ai/DeepSeek-R1` | 671.0B | 857,565 | ✓ 云租 (1342GB fp16) | vLLM |

## 💻 代码专用 (8 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| qwen2.5-coder-7b | `Qwen/Qwen2.5-Coder-7B-Instruct` | 7.0B | 2,440,272 | ✓ 云租 (14GB fp16) | vLLM |
| deepseek-coder-7b-instruct-v1.5 | `deepseek-ai/deepseek-coder-7b-instruct-v1.5` | 7.0B | 690,697 | ✓ 云租 (14GB fp16) | vLLM |
| qwen2.5-coder-14b-instruct | `Qwen/Qwen2.5-Coder-14B-Instruct` | 14.0B | 1,792,245 | ✓ 云租 (28GB fp16) | vLLM |
| deepseek-coder-v2-lite | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | 16.0B | 935,202 | ✓ 云租 (32GB fp16) | vLLM |
| codestral-22b | `mistralai/Codestral-22B-v0.1` | 22.0B | 19,431 | ✓ 云租 (44GB fp16) | vLLM |
| qwen3-coder-30b | `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 30.0B | 510,515 | ✓ 云租 (60GB fp16) | vLLM |
| qwen2.5-coder-32b | `Qwen/Qwen2.5-Coder-32B-Instruct` | 32.0B | 1,091,533 | ✓ 云租 (64GB fp16) | vLLM |
| deepseek-coder-v2 | `deepseek-ai/DeepSeek-Coder-V2-Instruct` | 236.0B | 12,026 | ✓ 云租 (472GB fp16) | vLLM |

## 👁️ 视觉多模态 (17 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| florence-2-base | `microsoft/Florence-2-base` | 0.27B | 3,046,535 | ✓ 云租 (1GB fp16) | vLLM |
| internvl2-1b | `OpenGVLab/InternVL2-1B` | 1.0B | 709,860 | ✓ 云租 (2GB fp16) | vLLM |
| internvl2-2b | `OpenGVLab/InternVL2-2B` | 2.0B | 704,959 | ✓ 云租 (4GB fp16) | vLLM |
| qwen3-vl-2b-instruct | `Qwen/Qwen3-VL-2B-Instruct` | 2.13B | 2,956,630 | ✓ 云租 (4GB fp16) | vLLM |
| qwen2.5-vl-3b-instruct | `Qwen/Qwen2.5-VL-3B-Instruct` | 3.0B | 2,372,984 | ✓ 云租 (6GB fp16) | vLLM |
| phi-3.5-vision-instruct | `microsoft/Phi-3.5-vision-instruct` | 4.2B | 758,084 | ✓ 云租 (8GB fp16) | vLLM |
| qwen3-vl-4b-instruct | `Qwen/Qwen3-VL-4B-Instruct` | 4.44B | 3,419,242 | ✓ 云租 (9GB fp16) | vLLM |
| qwen2.5-vl-7b | `Qwen/Qwen2.5-VL-7B-Instruct` | 7.0B | 6,396,890 | ✓ 云租 (14GB fp16) | vLLM |
| llava-onevision-qwen2-7b | `lmms-lab/llava-onevision-qwen2-7b-ov` | 7.0B | 38,764 | ✓ 云租 (14GB fp16) | vLLM |
| qwen2-vl-7b-instruct | `Qwen/Qwen2-VL-7B-Instruct` | 7.0B | 775,237 | ✓ 云租 (14GB fp16) | vLLM |
| internvl3-8b | `OpenGVLab/InternVL3-8B` | 8.0B | 84,114 | ✓ 云租 (16GB fp16) | vLLM |
| qwen3-vl-8b-instruct | `Qwen/Qwen3-VL-8B-Instruct` | 8.77B | 18,555,061 | ✓ 云租 (18GB fp16) | vLLM |
| gemma-4-26b-a4b | `google/gemma-4-26B-A4B-it` | 25.81B | 11,529,170 | ✓ 云租 (52GB fp16) | vLLM |
| qwen2.5-vl-32b-instruct | `Qwen/Qwen2.5-VL-32B-Instruct` | 32.0B | 913,384 | ✓ 云租 (64GB fp16) | vLLM |
| qwen3-vl-32b-instruct | `Qwen/Qwen3-VL-32B-Instruct` | 33.36B | 347,223 | ✓ 云租 (67GB fp16) | vLLM |
| qwen2.5-vl-72b | `Qwen/Qwen2.5-VL-72B-Instruct` | 72.0B | 77,956 | ✓ 云租 (144GB fp16) | vLLM |
| internvl3-78b | `OpenGVLab/InternVL3-78B` | 78.0B | 13,356 | ✓ 云租 (156GB fp16) | vLLM |

## 🌍 国际密集 (9 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| gemma-2-9b-it | `google/gemma-2-9b-it` | 9.0B | 1,146,361 | ✓ 云租 (18GB fp16) | vLLM |
| mistral-small-3 | `mistralai/Mistral-Small-3` | 22.0B | N/A | ✓ 云租 (44GB fp16) | vLLM |
| gemma-3-27b | `google/gemma-3-27b-it` | 27.0B | 402,003 | ✓ 云租 (54GB fp16) | vLLM |
| gemma-4-31b | `google/gemma-4-31B-it` | 31.27B | 9,436,030 | ✓ 云租 (63GB fp16) | vLLM |
| llama-3.1-70b | `meta-llama/Llama-3.1-70B` | 70.0B | 34,237 | ✓ 云租 (140GB fp16) | vLLM |
| llama-3.3-70b-instruct | `meta-llama/Llama-3.3-70B-Instruct` | 70.0B | 921,237 | ✓ 云租 (140GB fp16) | vLLM |
| openai-gpt-oss-120b | `openai/gpt-oss-120b` | 116.83B | 4,561,423 | ✓ 云租 (234GB fp16) | vLLM |
| mistral-large-2 | `mistralai/Mistral-Large-Instruct-2407` | 123.0B | 2,565 | ✓ 云租 (246GB fp16) | vLLM |
| llama-3.1-405b | `meta-llama/Llama-3.1-405B` | 405.0B | 107,506 | ✓ 云租 (810GB fp16) | vLLM |

## ⚡ 国际边缘 (14 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| llama-3.2-1b | `meta-llama/Llama-3.2-1B` | 1.0B | 806,970 | ✓ 云租 (2GB fp16) | vLLM |
| llama-3.2-1b-instruct | `meta-llama/Llama-3.2-1B-Instruct` | 1.0B | 7,420,279 | ✓ 云租 (2GB fp16) | vLLM |
| gemma-3-1b-it | `google/gemma-3-1b-it` | 1.0B | 3,368,913 | ✓ 云租 (2GB fp16) | vLLM |
| llama-3.2-3b | `meta-llama/Llama-3.2-3B` | 3.0B | 361,061 | ✓ 云租 (6GB fp16) | vLLM |
| llama-3.2-3b-instruct | `meta-llama/Llama-3.2-3B-Instruct` | 3.0B | 1,942,406 | ✓ 云租 (6GB fp16) | vLLM |
| phi-4-mini | `microsoft/Phi-4-mini-instruct` | 3.8B | 380,442 | ✓ 云租 (8GB fp16) | vLLM |
| phi-3.5-mini | `microsoft/Phi-3.5-mini-instruct` | 3.8B | 343,352 | ✓ 云租 (8GB fp16) | vLLM |
| nvidia-nemotron-3-nano-4b | `nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16` | 3.97B | 4,810,763 | ✓ 云租 (8GB fp16) | vLLM |
| gemma-3-4b | `google/gemma-3-4b-it` | 4.0B | 1,611,957 | ✓ 云租 (8GB fp16) | vLLM |
| mistral-7b-instruct-v0.2 | `mistralai/Mistral-7B-Instruct-v0.2` | 7.0B | 1,790,391 | ✓ 云租 (14GB fp16) | vLLM |
| llama-3.1-8b-instruct | `meta-llama/Llama-3.1-8B-Instruct` | 8.03B | 6,191,239 | ✓ 云租 (16GB fp16) | vLLM |
| gemma-3-9b | `google/gemma-3-9b-it` | 9.0B | N/A | ✓ 云租 (18GB fp16) | vLLM |
| phi-4 | `microsoft/phi-4` | 14.0B | 607,294 | ✓ 云租 (28GB fp16) | vLLM |
| openai-gpt-oss-20b | `openai/gpt-oss-20b` | 20.91B | 6,765,653 | ✓ 云租 (42GB fp16) | vLLM |

## 🔢 Embedding (28 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 | `sentence-transformers/all-MiniLM-L6-v2` | 0.02B | 245,656,284 | ✓ 云租 (0GB fp16) | vLLM |
| bge-small-zh-v1.5 | `BAAI/bge-small-zh-v1.5` | 0.02B | 5,013,989 | ✓ 云租 (0GB fp16) | vLLM |
| bge-small-en-v1.5 | `BAAI/bge-small-en-v1.5` | 0.03B | 63,423,862 | ✓ 云租 (0GB fp16) | vLLM |
| paraphrase-MiniLM-L6-v2 | `sentence-transformers/paraphrase-MiniLM-L6-v2` | 0.04B | 1,354,525 | ✓ 云租 (0GB fp16) | vLLM |
| all-distilroberta-v1 | `sentence-transformers/all-distilroberta-v1` | 0.08B | 2,735,901 | ✓ 云租 (0GB fp16) | vLLM |
| bge-base-zh-v1.5 | `BAAI/bge-base-zh-v1.5` | 0.1B | 719,092 | ✓ 云租 (0GB fp16) | vLLM |
| all-mpnet-base-v2 | `sentence-transformers/all-mpnet-base-v2` | 0.11B | 21,122,520 | ✓ 云租 (0GB fp16) | vLLM |
| bge-base-en-v1.5 | `BAAI/bge-base-en-v1.5` | 0.11B | 9,858,368 | ✓ 云租 (0GB fp16) | vLLM |
| e5-base-v2 | `intfloat/e5-base-v2` | 0.11B | 733,721 | ✓ 云租 (0GB fp16) | vLLM |
| paraphrase-multilingual-MiniLM-L12-v2 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 0.12B | 45,390,285 | ✓ 云租 (0GB fp16) | vLLM |
| multilingual-e5-small | `intfloat/multilingual-e5-small` | 0.12B | 12,075,000 | ✓ 云租 (0GB fp16) | vLLM |
| all-minilm-l12-v2 | `sentence-transformers/all-MiniLM-L12-v2` | 0.12B | 3,854,469 | ✓ 云租 (0GB fp16) | vLLM |
| nomic-embed-text-v1.5 | `nomic-ai/nomic-embed-text-v1.5` | 0.14B | 13,901,594 | ✓ 云租 (0GB fp16) | vLLM |
| distiluse-base-multilingual-cased-v2 | `sentence-transformers/distiluse-base-multilingual-cased-v2` | 0.14B | 1,087,889 | ✓ 云租 (0GB fp16) | vLLM |
| multilingual-e5-base | `intfloat/multilingual-e5-base` | 0.28B | 7,477,286 | ✓ 云租 (1GB fp16) | vLLM |
| paraphrase-multilingual-mpnet-base-v2 | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 0.28B | 9,823,937 | ✓ 云租 (1GB fp16) | vLLM |
| paraphrase-mpnet-base-v2 | `sentence-transformers/paraphrase-mpnet-base-v2` | 0.28B | 1,776,971 | ✓ 云租 (1GB fp16) | vLLM |
| multi-qa-mpnet-base-dot-v1 | `sentence-transformers/multi-qa-mpnet-base-dot-v1` | 0.28B | 1,469,197 | ✓ 云租 (1GB fp16) | vLLM |
| bge-large-zh-v1.5 | `BAAI/bge-large-zh-v1.5` | 0.3B | 904,808 | ✓ 云租 (1GB fp16) | vLLM |
| embeddinggemma-300m | `google/embeddinggemma-300m` | 0.3B | 2,882,794 | ✓ 云租 (1GB fp16) | vLLM |
| gte-multilingual-base | `Alibaba-NLP/gte-multilingual-base` | 0.31B | 1,485,407 | ✓ 云租 (1GB fp16) | vLLM |
| e5-large-v2 | `intfloat/e5-large-v2` | 0.34B | 1,412,885 | ✓ 云租 (1GB fp16) | vLLM |
| gte-large-en-v1.5 | `Alibaba-NLP/gte-large-en-v1.5` | 0.43B | 1,036,369 | ✓ 云租 (1GB fp16) | vLLM |
| multilingual-e5-large | `intfloat/multilingual-e5-large` | 0.56B | 7,362,605 | ✓ 云租 (1GB fp16) | vLLM |
| bge-m3 | `BAAI/bge-m3` | 0.6B | 36,622,223 | ✓ 云租 (1GB fp16) | vLLM |
| qwen3-embedding-0.6b | `Qwen/Qwen3-Embedding-0.6B` | 0.6B | 9,274,512 | ✓ 云租 (1GB fp16) | vLLM |
| gte-qwen2-7b-instruct | `Alibaba-NLP/gte-Qwen2-7B-instruct` | 7.0B | 111,253 | ✓ 云租 (14GB fp16) | vLLM |
| qwen3-embedding-8b | `Qwen/Qwen3-Embedding-8B` | 8.0B | 2,608,006 | ✓ 云租 (16GB fp16) | vLLM |

## 📊 Reranker (2 个)

| 模型 | HF Repo | size | Downloads | 档位 | 框架 |
|---|---|---|---|---|---|
| bge-reranker-large | `BAAI/bge-reranker-large` | 0.56B | 2,691,943 | ✓ 云租 (1GB fp16) | vLLM |
| bge-reranker-v2-m3 | `BAAI/bge-reranker-v2-m3` | 0.6B | 17,142,564 | ✓ 云租 (1GB fp16) | vLLM |

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

**快照时间**: 2026-09-26 12:30
**下次更新**: 下周一北京时间 8:00

**数据源**:
- HF 模型元数据：`data/hf-metadata-snapshot.json`
- GPU 价格：`data/gpu-prices-snapshot.json`
- 模型清单：`src/core/model_resolver.py`

**自动化工作流**: `.github/workflows/refresh-models.yml`
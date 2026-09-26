# auto_fetch_models.py · top 50 patch
# apply: 复制下方 { ... } 块，粘到 src/core/model_resolver.py 的 KNOWN_MODELS 末尾

# === auto_fetch_models.py patch · 185 条候选 ===
# 复制下列 { ... } 块到 src/core/model_resolver.py 的 KNOWN_MODELS 字典末尾
# 建议配合 --top=N 控制数量

    "sentence-transformers-paraphrase-multilingual-mpnet-base-v2": {
        "hf_repo": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "github": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 9823937,
            "likes": 524,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 9.82M DLs",
    },

    "qwen-qwen3-6-35b-a3b-fp8": {
        "hf_repo": "Qwen/Qwen3.6-35B-A3B-FP8",
        "github": "Qwen/Qwen3.6-35B-A3B-FP8",
        "category": "vision",
        "size_b": 35,
        "_auto_fetched": {
            "downloads": 7859348,
            "likes": 415,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 7.86M DLs",
    },

    "meta-llama-llama-3-2-1b-instruct": {
        "hf_repo": "meta-llama/Llama-3.2-1B-Instruct",
        "github": "meta-llama/Llama-3.2-1B-Instruct",
        "category": "international-edge",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 7420279,
            "likes": 1728,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 7.42M DLs · 1728 likes",
    },

    "qwen-qwen3-8-27b-fp8": {
        "hf_repo": "Qwen/Qwen3.8-27B-FP8",
        "github": "Qwen/Qwen3.8-27B-FP8",
        "category": "vision",
        "size_b": 27,
        "_auto_fetched": {
            "downloads": 5509853,
            "likes": 859,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 5.51M DLs",
    },

    "qwen-qwen3-6-27b-fp8": {
        "hf_repo": "Qwen/Qwen3.6-27B-FP8",
        "github": "Qwen/Qwen3.6-27B-FP8",
        "category": "vision",
        "size_b": 27,
        "_auto_fetched": {
            "downloads": 4622205,
            "likes": 357,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 4.62M DLs",
    },

    "sentence-transformers-all-minilm-l12-v2": {
        "hf_repo": "sentence-transformers/all-MiniLM-L12-v2",
        "github": "sentence-transformers/all-MiniLM-L12-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 3854469,
            "likes": 330,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 3.85M DLs",
    },

    "stabilityai-stable-diffusion-xl-base-1-0": {
        "hf_repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "github": "stabilityai/stable-diffusion-xl-base-1.0",
        "category": "image-generation",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 3598555,
            "likes": 8235,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 3.60M DLs",
    },

    "google-gemma-3-1b-it": {
        "hf_repo": "google/gemma-3-1b-it",
        "github": "google/gemma-3-1b-it",
        "category": "international-edge",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 3368913,
            "likes": 1189,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 3.37M DLs · 1189 likes",
    },

    "eleutherai-pythia-160m": {
        "hf_repo": "EleutherAI/pythia-160m",
        "github": "EleutherAI/pythia-160m",
        "category": "international-dense",
        "size_b": 0.16,
        "_auto_fetched": {
            "downloads": 3315221,
            "likes": 45,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 3.32M DLs · 45 likes",
    },

    "microsoft-florence-2-base": {
        "hf_repo": "microsoft/Florence-2-base",
        "github": "microsoft/Florence-2-base",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 3046535,
            "likes": 401,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 3.05M DLs",
    },

    "deepseek-ai-deepseek-v3-2": {
        "hf_repo": "deepseek-ai/DeepSeek-V3.2",
        "github": "deepseek-ai/DeepSeek-V3.2",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 2927777,
            "likes": 1496,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 2.93M DLs · 1496 likes",
    },

    "google-embeddinggemma-300m": {
        "hf_repo": "google/embeddinggemma-300m",
        "github": "google/embeddinggemma-300m",
        "category": "embedding",
        "size_b": 0.30,
        "_auto_fetched": {
            "downloads": 2882794,
            "likes": 1942,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 2.88M DLs",
    },

    "sentence-transformers-all-distilroberta-v1": {
        "hf_repo": "sentence-transformers/all-distilroberta-v1",
        "github": "sentence-transformers/all-distilroberta-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 2735901,
            "likes": 44,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 2.74M DLs",
    },

    "qwen-qwen2-5-vl-3b-instruct": {
        "hf_repo": "Qwen/Qwen2.5-VL-3B-Instruct",
        "github": "Qwen/Qwen2.5-VL-3B-Instruct",
        "category": "vision",
        "size_b": 3,
        "_auto_fetched": {
            "downloads": 2372984,
            "likes": 706,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 2.37M DLs",
    },

    "deepseek-ai-deepseek-ocr": {
        "hf_repo": "deepseek-ai/DeepSeek-OCR",
        "github": "deepseek-ai/DeepSeek-OCR",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 2231803,
            "likes": 3388,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 2.23M DLs",
    },

    "qwen-qwen3-vl-8b-instruct-fp8": {
        "hf_repo": "Qwen/Qwen3-VL-8B-Instruct-FP8",
        "github": "Qwen/Qwen3-VL-8B-Instruct-FP8",
        "category": "vision",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 2109221,
            "likes": 83,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 2.11M DLs",
    },

    "qwen-qwen2-vl-2b-instruct": {
        "hf_repo": "Qwen/Qwen2-VL-2B-Instruct",
        "github": "Qwen/Qwen2-VL-2B-Instruct",
        "category": "vision",
        "size_b": 2,
        "_auto_fetched": {
            "downloads": 1997712,
            "likes": 520,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 2.00M DLs",
    },

    "meta-llama-llama-3-2-3b-instruct": {
        "hf_repo": "meta-llama/Llama-3.2-3B-Instruct",
        "github": "meta-llama/Llama-3.2-3B-Instruct",
        "category": "international-edge",
        "size_b": 3,
        "_auto_fetched": {
            "downloads": 1942406,
            "likes": 2663,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.94M DLs · 2663 likes",
    },

    "qwen-qwen2-5-coder-14b-instruct": {
        "hf_repo": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "github": "Qwen/Qwen2.5-Coder-14B-Instruct",
        "category": "code",
        "size_b": 14,
        "_auto_fetched": {
            "downloads": 1792245,
            "likes": 189,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.79M DLs · 189 likes",
    },

    "mistralai-mistral-7b-instruct-v0-2": {
        "hf_repo": "mistralai/Mistral-7B-Instruct-v0.2",
        "github": "mistralai/Mistral-7B-Instruct-v0.2",
        "category": "international-edge",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 1790391,
            "likes": 3235,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.79M DLs · 3235 likes",
    },

    "sentence-transformers-paraphrase-mpnet-base-v2": {
        "hf_repo": "sentence-transformers/paraphrase-mpnet-base-v2",
        "github": "sentence-transformers/paraphrase-mpnet-base-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1776971,
            "likes": 51,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.78M DLs",
    },

    "moonshotai-kimi-k3": {
        "hf_repo": "moonshotai/Kimi-K3",
        "github": "moonshotai/Kimi-K3",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1701655,
            "likes": 11518,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 1.70M DLs",
    },

    "qwen-qwen3-30b-a3b": {
        "hf_repo": "Qwen/Qwen3-30B-A3B",
        "github": "Qwen/Qwen3-30B-A3B",
        "category": "domestic-general",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 1620719,
            "likes": 950,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.62M DLs · 950 likes",
    },

    "qwen-qwen3-5-35b-a3b-fp8": {
        "hf_repo": "Qwen/Qwen3.5-35B-A3B-FP8",
        "github": "Qwen/Qwen3.5-35B-A3B-FP8",
        "category": "vision",
        "size_b": 35,
        "_auto_fetched": {
            "downloads": 1562895,
            "likes": 157,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 1.56M DLs",
    },

    "qwen-qwen2-5-0-5b": {
        "hf_repo": "Qwen/Qwen2.5-0.5B",
        "github": "Qwen/Qwen2.5-0.5B",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1543648,
            "likes": 458,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.54M DLs · 458 likes",
    },

    "alibaba-nlp-gte-multilingual-base": {
        "hf_repo": "Alibaba-NLP/gte-multilingual-base",
        "github": "Alibaba-NLP/gte-multilingual-base",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1485407,
            "likes": 377,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.49M DLs",
    },

    "sentence-transformers-multi-qa-mpnet-base-dot-v1": {
        "hf_repo": "sentence-transformers/multi-qa-mpnet-base-dot-v1",
        "github": "sentence-transformers/multi-qa-mpnet-base-dot-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1469197,
            "likes": 194,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.47M DLs",
    },

    "intfloat-e5-large-v2": {
        "hf_repo": "intfloat/e5-large-v2",
        "github": "intfloat/e5-large-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1412885,
            "likes": 283,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.41M DLs",
    },

    "qwen-qwen3-1-7b-base": {
        "hf_repo": "Qwen/Qwen3-1.7B-Base",
        "github": "Qwen/Qwen3-1.7B-Base",
        "category": "domestic-general",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 1405245,
            "likes": 80,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.41M DLs · 80 likes",
    },

    "qwen-qwen3-4b-base": {
        "hf_repo": "Qwen/Qwen3-4B-Base",
        "github": "Qwen/Qwen3-4B-Base",
        "category": "domestic-general",
        "size_b": 4,
        "_auto_fetched": {
            "downloads": 1380742,
            "likes": 98,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.38M DLs · 98 likes",
    },

    "sentence-transformers-paraphrase-minilm-l6-v2": {
        "hf_repo": "sentence-transformers/paraphrase-MiniLM-L6-v2",
        "github": "sentence-transformers/paraphrase-MiniLM-L6-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1354525,
            "likes": 150,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.35M DLs",
    },

    "deepseek-ai-deepseek-v3-0324": {
        "hf_repo": "deepseek-ai/DeepSeek-V3-0324",
        "github": "deepseek-ai/DeepSeek-V3-0324",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1312304,
            "likes": 3175,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.31M DLs · 3175 likes",
    },

    "deepseek-ai-deepseek-v4-flash": {
        "hf_repo": "deepseek-ai/DeepSeek-V4-Flash",
        "github": "deepseek-ai/DeepSeek-V4-Flash",
        "category": "domestic-reasoning",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1307475,
            "likes": 2259,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.31M DLs · 2259 likes",
    },

    "eleutherai-pythia-70m-deduped": {
        "hf_repo": "EleutherAI/pythia-70m-deduped",
        "github": "EleutherAI/pythia-70m-deduped",
        "category": "international-dense",
        "size_b": 0.07,
        "_auto_fetched": {
            "downloads": 1272938,
            "likes": 30,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.27M DLs · 30 likes",
    },

    "apple-openelm-1-1b-instruct": {
        "hf_repo": "apple/OpenELM-1_1B-Instruct",
        "github": "apple/OpenELM-1_1B-Instruct",
        "category": "international-edge",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 1254147,
            "likes": 76,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.25M DLs · 76 likes",
    },

    "minimaxai-minimax-m2-7": {
        "hf_repo": "MiniMaxAI/MiniMax-M2.7",
        "github": "MiniMaxAI/MiniMax-M2.7",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1237573,
            "likes": 1246,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.24M DLs · 1246 likes",
    },

    "qwen-qwen3-vl-embedding-8b": {
        "hf_repo": "Qwen/Qwen3-VL-Embedding-8B",
        "github": "Qwen/Qwen3-VL-Embedding-8B",
        "category": "embedding",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 1231551,
            "likes": 483,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.23M DLs",
    },

    "nvidia-nvidia-nemotron-3-super-120b-a12b-bf16": {
        "hf_repo": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
        "github": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
        "category": "domestic-general",
        "size_b": 120,
        "_auto_fetched": {
            "downloads": 1224733,
            "likes": 428,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.22M DLs · 428 likes",
    },

    "google-gemma-2-9b-it": {
        "hf_repo": "google/gemma-2-9b-it",
        "github": "google/gemma-2-9b-it",
        "category": "international-edge",
        "size_b": 9,
        "_auto_fetched": {
            "downloads": 1146361,
            "likes": 978,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.15M DLs · 978 likes",
    },

    "qwen-qwen3-coder-30b-a3b-instruct-fp8": {
        "hf_repo": "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8",
        "github": "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8",
        "category": "code",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 1129731,
            "likes": 208,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.13M DLs · 208 likes",
    },

    "meta-llama-meta-llama-3-8b-instruct": {
        "hf_repo": "meta-llama/Meta-Llama-3-8B-Instruct",
        "github": "meta-llama/Meta-Llama-3-8B-Instruct",
        "category": "international-edge",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 1123590,
            "likes": 5118,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.12M DLs · 5118 likes",
    },

    "sentence-transformers-distiluse-base-multilingual-cased-v1": {
        "hf_repo": "sentence-transformers/distiluse-base-multilingual-cased-v1",
        "github": "sentence-transformers/distiluse-base-multilingual-cased-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1107373,
            "likes": 134,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.11M DLs",
    },

    "google-medgemma-4b-it": {
        "hf_repo": "google/medgemma-4b-it",
        "github": "google/medgemma-4b-it",
        "category": "vision",
        "size_b": 4,
        "_auto_fetched": {
            "downloads": 1101082,
            "likes": 1075,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 1.10M DLs",
    },

    "sentence-transformers-distiluse-base-multilingual-cased-v2": {
        "hf_repo": "sentence-transformers/distiluse-base-multilingual-cased-v2",
        "github": "sentence-transformers/distiluse-base-multilingual-cased-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1087889,
            "likes": 209,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.09M DLs",
    },

    "qwen-qwen3-coder-next-fp8": {
        "hf_repo": "Qwen/Qwen3-Coder-Next-FP8",
        "github": "Qwen/Qwen3-Coder-Next-FP8",
        "category": "code",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1084675,
            "likes": 187,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.08M DLs · 187 likes",
    },

    "qwen-qwen3-8-flash-next": {
        "hf_repo": "Qwen/Qwen3.8-Flash-Next",
        "github": "Qwen/Qwen3.8-Flash-Next",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1073493,
            "likes": 5713,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 1.07M DLs",
    },

    "qwen-qwen3-vl-embedding-2b": {
        "hf_repo": "Qwen/Qwen3-VL-Embedding-2B",
        "github": "Qwen/Qwen3-VL-Embedding-2B",
        "category": "embedding",
        "size_b": 2,
        "_auto_fetched": {
            "downloads": 1044650,
            "likes": 458,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.04M DLs",
    },

    "alibaba-nlp-gte-large-en-v1-5": {
        "hf_repo": "Alibaba-NLP/gte-large-en-v1.5",
        "github": "Alibaba-NLP/gte-large-en-v1.5",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1036369,
            "likes": 239,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 1.04M DLs",
    },

    "deepseek-ai-deepseek-v4-flash-dspark": {
        "hf_repo": "deepseek-ai/DeepSeek-V4-Flash-DSpark",
        "github": "deepseek-ai/DeepSeek-V4-Flash-DSpark",
        "category": "domestic-reasoning",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 1013784,
            "likes": 283,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 1.01M DLs · 283 likes",
    },

    "stabilityai-sdxl-turbo": {
        "hf_repo": "stabilityai/sdxl-turbo",
        "github": "stabilityai/sdxl-turbo",
        "category": "image-generation",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 990384,
            "likes": 2632,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 0.99M DLs",
    },

    "qwen-qwen3-4b-instruct-2507-fp8": {
        "hf_repo": "Qwen/Qwen3-4B-Instruct-2507-FP8",
        "github": "Qwen/Qwen3-4B-Instruct-2507-FP8",
        "category": "domestic-general",
        "size_b": 4,
        "_auto_fetched": {
            "downloads": 984064,
            "likes": 84,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.98M DLs · 84 likes",
    },

    "qwen-qwen2-5-7b": {
        "hf_repo": "Qwen/Qwen2.5-7B",
        "github": "Qwen/Qwen2.5-7B",
        "category": "domestic-general",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 967304,
            "likes": 319,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.97M DLs · 319 likes",
    },

    "deepseek-ai-deepseek-v4-flash-vision-exp": {
        "hf_repo": "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp",
        "github": "deepseek-ai/DeepSeek-V4-Flash-Vision-Exp",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 925431,
            "likes": 928,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.93M DLs",
    },

    "meta-llama-llama-3-3-70b-instruct": {
        "hf_repo": "meta-llama/Llama-3.3-70B-Instruct",
        "github": "meta-llama/Llama-3.3-70B-Instruct",
        "category": "international-dense",
        "size_b": 70,
        "_auto_fetched": {
            "downloads": 921237,
            "likes": 3060,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.92M DLs · 3060 likes",
    },

    "qwen-qwen2-5-vl-32b-instruct": {
        "hf_repo": "Qwen/Qwen2.5-VL-32B-Instruct",
        "github": "Qwen/Qwen2.5-VL-32B-Instruct",
        "category": "vision",
        "size_b": 32,
        "_auto_fetched": {
            "downloads": 913384,
            "likes": 501,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.91M DLs",
    },

    "qwen-qwen3-5-122b-a10b-fp8": {
        "hf_repo": "Qwen/Qwen3.5-122B-A10B-FP8",
        "github": "Qwen/Qwen3.5-122B-A10B-FP8",
        "category": "vision",
        "size_b": 122,
        "_auto_fetched": {
            "downloads": 856896,
            "likes": 117,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.86M DLs",
    },

    "deepseek-ai-deepseek-ocr-2": {
        "hf_repo": "deepseek-ai/DeepSeek-OCR-2",
        "github": "deepseek-ai/DeepSeek-OCR-2",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 847212,
            "likes": 1104,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.85M DLs",
    },

    "meta-llama-llama-2-7b-hf": {
        "hf_repo": "meta-llama/Llama-2-7b-hf",
        "github": "meta-llama/Llama-2-7b-hf",
        "category": "international-edge",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 825265,
            "likes": 2421,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.83M DLs · 2421 likes",
    },

    "qwen-qwen3-30b-a3b-instruct-2507": {
        "hf_repo": "Qwen/Qwen3-30B-A3B-Instruct-2507",
        "github": "Qwen/Qwen3-30B-A3B-Instruct-2507",
        "category": "domestic-general",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 800526,
            "likes": 840,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.80M DLs · 840 likes",
    },

    "sentence-transformers-multi-qa-minilm-l6-cos-v1": {
        "hf_repo": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
        "github": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 791826,
            "likes": 138,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.79M DLs",
    },

    "qwen-qwen3-coder-480b-a35b-instruct-fp8": {
        "hf_repo": "Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
        "github": "Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
        "category": "code",
        "size_b": 480,
        "_auto_fetched": {
            "downloads": 780585,
            "likes": 161,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.78M DLs · 161 likes",
    },

    "deepseek-ai-deepseek-r1-0528-qwen3-8b": {
        "hf_repo": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        "github": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        "category": "domestic-reasoning",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 780089,
            "likes": 1090,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.78M DLs · 1090 likes",
    },

    "qwen-qwen2-5-1-5b": {
        "hf_repo": "Qwen/Qwen2.5-1.5B",
        "github": "Qwen/Qwen2.5-1.5B",
        "category": "domestic-general",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 777064,
            "likes": 224,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.78M DLs · 224 likes",
    },

    "qwen-qwen2-vl-7b-instruct": {
        "hf_repo": "Qwen/Qwen2-VL-7B-Instruct",
        "github": "Qwen/Qwen2-VL-7B-Instruct",
        "category": "vision",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 775237,
            "likes": 1287,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.78M DLs",
    },

    "microsoft-phi-3-5-vision-instruct": {
        "hf_repo": "microsoft/Phi-3.5-vision-instruct",
        "github": "microsoft/Phi-3.5-vision-instruct",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 758084,
            "likes": 739,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.76M DLs",
    },

    "qwen-qwen3-0-6b-base": {
        "hf_repo": "Qwen/Qwen3-0.6B-Base",
        "github": "Qwen/Qwen3-0.6B-Base",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 748276,
            "likes": 197,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.75M DLs · 197 likes",
    },

    "eleutherai-pythia-6-9b": {
        "hf_repo": "EleutherAI/pythia-6.9b",
        "github": "EleutherAI/pythia-6.9b",
        "category": "international-edge",
        "size_b": 6,
        "_auto_fetched": {
            "downloads": 740169,
            "likes": 66,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.74M DLs · 66 likes",
    },

    "intfloat-e5-base-v2": {
        "hf_repo": "intfloat/e5-base-v2",
        "github": "intfloat/e5-base-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 733721,
            "likes": 157,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.73M DLs",
    },

    "nvidia-nvidia-nemotron-3-nano-30b-a3b-bf16": {
        "hf_repo": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
        "github": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
        "category": "domestic-general",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 732053,
            "likes": 823,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.73M DLs · 823 likes",
    },

    "qwen-qwen3-5-397b-a17b-fp8": {
        "hf_repo": "Qwen/Qwen3.5-397B-A17B-FP8",
        "github": "Qwen/Qwen3.5-397B-A17B-FP8",
        "category": "vision",
        "size_b": 397,
        "_auto_fetched": {
            "downloads": 724893,
            "likes": 185,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.72M DLs",
    },

    "nvidia-cosmos-reason2-2b": {
        "hf_repo": "nvidia/Cosmos-Reason2-2B",
        "github": "nvidia/Cosmos-Reason2-2B",
        "category": "vision",
        "size_b": 2,
        "_auto_fetched": {
            "downloads": 720471,
            "likes": 246,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.72M DLs",
    },

    "intfloat-e5-base": {
        "hf_repo": "intfloat/e5-base",
        "github": "intfloat/e5-base",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 714814,
            "likes": 26,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.71M DLs",
    },

    "opengvlab-internvl2-1b": {
        "hf_repo": "OpenGVLab/InternVL2-1B",
        "github": "OpenGVLab/InternVL2-1B",
        "category": "vision",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 709860,
            "likes": 83,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.71M DLs",
    },

    "opengvlab-internvl2-2b": {
        "hf_repo": "OpenGVLab/InternVL2-2B",
        "github": "OpenGVLab/InternVL2-2B",
        "category": "vision",
        "size_b": 2,
        "_auto_fetched": {
            "downloads": 704959,
            "likes": 82,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.70M DLs",
    },

    "tencent-hunyuanocr": {
        "hf_repo": "tencent/HunyuanOCR",
        "github": "tencent/HunyuanOCR",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 702569,
            "likes": 825,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.70M DLs",
    },

    "sentence-transformers-paraphrase-minilm-l3-v2": {
        "hf_repo": "sentence-transformers/paraphrase-MiniLM-L3-v2",
        "github": "sentence-transformers/paraphrase-MiniLM-L3-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 700542,
            "likes": 31,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.70M DLs",
    },

    "deepseek-ai-deepseek-coder-7b-instruct-v1-5": {
        "hf_repo": "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
        "github": "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
        "category": "code",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 690697,
            "likes": 163,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.69M DLs · 163 likes",
    },

    "sentence-transformers-labse": {
        "hf_repo": "sentence-transformers/LaBSE",
        "github": "sentence-transformers/LaBSE",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 678761,
            "likes": 348,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.68M DLs",
    },

    "google-gemma-4-31b": {
        "hf_repo": "google/gemma-4-31B",
        "github": "google/gemma-4-31B",
        "category": "vision",
        "size_b": 31,
        "_auto_fetched": {
            "downloads": 668262,
            "likes": 540,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.67M DLs",
    },

    "qwen-qwen3-8b-fp8": {
        "hf_repo": "Qwen/Qwen3-8B-FP8",
        "github": "Qwen/Qwen3-8B-FP8",
        "category": "domestic-general",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 666477,
            "likes": 64,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.67M DLs · 64 likes",
    },

    "qwen-qwen2-1-5b-instruct": {
        "hf_repo": "Qwen/Qwen2-1.5B-Instruct",
        "github": "Qwen/Qwen2-1.5B-Instruct",
        "category": "domestic-general",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 649628,
            "likes": 164,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.65M DLs · 164 likes",
    },

    "sentence-transformers-nli-mpnet-base-v2": {
        "hf_repo": "sentence-transformers/nli-mpnet-base-v2",
        "github": "sentence-transformers/nli-mpnet-base-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 643465,
            "likes": 15,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.64M DLs",
    },

    "qwen-qwen2-5-coder-7b": {
        "hf_repo": "Qwen/Qwen2.5-Coder-7B",
        "github": "Qwen/Qwen2.5-Coder-7B",
        "category": "code",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 642681,
            "likes": 173,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.64M DLs · 173 likes",
    },

    "qwen-qwen2-0-5b": {
        "hf_repo": "Qwen/Qwen2-0.5B",
        "github": "Qwen/Qwen2-0.5B",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 636457,
            "likes": 172,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.64M DLs · 172 likes",
    },

    "google-gemma-2-2b-it": {
        "hf_repo": "google/gemma-2-2b-it",
        "github": "google/gemma-2-2b-it",
        "category": "international-edge",
        "size_b": 2,
        "_auto_fetched": {
            "downloads": 627727,
            "likes": 1525,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.63M DLs · 1525 likes",
    },

    "google-diffusiongemma-26b-a4b-it": {
        "hf_repo": "google/diffusiongemma-26B-A4B-it",
        "github": "google/diffusiongemma-26B-A4B-it",
        "category": "vision",
        "size_b": 26,
        "_auto_fetched": {
            "downloads": 620041,
            "likes": 1255,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.62M DLs",
    },

    "sentence-transformers-all-roberta-large-v1": {
        "hf_repo": "sentence-transformers/all-roberta-large-v1",
        "github": "sentence-transformers/all-roberta-large-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 615289,
            "likes": 66,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.62M DLs",
    },

    "alibaba-nlp-gte-qwen2-1-5b-instruct": {
        "hf_repo": "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
        "github": "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
        "category": "embedding",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 608396,
            "likes": 238,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.61M DLs",
    },

    "intfloat-e5-small-v2": {
        "hf_repo": "intfloat/e5-small-v2",
        "github": "intfloat/e5-small-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 602752,
            "likes": 126,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.60M DLs",
    },

    "qwen-qwen2-5-coder-3b-instruct": {
        "hf_repo": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "github": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "category": "code",
        "size_b": 3,
        "_auto_fetched": {
            "downloads": 599469,
            "likes": 129,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.60M DLs · 129 likes",
    },

    "sentence-transformers-paraphrase-albert-small-v2": {
        "hf_repo": "sentence-transformers/paraphrase-albert-small-v2",
        "github": "sentence-transformers/paraphrase-albert-small-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 595684,
            "likes": 12,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.60M DLs",
    },

    "google-gemma-3-12b-it": {
        "hf_repo": "google/gemma-3-12b-it",
        "github": "google/gemma-3-12b-it",
        "category": "vision",
        "size_b": 12,
        "_auto_fetched": {
            "downloads": 573141,
            "likes": 842,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.57M DLs",
    },

    "meta-llama-llama-3-1-8b": {
        "hf_repo": "meta-llama/Llama-3.1-8B",
        "github": "meta-llama/Llama-3.1-8B",
        "category": "international-edge",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 570430,
            "likes": 2537,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.57M DLs · 2537 likes",
    },

    "eleutherai-gpt-neox-20b": {
        "hf_repo": "EleutherAI/gpt-neox-20b",
        "github": "EleutherAI/gpt-neox-20b",
        "category": "international-dense",
        "size_b": 20,
        "_auto_fetched": {
            "downloads": 556710,
            "likes": 587,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.56M DLs · 587 likes",
    },

    "microsoft-phi-2": {
        "hf_repo": "microsoft/phi-2",
        "github": "microsoft/phi-2",
        "category": "international-dense",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 555680,
            "likes": 3523,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.56M DLs · 3523 likes",
    },

    "qwen-qwen3-coder-next": {
        "hf_repo": "Qwen/Qwen3-Coder-Next",
        "github": "Qwen/Qwen3-Coder-Next",
        "category": "code",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 535641,
            "likes": 1663,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.54M DLs · 1663 likes",
    },

    "qwen-qwen2-5-coder-1-5b-instruct": {
        "hf_repo": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "github": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "category": "code",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 535347,
            "likes": 147,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.54M DLs · 147 likes",
    },

    "qwen-qwen1-5-moe-a2-7b": {
        "hf_repo": "Qwen/Qwen1.5-MoE-A2.7B",
        "github": "Qwen/Qwen1.5-MoE-A2.7B",
        "category": "domestic-general",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 534187,
            "likes": 229,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.53M DLs · 229 likes",
    },

    "eleutherai-gpt-neo-125m": {
        "hf_repo": "EleutherAI/gpt-neo-125m",
        "github": "EleutherAI/gpt-neo-125m",
        "category": "international-dense",
        "size_b": 0.12,
        "_auto_fetched": {
            "downloads": 531821,
            "likes": 229,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.53M DLs · 229 likes",
    },

    "eleutherai-pythia-14m": {
        "hf_repo": "EleutherAI/pythia-14m",
        "github": "EleutherAI/pythia-14m",
        "category": "international-dense",
        "size_b": 0.01,
        "_auto_fetched": {
            "downloads": 518394,
            "likes": 6,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.52M DLs · 6 likes",
    },

    "qwen-qwen3-8-flash-next-fp8": {
        "hf_repo": "Qwen/Qwen3.8-Flash-Next-FP8",
        "github": "Qwen/Qwen3.8-Flash-Next-FP8",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 514215,
            "likes": 231,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.51M DLs",
    },

    "nvidia-nemotron-3-embed-1b-bf16": {
        "hf_repo": "nvidia/Nemotron-3-Embed-1B-BF16",
        "github": "nvidia/Nemotron-3-Embed-1B-BF16",
        "category": "embedding",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 507802,
            "likes": 154,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.51M DLs",
    },

    "qwen-qwen3-5-4b-base": {
        "hf_repo": "Qwen/Qwen3.5-4B-Base",
        "github": "Qwen/Qwen3.5-4B-Base",
        "category": "vision",
        "size_b": 4,
        "_auto_fetched": {
            "downloads": 496141,
            "likes": 100,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.50M DLs",
    },

    "meta-llama-llama-2-7b-chat-hf": {
        "hf_repo": "meta-llama/Llama-2-7b-chat-hf",
        "github": "meta-llama/Llama-2-7b-chat-hf",
        "category": "international-edge",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 494078,
            "likes": 4876,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.49M DLs · 4876 likes",
    },

    "sentence-transformers-msmarco-distilbert-base-tas-b": {
        "hf_repo": "sentence-transformers/msmarco-distilbert-base-tas-b",
        "github": "sentence-transformers/msmarco-distilbert-base-tas-b",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 491368,
            "likes": 44,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.49M DLs",
    },

    "qwen-qwen3-8b-base": {
        "hf_repo": "Qwen/Qwen3-8B-Base",
        "github": "Qwen/Qwen3-8B-Base",
        "category": "domestic-general",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 486002,
            "likes": 131,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.49M DLs · 131 likes",
    },

    "deepseek-ai-deepseek-v4-pro": {
        "hf_repo": "deepseek-ai/DeepSeek-V4-Pro",
        "github": "deepseek-ai/DeepSeek-V4-Pro",
        "category": "domestic-reasoning",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 479024,
            "likes": 5598,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.48M DLs · 5598 likes",
    },

    "microsoft-florence-2-large": {
        "hf_repo": "microsoft/Florence-2-large",
        "github": "microsoft/Florence-2-large",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 474312,
            "likes": 1863,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.47M DLs",
    },

    "meta-llama-llama-3-1-405b-fp8": {
        "hf_repo": "meta-llama/Llama-3.1-405B-FP8",
        "github": "meta-llama/Llama-3.1-405B-FP8",
        "category": "international-dense",
        "size_b": 405,
        "_auto_fetched": {
            "downloads": 460007,
            "likes": 124,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.46M DLs · 124 likes",
    },

    "sentence-transformers-msmarco-bert-base-dot-v5": {
        "hf_repo": "sentence-transformers/msmarco-bert-base-dot-v5",
        "github": "sentence-transformers/msmarco-bert-base-dot-v5",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 458364,
            "likes": 21,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.46M DLs",
    },

    "qwen-qwen3-30b-a3b-instruct-2507-fp8": {
        "hf_repo": "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8",
        "github": "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8",
        "category": "domestic-general",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 453918,
            "likes": 133,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.45M DLs · 133 likes",
    },

    "opengvlab-internvl3-5-gpt-oss-20b-a4b-preview-hf": {
        "hf_repo": "OpenGVLab/InternVL3_5-GPT-OSS-20B-A4B-Preview-HF",
        "github": "OpenGVLab/InternVL3_5-GPT-OSS-20B-A4B-Preview-HF",
        "category": "vision",
        "size_b": 20,
        "_auto_fetched": {
            "downloads": 442084,
            "likes": 9,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.44M DLs",
    },

    "mistralai-mistral-7b-v0-1": {
        "hf_repo": "mistralai/Mistral-7B-v0.1",
        "github": "mistralai/Mistral-7B-v0.1",
        "category": "international-edge",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 430912,
            "likes": 4184,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.43M DLs · 4184 likes",
    },

    "qwen-qwen2-5-coder-1-5b": {
        "hf_repo": "Qwen/Qwen2.5-Coder-1.5B",
        "github": "Qwen/Qwen2.5-Coder-1.5B",
        "category": "code",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 426341,
            "likes": 111,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.43M DLs · 111 likes",
    },

    "nvidia-nvidia-nemotron-3-5-lightning-30b-a3b-bf16": {
        "hf_repo": "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16",
        "github": "nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16",
        "category": "domestic-general",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 425872,
            "likes": 221,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.43M DLs · 221 likes",
    },

    "qwen-qwen3-vl-30b-a3b-instruct": {
        "hf_repo": "Qwen/Qwen3-VL-30B-A3B-Instruct",
        "github": "Qwen/Qwen3-VL-30B-A3B-Instruct",
        "category": "vision",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 425757,
            "likes": 607,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.43M DLs",
    },

    "moonshotai-kimi-k2-6": {
        "hf_repo": "moonshotai/Kimi-K2.6",
        "github": "moonshotai/Kimi-K2.6",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 424027,
            "likes": 1611,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.42M DLs",
    },

    "qwen-qwen3-235b-a22b-instruct-2507-fp8": {
        "hf_repo": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
        "github": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
        "category": "domestic-general",
        "size_b": 235,
        "_auto_fetched": {
            "downloads": 418547,
            "likes": 150,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.42M DLs · 150 likes",
    },

    "qwen-qwen3-4b-thinking-2507": {
        "hf_repo": "Qwen/Qwen3-4B-Thinking-2507",
        "github": "Qwen/Qwen3-4B-Thinking-2507",
        "category": "domestic-general",
        "size_b": 4,
        "_auto_fetched": {
            "downloads": 405001,
            "likes": 618,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.41M DLs · 618 likes",
    },

    "nousresearch-hermes-3-llama-3-1-8b": {
        "hf_repo": "NousResearch/Hermes-3-Llama-3.1-8B",
        "github": "NousResearch/Hermes-3-Llama-3.1-8B",
        "category": "international-edge",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 393416,
            "likes": 507,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.39M DLs · 507 likes",
    },

    "stabilityai-sd-turbo": {
        "hf_repo": "stabilityai/sd-turbo",
        "github": "stabilityai/sd-turbo",
        "category": "image-generation",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 388670,
            "likes": 464,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 0.39M DLs",
    },

    "google-gemma-4-31b-it-qat-w4a16-ct": {
        "hf_repo": "google/gemma-4-31B-it-qat-w4a16-ct",
        "github": "google/gemma-4-31B-it-qat-w4a16-ct",
        "category": "vision",
        "size_b": 31,
        "_auto_fetched": {
            "downloads": 381717,
            "likes": 72,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.38M DLs",
    },

    "nvidia-nvidia-nemotron-nano-9b-v2": {
        "hf_repo": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
        "github": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
        "category": "domestic-general",
        "size_b": 9,
        "_auto_fetched": {
            "downloads": 376664,
            "likes": 520,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.38M DLs · 520 likes",
    },

    "alibaba-nlp-gte-base-en-v1-5": {
        "hf_repo": "Alibaba-NLP/gte-base-en-v1.5",
        "github": "Alibaba-NLP/gte-base-en-v1.5",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 369490,
            "likes": 72,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.37M DLs",
    },

    "qwen-qwen3-5-9b-base": {
        "hf_repo": "Qwen/Qwen3.5-9B-Base",
        "github": "Qwen/Qwen3.5-9B-Base",
        "category": "vision",
        "size_b": 9,
        "_auto_fetched": {
            "downloads": 366329,
            "likes": 118,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.37M DLs",
    },

    "qwen-qwen3-vl-4b-instruct-fp8": {
        "hf_repo": "Qwen/Qwen3-VL-4B-Instruct-FP8",
        "github": "Qwen/Qwen3-VL-4B-Instruct-FP8",
        "category": "vision",
        "size_b": 4,
        "_auto_fetched": {
            "downloads": 358843,
            "likes": 67,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.36M DLs",
    },

    "eleutherai-gpt-j-6b": {
        "hf_repo": "EleutherAI/gpt-j-6b",
        "github": "EleutherAI/gpt-j-6b",
        "category": "international-edge",
        "size_b": 6,
        "_auto_fetched": {
            "downloads": 352598,
            "likes": 1525,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.35M DLs · 1525 likes",
    },

    "microsoft-phi-3-mini-4k-instruct": {
        "hf_repo": "microsoft/Phi-3-mini-4k-instruct",
        "github": "microsoft/Phi-3-mini-4k-instruct",
        "category": "international-dense",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 335430,
            "likes": 1465,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.34M DLs · 1465 likes",
    },

    "qwen-qwen2-5-3b": {
        "hf_repo": "Qwen/Qwen2.5-3B",
        "github": "Qwen/Qwen2.5-3B",
        "category": "domestic-general",
        "size_b": 3,
        "_auto_fetched": {
            "downloads": 335188,
            "likes": 205,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.34M DLs · 205 likes",
    },

    "minimaxai-minimax-m2-5": {
        "hf_repo": "MiniMaxAI/MiniMax-M2.5",
        "github": "MiniMaxAI/MiniMax-M2.5",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 332983,
            "likes": 1507,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.33M DLs · 1507 likes",
    },

    "google-gemma-4-26b-a4b-it-qat-q4-0-unquantized": {
        "hf_repo": "google/gemma-4-26B-A4B-it-qat-q4_0-unquantized",
        "github": "google/gemma-4-26B-A4B-it-qat-q4_0-unquantized",
        "category": "vision",
        "size_b": 26,
        "_auto_fetched": {
            "downloads": 330337,
            "likes": 54,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.33M DLs",
    },

    "qwen-qwen3-vl-235b-a22b-instruct": {
        "hf_repo": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "github": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "category": "vision",
        "size_b": 235,
        "_auto_fetched": {
            "downloads": 327368,
            "likes": 419,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.33M DLs",
    },

    "qwen-qwen2-5-math-1-5b-instruct": {
        "hf_repo": "Qwen/Qwen2.5-Math-1.5B-Instruct",
        "github": "Qwen/Qwen2.5-Math-1.5B-Instruct",
        "category": "domestic-general",
        "size_b": 1,
        "_auto_fetched": {
            "downloads": 323912,
            "likes": 58,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.32M DLs · 58 likes",
    },

    "qwen-qwen3-5-0-8b-base": {
        "hf_repo": "Qwen/Qwen3.5-0.8B-Base",
        "github": "Qwen/Qwen3.5-0.8B-Base",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 321864,
            "likes": 110,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.32M DLs",
    },

    "deepseek-ai-deepseek-v3-1": {
        "hf_repo": "deepseek-ai/DeepSeek-V3.1",
        "github": "deepseek-ai/DeepSeek-V3.1",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 319041,
            "likes": 833,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.32M DLs · 833 likes",
    },

    "nvidia-nvidia-nemotron-3-nano-30b-a3b-fp8": {
        "hf_repo": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8",
        "github": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8",
        "category": "domestic-general",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 311270,
            "likes": 362,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.31M DLs · 362 likes",
    },

    "qwen-qwen3-next-80b-a3b-instruct": {
        "hf_repo": "Qwen/Qwen3-Next-80B-A3B-Instruct",
        "github": "Qwen/Qwen3-Next-80B-A3B-Instruct",
        "category": "domestic-general",
        "size_b": 80,
        "_auto_fetched": {
            "downloads": 310104,
            "likes": 1053,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.31M DLs · 1053 likes",
    },

    "moonshotai-kimi-k2-5": {
        "hf_repo": "moonshotai/Kimi-K2.5",
        "github": "moonshotai/Kimi-K2.5",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 308898,
            "likes": 2876,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.31M DLs",
    },

    "google-medgemma-1-5-4b-it": {
        "hf_repo": "google/medgemma-1.5-4b-it",
        "github": "google/medgemma-1.5-4b-it",
        "category": "vision",
        "size_b": 4,
        "_auto_fetched": {
            "downloads": 308892,
            "likes": 924,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.31M DLs",
    },

    "qwen-qwen3-0-6b-fp8": {
        "hf_repo": "Qwen/Qwen3-0.6B-FP8",
        "github": "Qwen/Qwen3-0.6B-FP8",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 304286,
            "likes": 62,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.30M DLs · 62 likes",
    },

    "qwen-qwen3-14b-base": {
        "hf_repo": "Qwen/Qwen3-14B-Base",
        "github": "Qwen/Qwen3-14B-Base",
        "category": "domestic-general",
        "size_b": 14,
        "_auto_fetched": {
            "downloads": 302919,
            "likes": 59,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.30M DLs · 59 likes",
    },

    "qwen-qwen2-7b-instruct": {
        "hf_repo": "Qwen/Qwen2-7B-Instruct",
        "github": "Qwen/Qwen2-7B-Instruct",
        "category": "domestic-general",
        "size_b": 7,
        "_auto_fetched": {
            "downloads": 300840,
            "likes": 688,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.30M DLs · 688 likes",
    },

    "qwen-qwen2-0-5b-instruct": {
        "hf_repo": "Qwen/Qwen2-0.5B-Instruct",
        "github": "Qwen/Qwen2-0.5B-Instruct",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 299949,
            "likes": 204,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.30M DLs · 204 likes",
    },

    "qwen-qwen2-5-72b-instruct": {
        "hf_repo": "Qwen/Qwen2.5-72B-Instruct",
        "github": "Qwen/Qwen2.5-72B-Instruct",
        "category": "domestic-general",
        "size_b": 72,
        "_auto_fetched": {
            "downloads": 294307,
            "likes": 995,
            "pipeline": "text-generation",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched · 0.29M DLs · 995 likes",
    },

    "qwen-qwen-image": {
        "hf_repo": "Qwen/Qwen-Image",
        "github": "Qwen/Qwen-Image",
        "category": "domestic-general",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 290124,
            "likes": 2656,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 0.29M DLs",
    },

    "google-paligemma-3b-pt-224": {
        "hf_repo": "google/paligemma-3b-pt-224",
        "github": "google/paligemma-3b-pt-224",
        "category": "vision",
        "size_b": 3,
        "_auto_fetched": {
            "downloads": 273293,
            "likes": 598,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.27M DLs",
    },

    "sentence-transformers-bert-base-nli-mean-tokens": {
        "hf_repo": "sentence-transformers/bert-base-nli-mean-tokens",
        "github": "sentence-transformers/bert-base-nli-mean-tokens",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 270823,
            "likes": 40,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.27M DLs",
    },

    "sentence-transformers-paraphrase-minilm-l12-v2": {
        "hf_repo": "sentence-transformers/paraphrase-MiniLM-L12-v2",
        "github": "sentence-transformers/paraphrase-MiniLM-L12-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 225928,
            "likes": 7,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.23M DLs",
    },

    "qwen-qwen3-5-2b-base": {
        "hf_repo": "Qwen/Qwen3.5-2B-Base",
        "github": "Qwen/Qwen3.5-2B-Base",
        "category": "vision",
        "size_b": 2,
        "_auto_fetched": {
            "downloads": 225728,
            "likes": 95,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.23M DLs",
    },

    "microsoft-florence-2-base-ft": {
        "hf_repo": "microsoft/Florence-2-base-ft",
        "github": "microsoft/Florence-2-base-ft",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 222967,
            "likes": 147,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.22M DLs",
    },

    "google-paligemma-3b-ft-cococap-448": {
        "hf_repo": "google/paligemma-3b-ft-cococap-448",
        "github": "google/paligemma-3b-ft-cococap-448",
        "category": "vision",
        "size_b": 3,
        "_auto_fetched": {
            "downloads": 211583,
            "likes": 4,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.21M DLs",
    },

    "qwen-qwen3-vl-32b-instruct-fp8": {
        "hf_repo": "Qwen/Qwen3-VL-32B-Instruct-FP8",
        "github": "Qwen/Qwen3-VL-32B-Instruct-FP8",
        "category": "vision",
        "size_b": 32,
        "_auto_fetched": {
            "downloads": 197925,
            "likes": 54,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.20M DLs",
    },

    "moonshotai-kimi-vl-a3b-instruct": {
        "hf_repo": "moonshotai/Kimi-VL-A3B-Instruct",
        "github": "moonshotai/Kimi-VL-A3B-Instruct",
        "category": "vision",
        "size_b": 3,
        "_auto_fetched": {
            "downloads": 197676,
            "likes": 284,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.20M DLs",
    },

    "qwen-qwen3-5-27b-fp8": {
        "hf_repo": "Qwen/Qwen3.5-27B-FP8",
        "github": "Qwen/Qwen3.5-27B-FP8",
        "category": "vision",
        "size_b": 27,
        "_auto_fetched": {
            "downloads": 196530,
            "likes": 138,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.20M DLs",
    },

    "sentence-transformers-msmarco-minilm-l6-v3": {
        "hf_repo": "sentence-transformers/msmarco-MiniLM-L6-v3",
        "github": "sentence-transformers/msmarco-MiniLM-L6-v3",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 194025,
            "likes": 15,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.19M DLs",
    },

    "qwen-qwen3-vl-30b-a3b-instruct-fp8": {
        "hf_repo": "Qwen/Qwen3-VL-30B-A3B-Instruct-FP8",
        "github": "Qwen/Qwen3-VL-30B-A3B-Instruct-FP8",
        "category": "vision",
        "size_b": 30,
        "_auto_fetched": {
            "downloads": 181357,
            "likes": 115,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.18M DLs",
    },

    "google-gemma-3n-e2b-it": {
        "hf_repo": "google/gemma-3n-E2B-it",
        "github": "google/gemma-3n-E2B-it",
        "category": "vision",
        "size_b": 2,
        "_auto_fetched": {
            "downloads": 177464,
            "likes": 328,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.18M DLs",
    },

    "nvidia-nvidia-nemotron-parse-v1-1": {
        "hf_repo": "nvidia/NVIDIA-Nemotron-Parse-v1.1",
        "github": "nvidia/NVIDIA-Nemotron-Parse-v1.1",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 177116,
            "likes": 171,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.18M DLs",
    },

    "coherelabs-north-micro-vision-instruct": {
        "hf_repo": "CohereLabs/North-Micro-Vision-Instruct",
        "github": "CohereLabs/North-Micro-Vision-Instruct",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 169774,
            "likes": 148,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.17M DLs",
    },

    "meta-llama-llama-4-scout-17b-16e-instruct": {
        "hf_repo": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "github": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "category": "vision",
        "size_b": 17,
        "_auto_fetched": {
            "downloads": 166674,
            "likes": 1357,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.17M DLs",
    },

    "minimaxai-minimax-m3": {
        "hf_repo": "MiniMaxAI/MiniMax-M3",
        "github": "MiniMaxAI/MiniMax-M3",
        "category": "vision",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 165673,
            "likes": 1551,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.17M DLs",
    },

    "qwen-qwen3-vl-8b-thinking": {
        "hf_repo": "Qwen/Qwen3-VL-8B-Thinking",
        "github": "Qwen/Qwen3-VL-8B-Thinking",
        "category": "vision",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 153613,
            "likes": 225,
            "pipeline": "image-text-to-text",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched vision · 0.15M DLs",
    },

    "sentence-transformers-msmarco-minilm-l12-cos-v5": {
        "hf_repo": "sentence-transformers/msmarco-MiniLM-L12-cos-v5",
        "github": "sentence-transformers/msmarco-MiniLM-L12-cos-v5",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 145554,
            "likes": 10,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.15M DLs",
    },

    "alibaba-nlp-gte-modernbert-base": {
        "hf_repo": "Alibaba-NLP/gte-modernbert-base",
        "github": "Alibaba-NLP/gte-modernbert-base",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 141041,
            "likes": 201,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.14M DLs",
    },

    "sentence-transformers-sentence-t5-base": {
        "hf_repo": "sentence-transformers/sentence-t5-base",
        "github": "sentence-transformers/sentence-t5-base",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 139116,
            "likes": 51,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.14M DLs",
    },

    "intfloat-e5-large": {
        "hf_repo": "intfloat/e5-large",
        "github": "intfloat/e5-large",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 135646,
            "likes": 83,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.14M DLs",
    },

    "stabilityai-stable-diffusion-3-5-medium": {
        "hf_repo": "stabilityai/stable-diffusion-3.5-medium",
        "github": "stabilityai/stable-diffusion-3.5-medium",
        "category": "image-generation",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 115315,
            "likes": 1140,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 0.12M DLs",
    },

    "sentence-transformers-multi-qa-mpnet-base-cos-v1": {
        "hf_repo": "sentence-transformers/multi-qa-mpnet-base-cos-v1",
        "github": "sentence-transformers/multi-qa-mpnet-base-cos-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 103140,
            "likes": 42,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.10M DLs",
    },

    "stabilityai-stable-diffusion-3-5-large": {
        "hf_repo": "stabilityai/stable-diffusion-3.5-large",
        "github": "stabilityai/stable-diffusion-3.5-large",
        "category": "image-generation",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 100154,
            "likes": 3923,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 0.10M DLs",
    },

    "nvidia-nemotron-3-embed-8b-bf16": {
        "hf_repo": "nvidia/Nemotron-3-Embed-8B-BF16",
        "github": "nvidia/Nemotron-3-Embed-8B-BF16",
        "category": "embedding",
        "size_b": 8,
        "_auto_fetched": {
            "downloads": 100033,
            "likes": 102,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.10M DLs",
    },

    "sentence-transformers-clip-vit-b-32-multilingual-v1": {
        "hf_repo": "sentence-transformers/clip-ViT-B-32-multilingual-v1",
        "github": "sentence-transformers/clip-ViT-B-32-multilingual-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 93895,
            "likes": 194,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.09M DLs",
    },

    "sentence-transformers-multi-qa-distilbert-cos-v1": {
        "hf_repo": "sentence-transformers/multi-qa-distilbert-cos-v1",
        "github": "sentence-transformers/multi-qa-distilbert-cos-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 89517,
            "likes": 24,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.09M DLs",
    },

    "sentence-transformers-multi-qa-minilm-l6-dot-v1": {
        "hf_repo": "sentence-transformers/multi-qa-MiniLM-L6-dot-v1",
        "github": "sentence-transformers/multi-qa-MiniLM-L6-dot-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 88292,
            "likes": 17,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.09M DLs",
    },

    "sentence-transformers-msmarco-distilbert-base-v4": {
        "hf_repo": "sentence-transformers/msmarco-distilbert-base-v4",
        "github": "sentence-transformers/msmarco-distilbert-base-v4",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 84765,
            "likes": 12,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.08M DLs",
    },

    "sentence-transformers-stsb-roberta-base-v2": {
        "hf_repo": "sentence-transformers/stsb-roberta-base-v2",
        "github": "sentence-transformers/stsb-roberta-base-v2",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 83282,
            "likes": 6,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.08M DLs",
    },

    "sentence-transformers-gtr-t5-base": {
        "hf_repo": "sentence-transformers/gtr-t5-base",
        "github": "sentence-transformers/gtr-t5-base",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 73527,
            "likes": 27,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.07M DLs",
    },

    "sentence-transformers-distilbert-base-nli-stsb-mean-tokens": {
        "hf_repo": "sentence-transformers/distilbert-base-nli-stsb-mean-tokens",
        "github": "sentence-transformers/distilbert-base-nli-stsb-mean-tokens",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 73502,
            "likes": 11,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.07M DLs",
    },

    "stabilityai-stable-diffusion-3-medium-diffusers": {
        "hf_repo": "stabilityai/stable-diffusion-3-medium-diffusers",
        "github": "stabilityai/stable-diffusion-3-medium-diffusers",
        "category": "image-generation",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 70095,
            "likes": 483,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 0.07M DLs",
    },

    "sentence-transformers-stsb-xlm-r-multilingual": {
        "hf_repo": "sentence-transformers/stsb-xlm-r-multilingual",
        "github": "sentence-transformers/stsb-xlm-r-multilingual",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 69711,
            "likes": 53,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.07M DLs",
    },

    "sentence-transformers-multi-qa-distilbert-dot-v1": {
        "hf_repo": "sentence-transformers/multi-qa-distilbert-dot-v1",
        "github": "sentence-transformers/multi-qa-distilbert-dot-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 64282,
            "likes": 1,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.06M DLs",
    },

    "sentence-transformers-msmarco-distilbert-cos-v5": {
        "hf_repo": "sentence-transformers/msmarco-distilbert-cos-v5",
        "github": "sentence-transformers/msmarco-distilbert-cos-v5",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 54363,
            "likes": 10,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.05M DLs",
    },

    "sentence-transformers-gtr-t5-large": {
        "hf_repo": "sentence-transformers/gtr-t5-large",
        "github": "sentence-transformers/gtr-t5-large",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 52201,
            "likes": 40,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.05M DLs",
    },

    "sentence-transformers-paraphrase-distilroberta-base-v1": {
        "hf_repo": "sentence-transformers/paraphrase-distilroberta-base-v1",
        "github": "sentence-transformers/paraphrase-distilroberta-base-v1",
        "category": "embedding",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 51938,
            "likes": 7,
            "pipeline": "sentence-similarity",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched embedding · 0.05M DLs",
    },

    "stabilityai-stable-diffusion-3-5-large-controlnet-canny": {
        "hf_repo": "stabilityai/stable-diffusion-3.5-large-controlnet-canny",
        "github": "stabilityai/stable-diffusion-3.5-large-controlnet-canny",
        "category": "image-generation",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 51788,
            "likes": 15,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 0.05M DLs",
    },

    "stabilityai-stable-diffusion-3-5-large-controlnet-depth": {
        "hf_repo": "stabilityai/stable-diffusion-3.5-large-controlnet-depth",
        "github": "stabilityai/stable-diffusion-3.5-large-controlnet-depth",
        "category": "image-generation",
        "size_b": 0,
        "_auto_fetched": {
            "downloads": 51130,
            "likes": 15,
            "pipeline": "text-to-image",
            "fetched_at": "<ISO_TIMESTAMP>",
        },
        "note": "Auto-fetched image gen · 0.05M DLs",
    },


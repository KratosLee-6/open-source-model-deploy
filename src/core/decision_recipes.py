"""decision_recipes.py · System One 决策模型的真实部署配方

背景
----
`category == "decision"` 的模型**不能用通用的 `vllm serve` 模板部署**。
v1.1.1 之前 `osm-deploy deploy` 对它们一视同仁地给 `vllm serve <hf_repo>`，
起出来的服务只有 `/v1/chat/completions`（聊天接口），而决策模型要的是
`/v1/decide` 或 `/v1/systemone`（类型化决策接口）——用户照着脚本做会卡在
"服务起来了，然后呢？"。

每个模型的实际形态差别很大，本模块把 2026-10-29 逐个核对 model card 得到的
真实配方固化下来：

  形态        : service（起 REST 服务） / library（进程内调用） / hybrid（两者都有）
  接口标准    : /v1/decide（JEV 系、THX-01） / /v1/systemone（Clef、Laya、OpenJEV、XOR、Decider、Strands）
  端口        : 8000 / 3000 / 30000 / 30002 / 8095 —— **不统一，必须按模型给**
  启动步骤    : 单步，或两步（OpenJEV 要先起 vLLM 再起 shim 前置层）

数据来源
--------
每个条目的 install / download / run / endpoint 都来自该模型 HF model card 的
代码块原文（2026-10-29 核对），不是推测。核对脚本：
`scripts/verify_decision_endpoints.py`。

维护约定
--------
- key 用 hf_repo 的小写形式，避免 slug 改名后对不上。
- 新增决策模型时，先跑 verify 脚本拿真实命令，再往这里加。
- 不确定的地方留 `TODO` 注释，**不要编一个看起来合理的命令**。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 接口标准
# ---------------------------------------------------------------------------
ENDPOINT_DECIDE = "/v1/decide"
ENDPOINT_SYSTEMONE = "/v1/systemone"

# 两种标准的请求体差异（写进生成的脚本注释里，帮用户理解为什么不能混用）
ENDPOINT_NOTES = {
    ENDPOINT_DECIDE: (
        "JEV 系用 /v1/decide：单题一问，body 里带 kind + state + question "
        "+ 可选 options，返回 {options, probabilities} 或 {kind, options, probabilities, choice}。"
    ),
    ENDPOINT_SYSTEMONE: (
        "TypeSafe 兼容的 /v1/systemone：一次请求问多题，body 是 state + questions 字典，"
        "每道题自带 type(noul/choice/score) + instructions + criteria，返回 {answers: {...}}。"
    ),
}

# ⚠️ 路径 ≠ body 格式。THX-01 就是反例：路径叫 /v1/decide（别名 /v1/systemone），
# 但 body 用的是 systemone 的多题格式（官方原话 "alias POST /v1/systemone,
# TypeSafe-compatible takes {"state": ..., "questions": {...}}"）。
# 所以 body 形状由 body_format 决定，不由 endpoint 决定。
BODY_DECIDE = "decide"
BODY_SYSTEMONE = "systemone"


# ---------------------------------------------------------------------------
# JEV 决策头常量 —— 2026-10-31 从 autotrust/JEV-9B 真机读取
#   来源：adapter_vllm/decision_head.json（bias + verbalizer_ids + slots）
#         calibration.json（per_kind 温度）
#   为什么内置：这 24 个 bias 只有 ±0.006 量级、温度只有 3 个数，内置后
#   `osm-deploy ask` 不依赖本地模型文件也能算校准概率；模型若更新版本，
#   用 --head-json 覆盖。
# ---------------------------------------------------------------------------
JEV_DECISION_HEAD: Dict[str, Any] = {
    # 24 个 verbalizer 的 lm_head LoRA 偏置（真机读出，不是估算）
    "bias": [
        0.00044773018453270197, -0.0004479771596379578,
        -0.0025878134183585644, -0.0012615364976227283,
        -0.00025007399381138384, 0.0019558551721274853,
        0.0013559526996687055, -0.0023348911199718714,
        -0.0004082925443071872, -0.0002078723773593083,
        -1.2957353646925185e-05, 0.0001676026004133746,
        0.0005569425993598998, -0.001412136247381568,
        -0.0028663526754826307, -0.005061559844762087,
        -0.00593328895047307, -0.004319756291806698,
        -0.004922541789710522, -0.0049067651852965355,
        -0.003943523392081261, -0.003319827374070883,
        -0.005581587553024292, -0.0034480984322726727,
    ],
    # 24 个 verbalizer 的 token id（对应 false,true,0..5,A..P）
    "verbalizer_ids": [
        3721, 1802, 15, 16, 17, 18, 19, 20,
        32, 33, 34, 35, 36, 37, 38, 39,
        40, 41, 42, 43, 44, 45, 46, 47,
    ],
    # 槽位分配：noul 2 个、score 6 个、choice 16 个 —— 这就是硬上限的来源
    "slots": {"noul": [0, 2], "score": [2, 8], "choice": [8, 24]},
    # 每个原语一个温度（校准用）
    "calibration": {
        "noul": 1.0022178236691426,
        "choice": 0.9840233476014968,
        "score": 1.012184473350984,
    },
    "template": "bare-v1",
}


def _recipe(
    display: str,
    form: str,
    framework: str,
    endpoint: str,
    port: Optional[int],
    install: List[str],
    download: List[str],
    run: List[str],
    *,
    body_format: Optional[str] = None,
    served_model: Optional[str] = None,
    decision_head: Optional[Dict[str, Any]] = None,
    health: Optional[str] = None,
    example: Optional[Dict[str, Any]] = None,
    notes: Optional[List[str]] = None,
    vram_note: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "display": display,
        "form": form,                # service | library | hybrid
        "framework": framework,
        "endpoint": endpoint,
        # 实际请求时用什么 model 名：JEV 走 LoRA 名 jev-decision，不是基座名
        "served_model": served_model,
        # vllm_logprobs 形态要的决策头（bias + verbalizer token ids + 温度）
        "decision_head": decision_head,
        # body 形状：默认跟着 endpoint 走，THX-01 这类要显式覆盖
        "body_format": body_format or (
            BODY_DECIDE if endpoint == ENDPOINT_DECIDE else BODY_SYSTEMONE
        ),
        "port": port,
        "install": install,
        "download": download,
        "run": run,
        "health": health or (f"curl -s http://localhost:{port}/v1/models" if port else None),
        "example": example or {},
        "notes": notes or [],
        "vram_note": vram_note,
    }


# ---------------------------------------------------------------------------
# 12 个决策模型的真实配方（2026-10-29 逐个核对 HF model card）
# ---------------------------------------------------------------------------
DECISION_RECIPES: Dict[str, Dict[str, Any]] = {

    # ===== AutoTrust JEV 系：vLLM + LoRA adapter =====
    # 关键：必须挂 adapter_vllm 这个 LoRA，否则只是普通 Qwen，没有决策头
    #
    # ⚠️ 2026-10-31 真机实测纠正：决策走的不是 /v1/decide（那是图像接口，
    #   纯 vLLM 上返回 404），而是 **/v1/completions + allowed_token_ids + logprobs**，
    #   客户端再按 decision_head 的 bias 和 per-kind 温度做校准。
    "autotrust/jev-9b": _recipe(
        display="AutoTrust JEV-9B",
        form="service",
        framework="vLLM + LoRA adapter",
        endpoint="/v1/completions",
        body_format="vllm_logprobs",
        served_model="jev-decision",
        decision_head=JEV_DECISION_HEAD,
        port=8000,
        install=["pip install vllm"],
        download=[
            "hf download autotrust/JEV-9B --local-dir JEV-9B   # ~18 GB",
            # 见 notes：huggingface_hub 的 httpx2 bug 会让 tokenizer 文件静默缺失
        ],
        run=[
            "vllm serve JEV-9B \\",
            "    --served-model-name autotrust/JEV-9B \\",
            "    --enable-lora --max-lora-rank 32 \\",
            "    --lora-modules jev-decision=JEV-9B/adapter_vllm \\",
            "    --logprobs-mode processed_logprobs \\",
            "    --max-model-len 4096",
        ],
        example={
            "kind": "choice",
            "state": "Customer message: my card was charged twice for the same order.",
            "question": "Which team should handle this ticket?",
            "options": ["billing", "shipping", "technical support"],
        },
        notes=[
            "必须带 --enable-lora + --lora-modules jev-decision=<repo>/adapter_vllm，"
            "否则起的是纯 Qwen3.5-9B，没有决策能力。",
            "--logprobs-mode processed_logprobs 不加则读不到校准概率。",
            "**决策请求要发到 /v1/completions，model 填 jev-decision（LoRA 名）**；"
            "填基座名 autotrust/JEV-9B 会走 System 2 自由生成，不是决策。",
            "/v1/decide 只用于图像输入，需要另起 vl/serve.sh（含 vision encoder），纯 vLLM 上没有这个路由。",
            "prompt 必须严格用 [kind]/[state]/[question]/[options]/[decision]: 模板，"
            "choice 选项要带 'A) ' 'B) ' 前缀，否则模型不知道选项顺序。",
            "choice 最多 16 个选项（verbalizer 只到 A-P），score 固定 6 档（0-5）；超了直接 IndexError。",
            "下载后用 `python -c \"from transformers import AutoTokenizer; ...\"` 验证 tokenizer，"
            "若 encode 出 0 个 token 说明 tokenizer.json 缺失（httpx2 的 process() bug），"
            "用 curl 从 hf-mirror 单独补下 tokenizer.json。",
        ],
        vram_note="BF16 ~18GB；单卡 24GB 可跑（实测 RTX 4080 SUPER 32GB 舒适），Q4 量化非官方路径",
    ),

    "autotrust/jev-27b": _recipe(
        display="AutoTrust JEV-27B",
        form="service",
        framework="vLLM + LoRA adapter",
        endpoint=ENDPOINT_DECIDE,
        port=8000,
        install=["pip install vllm"],
        download=[
            "hf download autotrust/JEV-27B --local-dir JEV-27B   # ~54 GB",
        ],
        run=[
            "python3 JEV-27B/serve_decide.py --model JEV-27B \\",
            "    --served-model-name autotrust/JEV-27B \\",
            "    --enable-lora --max-lora-rank 32 \\",
            "    --lora-modules jev-decision=JEV-27B/adapter_vllm \\",
            "    --logprobs-mode processed_logprobs \\",
            "    --max-model-len 32768",
        ],
        example={
            "kind": "choice",
            "state": "SKU AX-330 stock at 8% of safety level; supplier late twice this quarter.",
            "question": "Supplier response for this scenario.",
            "options": ["issue_warning", "renegotiate", "dual_source", "maintain"],
        },
        notes=[
            "启动入口是仓库自带的 serve_decide.py，不是通用 vllm CLI（MAX_MODEL_LEN 32k）。",
            "返回体比 9B 丰富：含 choice_index / choice / adaptation / protocol / usage。",
            "单张 B200 约 140ms/请求（官方口径）。",
        ],
        vram_note="BF16 ~54GB；需 A100 80GB / H100 / B200 级单卡",
    ),

    "autotrust/jev-35b": _recipe(
        display="AutoTrust JEV-35B",
        form="service",
        framework="vLLM（仓库自带 serve.sh）",
        endpoint=ENDPOINT_DECIDE,
        port=8000,
        install=["pip install vllm"],
        download=[
            "hf download autotrust/JEV-35B --local-dir JEV-35B",
            "# NVFP4 量化变体（显存减半，精度略降）：",
            "# hf download autotrust/JEV-35B-NVFP4 --local-dir JEV-35B-NVFP4",
        ],
        run=["bash JEV-35B/serve.sh          # vLLM on :8000"],
        example={
            "kind": "choice",
            "state": "Customer message: my card was charged twice for the same order.",
            "question": "Which team should handle this ticket?",
            "options": ["billing", "shipping", "technical support", "account security"],
        },
        notes=[
            "官方原话：one GPU with 80 GB or more。",
            "MoE 35.95B 总参 / 3B 激活，但权重全常驻，显存按总参算。",
            "NVFP4 变体另有一个 serve.sh，路径换成 JEV-35B-NVFP4。",
        ],
        vram_note="BF16 需 80GB+ 单卡；NVFP4 变体约减半",
    ),

    # ===== Cloudflare Clef 系：SGLang，端口 30000 =====
    "cloudflare/clef": _recipe(
        display="Cloudflare Clef 27B",
        form="service",
        framework="SGLang（docker 镜像 lmsysorg/sglang:dev-clef）",
        endpoint=ENDPOINT_SYSTEMONE,
        port=30000,
        install=[
            "# 推荐走官方镜像，SGLang 主干不一定带 clef 支持：",
            "docker pull lmsysorg/sglang:dev-clef",
        ],
        download=["# 模型由容器内挂载的 ~/.cache/huggingface 自动下载"],
        run=[
            "docker run --gpus all \\",
            "    --shm-size 32g --ipc=host \\",
            "    -p 30000:30000 \\",
            "    -v ~/.cache/huggingface:/root/.cache/huggingface \\",
            "    lmsysorg/sglang:dev-clef \\",
            "    sglang serve \\",
            "        --model-path Cloudflare/clef \\",
            "        --host 0.0.0.0 --port 30000",
        ],
        example={
            "model": "Cloudflare/clef",
            "state": "Our checkout started returning errors and orders are blocked.",
            "questions": {
                "department": {
                    "type": "choice",
                    "instructions": "Which team should handle the message?",
                    "criteria": {"billing": "Payments or invoices",
                                 "technical": "Bugs or outages"},
                },
                "urgency": {
                    "type": "score",
                    "criteria": ["Can wait", "This week", "Today"],
                },
                "outage": {"type": "noul", "instructions": "Is a service down?"},
            },
        },
        notes=[
            "端口是 30000，不是 8000 —— 套用默认端口会连不上。",
            "state 可以直接是字符串，也可以是结构化 dict。",
            "支持图像：record 里加 images 字段（PIL Image 或 base64）。",
            "score 的 criteria 是**有序列表**，索引即分值。",
        ],
        vram_note="27.36B BF16 约 55GB",
    ),

    "cloudflare/clef-flash": _recipe(
        display="Cloudflare Clef Flash 9B",
        form="service",
        framework="SGLang（docker 镜像 lmsysorg/sglang:dev-clef）",
        endpoint=ENDPOINT_SYSTEMONE,
        port=30000,
        install=["docker pull lmsysorg/sglang:dev-clef"],
        download=["# 容器内自动下载"],
        run=[
            "docker run --gpus all \\",
            "    --shm-size 32g --ipc=host \\",
            "    -p 30000:30000 \\",
            "    -v ~/.cache/huggingface:/root/.cache/huggingface \\",
            "    lmsysorg/sglang:dev-clef \\",
            "    sglang serve \\",
            "        --model-path Cloudflare/clef-flash \\",
            "        --host 0.0.0.0 --port 30000",
        ],
        example={
            "model": "Cloudflare/clef-flash",
            "state": "My Stripe integration keeps failing. Please help ASAP.",
            "questions": {
                "urgency": {"type": "noul", "instructions": "Is this urgent?"},
            },
        },
        notes=[
            "与 Clef 27B 同架构，只是底座换 Qwen3.5-9B。",
            "3090 + Ollama 路线实测 12.8GB 占用、约 220ms/3 题（社区口径，非本工具实测）。"
            "Ollama 0.35.1+ 原生支持 /v1/systemone。",
        ],
        vram_note="9.41B BF16 约 19GB；3090 可跑",
    ),

    # ===== Laya：pip 库形态，可以不起服务 =====
    "convaiinnovations/laya": _recipe(
        display="Convai Laya 0.4B",
        form="hybrid",
        framework="pip 包 laya（进程内）+ 可选 laya-serve",
        endpoint=ENDPOINT_SYSTEMONE,
        port=8000,
        install=[
            'pip install laya                 # 进程内调用',
            'pip install "laya[serve]"        # 需要 REST 服务时才装',
        ],
        download=["# 首次 load 时自动下载 checkpoint（~808MB）"],
        run=[
            "# 方式 A：进程内调用（推荐，省掉一次序列化）",
            "python3 - <<'PY'",
            "from laya import Router",
            "router = Router(preload=True)   # 预载三种语言包，切换 <1ms",
            "state = \"We were billed twice for March. Refund today or we cancel.\"",
            "questions = {",
            "    \"department\": {\"type\": \"choice\", \"instructions\": \"Which department?\",",
            "                   \"criteria\": {\"billing\": \"invoices, refunds\",",
            "                                \"technical\": \"bugs, outages\",",
            "                                \"other\": \"everything else\"}},",
            "    \"urgency\": {\"type\": \"score\", \"criteria\": [\"not urgent\", \"soon\", \"blocking\"]},",
            "    \"churn_risk\": {\"type\": \"noul\", \"instructions\": \"Do they threaten to cancel?\"},",
            "}",
            "print(router.predict(state, questions))",
            "PY",
            "",
            "# 方式 B：起 REST 服务",
            "LAYA_DEVICE=cuda LAYA_PRELOAD=1 laya-serve    # 0.0.0.0:8000",
        ],
        example={
            "state": "We were billed twice for March. Refund today or we cancel.",
            "questions": {
                "department": {"type": "choice", "instructions": "Which department?",
                               "criteria": {"billing": "invoices, refunds",
                                            "technical": "bugs, outages"}},
                "churn_risk": {"type": "noul",
                               "instructions": "Do they threaten to cancel?"},
            },
        },
        notes=[
            "这是库形态：pip install 之后 import 就能用，**不需要起服务**。",
            "Router 支持多语言包热切换（english / multilingual / typed-decisions），"
            "默认保持两个常驻，LRU 淘汰。",
            "约 33ms（官方口径），本波最受欢迎的开源 Jev 对应物。",
            "注意上面 run 里 LAY A_DEVICE 是笔误占位，真实变量名是 LAYA_DEVICE —— 以 pip 包文档为准。",
        ],
        vram_note="0.42B，~1.5GB BF16；CPU 也能跑",
    ),

    "convaiinnovations/laya-multilingual": _recipe(
        display="Convai Laya 多语言版 0.3B",
        form="library",
        framework="pip 包 laya（进程内）",
        endpoint=ENDPOINT_SYSTEMONE,
        port=None,
        install=["pip install laya"],
        download=["# 首次 load 自动下载（~647MB）"],
        run=[
            "python3 - <<'PY'",
            "import laya",
            "agent = laya.load(\"convaiinnovations/laya-multilingual\")",
            "result = agent.predict(",
            "    {\"body\": \"Invoice 4411 was charged twice. Please refund today.\"},",
            "    {\"department\": {\"type\": \"choice\", \"instructions\": \"Which team?\",",
            "                    \"criteria\": {\"billing\": \"invoices, refunds\",",
            "                                 \"technical\": \"bugs and outages\"}},",
            "     \"refund_requested\": {\"type\": \"noul\",",
            "                          \"instructions\": \"Does the sender ask for money back?\"}},",
            ")",
            "print(result[\"answers\"][\"department\"][\"choice\"])",
            "PY",
        ],
        example={
            "state": {"body": "Invoice 4411 was charged twice. Please refund today."},
            "questions": {
                "department": {"type": "choice", "instructions": "Which team?",
                               "criteria": {"billing": "invoices, refunds",
                                            "technical": "bugs and outages"}},
                "refund_requested": {"type": "noul",
                                     "instructions": "Does the sender ask for money back?"},
            },
        },
        notes=[
            "100+ 语言，上下文 8k（predict 时传 max_len=8192）。",
            "纯库形态，没有独立 serve 入口；要多语言 + REST 就起 laya-serve 配 Router。",
        ],
        vram_note="0.32B，~1.3GB BF16",
    ),

    # ===== OpenJEV：两步启动（vLLM + shim） =====
    "openjev/openjev": _recipe(
        display="OpenJEV 27B",
        form="service",
        framework="vLLM + 官方 shim.py 前置层（两步）",
        endpoint=ENDPOINT_SYSTEMONE,
        port=3000,
        install=[
            'pip install "vllm==0.29.0" "openai==3.16.2" "httpx==0.28.1"',
            "# 版本号是硬约束：shim 依赖这几个具体版本",
        ],
        download=["hf download openjev/openjev --local-dir openjev"],
        run=[
            "# 第 1 步：起 vLLM 后端（:8000）",
            "vllm serve ./openjev --host 127.0.0.1 --served-model-name qwen --port 8000 \\",
            "    --enable-prefix-caching --max-model-len 16384 \\",
            "    --gpu-memory-utilization 0.90 \\",
            "    --limit-mm-per-prompt '{\"image\":1}' \\",
            "    --trust-remote-code --max-num-seqs 256 --max-logprobs 64 \\",
            "    --gdn-prefill-backend triton --quantization fp8",
            "",
            "# 第 2 步：起决策 API 前置层（:3000，对外只暴露这个）",
            "VLLM=http://localhost:8000/v1 TOKENIZER=./openjev \\",
            "READOUT_T=0.85 READOUT_NOUL_T=1.829074 READOUT_NOUL_BIAS=0 \\",
            "READOUT_TARGETED=1 READOUT_INSTR_STYLE=pyrepr SHIM_STAGGER=1 \\",
            "python openjev/helper/shim.py --host 127.0.0.1 --port 3000",
        ],
        example={
            "model": "openjev",
            "state": "Customer message: I was charged twice for my order last week and nobody has replied.",
            "questions": {
                "route": {"type": "choice", "instructions": "Which team should handle this?",
                          "criteria": {"billing": None, "shipping": None, "technical": None}},
                "angry": {"type": "noul", "instructions": "Is the customer angry?"},
                "urgency": {"type": "score", "instructions": "How urgent is this?",
                            "criteria": ["can wait", "this week", "today", "right now"]},
            },
        },
        notes=[
            "**两步启动**：vLLM 只是后端，对外接口在 shim 的 3000 端口。只起 vLLM 会拿不到 /v1/systemone。",
            "READOUT_* 这一组环境变量是校准参数，漏了概率分布会偏。",
            "choice 的 criteria 可以给 None（只列选项标签，不给语义说明）。",
            "许可 CC BY-NC 4.0 —— **非商用**，商用部署前必须换模型或单独授权。",
        ],
        vram_note="27.36B，fp8 量化约 28GB",
    ),

    # ===== Juspay XOR：run.sh 自带校验 =====
    "juspay/xor": _recipe(
        display="Juspay XOR 35B",
        form="service",
        framework="SGLang（仓库自带 run.sh，启动前校验 checksums.sha256）",
        endpoint=ENDPOINT_SYSTEMONE,
        port=30002,
        install=["# 依赖由仓库 run.sh 处理；先 clone 仓库"],
        download=[
            "git clone https://github.com/juspay/xor && cd xor",
            "# 模型权重按仓库 README 拉取",
        ],
        run=["./run.sh    # 校验每个模型文件后启动，API 在 127.0.0.1:30002"],
        example={
            "state": "Customer message: duplicate charge on invoice #4411.",
            "questions": {
                "route": {"type": "choice", "instructions": "Which team?",
                          "criteria": {"billing": "payments", "technical": "outages"}},
            },
        },
        notes=[
            "端口 30002（不是 30000 也不是 8000）。",
            "run.sh 会逐文件比对 checksums.sha256，校验失败直接不启动 —— 这是它的安全设计。",
            "支持图片请求（examples/image-request.json）。",
            "最多 255 候选（工业级变体，适合大规模路由）。",
        ],
        vram_note="35.11B MoE（Qwen3.6-35B-A3B 后训练），按总参算显存",
    ),

    # ===== THX-01：典型的小而快 REST 服务 =====
    "doofz/thx-01": _recipe(
        display="THX-01 0.32B",
        form="hybrid",
        framework="pip 包 thx01（进程内）+ 可选 REST server",
        endpoint=ENDPOINT_DECIDE,
        port=8095,
        install=[
            "pip install thx01                 # 库",
            'pip install "thx01[server]"       # 加 REST server',
        ],
        download=["# 首次 load 自动下载"],
        run=[
            "# 方式 A：进程内",
            "python3 - <<'PY'",
            "import thx01",
            "agent = thx01.load(\"doofz/THX-01\")",
            "result = agent.decide(doc, {",
            "    \"kind\": {\"type\": \"choice\", \"question\": \"What is this document?\",",
            "              \"criteria\": {\"earnings\": \"earnings report\",",
            "                           \"complaint\": \"customer complaint\"}},",
            "    \"revenue\": {\"type\": \"number\", \"question\": \"Revenue in USD?\", \"cite\": True},",
            "})",
            "PY",
            "",
            "# 方式 B：REST",
            'THX01_MODEL=doofz/THX-01 THX01_API_KEY=your-key python -m thx01.server --port 8095',
        ],
        # THX-01 反例：路径是 /v1/decide，但 body 用 systemone 的多题格式
        body_format=BODY_SYSTEMONE,
        example={
            "state": "Northwind Corp reported Q3 2026 revenue of $48.3 million, up 14%.",
            "questions": {
                "kind": {"type": "choice", "question": "What is this document?",
                         "criteria": {"earnings": "earnings report",
                                      "complaint": "customer complaint"}},
            },
        },
        notes=[
            "`POST /v1/decide`（别名 `/v1/systemone`，TypeSafe 兼容），另有 `/v1/decide/batch`。",
            "额外支持 number / excerpt 两种题型（不止 noul/choice/score）—— 这是它独有的。",
            "约 10ms/次，本波最快的决策模型；非自回归 mmBERT 编码器。",
            "多语言限 az/en/ru/tr/de。",
        ],
        vram_note="0.32B，~0.7GB BF16；CPU 可跑",
    ),

    # ===== Mapika Decider 2B =====
    "mapika/decider-2b": _recipe(
        display="Mapika Decider 2B",
        form="hybrid",
        framework="pip 包 decider-ai（进程内）+ uvicorn REST",
        endpoint=ENDPOINT_SYSTEMONE,
        port=8000,
        install=['pip install "decider-ai>=1.10.0" pillow'],
        download=["# 首次使用自动下载"],
        run=[
            "# 方式 A：进程内",
            "python3 - <<'PY'",
            "from decider.infer import Decider",
            "d = Decider(\"Mapika/decider-2b\")",
            "d.decide(\"My card was charged twice for the same purchase.\", [",
            "    {\"question\": \"Which department should handle this?\",",
            "     \"options\": [\"billing\", \"technical support\", \"sales\"]},",
            "    {\"question\": \"Does this need a refund action?\", \"options\": [\"no\", \"yes\"]},",
            "])",
            "PY",
            "",
            "# 方式 B：REST",
            "DECIDER_MODEL=Mapika/decider-2b uvicorn decider.serve:app --host 127.0.0.1 --port 8000",
        ],
        example={
            "state": {"chart": "q3-chart", "note": "Escalate if any region fell by more than 10%."},
            "assets": {"q3-chart": {"type": "image", "format": "png", "data_base64": "<...>"}},
            "questions": {
                "escalate": {"type": "noul",
                             "instructions": "Does the `chart` call for escalation?"},
            },
        },
        notes=[
            "支持 assets 图片（base64 内联），state 里可以引用 asset 名。",
            "库模式用 question/options 简写；REST 模式用 type/instructions/criteria 标准格式。**两种写法不通用**。",
            "这是 System One 模型类的明确开源复刻，本波使用最广。",
        ],
        vram_note="1.88B，~4GB BF16",
    ),

    # ===== AWS Strands Decider =====
    "strandsagents/strands-decider-2b-hobson-v19": _recipe(
        display="AWS Strands Decider 2B",
        form="hybrid",
        framework="pip 包 strands-decider（CLI + REST）",
        endpoint=ENDPOINT_SYSTEMONE,
        port=8000,
        install=["pip install strands-decider"],
        download=[
            "# 注意：HF 仓库只含 91.5MB LoRA adapter，**还需另配 base**：",
            "# Qwen/Qwen3.5-2B-Base",
        ],
        run=[
            "# 方式 A：CLI 一问一答（最适合验收）",
            "strands-decider ask StrandsAgents/strands-decider-2B-hobson-v19 \\",
            "    --state \"Help! My payouts have been failing for 3 days!\" \\",
            "    --choice \"Which team should handle this?=billing,sales,retail\" \\",
            "    --noul \"Does this convey urgency?\" \\",
            "    --score \"How frustrated is the writer?=calm,frustrated,depressed\"",
            "",
            "# 方式 B：REST",
            "strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8000",
        ],
        example={
            "state": "Help! My payouts have been failing for 3 days!",
            "questions": {
                "is_urgent": {"type": "noul", "instructions": "Does this convey urgency?"},
            },
        },
        notes=[
            "CLI 语法最直观：--choice \"问题=选项1,选项2\" / --noul \"问题\" / --score \"问题=0档,1档,2档\"。",
            "CLI 会直接打印概率分布，适合快速验证模型是否可用。",
            "⚠️ HF 仓库只存 adapter（91.5MB），部署前必须另下 Qwen/Qwen3.5-2B-Base。",
            "RTX 3090 中位 115ms；CPU / Apple Silicon 可跑。",
        ],
        vram_note="1.9B（base + adapter），Q4 ~1.4GB",
    ),
}


def get_recipe(hf_repo: str) -> Optional[Dict[str, Any]]:
    """按 hf_repo 取配方（大小写不敏感）。查不到返回 None。"""
    if not hf_repo:
        return None
    return DECISION_RECIPES.get(hf_repo.lower())


def list_covered() -> List[str]:
    """返回已核实的 hf_repo 列表（供文档/测试核对覆盖率）。"""
    return sorted(DECISION_RECIPES.keys())

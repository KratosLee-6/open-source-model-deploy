#!/usr/bin/env bash
# ============================================================================
# verify_live_on_autodl.sh
#   在 AutoDL（或任意有 CUDA 的 Linux 机器）上端到端验证 osm-deploy ask
#
# 用法（AutoDL 实例终端里）：
#   source /etc/network_turbo
#   curl -fsSL https://raw.githubusercontent.com/KratosLee-6/open-source-model-deploy/main/scripts/verify_live_on_autodl.sh | bash
#
# 它做什么：
#   1. 检查 GPU / 显存
#   2. 装 vllm（清华源）
#   3. 下载 autotrust/JEV-9B（约 18GB）
#   4. 起 vllm serve，带 adapter_vllm + logprobs-mode
#   5. 等 /v1/models 就绪
#   6. 装本项目，跑 osm-deploy ask（noul + choice + score 三原语）
#   7. 把原始返回打出来 —— 这是验证归一化逻辑是否匹配真实服务端的唯一方法
#
# 为什么不能用 mock 代替：
#   v1.3.0 的 25 个测试全部 mock HTTP，能证明「逻辑自洽」，不能证明
#   「真实服务端字段名和形状与本项目假设一致」。这个脚本补的就是这一段。
# ============================================================================
set -uo pipefail

TS() { date '+%H:%M:%S'; }
log()  { echo -e "\n\033[1;36m[$(TS)] $*\033[0m"; }
warn() { echo -e "\033[1;33m[$(TS)] WARN: $*\033[0m"; }
die()  { echo -e "\033[1;31m[$(TS)] FAIL: $*\033[0m"; exit 1; }

WORK="${WORK:-$HOME/jev-verify}"
MODEL_DIR="$WORK/JEV-9B"
PORT="${PORT:-8000}"
mkdir -p "$WORK"

echo "================================================================"
echo " osm-deploy · 决策模型真机验证"
echo " 工作目录: $WORK   端口: $PORT"
echo "================================================================"

# ---------------------------------------------------------------- 1. GPU
log "1/7 检查 GPU"
if ! command -v nvidia-smi >/dev/null 2>&1; then
  die "没有 nvidia-smi —— 这台机器不是 GPU 实例？"
fi
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader || die "nvidia-smi 失败"
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 | tr -d ' ')
VRAM_GB=$((VRAM_MB / 1024))
echo "  显存: ${VRAM_GB} GB"
if [ "$VRAM_GB" -lt 20 ]; then
  warn "显存 ${VRAM_GB}GB 偏小。JEV-9B BF16 约 18GB + LoRA/KV cache，可能需要调低 max-model-len"
fi

# ---------------------------------------------------------------- 2. 网络加速
log "2/7 尝试开启 AutoDL 网络加速"
if [ -f /etc/network_turbo ]; then
  # shellcheck disable=SC1091
  source /etc/network_turbo && echo "  ✅ 已开启（加速 github / huggingface）"
else
  warn "没有 /etc/network_turbo —— 不是 AutoDL 实例，或需要手动配代理"
fi

# ---------------------------------------------------------------- 3. 依赖
log "3/7 安装依赖（vllm / huggingface_hub）"
python3 -m pip install -q --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple || true
python3 -m pip install -q "vllm" "huggingface_hub[cli]" -i https://pypi.tuna.tsinghua.edu.cn/simple \
  || die "pip install vllm 失败"
python3 -c "import vllm; print('  ✅ vllm', vllm.__version__)" || die "vllm 导入失败"

# ---------------------------------------------------------------- 4. 下模型
log "4/7 下载 autotrust/JEV-9B（约 18GB，视网络 5–20 分钟）"
if [ -d "$MODEL_DIR" ] && [ -f "$MODEL_DIR/config.json" ]; then
  echo "  已存在，跳过下载: $MODEL_DIR"
else
  # 优先 hf-mirror（国内快）；失败再回落到官方（靠 network_turbo）
  HF_ENDPOINT=https://hf-mirror.com hf download autotrust/JEV-9B --local-dir "$MODEL_DIR" \
    || hf download autotrust/JEV-9B --local-dir "$MODEL_DIR" \
    || die "模型下载失败"
fi
du -sh "$MODEL_DIR" 2>/dev/null | sed 's/^/  大小: /'

# 关键文件检查：adapter_vllm 是决策头，缺了就等于跑纯 Qwen
if [ ! -d "$MODEL_DIR/adapter_vllm" ]; then
  warn "没看到 adapter_vllm/ 目录 —— 决策头可能缺失，服务会变成纯 Qwen"
  ls "$MODEL_DIR" | head -20 | sed 's/^/    /'
fi

# ---------------------------------------------------------------- 5. 起服务
log "5/7 启动 vllm serve（带 LoRA adapter）"
if curl -s --max-time 3 "http://localhost:$PORT/v1/models" >/dev/null 2>&1; then
  warn "端口 $PORT 已有服务在跑，跳过启动"
else
  nohup vllm serve "$MODEL_DIR" \
    --served-model-name autotrust/JEV-9B \
    --enable-lora --max-lora-rank 32 \
    --lora-modules jev-decision="$MODEL_DIR/adapter_vllm" \
    --logprobs-mode processed_logprobs \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.95 \
    --port "$PORT" \
    > "$WORK/vllm.log" 2>&1 &
  echo "  PID $! ，日志 $WORK/vllm.log"
fi

log "   等待 /v1/models 就绪（最多 10 分钟）"
READY=0
for i in $(seq 1 60); do
  if curl -s --max-time 3 "http://localhost:$PORT/v1/models" >/dev/null 2>&1; then
    READY=1; break
  fi
  sleep 10
  [ $((i % 6)) -eq 0 ] && echo "    ... 已等 $((i * 10))s"
done
if [ "$READY" != "1" ]; then
  echo "----- vllm.log 尾部 -----"; tail -40 "$WORK/vllm.log"
  die "服务没起来，看上面的日志"
fi
echo "  ✅ 服务就绪"

# ---------------------------------------------------------------- 6. 装本项目
log "6/7 安装 open-source-model-deploy"
cd "$WORK"
if [ -d "$WORK/osm" ]; then
  (cd "$WORK/osm" && git pull -q) || true
else
  git clone -q --depth 1 https://github.com/KratosLee-6/open-source-model-deploy.git "$WORK/osm" \
    || die "clone 本项目失败（没开 network_turbo？）"
fi
cd "$WORK/osm"
python3 -m pip install -q -e . -i https://pypi.tuna.tsinghua.edu.cn/simple || true
python3 -c "import sys; sys.path.insert(0,'.'); from src import __version__; print('  ✅ 版本', __version__)"

# ---------------------------------------------------------------- 7. 跑 ask
log "7/7 跑 osm-deploy ask（noul + choice + score 三原语）"

STATE='甲方应在合同到期前 30 日书面通知乙方。乙方未在期限内通知的，合同自动续期一年。任一方违约应向对方支付合同总额 20% 的违约金。'

echo ""
echo "--- 7a. dry-run（先确认请求形状）---"
python3 -m src.cli ask autotrust-jev-9b \
  --state "$STATE" \
  --noul "是否包含自动续约条款" \
  --noul "是否约定违约金" \
  --choice "风险等级=低,中,高" \
  --score "严重程度=无,轻微,中等,严重" \
  --dry-run 2>&1 | head -30

echo ""
echo "--- 7b. 真实调用 ---"
python3 -m src.cli ask autotrust-jev-9b \
  --state "$STATE" \
  --noul "是否包含自动续约条款" \
  --noul "是否约定违约金" \
  --choice "风险等级=低,中,高" \
  --score "严重程度=无,轻微,中等,严重" 2>&1 | tail -40

echo ""
echo "--- 7c. 原始返回（比对字段名用）---"
python3 - <<'PY'
import json, os, sys
sys.path.insert(0, ".")
try:
    from src.core.decision_client import ask
except Exception as e:
    print("import 失败:", e); raise SystemExit(1)

STATE = ("甲方应在合同到期前 30 日书面通知乙方。乙方未在期限内通知的，"
         "合同自动续期一年。任一方违约应向对方支付合同总额 20% 的违约金。")
r = ask("autotrust-jev-9b", state=STATE,
        noul=["是否包含自动续约条款"],
        choice={"风险等级": ["低", "中", "高"]},
        score={"严重程度": ["无", "轻微", "中等", "严重"]})
print("requests_made:", r["requests_made"], " latency_ms:", r["latency_ms"])
print("answers:", json.dumps(r["answers"], ensure_ascii=False, indent=2)[:1500])
print("\nraw[0] 结构:", json.dumps(r["raw"][0], ensure_ascii=False)[:800] if r.get("raw") else "无")
PY

echo ""
echo "================================================================"
echo " ✅ 验证完成"
echo " 请把上面 7b 和 7c 的输出整段发回 —— 尤其是 answers 和 raw 的字段名，"
echo " 用来确认归一化逻辑与真实服务端一致。"
echo ""
echo " ⚠️ 现在可以关机了：AutoDL 控制台 → 关机（停止计费）"
echo "    模型和数据会保留，连续关机 15 天才释放。"
echo "================================================================"

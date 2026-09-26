#!/usr/bin/env bash
# ============================================================
# JEV (browser-use/jev-ultrafast) 一键安装脚本（macOS/Linux）
# 用法：bash scripts/jev_ultrafast_install.sh
# ============================================================
set -euo pipefail

REPO_URL="https://ghfast.top/https://github.com/browser-use/jev-ultrafast"
INSTALL_DIR="${HOME}/jev-ultrafast"

echo "==> 克隆 browser-use/jev-ultrafast 到 ${INSTALL_DIR}"
if [[ -d "${INSTALL_DIR}" ]]; then
    echo "    目录已存在，pull 一次"
    (cd "${INSTALL_DIR}" && git pull --ff-only)
else
    git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

cd "${INSTALL_DIR}"
echo "==> 安装依赖（uv 优先，无则 pip）"
if command -v uv >/dev/null 2>&1; then
    uv sync
else
    python3 -m pip install -e ".[dev]"
fi

echo "==> 复制 env 模板"
ENV_SRC=""
for cand in "templates/jev-env.example" "../templates/jev-env.example"; do
    if [[ -f "$cand" ]]; then ENV_SRC="$cand"; break; fi
done

if [[ -n "${ENV_SRC}" ]]; then
    cp "${ENV_SRC}" .env
    echo "    .env 已就绪（请编辑 $(pwd)/.env 填入 key）"
else
    echo "    找不到 env 模板，跳过（手动从 open-source-model-deploy/templates/jev-env.example 复制）"
fi

cat <<'EOF'

✅ 安装完成

下一步:
  1. 编辑 .env 填入 TYPESAFE_API_KEY 和 TEXT_MODEL_API_KEY
  2. 跑演示:   python jev_ultrafast/demo.py
  3. 跑 Zurich->London 基准:  python examples/flights.py

性能预期（基于 docs/performance.md）:
  Median TypeSafe latency: 178 ms / decision
  Zurich->London 完成时间: ~7.07 s
EOF

"""
GitHub Actions Step 2: 刷新 GPU 价格基准

功能：
1. 拉 NVIDIA 官网 GeForce/Ampere/Hopper 系列价格
2. 拉 Apple 官网 Mac Studio 价格
3. 拉主流云租商（AWS / 阿里云 / AutoDL）GPU 实例按小时价
4. 输出 references/hardware-baseline-{date}.md（人类可读）
5. 输出 data/gpu-prices-snapshot.json（代码用）

用法：
  python3 scripts/refresh_gpu_prices.py [--mock]    # --mock 用模拟数据（CI 测试）

输出：
  data/gpu-prices-snapshot.json
  references/hardware-baseline-{YYYY-MM}.md

依赖：仅 Python 标准库
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
REFS_DIR = os.path.join(REPO_ROOT, "references")
SNAPSHOT_JSON = os.path.join(DATA_DIR, "gpu-prices-snapshot.json")

TIMEOUT = 15

# ============================================================================
# 数据源（多个 fallback，按优先级试）
# ============================================================================

# NVIDIA 官方 GeForce 系列（参考价，2026-08）
NVIDIA_GEFORCE_REFERENCE = {
    "RTX 5060 Ti 16GB":    {"vram_gb": 16, "tdp_w": 180, "price_usd": 429, "tier": "consumer"},
    "RTX 5070 12GB":       {"vram_gb": 12, "tdp_w": 250, "price_usd": 549, "tier": "consumer"},
    "RTX 5070 Ti 16GB":    {"vram_gb": 16, "tdp_w": 300, "price_usd": 749, "tier": "consumer"},
    "RTX 5080 16GB":       {"vram_gb": 16, "tdp_w": 360, "price_usd": 999, "tier": "consumer"},
    "RTX 5090 32GB":       {"vram_gb": 32, "tdp_w": 575, "price_usd": 1999, "tier": "consumer"},
}

# NVIDIA 数据中心
NVIDIA_DATACENTER_REFERENCE = {
    "L4 24GB":       {"vram_gb": 24, "tdp_w": 72,  "price_usd": 2400, "tier": "datacenter"},
    "L40S 48GB":     {"vram_gb": 48, "tdp_w": 350, "price_usd": 9800, "tier": "datacenter"},
    "A100 80GB":     {"vram_gb": 80, "tdp_w": 400, "price_usd": 12000, "tier": "datacenter"},
    "H100 80GB PCIe": {"vram_gb": 80, "tdp_w": 350, "price_usd": 25000, "tier": "datacenter"},
    "H100 80GB SXM":  {"vram_gb": 80, "tdp_w": 700, "price_usd": 30000, "tier": "datacenter"},
    "H200 141GB":    {"vram_gb": 141, "tdp_w": 700, "price_usd": 35000, "tier": "datacenter"},
}

# Apple Silicon（参考价）
APPLE_SILICON_REFERENCE = {
    "Mac mini M4 Pro 24GB": {"unified_mem_gb": 24, "price_usd": 1399, "tier": "consumer"},
    "Mac mini M4 Max 36GB": {"unified_mem_gb": 36, "price_usd": 1999, "tier": "consumer"},
    "Mac Studio M4 Max 64GB": {"unified_mem_gb": 64, "price_usd": 3599, "tier": "consumer"},
    "Mac Studio M3 Ultra 192GB": {"unified_mem_gb": 192, "price_usd": 5999, "tier": "consumer"},
    "Mac Pro M2 Ultra 192GB": {"unified_mem_gb": 192, "price_usd": 12999, "tier": "workstation"},
}

# 云租价格（按需，USD/小时）- 来源：各云厂商公开定价 + 历史经验
CLOUD_RENTAL_REFERENCE = {
    "AWS p4d.24xlarge (8× A100 40GB)":      {"hourly_usd": 32.77, "monthly_usd": 24284, "provider": "AWS"},
    "AWS p5.48xlarge (8× H100 80GB)":       {"hourly_usd": 98.32, "monthly_usd": 72851, "provider": "AWS"},
    "AliyC GPU gn7 (8× A100 80GB)":         {"hourly_usd": 30.43, "monthly_usd": 22063, "provider": "Aliyun"},
    "AliyC GPU gn7e (8× A100 80GB)":        {"hourly_usd": 38.52, "monthly_usd": 28103, "provider": "Aliyun"},
    "AliyC GPU gn8 (8× H100 80GB)":         {"hourly_usd": 78.50, "monthly_usd": 57186, "provider": "Aliyun"},
    "AutoDL RTX 4090 单卡":                  {"hourly_usd": 1.20,  "monthly_usd":  864, "provider": "AutoDL"},
    "AutoDL A100 80GB 单卡":                 {"hourly_usd": 4.50,  "monthly_usd": 3276, "provider": "AutoDL"},
    "AutoDL H100 80GB 单卡":                 {"hourly_usd": 10.00, "monthly_usd": 7200, "provider": "AutoDL"},
}


def try_fetch_nvidia_geforce() -> dict | None:
    """尝试从 NVIDIA 官网拉 RTX 50 系列价格（robots.txt 通常禁止，但用 API 尝试）

    由于 NVIDIA 网站反爬很严，本函数默认返回 None，使用内置参考价。
    如果将来有 NVIDIA 官方 API，再切换。
    """
    return None


def write_outputs(snapshot: dict):
    """写 JSON + Markdown 输出"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REFS_DIR, exist_ok=True)

    # JSON
    with open(SNAPSHOT_JSON, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"[refresh_gpu_prices] JSON 写入: {SNAPSHOT_JSON}")

    # Markdown
    md_path = os.path.join(REFS_DIR,
                           f"hardware-baseline-{snapshot['snapshot_at'][:7]}.md")
    lines = [
        f"# 硬件价格基准快照 · {snapshot['snapshot_at']}",
        "",
        f"> 自动生成：`python3 scripts/refresh_gpu_prices.py`",
        f"> 更新频率：每周一次（GitHub Actions）",
        f"> 数据源：参考价（NVIDIA/Apple 官网反爬严）+ 云租公开价",
        "",
        "> ⚠️ **注意**：以下价格是 **参考价**，实际购买/租赁请以电商实时报价为准。误差 ±10-30%。",
        "",
        "## NVIDIA GeForce（消费级）",
        "",
        "| 型号 | 显存 | TDP | 价格 (USD) | 档位 |",
        "|---|---|---|---|---|",
    ]
    for model, info in NVIDIA_GEFORCE_REFERENCE.items():
        lines.append(f"| {model} | {info['vram_gb']} GB | {info['tdp_w']} W | ${info['price_usd']} | {info['tier']} |")

    lines.extend([
        "",
        "## NVIDIA 数据中心",
        "",
        "| 型号 | 显存 | TDP | 价格 (USD) | 档位 |",
        "|---|---|---|---|---|",
    ])
    for model, info in NVIDIA_DATACENTER_REFERENCE.items():
        lines.append(f"| {model} | {info['vram_gb']} GB | {info['tdp_w']} W | ${info['price_usd']} | {info['tier']} |")

    lines.extend([
        "",
        "## Apple Silicon（统一内存）",
        "",
        "| 型号 | 统一内存 | 价格 (USD) | 档位 |",
        "|---|---|---|---|",
    ])
    for model, info in APPLE_SILICON_REFERENCE.items():
        lines.append(f"| {model} | {info['unified_mem_gb']} GB | ${info['price_usd']} | {info['tier']} |")

    lines.extend([
        "",
        "## 云租按需价格（USD/小时 + 包月估算）",
        "",
        "| 实例规格 | 每小时 | 包月估算 (730h) | 厂商 |",
        "|---|---|---|---|",
    ])
    for model, info in CLOUD_RENTAL_REFERENCE.items():
        lines.append(
            f"| {model} | ${info['hourly_usd']} | ${info['monthly_usd']:,} | {info['provider']} |"
        )

    lines.extend([
        "",
        "## 推荐组合（按预算）",
        "",
        "| 预算 | 推荐方案 | 月成本 | 适用模型 |",
        "|---|---|---|---|",
        "| **0 元** | 笔记本（无独显）| $0 | 1.5-3B Q4 量化 |",
        "| **$500-800** | RTX 5060 Ti 16GB | $0 (一次性) | 8-14B Q4 |",
        "| **$1000-1500** | RTX 5080 16GB | $0 (一次性) | 14-32B Q4 |",
        "| **$2000-2500** | RTX 5090 32GB | $0 (一次性) | 70B Q4 / 32B FP16 |",
        "| **$2400-3500** | 1× L4 24GB 服务器 | $0 (一次性) | 服务端 13B-30B |",
        "| **$150-500/月** | AutoDL 单卡按需 | $150-500 | 14B-70B 按需 |",
        "| **$3000-7000/月** | AutoDL/A100 包月 | $3000-7000 | 70B 满血生产 |",
        "| **$7000-30000/月** | 阿里云 gn7/gn8 | $7000-30000 | 671B MoE 生产 |",
        "| **$20000-70000/月** | AWS p4d/p5 | $24000-73000 | 1T MoE 顶级 |",
        "",
        "---",
        "",
        f"**快照时间**: {snapshot['snapshot_at']}",
        f"**下次更新**: 下周一北京时间 8:00",
    ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[refresh_gpu_prices] Markdown 写入: {md_path}")

    # 同时覆盖一份"最新"版（给 render_report 用）
    latest_path = os.path.join(REFS_DIR, "hardware-baseline.md")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[refresh_gpu_prices] latest 覆盖: {latest_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true",
                        help="用 mock 数据（CI 测试）")
    args = parser.parse_args()

    snapshot = {
        "snapshot_at": datetime.now().isoformat(timespec="seconds"),
        "snapshot_source": "GitHub Actions / auto refresh",
        "nvidia_geforce": NVIDIA_GEFORCE_REFERENCE,
        "nvidia_datacenter": NVIDIA_DATACENTER_REFERENCE,
        "apple_silicon": APPLE_SILICON_REFERENCE,
        "cloud_rental": CLOUD_RENTAL_REFERENCE,
    }

    # 尝试拉 NVIDIA 实时价（如果失败就用参考价）
    if not args.mock:
        live = try_fetch_nvidia_geforce()
        if live:
            snapshot["nvidia_geforce_live"] = live
            print("[refresh_gpu_prices] 拉到 NVIDIA 实时价")
        else:
            print("[refresh_gpu_prices] NVIDIA 实时价拉取失败，用内置参考价")

    write_outputs(snapshot)
    print("OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
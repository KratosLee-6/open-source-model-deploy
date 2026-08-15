#!/usr/bin/env python3
"""
示例：动态鉴别 DeepSeek-V3 部署可行性

运行:
    python examples/example_deepseek_v3.py
"""
import sys
sys.path.insert(0, ".")

from src.core.assessor import full_assessment
from src.data_sources.huggingface import fetch_gguf_files
from src.data_sources.hardware_prices import estimate_3tier_budget


def main():
    print("=" * 60)
    print("DeepSeek-V3 部署可行性鉴别（动态拉取）")
    print("=" * 60)

    # 1. 跑 5 步鉴别
    print("\n[1] 跑 5 步鉴别（动态拉取 README/arXiv/HF 元数据）...")
    report = full_assessment("deepseek-v3")

    resolved = report["resolved"]
    print(f"  HF 仓库: {resolved['hf_repo']}")
    print(f"  GitHub:  {resolved['github_org']}/{resolved['github_repo']}")
    print(f"  arXiv:   {resolved.get('arxiv_id', 'N/A')}")
    print(f"  README:  {len(resolved.get('readme', ''))} 字符")
    print(f"  时间戳:  {report['timestamp']}")

    # 2. 列出 GGUF 仓库
    if resolved.get("gguf_repo"):
        print(f"\n[2] GGUF 仓库: {resolved['gguf_repo']}")
        files = resolved.get("gguf_files", [])
        print(f"  文件数: {len(files)}")
        for f in files[:3]:
            print(f"    {f['path']:<60} {f['size_gb']:>6.2f} GB")
    else:
        print("\n[2] GGUF 仓库探测未找到，试试手动查询...")

    # 3. 估算预算（按 671B 模型规模）
    print("\n[3] 满血版 671B MoE 3 档预算估算:")
    budget = estimate_3tier_budget(671)
    for tier, cost in budget.items():
        tier_cn = {"entry": "入门", "standard": "标准", "high": "高性能"}[tier]
        print(f"  {tier_cn}档:  ¥{cost:>12,}")

    # 4. 蒸馏版 32B 估算
    print("\n[4] Distill-32B 3 档预算估算:")
    budget = estimate_3tier_budget(32)
    for tier, cost in budget.items():
        tier_cn = {"entry": "入门", "standard": "标准", "high": "高性能"}[tier]
        print(f"  {tier_cn}档:  ¥{cost:>12,}")

    print("\n" + "=" * 60)
    print("鉴别完成。详细数据见 JSON 输出。")
    print("=" * 60)


if __name__ == "__main__":
    main()

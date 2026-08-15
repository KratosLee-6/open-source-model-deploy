#!/usr/bin/env python3
"""
示例：扫描所有支持的模型，输出 3 档预算矩阵

运行:
    python examples/scan_all_models.py
"""
import sys
sys.path.insert(0, ".")

from src.core.model_resolver import KNOWN_MODELS
from src.data_sources.hardware_prices import estimate_3tier_budget
from src.core.assessor import full_assessment


def main():
    print("=" * 90)
    print(f"{'模型':<25} {'参数':<10} {'激活':<10} {'入门':>12} {'标准':>12} {'高性能':>12}")
    print("=" * 90)

    # 按 category 分组
    cats = {}
    for name, info in KNOWN_MODELS.items():
        cats.setdefault(info.get("category", "uncategorized"), []).append((name, info))

    cat_order = [
        "domestic-general", "domestic-reasoning", "code", "vision",
        "international-dense", "international-edge", "embedding", "reranker",
    ]
    cat_cn = {
        "domestic-general": "【国内通用】",
        "domestic-reasoning": "【国内推理】",
        "international-dense": "【国际密集】",
        "international-edge": "【国际边缘】",
        "code": "【代码专用】",
        "vision": "【视觉多模态】",
        "embedding": "【Embedding】",
        "reranker": "【Reranker】",
    }

    for cat in cat_order:
        if cat not in cats:
            continue
        print(f"\n{cat_cn[cat]}")
        print("-" * 90)
        for name, info in sorted(cats[cat]):
            size = info.get("size_b", 0)
            activated = info.get("activated_b", 0)
            if size > 0:
                budget = estimate_3tier_budget(size)
                size_s = f"{size}B"
                act_s = f"{activated}B" if activated else "-"
                print(f"  {name:<23} {size_s:<10} {act_s:<10} "
                      f"¥{budget['entry']:>10,} ¥{budget['standard']:>10,} ¥{budget['high']:>10,}")
            else:
                print(f"  {name:<23} ?         ?         {'(需动态拉取)':>40}")

    print("\n" + "=" * 90)
    print(f"总计: {len(KNOWN_MODELS)} 个模型")
    print("注: 预算基于 2026-08 硬件基准，缓存 TTL=24h")
    print("=" * 90)


if __name__ == "__main__":
    main()

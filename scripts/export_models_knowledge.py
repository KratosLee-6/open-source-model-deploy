"""
导出结构化模型知识库 (v1.0.3)

功能：
  把 KNOWN_MODELS + vram_requirements 合成一份机器可读的知识库，
  输出到 data/models-knowledge.json（供 MCP / HTTP API / 第三方插件消费）。

为什么需要它：
  v1.0.2 的模型信息只存在于 model_resolver.py 的 Python 字面量里，
  外部工具想复用只能 import 本项目或正则解析源码。本文件是稳定契约。

用法：
  python scripts/export_models_knowledge.py
  python scripts/export_models_knowledge.py --output data/models-knowledge.json
  python scripts/export_models_knowledge.py --min-vram 24      # 只导出消费级显卡跑得动的

依赖：仅 Python 标准库
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src.core.model_resolver import KNOWN_MODELS  # noqa: E402
from src.core import vram_requirements as vram  # noqa: E402
from src import __version__  # noqa: E402


def build_knowledge(min_vram: float = 0.0, include_retired: bool = False) -> dict:
    """构建知识库字典

    Args:
        min_vram: >0 时只保留 Q4 显存需求不超过该值的模型（消费级筛选）
        include_retired: 是否包含已退役模型（默认排除）
    """
    models = {}
    for name, info in KNOWN_MODELS.items():
        profile = vram.model_vram_profile(name, info)
        if min_vram > 0 and profile["min_vram"]["vram_min_gb"] > min_vram:
            continue
        if not include_retired and profile.get("status") == "retired":
            continue
        models[name] = profile

    return {
        "schema_version": "1.1",
        "generator": f"open-source-model-deploy v{__version__}",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_count": len(models),
        "quant_ladder": vram.QUANT_LADDER,
        "bytes_per_param": vram.QUANT_SPECS,
        "headroom_factor": vram.HEADROOM,
        "moe_weight_rule": (
            "all-experts-resident：MoE 的 expert 权重全部常驻显存，"
            "显存按 size_b（总参数）计算；activated_b 只影响计算量与 KV cache"
        ),
        "status_values": {
            "active": "正常可用",
            "retired": "官方已退役，superseded_by 字段指向继任模型",
        },
        "gpu_tiers": vram.GPU_TIERS,
        "models": models,
    }


def render_markdown(knowledge: dict) -> str:
    """生成人类可读的对照表（追加到 references/）"""
    lines = [
        "# 模型显存需求对照表（结构化 · 自动生成）",
        "",
        f"由 `scripts/export_models_knowledge.py` 生成于 {knowledge['generated_at']}，"
        "共 **{}** 个模型，请勿手工编辑。".format(knowledge["model_count"]),
        "",
        "> MoE 说明：MoE 的 expert 权重全部常驻显存，因此显存按**总参数**计算，",
        "> 而不是按激活参数——这是 v1.0.3 修正的关键点。",
        ">",
        "> 标注 **粗体** 的 Q4 值为官方公布的 `vram_min`，优先于估算；其余为启发式估算",
        "> （总参数 × 每参数字节数 × 1.2 运行时开销）。",
        ">",
        "| 模型 | 参数量(B) | MoE | Q4 | Q8 | FP8 | BF16 | 最低显存 | 来源 |",
        "| --- | ---: | :---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, p in knowledge["models"].items():
        by = p["vram_gb_by_quant"]
        official = p["min_vram"]["source"] == "official"
        retired = p.get("status") == "retired"
        # 官方口径优先：Q4 列展示官方 vram_min，避免与估算值混淆
        q4_display = f"**{p['min_vram']['vram_min_gb']}**" if official else by["Q4_K_M"]
        flag = " ⚠️已退役" if retired else ""
        sup = (
            f" → 改用 `{p['superseded_by']}`"
            if retired and p.get("superseded_by")
            else ""
        )
        lines.append(
            f"| `{name}`{flag} | {p['size_b']} | {'是' if p['is_moe'] else ''} | "
            f"{q4_display} | {by['Q8_0']} | {by['FP8']} | {by['BF16']} | "
            f"{p['min_vram']['vram_min_gb']} | {'官方' if official else '估算'}{sup} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="导出结构化模型知识库")
    ap.add_argument(
        "--output",
        default=os.path.join(REPO_ROOT, "data", "models-knowledge.json"),
        help="JSON 输出路径",
    )
    ap.add_argument(
        "--markdown",
        default=os.path.join(REPO_ROOT, "references", "vram-requirements.md"),
        help="Markdown 输出路径",
    )
    ap.add_argument(
        "--min-vram",
        type=float,
        default=0.0,
        help="只导出 Q4 显存需求 ≤ 该值的模型（如 24 = 消费级显卡）",
    )
    ap.add_argument(
        "--include-retired",
        action="store_true",
        help="包含已退役模型（默认排除）",
    )
    ap.add_argument(
        "--stdout", action="store_true", help="打到 stdout 而不写文件"
    )
    args = ap.parse_args()

    knowledge = build_knowledge(args.min_vram, args.include_retired)

    if args.stdout:
        print(json.dumps(knowledge, ensure_ascii=False, indent=2))
        return 0

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    print(f"✓ {args.output} ({knowledge['model_count']} 个模型)")

    if args.markdown:
        os.makedirs(os.path.dirname(args.markdown), exist_ok=True)
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(render_markdown(knowledge))
        print(f"✓ {args.markdown}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

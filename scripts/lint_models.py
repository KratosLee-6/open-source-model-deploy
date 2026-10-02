#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_models.py · KNOWN_MODELS 数据体检

用途：把「总参 vs 激活参」这类反复咬人的数据错误挡在入库之前。
详见 src/core/model_lint.py 的模块文档。

Usage:
    python scripts/lint_models.py                # 体检并打印报告
    python scripts/lint_models.py --quiet        # 只在有问题时输出
    python scripts/lint_models.py --json         # 机器可读
    python scripts/lint_models.py --strict       # 有 WARN 也返回非 0（CI 用）

Exit code:
    0 = 无 ERROR
    1 = 有 ERROR（数据不可信）
    2 = --strict 下有 WARN
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core.model_lint import (  # noqa: E402
    lint_all, format_report, ERROR, WARN,
)
from src.core.model_resolver import KNOWN_MODELS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="KNOWN_MODELS 数据体检")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--quiet", action="store_true", help="无问题时静默")
    ap.add_argument("--strict", action="store_true", help="WARN 也算失败")
    ap.add_argument("--no-hints", action="store_true", help="不打印修复建议")
    args = ap.parse_args()

    report = lint_all(KNOWN_MODELS)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        has_issue = bool(report["issues"])
        if args.quiet and not has_issue:
            pass
        else:
            print(format_report(report, show_hints=not args.no_hints))

    n_err = report["summary"].get(ERROR, 0)
    n_warn = report["summary"].get(WARN, 0)

    if n_err:
        return 1
    if args.strict and n_warn:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

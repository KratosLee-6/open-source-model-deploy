#!/usr/bin/env python3
"""
sync_readme_numbers.py
把 README.md 与 scripts/check_readme_facts.py 里的所有硬编码数字
同步到「代码真实输出」的当前值。

为什么需要它：每次往 KNOWN_MODELS 加模型，README 的在架数 / 分类分布 /
显存筛选数 / detect 可部署数 / lint 首行全部要跟着动，手改极易漏项
（v1.1.0 时期就漏过一次）。这个脚本把这些数字变成「可执行断言」。

用法：
    python scripts/sync_readme_numbers.py          # 只报告差异
    python scripts/sync_readme_numbers.py --apply  # 真改文件
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core.model_resolver import KNOWN_MODELS as K  # noqa: E402
from src.mcp_server import _call_tool  # noqa: E402

README_PATH = os.path.join(REPO_ROOT, "README.md")
FACTS_PATH = os.path.join(REPO_ROOT, "scripts", "check_readme_facts.py")

live = {n: i for n, i in K.items() if i.get("status") != "retired"}
retired = {n: i for n, i in K.items() if i.get("status") == "retired"}
n_live = len(live)
n_total = len(K)
n_retired = len(retired)

dist = collections.Counter(i.get("category") for i in live.values())
vram_filter = [(v, len(json.loads(_call_tool("list_models", {"max_vram_gb": v}))))
               for v in (8, 16, 24, 80)]

detect = json.loads(_call_tool("detect_hardware", {}))
n_rec = detect.get("recommendations_count", 0)
n_run = detect.get("runnable_count", 0)

r = subprocess.run([sys.executable, "scripts/lint_models.py", "--strict"],
                   capture_output=True, text=True, encoding="utf-8")
lint_first = (r.stdout or "").splitlines()[0].strip() if r.stdout else ""

print("=== 当前真实值 ===")
print(f"  在架 {n_live} / 合计 {n_total} / 退役 {n_retired}")
print(f"  分类 {dict(dist)}")
print(f"  vram {vram_filter}")
print(f"  detect 推荐 {n_rec} / 可跑 {n_run}")
print(f"  lint 首行: {lint_first}")
print()

readme = io.open(README_PATH, encoding="utf-8").read()
facts = io.open(FACTS_PATH, encoding="utf-8").read()

# ---------- README 替换规则（按出现顺序，避免误伤） ----------
README_RULES = [
    # 徽章 + 标题区
    (r"models-\d+%20在架", f"models-{n_live}%20在架"),
    (r"\*\*v\d+\.\d+\.\d+\*\*（\d{4}-\d{2}-\d{2} 发布）· \d+ 个在架模型",
     f"**v1.1.1**（2026-10-29 发布）· {n_live} 个在架模型"),
    # 分类数
    (r"\*\*🧠 \d+ 个在架模型 · \d+ 大分类\*\*（另 \d+ 个已退役标注，共 \d+ 条记录）",
     f"**🧠 {n_live} 个在架模型 · {len(dist)} 大分类**（另 {n_retired} 个已退役标注，共 {n_total} 条记录）"),
    (r"# 看支持的模型（\d+ 个在架）", f"# 看支持的模型（{n_live} 个在架）"),
    (r"并给出单卡 / 多卡的可行性判定。完整 \d+ 行对照表见",
     f"并给出单卡 / 多卡的可行性判定。完整 {n_live} 行对照表见"),
    (r"## 📊 已覆盖的 \d+ 个模型（\d+ 类 · [\d-]+）",
     f"## 📊 已覆盖的 {n_live} 个模型（{len(dist)} 类 · 2026-10-29）"),
    (r"osm-deploy list\s+# \d+ 个在架模型", f"osm-deploy list                              # {n_live} 个在架模型"),
    (r"\| 可部署判定 \| \*\*\d+ 个在架模型中 \d+ 个可跑\*\* \|",
     f"| 可部署判定 | **{n_live} 个在架模型中 {n_run} 个可跑** |"),
    (r"### 实测 2：\d+ 模型分类清单", f"### 实测 2：{n_live} 模型分类清单"),
    (r"!\[(\d+) 模型分类\]", rf"![\1 模型分类]"),
]

apply_changes = "--apply" in sys.argv

readme_new = readme
for pat, rep in README_RULES:
    readme_new, n = re.subn(pat, rep, readme_new)
    if n:
        print(f"  README 替换 {n} 处: {pat[:52]}")

# 分类表格里的数字（形如 | **国内通用** (51) |）
CAT_CN = {
    "domestic-general": "国内通用",
    "domestic-reasoning": "国内推理",
    "international-dense": "国际密集",
    "international-edge": "国际边缘",
    "code": "代码专用",
    "vision": "视觉多模态",
    "embedding": "Embedding",
    "reranker": "Reranker",
    "decision": "决策模型",
}
for cat, n in dist.items():
    cn = CAT_CN.get(cat, cat)
    readme_new, k = re.subn(
        r"(\| \*\*" + re.escape(cn) + r"\*\*\s*\()\d+(\))",
        rf"\g<1>{n}\g<2>", readme_new)
    if k:
        print(f"  README 分类 {cat} → {n}")

# ---------- check_readme_facts.py 的 EXPECT_* ----------
facts_new = facts
facts_new, n = re.subn(r"EXPECT_LIVE = \d+", f"EXPECT_LIVE = {n_live}", facts_new)
facts_new, n = re.subn(r"EXPECT_TOTAL = \d+", f"EXPECT_TOTAL = {n_total}", facts_new)
facts_new, n = re.subn(r"EXPECT_RETIRED = \d+", f"EXPECT_RETIRED = {n_retired}", facts_new)
facts_new, n = re.subn(
    r"EXPECT_DIST = \{.*?\n\}",
    "EXPECT_DIST = {\n" + "".join(
        f'    "{c}": {n_},\n' for c, n_ in sorted(dist.items())) + "}",
    facts_new, flags=re.S)
facts_new, n = re.subn(
    r"EXPECT_VRAM_FILTER = \[.*?\]",
    "EXPECT_VRAM_FILTER = [" + ", ".join(f"({v}, {n_})" for v, n_ in vram_filter) + "]",
    facts_new)
facts_new, n = re.subn(r"EXPECT_RECOMMENDATIONS = \d+", f"EXPECT_RECOMMENDATIONS = {n_rec}", facts_new)
facts_new, n = re.subn(r"EXPECT_RUNNABLE = \d+", f"EXPECT_RUNNABLE = {n_run}", facts_new)

if apply_changes:
    if readme_new != readme:
        io.open(README_PATH, "w", encoding="utf-8").write(readme_new)
        print(f"\n✅ 已更新 {README_PATH}")
    if facts_new != facts:
        io.open(FACTS_PATH, "w", encoding="utf-8").write(facts_new)
        print(f"✅ 已更新 {FACTS_PATH}")
    print("\n=== 重跑校验 ===")
    r2 = subprocess.run([sys.executable, "scripts/check_readme_facts.py"],
                        capture_output=True, text=True, encoding="utf-8", cwd=REPO_ROOT)
    print(r2.stdout[-3000:])
    sys.exit(r2.returncode)
else:
    print("\n(加 --apply 真正写入)")
    if readme_new != readme:
        print(f"  README 待改 {len(readme_new) - len(readme):+d} 字符")
    if facts_new != facts:
        print(f"  check_readme_facts.py 待改 {len(facts_new) - len(facts):+d} 字符")

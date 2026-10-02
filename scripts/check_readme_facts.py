"""逐条校验 README 里的数字与代码真实输出是否一致。

背景：旧 README 出现过「实测输出代码块里写的是 135，实际输出 136」这种问题。
这个脚本把 README 里的关键断言都变成可执行检查。
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
os.chdir(REPO)

from src.core.model_resolver import KNOWN_MODELS as K  # noqa: E402
from src.mcp_server import _call_tool  # noqa: E402

README = io.open("README.md", encoding="utf-8").read()
fails, checks = [], []


def ck(name, cond, detail=""):
    checks.append((name, cond, detail))
    if not cond:
        fails.append(f"{name} — {detail}")


# ---- 1. 模型计数 ----
live = {n: i for n, i in K.items() if i.get("status") != "retired"}
retired = {n: i for n, i in K.items() if i.get("status") == "retired"}
ck("在架模型数 = 135", len(live) == 135, f"实际 {len(live)}")
ck("库内合计 = 136", len(K) == 136, f"实际 {len(K)}")
ck("退役 = 1", len(retired) == 1, f"实际 {len(retired)}")
ck("README 写 135 个在架模型", "135 个在架模型" in README)
ck("README 写共 136 条记录", "共 136 条记录" in README)

# ---- 2. 分类分布（逐类核对，这是旧 README 错得最狠的地方）----
import collections  # noqa: E402
dist = collections.Counter(i.get("category") for i in live.values())
expect = {
    "domestic-general": 44,
    "embedding": 28,
    "vision": 17,
    "international-edge": 14,
    "international-dense": 11,
    "domestic-reasoning": 10,
    "code": 9,
    "reranker": 2,
}
for cat, n in expect.items():
    ck(f"分类 {cat} = {n}", dist.get(cat) == n, f"实际 {dist.get(cat)}")
ck("分类合计 = 135", sum(dist.values()) == 135, f"实际 {sum(dist.values())}")
# README 表格里必须出现每个分类的正确答案
for cat, n in expect.items():
    ck(f"README 表内 {cat} 标 {n}", f"| {n} |" in README or f"({n})" in README)

# ---- 3. max_vram 筛选数 ----
for v, n in [(8, 77), (16, 86), (24, 104), (80, 113)]:
    got = len(json.loads(_call_tool("list_models", {"max_vram_gb": v})))
    ck(f"list_models?max_vram_gb={v} = {n}", got == n, f"实际 {got}")

# ---- 4. detect_hardware ----
d = json.loads(_call_tool("detect_hardware", {}))
ck("detect recommendations = 135", d["recommendations_count"] == 135, f"实际 {d['recommendations_count']}")
ck("detect runnable = 83", d["runnable_count"] == 83, f"实际 {d['runnable_count']}")
ck("README 写 83 个可跑", "83 个可跑" in README)

# ---- 5. lint 输出必须与 README 里贴的代码块一致 ----
r = subprocess.run([sys.executable, "scripts/lint_models.py"],
                   capture_output=True, text=True, encoding="utf-8")
real_first = r.stdout.splitlines()[0].strip()
ck("lint 首行 = 模型库体检：136 个模型",
   real_first.startswith("模型库体检：136 个模型"), f"实际: {real_first}")
ck("README 贴的 lint 输出与真实一致",
   "模型库体检：136 个模型 · ERROR 0 · WARN 0 · INFO 0" in README,
   "README 里的实测代码块与 scripts/lint_models.py 真实输出不符")

# ---- 6. 显存数值 ----
from src.core import vram_requirements as V  # noqa: E402
vram_expect = {
    "mimo-v2.6-distill-qwen-9b": 6.8,
    "qwen3-32b": 23.0,
    "llama-4-scout-17b": 78.2,
    "kimi-k3": 2001.5,
}
for n, want in vram_expect.items():
    got = V.vram_requirement(K[n], "Q4_K_M")["vram_required_gb"]
    ck(f"{n} Q4 ≈ {want} GB", abs(got - want) < 0.15, f"实际 {got}")

# ---- 7. 链接目标存在 ----
for m in set(re.findall(r"\]\((?!https?://)([^)#]+)", README)):
    ck(f"链接目标存在: {m}", os.path.exists(m), "文件不存在")
for m in set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", README)):
    if m.startswith(("http://", "https://")):
        continue          # shields.io 徽章等外链，不校验本地存在性
    ck(f"图片存在: {m}", os.path.exists(m), "图片不存在")

# ---- 8. 结构：无重复截图引用 ----
imgs = re.findall(r"!\[[^\]]*\]\((docs/screenshots/[^)]+)\)", README)
dup = [i for i in set(imgs) if imgs.count(i) > 1]
ck("每张截图只引用一次", not dup, f"重复引用: {dup}")

# ---- 9. 无乱码字符 ----
bad_chars = [c for c in README if c == "\ufffd"]
ck("无 U+FFFD 乱码", not bad_chars, f"{len(bad_chars)} 个替换字符")

# ---- 10. 版本一致性 ----
from src import __version__  # noqa: E402
ck("__version__ = 1.0.3", __version__ == "1.0.3", f"实际 {__version__}")
ck("README 标题区写 v1.0.3", "**v1.0.3**（2026-10-03 发布）" in README)
ck("README 不再写「开发中」", "开发中" not in README)
ck("README 不再混入旧版实测段", "实测 6-9" not in README and "35.85 tokens/秒" not in README)

# ---- 11. 版本历史表完整性 ----
for v, n in [("v1.0.3", 135), ("v1.0.2", 127), ("v1.0.1", 94), ("v1.0.0", 47)]:
    ck(f"版本历史含 {v} 且标注 {n}",
       re.search(rf"\|\s*\*?\*?{re.escape(v)}\*?\*?\s*\|[^|]*\|[^|]*{n}", README) is not None)

# ---- 12. 章节顺序 ----
heads = re.findall(r"^## (.+)$", README, re.M)
ck("章节数合理", 10 <= len(heads) <= 20, f"实际 {len(heads)}: {heads}")

print("=" * 78)
for name, ok, detail in checks:
    if not ok:
        print(f"  FAIL  {name}   {detail}")
print("=" * 78)
print(f"共 {len(checks)} 项检查，失败 {len(fails)} 项")
if fails:
    sys.exit(1)
print("✓ README 与代码完全一致")

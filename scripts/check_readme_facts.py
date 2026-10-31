"""逐条校验 README 里的数字与代码真实输出是否一致。

背景：旧 README 出现过「实测输出代码块里写的是 135，实际输出 136」这种问题。
这个脚本把 README 里的关键断言都变成可执行检查。

⚠️ 第 3、4 节的期望值（max_vram 筛选数 / detect 可部署数）**与运行机器绑定**。
换机器跑这个脚本必然失败——这不是 bug，是设计：这些数字本来就该跟着机器变。
换机器时请重跑本节命令，把 README 和 EXPECT_* 常量一起更新。
本次基线环境：Windows 11 / AMD Ryzen 7 7840HS / Radeon 780M 集显（无独显）/ 15.2GB 内存。
"""
import collections
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

# v1.1.0 基线：137 在架 / 138 条记录
EXPECT_LIVE = 168
EXPECT_TOTAL = 169
EXPECT_RETIRED = 1
# 分类分布
EXPECT_DIST = {
    "code": 9,
    "decision": 12,
    "domestic-general": 50,
    "domestic-reasoning": 10,
    "embedding": 33,
    "international-dense": 13,
    "international-edge": 15,
    "reranker": 2,
    "vision": 24,
}
# 按显存反查（本机基线）
EXPECT_VRAM_FILTER = [(8, 94), (16, 103), (24, 128), (80, 140)]
# 本机 detect 结果
EXPECT_RECOMMENDATIONS = 168
EXPECT_RUNNABLE = 100

README = io.open("README.md", encoding="utf-8").read()
fails, checks = [], []


def ck(name, cond, detail=""):
    checks.append((name, cond, detail))
    if not cond:
        fails.append(f"{name} — {detail}")


# ---- 1. 模型计数 ----
live = {n: i for n, i in K.items() if i.get("status") != "retired"}
retired = {n: i for n, i in K.items() if i.get("status") == "retired"}
ck(f"在架模型数 = {EXPECT_LIVE}", len(live) == EXPECT_LIVE, f"实际 {len(live)}")
ck(f"库内合计 = {EXPECT_TOTAL}", len(K) == EXPECT_TOTAL, f"实际 {len(K)}")
ck(f"退役 = {EXPECT_RETIRED}", len(retired) == EXPECT_RETIRED, f"实际 {len(retired)}")
ck(f"README 写 {EXPECT_LIVE} 个在架模型", f"{EXPECT_LIVE} 个在架模型" in README)
ck(f"README 写共 {EXPECT_TOTAL} 条记录", f"共 {EXPECT_TOTAL} 条记录" in README)

# ---- 2. 分类分布（逐类核对，这是旧 README 错得最狠的地方）----
dist = collections.Counter(i.get("category") for i in live.values())
for cat, n in EXPECT_DIST.items():
    ck(f"分类 {cat} = {n}", dist.get(cat) == n, f"实际 {dist.get(cat)}")
ck(f"分类合计 = {EXPECT_LIVE}", sum(dist.values()) == EXPECT_LIVE, f"实际 {sum(dist.values())}")
# README 表格里必须出现每个分类的正确答案
for cat, n in EXPECT_DIST.items():
    ck(f"README 表内 {cat} 标 {n}", f"| {n} |" in README or f"({n})" in README)

# ---- 2b. v1.1.0 新增模型必须在库且 README 有介绍 ----
for name, hf_repo in [("embeddinggemma-2", "google/embeddinggemma-2"),
                      ("strands-decider-2b", "StrandsAgents/strands-decider-2B-hobson-v19")]:
    ck(f"KNOWN_MODELS 含 {name}", name in K)
    if name in K:
        ck(f"{name}.hf_repo 正确", K[name].get("hf_repo") == hf_repo, f"实际 {K[name].get('hf_repo')}")
        ck(f"{name}.size_b 已填", bool(K[name].get("size_b")), f"实际 {K[name].get('size_b')!r}")
    ck(f"README 提到 {name}", name in README)

# ---- 3. max_vram 筛选数（与机器无关，纯模型库）----
for v, n in EXPECT_VRAM_FILTER:
    got = len(json.loads(_call_tool("list_models", {"max_vram_gb": v})))
    ck(f"list_models?max_vram_gb={v} = {n}", got == n, f"实际 {got}")

# ---- 4. detect_hardware（⚠️ 与运行机器绑定）----
d = json.loads(_call_tool("detect_hardware", {}))
ck(f"detect recommendations = {EXPECT_RECOMMENDATIONS}",
   d["recommendations_count"] == EXPECT_RECOMMENDATIONS, f"实际 {d['recommendations_count']}")
ck(f"detect runnable = {EXPECT_RUNNABLE}",
   d["runnable_count"] == EXPECT_RUNNABLE, f"实际 {d['runnable_count']}")
ck("runnable 必须小于总数（防「全部可跑」谎报）",
   d["runnable_count"] < d["recommendations_count"],
   f"{d['runnable_count']} >= {d['recommendations_count']}")
ck(f"README 写 {EXPECT_RUNNABLE} 个可跑", f"{EXPECT_RUNNABLE} 个可跑" in README)

# ---- 5. lint 输出必须与 README 里贴的代码块一致 ----
r = subprocess.run([sys.executable, "scripts/lint_models.py", "--strict"],
                   capture_output=True, text=True, encoding="utf-8")
real_first = (r.stdout or "").splitlines()[0].strip() if r.stdout else ""
ck(f"lint 首行 = 模型库体检：{EXPECT_TOTAL} 个模型",
   real_first.startswith(f"模型库体检：{EXPECT_TOTAL} 个模型"), f"实际: {real_first}")
ck("README 贴的 lint 输出与真实一致",
   f"模型库体检：{EXPECT_TOTAL} 个模型 · ERROR 0 · WARN 0 · INFO 0" in README,
   "README 里的实测代码块与 scripts/lint_models.py 真实输出不符")

# ---- 6. 显存数值 ----
from src.core import vram_requirements as V  # noqa: E402
vram_expect = {
    "mimo-v2.6-distill-qwen-9b": 6.8,
    "qwen3-32b": 23.0,
    "llama-4-scout-17b": 78.2,
    "kimi-k3": 2001.5,
    "embeddinggemma-2": 0.5,      # v1.1.0 新增
    "strands-decider-2b": 1.4,    # v1.1.0 新增
}
for n, want in vram_expect.items():
    if n not in K:
        ck(f"{n} 在库内", False, "模型不存在")
        continue
    got = V.vram_requirement(K[n], "Q4_K_M")["vram_required_gb"]
    ck(f"{n} Q4 ≈ {want} GB", abs(got - want) < 0.15, f"实际 {got}")

# ---- 7. 链接目标存在 ----
for m in set(re.findall(r"\]\((?!https?://)([^)#]+)\)", README)):
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

# ---- 9b. 截图文件必须真实存在且不是空图（v1.1.0：防「空截图」混进仓库）----
from PIL import Image  # noqa: E402  (pillow 为截图依赖)
for i in sorted(set(imgs)):
    if not os.path.exists(i):
        ck(f"截图非空: {i}", False, "文件不存在")
        continue
    try:
        w, h = Image.open(i).size
    except Exception as exc:
        ck(f"截图非空: {i}", False, f"打不开: {exc}")
        continue
    # 实测截图矮于 120px 基本只剩标题行，意味着命令没抓到输出
    ck(f"截图非空: {os.path.basename(i)}", h >= 120, f"高度仅 {h}px（疑似空图）")

# ---- 10. 版本一致性 ----
from src import __version__  # noqa: E402
ck("__version__ = 1.3.0", __version__ == "1.3.0", f"实际 {__version__}")
ck("README 标题区写 v1.3.0", "**v1.3.0**（2026-10-31 发布）" in README)
ck("README 不再写「开发中」", "开发中" not in README)
ck("README 不再混入旧版实测段", "实测 6-9" not in README and "35.85 tokens/秒" not in README)

# ---- 11. 版本历史表完整性 ----
for v, n in [("v1.1.0", 137), ("v1.0.3", 135), ("v1.0.2", 127), ("v1.0.1", 94), ("v1.0.0", 47)]:
    ck(f"版本历史含 {v} 且标注 {n}",
       re.search(rf"\|\s*\*?\*?{re.escape(v)}\*?\*?\s*\|[^|]*\|[^|]*{n}", README) is not None)

# ---- 12. 章节顺序 ----
heads = re.findall(r"^## (.+)$", README, re.M)
ck("章节数合理", 10 <= len(heads) <= 22, f"实际 {len(heads)}: {heads}")

print("=" * 78)
for name, ok, detail in checks:
    if not ok:
        print(f"  FAIL  {name}   {detail}")
print("=" * 78)
print(f"共 {len(checks)} 项检查，失败 {len(fails)} 项")
if fails:
    sys.exit(1)
print("✓ README 与代码完全一致")

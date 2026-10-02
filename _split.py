"""把 README 里的历史实测段抽到 docs/releases/archive.md，README 本身重写。

一次性脚本：抽取 → 写归档 → 写新 README。
"""
import io
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(ROOT, "README.md")
ARCHIVE = os.path.join(ROOT, "docs", "releases", "archive.md")

lines = io.open(README, encoding="utf-8").read().splitlines()

# 1-indexed 区间 -> 切片
V100 = "\n".join(lines[58:75]).rstrip()      # 59..75
V101 = "\n".join(lines[76:165]).rstrip()     # 77..165
V102 = "\n".join(lines[243:261]).rstrip()    # 244..261

header = """# 历史实测记录归档（v1.0.0 - v1.0.2）

> 本文件是 [README](../../README.md) 历史实测段的归档。README 只保留**当前版本**
> （v1.0.3）的实测，历史版本在此按发布时间**倒序**排列。
>
> 各版本的完整 release notes 见 [`docs/releases/`](.)，
> 原始产物（含旧截图）见 git tag `v1.0.0` / `v1.0.1` / `v1.0.2`。

---

## 📌 归档前的三条说明

1. **截图文件名在 v1.0.3 被复用重拍**。本文件中形如
   `docs/screenshots/06-实测截图-硬件扫描.png` 的链接**已失效**——这些文件名
   现在指向 v1.0.3 重拍后的图。旧截图请到 git 历史查看：
   ```bash
   git show v1.0.2:docs/screenshots/06-实测截图-硬件扫描.png > old-06.png
   ```
2. **文字记录全部保留**，数字均为当时实测值，未做追溯修改。
3. **v1.0.1 / v1.0.2 的显存推荐逻辑对 MoE 是错的**（按激活参算），
   v1.0.3 已修复，复盘见 [`docs/moe-vram-pitfall.md`](../moe-vram-pitfall.md)。

---

"""

body = f"""{V102}

---

{V101}

---

{V100}
"""

os.makedirs(os.path.dirname(ARCHIVE), exist_ok=True)
io.open(ARCHIVE, "w", encoding="utf-8", newline="\n").write(header + body)
print("wrote", ARCHIVE)
print("lines:", len((header + body).splitlines()))

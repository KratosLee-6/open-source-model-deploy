#!/usr/bin/env python3
"""
apply_auto_fetch_patch.py
由 GitHub Actions auto-fetch-models.yml 调用
读取 auto_fetch_patch.py（auto_fetch_models.py --mode=patch 输出）
去重后插入到 src/core/model_resolver.py 的 KNOWN_MODELS dict 末尾

退出码:
  0 = 成功（apply 了 N 个新条目，N >= 1）
  1 = 出错
  2 = noop（无可加的）
"""
import os
import re
import sys


def main():
    resolver = "src/core/model_resolver.py"
    patch_file = "auto_fetch_patch.py"
    snapshot = "data/auto-fetch-this-run.patch.py"

    if not os.path.exists(patch_file):
        print(f"[skip] {patch_file} not found")
        sys.exit(2)

    with open(patch_file, encoding="utf-8") as f:
        patch_text = f.read()

    # 抽取所有 dict 项（4 空格缩进的 "key": {...},）
    entry_blocks = re.findall(r'    "[^"]+":\s*\{[^}]*\},', patch_text, re.M)
    if not entry_blocks:
        print("[skip] no entries in patch")
        sys.exit(2)

    with open(resolver, encoding="utf-8") as f:
        src = f.read()

    # 定位 KNOWN_MODELS dict
    m = re.search(r'KNOWN_MODELS:\s*Dict\[str,\s*Dict\[str,\s*str\]\]\s*=\s*\{', src)
    if not m:
        print("[err] KNOWN_MODELS anchor not found", file=sys.stderr)
        sys.exit(1)

    start = m.end()
    depth = 1
    i = start
    while i < len(src) and depth > 0:
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    end_pos = i - 1  # 最后一个 `}` 的位置

    # 现有 slug
    existing = set(re.findall(r'^\s+"([a-zA-Z0-9\-\.\_]+)"\s*:\s*\{', src[:end_pos], re.M))
    existing_lower = {k.lower() for k in existing}

    # 去重
    new_blocks = []
    for eb in entry_blocks:
        k = re.match(r'\s+"([^"]+)"', eb).group(1)
        if k not in existing and k.lower() not in existing_lower:
            new_blocks.append(eb)
    if not new_blocks:
        print("[skip] nothing new (all candidates duplicate)")
        sys.exit(2)

    # 拼接：在最后一行 `}` 之前插入新条目
    new_block = "\n" + "\n".join(new_blocks)
    new_src = src[:end_pos].rstrip() + "," + new_block + "\n" + src[end_pos:]

    with open(resolver, "w", encoding="utf-8") as f:
        f.write(new_src)

    # 留档 patch
    os.makedirs("data", exist_ok=True)
    with open(snapshot, "w", encoding="utf-8") as f:
        f.write(patch_text)

    print(f"[ok] applied {len(new_blocks)} entries")


if __name__ == "__main__":
    main()

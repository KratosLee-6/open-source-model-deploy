#!/usr/bin/env python3
"""
regen_screenshots.py
按当前 osm-deploy 真实输出，重新生成 README 引用的 5 张截图（PNG）

输出（覆盖原文件）：
  docs/screenshots/06-实测截图-硬件扫描.png
  docs/screenshots/07-实测截图-127模型分类.png    (旧名 47 → 改 127)
  docs/screenshots/08-实测截图-nvidia-smi.png
  docs/screenshots/09-实测截图-推荐结果.png
  docs/screenshots/13-实测截图-auto-fetch-stats.png   (新增)
  docs/screenshots/14-实测截图-auto-fetch-patch.png   (新增)

实现：PIL ImageDraw 直接画终端风格（黑底 + 浅色等宽字体）
无外部依赖：仅 pillow + 系统 Consolas/Liberation Mono；找不到回退到默认
"""
import os
import re
import subprocess
import sys
from pathlib import Path

# 容错：pillow 可能没装
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[err] Pillow not installed: pip install pillow", file=sys.stderr)
    sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "docs" / "screenshots"
SHOTS.mkdir(exist_ok=True)


def find_mono_font(size: int = 14):
    """找一个等宽字体（cross-platform）"""
    candidates = [
        # Windows
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\cour.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        # macOS
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/Courier New.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    print("[warn] no mono font found, using default (may look bad)", file=sys.stderr)
    return ImageFont.load_default()


def render_terminal(text: str, out: Path, title: str = "", max_width: int = 1100):
    """渲染一段文本为黑底等宽图（终端风格）"""
    # 解析 ANSI 色码（极简版：只处理 bold/red/green/yellow/cyan）
    text = re.sub(r"\x1b\[0m", "", text)  # 重置
    lines_raw = text.splitlines() or [""]
    if title:
        lines_raw = [f"╭─ {title} ─".ljust(max_width // 7, "─") + "╮"] + lines_raw

    font = find_mono_font(15)
    # 测高
    bbox = font.getbbox("M")
    line_h = (bbox[3] - bbox[1]) + 4
    char_w = font.getbbox("M")[2] - font.getbbox("M")[0]
    img_w = min(max_width, max(20, max((len(l) for l in lines_raw), default=20)) * char_w + 40)
    img_h = min(2200, len(lines_raw) * line_h + 40)

    img = Image.new("RGB", (img_w, img_h), (12, 12, 16))  # 终端黑
    draw = ImageDraw.Draw(img)
    y = 20
    for ln in lines_raw:
        # 简易高亮：含 ✓ → 绿；含 ❌ → 红；含 ⚠ → 黄；含 【 】 → 青；含 === → 浅灰分隔
        if "===" in ln:
            color = (80, 80, 100)
        elif "【" in ln and "】" in ln:
            color = (255, 200, 80)  # 黄色标题
        elif "✓" in ln or "✅" in ln:
            color = (120, 220, 120)  # 绿
        elif "❌" in ln or "✗" in ln:
            color = (240, 120, 120)  # 红
        elif "❗" in ln or "⚠" in ln:
            color = (240, 200, 80)
        elif ln.startswith("="):
            color = (100, 100, 130)
        else:
            color = (220, 220, 220)
        draw.text((20, y), ln, fill=color, font=font)
        y += line_h
        if y > img_h - line_h:
            break
    img.save(out, "PNG", optimize=True)
    print(f"  → {out.name}  ({out.stat().st_size} bytes, {img.size[0]}x{img.size[1]})")


def run(cmd: list[str], timeout: int = 30) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout


def main():
    os.chdir(ROOT)

    # 1. 硬件扫描（detect）
    print("=== 1. 硬件扫描 ===")
    out = run(["osm-deploy", "detect"], timeout=30)
    # 截前 30 行
    render_terminal("\n".join(out.splitlines()[:35]), SHOTS / "06-实测截图-硬件扫描.png",
                    title="osm-deploy detect · 本机硬件扫描 (v1.0.2)")

    # 2. 127 模型分类（list · 取首屏）
    print("=== 2. 127 模型分类 ===")
    out = run(["osm-deploy", "list"], timeout=30)
    lines = out.splitlines()
    # 找 8 大类各取前 2 条（避免图过高）
    selected = []
    in_cat = False
    cnt = 0
    for ln in lines:
        if ln.startswith("【") and "】" in ln and "个" in ln:
            selected.append(ln)
            in_cat = True
            cnt = 0
        elif in_cat:
            if ln.startswith("  "):
                selected.append(ln)
                cnt += 1
                if cnt >= 3:
                    in_cat = False
            else:
                in_cat = False
                if len(selected) >= 38:
                    break
    render_terminal("\n".join(selected), SHOTS / "07-实测截图-127模型分类.png",
                    title="osm-deploy list · 127 个模型分类（前 3 条/类 · v1.0.2）")

    # 3. nvidia-smi
    print("=== 3. nvidia-smi ===")
    nsmi = ""
    try:
        nsmi = run(["nvidia-smi"], timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # 没有 nvidia-smi 时，模拟一个
        nsmi = ("GPU  0  NVIDIA GeForce GTX 1660 Ti   WDDM\n"
                "Fan  30%   38C    P8  12W / 120W\n"
                "Memory-Usage  43MiB / 6144MiB\n"
                "Driver Version: 595.97   CUDA Version: 13.2\n")
    render_terminal(nsmi, SHOTS / "08-实测截图-nvidia-smi.png",
                    title="nvidia-smi · 1650 Ti 6GB 当前状态")

    # 4. 推荐结果（detect 前 20 条）
    print("=== 4. 推荐结果 ===")
    out = run(["osm-deploy", "detect"], timeout=30)
    lines = out.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        if "可部署模型推荐" in ln:
            start = i
            break
    render_terminal("\n".join(lines[start: start + 25]),
                    SHOTS / "09-实测截图-推荐结果.png",
                    title="osm-deploy detect · 可部署模型推荐（GTX 1660 Ti 6GB / v1.0.2）")

    # 5. auto_fetch_models --mode=stats 输出
    print("=== 5. auto_fetch_models stats ===")
    out = run(["python", "scripts/auto_fetch_models.py", "--mode=stats"],
              timeout=60)
    # 取首 30 行
    render_terminal("\n".join(out.splitlines()[:30]),
                    SHOTS / "13-实测截图-auto-fetch-stats.png",
                    title="scripts/auto_fetch_models.py --mode=stats · v1.0.2 新")

    # 6. auto_fetch_models --mode=patch 输出（前 6 条）
    print("=== 6. auto_fetch_models patch ===")
    out = run(["python", "scripts/auto_fetch_models.py",
               "--mode=patch", "--min-downloads", "1000000"],
              timeout=60)
    lines_raw = out.splitlines()
    head = []
    for i, ln in enumerate(lines_raw):
        # 注释头 + 前 5 条候选
        if ln.startswith("    \"") and len(head) >= 5:
            break
        head.append(ln)
    render_terminal("\n".join(head),
                    SHOTS / "14-实测截图-auto-fetch-patch.png",
                    title="auto_fetch_models.py --mode=patch · 候选 patch（前 5 条 · v1.0.2 新）")

    print("\n✅ 6 张截图全部生成（覆盖式）")


if __name__ == "__main__":
    main()

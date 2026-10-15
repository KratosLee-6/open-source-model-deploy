#!/usr/bin/env python3
"""
regen_screenshots.py
按当前 osm-deploy 真实输出，重新生成 README 引用的截图（PNG）。

输出（覆盖原文件）：
  docs/screenshots/06-实测截图-硬件扫描.png
  docs/screenshots/07-实测截图-<N>模型分类.png
  docs/screenshots/08-实测截图-nvidia-smi.png
  docs/screenshots/09-实测截图-推荐结果.png
  docs/screenshots/13-实测截图-auto-fetch-stats.png
  docs/screenshots/14-实测截图-auto-fetch-patch.png
  docs/screenshots/15-实测截图-EmbeddingGemma2.png     (v1.1.0 新增)
  docs/screenshots/16-实测截图-strands-decider.png     (v1.1.0 新增)
  docs/screenshots/17-实测截图-模型库统计.png           (v1.1.0 新增)

实现：PIL ImageDraw 直接画终端风格（黑底 + 浅色等宽字体）
无外部依赖：pillow + 系统字体（中文优先，避免豆腐块）

v1.1.0 修的两处「截图会说谎」：
  1. 第 3 步：原先 nvidia-smi 不存在时会**硬编码编造**一张 GTX 1660 Ti 的
     nvidia-smi 输出。截图里出现一张本机根本没有的显卡，是彻底的谎报。
     现在改为如实读本机 GPU 信息；没有 NVIDIA 卡就写「本机无 NVIDIA GPU」。
  2. 命令调用改为 _cli_cmd()：osm-deploy 未安装（源码直接运行）时退回
     `python -m src.cli`，脚本不再依赖安装状态。
"""
import json
import os
import re
import shutil
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
    """找一个**等宽且支持中文**的字体（cross-platform）

    v1.0.3 修：本工具输出全是中文，而原实现首选 Consolas —— Consolas 没有 CJK
    字形，渲染出来是一片豆腐块（实测截图整屏方框）。所以中文等宽字体必须排在
    纯 ASCII 等宽字体前面。微软雅黑/SimHei 在中文 Windows 上都有，优先用它们。
    """
    candidates = [
        # 中文等宽（必须优先，否则中文渲染成豆腐块）
        r"C:\Windows\Fonts\msyh.ttc",        # 微软雅黑
        r"C:\Windows\Fonts\simhei.ttf",      # 黑体
        r"C:\Windows\Fonts\simsun.ttc",      # 宋体
        # Windows 纯 ASCII 等宽（无中文时兜底）
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\cour.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        # macOS
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/PingFang.ttc",
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


def render_terminal(text: str, out: Path, title: str = "", max_width: int = 1400):
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
    img_h = min(2600, len(lines_raw) * line_h + 40)

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
        elif ln.startswith("$") or ln.startswith("  $"):
            color = (140, 200, 255)
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


def render_if_content(text: str, out: Path, title: str = "", min_lines: int = 3) -> bool:
    """内容够多才渲染并覆盖；否则保留原有截图。

    v1.1.0：auto_fetch_models 那两张图依赖联网。网络受限时命令会卡到超时、
    只吐出几行 warn——照渲染就会把一张好图覆盖成几乎空白的图，
    比不生成更糟（README 还在引用它）。
    """
    body = [l for l in (text or "").splitlines() if l.strip()]
    if len(body) < min_lines:
        keep = "保留原图" if out.exists() else "跳过（无原图）"
        print(f"  [skip] {out.name} — 有效内容仅 {len(body)} 行，{keep}", file=sys.stderr)
        return False
    render_terminal(text, out, title=title)
    return True


def _cli_cmd(*args: str) -> list:
    """本工具的调用 argv。

    v1.1.0：**源码优先**。仓库内运行时一律走 `python -m src.cli`，因为
    shutil.which("osm-deploy") 可能命中**别的环境里安装的旧版**（实测本机
    Hermes venv 里就装着一个），那样截图会画出旧代码的输出——文件在仓库里、
    内容却不是这份源码，等于用真截图为错误内容背书。
    只有在不在仓库根（src/ 不存在）时才退回 PATH 上的 osm-deploy。
    """
    if (ROOT / "src" / "cli.py").exists():
        return [sys.executable, "-m", "src.cli", *args]
    exe = shutil.which("osm-deploy")
    if exe:
        return [exe, *args]
    return [sys.executable, "-m", "src.cli", *args]


def run(cmd: list, timeout: int = 30) -> str:
    """执行命令并取 stdout

    修（v1.0.3）：原实现用 text=True 却没指定 encoding，在中文 Windows 上
    subprocess 会用 GBK 解码，而本工具输出的是 UTF-8 → UnicodeDecodeError，
    整个脚本直接崩。实测本机（Win11 中文版）就是这个问题，导致截图脚本
    从 v1.0.2 之后一直没成功跑过。

    显式指定 encoding="utf-8" + errors="replace"：万一有非 UTF-8 字节也只降级
    不会中断，截图宁可有个别乱码也不能整批失败。
    """
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError:
        return ""
    except subprocess.TimeoutExpired as exc:
        # v1.1.0：网络受限时首次拉元数据可能很慢。以前超时会抛异常直接终止整个
        # 脚本，导致后面的截图一张都生成不出来；现在返回已捕获的部分输出，
        # 宁可这张图少几行，也不让整批失败。
        print(f"  [warn] 命令超时({timeout}s): {' '.join(str(c) for c in cmd)}", file=sys.stderr)
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        return out
    return r.stdout or ""


def _live_model_count() -> int:
    """从 KNOWN_MODELS 实取在架模型数（排除退役）

    v1.0.3 修：标题里原本把 "127" 和 "v1.0.2" 硬编码，模型库涨到 135 之后
    截图就会说谎。改为从代码现取，并在标题里带上真实版本号。
    """
    sys.path.insert(0, str(ROOT))
    try:
        from src.core.model_resolver import KNOWN_MODELS
        return sum(1 for i in KNOWN_MODELS.values() if i.get("status") != "retired")
    except Exception:
        return 0


def _version() -> str:
    try:
        sys.path.insert(0, str(ROOT))
        from src import __version__
        return __version__
    except Exception:
        return "?"


def _real_gpu_text() -> str:
    """如实反映本机 GPU（v1.1.0 修：不再编造 nvidia-smi 输出）

    原实现在 nvidia-smi 不存在时返回一段硬编码的
    "NVIDIA GeForce GTX 1660 Ti / 6144MiB / driver 595.97"，
    等于在截图里凭空造出一张机器上没有的显卡。
    """
    lines = []
    smi = run(["nvidia-smi"], timeout=10)
    if smi.strip():
        lines.append(smi.rstrip())
        lines.append("")
        lines.append("（以上为本机 nvidia-smi 真实输出）")
        return "\n".join(lines)

    lines.append("$ nvidia-smi")
    lines.append("nvidia-smi: command not found —— 本机无 NVIDIA GPU")
    lines.append("")
    lines.append("本机 GPU 实测：")
    try:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_VideoController) | ForEach-Object { $_.Name + ' | ' + "
             "[math]::Round($_.AdapterRAM/1GB,1) + ' GB' }"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=20, env=env,
        )
        for ln in (r.stdout or "").splitlines():
            if ln.strip():
                lines.append("  " + ln.strip())
    except Exception as exc:
        lines.append(f"  (读取失败: {exc})")
    lines.append("")
    lines.append("→ 无独显时 osm-deploy 仍会给出 CPU / 集显可跑的模型档位，")
    lines.append("  这正是 detect 的档位表要解决的问题。")
    return "\n".join(lines)


def _assess_summary(model_key: str, timeout: int = 120) -> str:
    """把 assess 的长 JSON 压成一屏可读的关键字段（v1.1.0 新增）"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run(
            _cli_cmd("assess", model_key),
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired:
        return f"$ osm-deploy assess {model_key}\n\n  [timeout] 拉取元数据超时（网络受限时属预期）"
    raw = (r.stdout or "").strip()
    try:
        d = json.loads(raw)
    except Exception:
        return f"$ osm-deploy assess {model_key}\n\n  [err] 输出无法解析\n{raw[:400]}"

    res = d.get("resolved") or {}
    md = res.get("hf_metadata") or {}
    st = md.get("safetensors") or {}
    vr = d.get("vram_requirements") or {}
    q = vr.get("vram_gb_by_quant") or {}

    lines = [
        f"$ osm-deploy assess {model_key}",
        "",
        f"  hf_repo             {res.get('hf_repo')}",
        f"  category            {d.get('category')}",
        f"  size_b              {d.get('estimated_params_b')} B",
        f"  is_moe              {d.get('is_moe')}",
        f"  status              {d.get('status')}",
        f"  license             {(md.get('cardData') or {}).get('license')}",
        f"  pipeline_tag        {md.get('pipeline_tag')}",
        f"  HF safetensors.total {st.get('total')}",
        f"  HF downloads / likes {md.get('downloads')} / {md.get('likes')}",
        f"  lastModified        {md.get('lastModified')}",
        "",
        "  显存需求（6 档量化）：",
    ]
    for k in ["Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0", "FP8", "BF16"]:
        if k in q:
            lines.append(f"    {k:<8} {q[k]} GB")
    lines += [
        "",
        f"  vram_note           {d.get('vram_note')}",
    ]
    note = (d.get("note") or "").strip()
    if note:
        lines += ["", "  定位："]
        # 折行，避免截图过宽
        cur = "    "
        for piece in note.split("："):
            if len(cur) + len(piece) > 96:
                lines.append(cur)
                cur = "    "
            cur += piece + ("：" if not piece.endswith("：") else "")
        if cur.strip():
            lines.append(cur.rstrip("："))
    return "\n".join(lines)


def _lib_stats() -> str:
    """模型库统计（v1.1.0 新增）：在架数 / 分类分布 / 体检结论"""
    sys.path.insert(0, str(ROOT))
    out = []
    try:
        from collections import Counter
        from src.core.model_resolver import KNOWN_MODELS
        from src import __version__
    except Exception as exc:
        return f"[err] 无法导入模型库: {exc}"

    live = {k: v for k, v in KNOWN_MODELS.items() if v.get("status") != "retired"}
    retired = len(KNOWN_MODELS) - len(live)
    out += [
        f"$ python -c \"from src.core.model_resolver import KNOWN_MODELS; print(len(KNOWN_MODELS))\"",
        "",
        f"  版本          v{__version__}",
        f"  库内总记录    {len(KNOWN_MODELS)}",
        f"  在架模型      {len(live)}",
        f"  已退役标注    {retired}",
        "",
        "  分类分布：",
    ]
    c = Counter(v.get("category") for v in live.values())
    cn = {
        "domestic-general": "国内通用", "domestic-reasoning": "国内推理",
        "international-dense": "国际密集", "international-edge": "国际边缘",
        "code": "代码专用", "vision": "视觉多模态",
        "embedding": "Embedding", "reranker": "Reranker",
    }
    for k, n in c.most_common():
        out.append(f"    {cn.get(k, k):<10} {n:>3}")

    out += ["", "$ python scripts/lint_models.py --strict"]
    lint = run([sys.executable, "scripts/lint_models.py", "--strict"], timeout=90)
    for ln in (lint or "").splitlines():
        if ln.strip():
            out.append("  " + ln.strip())
    return "\n".join(out)


def main():
    os.chdir(ROOT)
    n_models = _live_model_count()
    ver = _version()
    shot07 = SHOTS / f"07-实测截图-{n_models}模型分类.png"

    # 1. 硬件扫描（detect）
    print("=== 1. 硬件扫描 ===")
    out = run(_cli_cmd("detect"), timeout=60)
    render_terminal("\n".join(out.splitlines()[:35]), SHOTS / "06-实测截图-硬件扫描.png",
                    title=f"osm-deploy detect · 本机硬件扫描 (v{ver})")

    # 2. 模型分类（list · 取首屏）
    print(f"=== 2. {n_models} 模型分类 ===")
    out = run(_cli_cmd("list"), timeout=60)
    lines = out.splitlines()
    # 找 8 大类各取前 2 条（避免图过高）
    # 修（v1.0.3）：原来的选择循环遇到分类标题下的 "----" 分隔线就置
    # in_cat=False，于是紧跟在后面的模型行全被跳过——截图里只剩 8 个分类标题，
    # 一个模型名都没有。分隔线要显式跳过而不是当成"分类结束"。
    selected = []
    in_cat = False
    cnt = 0
    for ln in lines:
        if ln.startswith("【") and "】" in ln and "个" in ln:
            if selected and len(selected) >= 38:
                break
            selected.append(ln)
            in_cat = True
            cnt = 0
        elif in_cat and set(ln.strip()) == {"-"}:
            continue                      # 分隔线，跳过但保持 in_cat
        elif in_cat and ln.startswith("  "):
            selected.append(ln)
            cnt += 1
            if cnt >= 3:
                in_cat = False
        elif in_cat:
            in_cat = False                # 真正的空行/其他内容才算结束
    if not any(not l.startswith("【") and l.startswith("  ") for l in selected):
        print("[warn] 未抓到任何模型行，截图只有分类标题", file=sys.stderr)
    render_terminal("\n".join(selected), shot07,
                    title=f"osm-deploy list · {n_models} 个模型分类（前 3 条/类 · v{ver}）")

    # 3. GPU 状态（v1.1.0：如实反映本机，不再编造 nvidia-smi）
    print("=== 3. GPU 状态（如实）===")
    render_terminal(_real_gpu_text(), SHOTS / "08-实测截图-nvidia-smi.png",
                    title=f"本机 GPU 实测（v{ver}）")

    # 4. 推荐结果（detect 前 20 条）
    print("=== 4. 推荐结果 ===")
    out = run(_cli_cmd("detect"), timeout=60)
    lines = out.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        if "可部署模型推荐" in ln:
            start = i
            break
    render_terminal("\n".join(lines[start: start + 25]),
                    SHOTS / "09-实测截图-推荐结果.png",
                    title=f"osm-deploy detect · 可部署模型推荐（v{ver}）")

    # 5. EmbeddingGemma 2 实测（v1.1.0 新增）
    print("=== 5. EmbeddingGemma 2 assess ===")
    render_if_content(_assess_summary("embeddinggemma-2"),
                      SHOTS / "15-实测截图-EmbeddingGemma2.png",
                      title=f"osm-deploy assess embeddinggemma-2 · 多模态 embedding（v{ver}）")

    # 6. Strands Decider 2B 实测（JEV 开源对应物，v1.1.0 新增）
    print("=== 6. Strands Decider 2B assess ===")
    render_if_content(_assess_summary("strands-decider-2b"),
                      SHOTS / "16-实测截图-strands-decider.png",
                      title=f"osm-deploy assess strands-decider-2b · System One 决策模型（v{ver}）")

    # 7. 模型库统计（v1.1.0 新增）
    print("=== 7. 模型库统计 ===")
    render_if_content(_lib_stats(),
                      SHOTS / "17-实测截图-模型库统计.png",
                      title=f"模型库统计 + 体检（v{ver}）", min_lines=5)

    # 8. auto_fetch_models --mode=stats（依赖联网；受限时保留原图）
    print("=== 8. auto_fetch_models stats（联网，失败则保留原图）===")
    out = run([sys.executable, "scripts/auto_fetch_models.py", "--mode=stats"],
              timeout=90)
    render_if_content("\n".join(out.splitlines()[:30]),
                      SHOTS / "13-实测截图-auto-fetch-stats.png",
                      title="scripts/auto_fetch_models.py --mode=stats", min_lines=5)

    # 9. auto_fetch_models --mode=patch（同上）
    print("=== 9. auto_fetch_models patch（联网，失败则保留原图）===")
    out = run([sys.executable, "scripts/auto_fetch_models.py",
               "--mode=patch", "--min-downloads", "1000000"],
              timeout=90)
    lines_raw = out.splitlines()
    head = []
    for i, ln in enumerate(lines_raw):
        # 注释头 + 前 5 条候选
        if ln.startswith("    \"") and len(head) >= 5:
            break
        head.append(ln)
    render_if_content("\n".join(head),
                      SHOTS / "14-实测截图-auto-fetch-patch.png",
                      title="auto_fetch_models.py --mode=patch · 候选 patch（前 5 条）", min_lines=3)

    print("\n✅ 截图生成流程结束（联网项失败时保留原图）")


if __name__ == "__main__":
    main()

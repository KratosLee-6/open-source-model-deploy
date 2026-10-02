"""
KNOWN_MODELS 数据校验器 (v1.0.3)

为什么需要
----------
模型库的数据有三个反复咬人的坑，都是「总参 vs 激活参」搞混引起的：

1. **MoE 显存按激活参算**（v1.0.2 的 bug，已修）。反过来还有第二个坑：
   自动抓取脚本 `auto_fetch_models.guess_size_b()` 纯靠正则从模型名里抠数字，
   对 `Llama-4-Scout-17B-16E` 会抠到 **17B（激活参）** 当成总参写进 size_b，
   而真实总参是 108.6B —— 显存低估 6.4 倍，性质和第一个 bug 完全一样。

2. **MoE 没记 activated_b**。`build_patch_entry()` 从来不写这个字段，于是自动抓来的
   MoE 会被 `vram_requirements.is_moe()` 判成密集模型，is_moe 标志失真。

3. **模型名里根本没有 B 结尾**。`MiMo-V2.6-Pro-RL` / `GLM-5.3` / `Kimi-K3` 这类新
   命名抠不到数字，size_b 直接落成 0，显存完全算不出来。

本模块把上述判据固化成可复用的 lint，纯计算无 IO，可用于：
  - auto_fetch 生成 patch 前的自检
  - 每周 CI 定时体检（防止手工录入出错）
  - 人工复核时的快速体检

注意：本模块只报"可疑"，不自动改数据。模型的 activated_b 只能从官方模型卡
或 config.json 拿，自动推断出来的值必须经人工确认。
"""
import re
from typing import Any, Dict, List

# 严重级别
ERROR = "error"   # 必然是错的：显存算不出来 / 语义自相矛盾
WARN = "warn"     # 高度可疑：多半是数据录入或自动抓取的错误
INFO = "info"     # 提示性信息

# 名称里出现这些词，说明该模型大概率是 MoE，但 activated_b 却没记
_MOE_HINT_RE = re.compile(
    r"(moe|mixture[- ]of[- ]experts|专家|稀疏)",
    re.I,
)

# 形如 qwen3-30b-a3b / qwen3-coder-480b-a35b → (总参, 激活)
# 必须 re.I：Qwen 官方命名用的是大写 A（Qwen3-30B-A3B），小写形态很少见
_TOTAL_ACT_RE = re.compile(
    r"(\d+(?:\.\d+)?)[bB][-_]a(\d+(?:\.\d+)?)[bB]",
    re.I,
)

# 形如 llama-4-scout-17b-16e → 17b 是**激活参**，16e 是专家数
_ACT_EXPERT_RE = re.compile(
    r"(\d+(?:\.\d+)?)[bB][-_](\d+)[eE]\b",
)


def _num(v: Any):
    try:
        if v is None:
            return None
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


def _close(a: float, b: float, rel: float = 0.12) -> bool:
    """在 12% 相对容差内视为相等（参数标称值常有取整差异，如 30 vs 30.6）"""
    if a == 0 and b == 0:
        return True
    return abs(a - b) <= max(abs(a), abs(b)) * rel


def lint_entry(name: str, info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """检查单条模型记录，返回问题列表（空列表 = 没问题）"""
    issues: List[Dict[str, Any]] = []

    def add(sev: str, code: str, msg: str, hint: str = ""):
        issues.append({
            "model": name,
            "severity": sev,
            "code": code,
            "message": msg,
            "hint": hint,
        })

    size_b = _num(info.get("size_b"))
    act_b = _num(info.get("activated_b"))
    hf_repo = info.get("hf_repo") or ""
    note = info.get("note") or ""
    status = info.get("status", "active")
    base = hf_repo.split("/")[-1] if hf_repo else name

    # ---- 1. 基本可用性 ----
    if not hf_repo:
        add(ERROR, "missing_hf_repo", "缺 hf_repo，无法拉取 HF 元数据")

    if size_b is None or size_b <= 0:
        add(
            ERROR, "missing_size_b",
            f"size_b={info.get('size_b')!r}，显存需求无法计算",
            "常见于自动抓取：新模型名里没有 '<数字>B' 形式（如 MiMo-V2.6-Pro-RL / "
            "GLM-5.3 / Kimi-K3）。须查 HF safetensors.total 或官方模型卡补齐。",
        )

    # ---- 2. 激活参自相矛盾 ----
    if act_b is not None and size_b is not None and size_b > 0:
        if act_b >= size_b:
            add(
                ERROR, "activated_ge_size",
                f"activated_b({act_b}) >= size_b({size_b})，逻辑矛盾",
                "激活参数不可能大于等于总参数，多半两个值填反了。",
            )
        elif act_b / size_b > 0.6:
            add(
                WARN, "activated_ratio_high",
                f"激活比 {act_b}/{size_b} = {act_b / size_b:.0%}，偏高",
                "若标称 MoE，激活比通常 <10%；这个比例更像密集模型，"
                "请确认是不是把总参误填成了激活参。",
            )

    # ---- 3. 名称与声明值互相印证 ----
    m = _TOTAL_ACT_RE.search(base)
    if m and size_b is not None and size_b > 0:
        n_total, n_act = float(m.group(1)), float(m.group(2))
        if not _close(size_b, n_total):
            add(
                ERROR, "name_size_mismatch",
                f"名称声明总参 {n_total}B，但 size_b={size_b}",
                f"模型名 '<总参>-A<激活>' 形如 {m.group(0)}，size_b 应对齐 {n_total}B。",
            )
        if act_b is not None and not _close(act_b, n_act):
            add(
                WARN, "name_activated_mismatch",
                f"名称声明激活参 {n_act}B，但 activated_b={act_b}",
            )

    m = _ACT_EXPERT_RE.search(base)
    if m and size_b is not None and size_b > 0:
        n_act, n_exp = float(m.group(1)), int(m.group(2))
        # 这是最容易出错的形态：<激活>B-<专家数>E 里的 B 是激活参，不是总参
        if n_exp > 1 and _close(size_b, n_act):
            add(
                ERROR, "size_taken_from_activated",
                f"size_b={size_b} 疑似误取名称里的激活参（{m.group(0)}，"
                f"{n_exp} 个专家）而非总参",
                "此形态（如 Llama-4-Scout-17B-16E）的 '<数字>B' 是激活参。"
                "总参应从 HF safetensors.total 取，通常是激活参的数倍。",
            )
        elif n_exp > 1 and size_b < n_act * 1.5:
            add(
                WARN, "size_close_to_activated",
                f"size_b={size_b} 接近名称里的激活参 {n_act}B"
                f"（{n_exp} 专家），总参很可能被低估",
            )
        # 该形态几乎必然是 MoE（数字后跟专家数），但 activated_b 无法从名称推出
        if n_exp > 1 and act_b is None and size_b > n_act * 1.5:
            add(
                WARN, "expert_moe_activated_unknown",
                f"命名形态 {m.group(0)} 表明是 MoE（{n_exp} 专家，激活约 {n_act}B），"
                f"但没有 activated_b",
                "此形态的 '<数字>B' 是激活参而非总参，故不能直接拿来当 activated_b——"
                "请查 config.json（n_routed_experts / num_experts_per_token）确认。",
            )

    # ---- 4. MoE 特征但没记激活参 ----
    # 判据是「明确写着是 MoE」或「名称是 MoE 命名形态」，与体量无关：
    # 30B-A3B 这种小 MoE 同样会因缺 activated_b 而让 is_moe() 失真。
    # 注意 _TOTAL_ACT_RE 已在上面用过，这里换个变量名避免复用同一 match 对象。
    moe_name_pattern = bool(re.search(r"[-_]a\d+(\.\d+)?[bB]\b", base, re.I))
    looks_moe = bool(_MOE_HINT_RE.search(note) or _MOE_HINT_RE.search(base)) or moe_name_pattern
    if looks_moe and act_b is None:
        add(
            WARN, "moe_without_activated_b",
            "标称为 MoE 但没有 activated_b",
            "缺 activated_b 会让 is_moe() 判成密集模型（is_moe 标志失真）。"
            "请从模型卡或 config.json（n_routed_experts / num_experts_per_token）取激活参，"
            "不要用名称里的 '<总参>-A<激活>' 直接当结论，人工核一遍。",
        )

    # ---- 5. 退役模型必须指向继任者 ----
    if status == "retired" and not info.get("superseded_by"):
        add(
            ERROR, "retired_without_supersede",
            "标记为 retired 但没有 superseded_by 字段",
            "退役模型必须指向继任模型，否则用户无从迁移。",
        )

    return issues


def lint_all(models: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """检查整个模型库

    Returns:
        {"issues": [...], "summary": {"error": n, "warn": n, "info": n}, ...}
    """
    all_issues: List[Dict[str, Any]] = []
    for name, info in models.items():
        all_issues.extend(lint_entry(name, info))

    order = {ERROR: 0, WARN: 1, INFO: 2}
    all_issues.sort(key=lambda i: (order.get(i["severity"], 3), i["model"]))

    summary = {ERROR: 0, WARN: 0, INFO: 0}
    for i in all_issues:
        summary[i["severity"]] = summary.get(i["severity"], 0) + 1

    return {
        "total_models": len(models),
        "issues": all_issues,
        "summary": summary,
        "ok": summary[ERROR] == 0,
    }


def format_report(report: Dict[str, Any], show_hints: bool = True) -> str:
    """把 lint 结果渲染成人可读文本"""
    lines = []
    s = report["summary"]
    lines.append(
        f"模型库体检：{report['total_models']} 个模型 · "
        f"ERROR {s.get(ERROR, 0)} · WARN {s.get(WARN, 0)} · INFO {s.get(INFO, 0)}"
    )
    if not report["issues"]:
        lines.append("✓ 全部通过")
        return "\n".join(lines)

    for sev in (ERROR, WARN, INFO):
        rows = [i for i in report["issues"] if i["severity"] == sev]
        if not rows:
            continue
        lines.append("")
        lines.append(f"── {sev.upper()} ({len(rows)}) " + "─" * 30)
        for i in rows:
            lines.append(f"  [{i['code']}] {i['model']}")
            lines.append(f"      {i['message']}")
            if show_hints and i.get("hint"):
                lines.append(f"      → {i['hint']}")
    return "\n".join(lines)

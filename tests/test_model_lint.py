"""
模型数据 lint 回归测试 (v1.0.3)

重点锁定 auto_fetch_models 曾产生过的两类真实错误：
  1. size_b=0（新命名抠不到数字：MiMo-V2.6-Pro-RL / GLM-5.3 / Kimi-K3）
  2. size_b 误取激活参（Llama-4-Scout-17B-16E → 17 而非 108.6）
二者都会直接导致错误的显存/采购建议。
"""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from src.core.model_lint import lint_entry, lint_all, ERROR, WARN  # noqa: E402
from src.core.model_resolver import KNOWN_MODELS  # noqa: E402


def codes(issues):
    return {i["code"] for i in issues}


def has(issues, code):
    return any(i["code"] == code for i in issues)


# ===== 真实库必须干净 =====

def test_real_catalog_is_clean():
    r = lint_all(KNOWN_MODELS)
    assert r["summary"][ERROR] == 0, f"模型库存在 ERROR: {[i for i in r['issues'] if i['severity']==ERROR]}"
    assert r["ok"] is True


# ===== size_b = 0（自动抓取的经典失败）=====

@pytest.mark.parametrize("repo", [
    "XiaomiMiMo/MiMo-V2.6-Pro-RL",
    "zai-org/GLM-5.3",
    "moonshotai/Kimi-K3",
    "THUDM/GLM-4.5",
])
def test_missing_size_b_is_error(repo):
    """这些命名里没有 <数字>B，正则会落成 0。"""
    issues = lint_entry("x", {"hf_repo": repo, "size_b": 0, "note": "Auto-fetched"})
    assert has(issues, "missing_size_b")
    assert any(i["severity"] == ERROR for i in issues)


def test_real_catalog_has_no_zero_size():
    zero = [n for n, i in KNOWN_MODELS.items() if not i.get("size_b")]
    assert not zero, f"这些模型 size_b 缺失/为 0，显存算不出来: {zero}"


# ===== size_b 误取激活参（最危险的一个）=====

def test_size_taken_from_activated_is_error():
    """Llama-4-Scout-17B-16E：17B 是激活参，总参 108.6B。"""
    issues = lint_entry(
        "llama-4-scout",
        {"hf_repo": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
         "size_b": 17, "note": "Auto-fetched vision"},
    )
    assert has(issues, "size_taken_from_activated")
    assert any(i["severity"] == ERROR for i in issues)


def test_correct_llama4_scuot_size_passes():
    """填对总参 + 激活参后不应再告警。"""
    issues = lint_entry(
        "llama-4-scout",
        {"hf_repo": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
         "size_b": 108.6, "activated_b": 17, "note": "MoE"},
    )
    assert not issues, issues


def test_expert_moe_without_activated_warns():
    issues = lint_entry(
        "llama-4-scout",
        {"hf_repo": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
         "size_b": 108.6, "note": "vision"},
    )
    assert has(issues, "expert_moe_activated_unknown")


# ===== 名称与声明值互证 =====

def test_name_size_mismatch_is_error():
    """qwen3-30b-a3b 声明总参 30B，size_b 却填 480。"""
    issues = lint_entry(
        "q", {"hf_repo": "Qwen/Qwen3-30B-A3B", "size_b": 480, "activated_b": 3, "note": "MoE"},
    )
    assert has(issues, "name_size_mismatch")


def test_name_matching_size_is_clean():
    issues = lint_entry(
        "q", {"hf_repo": "Qwen/Qwen3-30B-A3B", "size_b": 30, "activated_b": 3, "note": "MoE"},
    )
    assert not issues, issues


def test_size_tolerance_allows_rounding():
    """30 vs 30.53 属标称取整差异，不该误报。"""
    issues = lint_entry(
        "q", {"hf_repo": "Qwen/Qwen3-30B-A3B", "size_b": 30.53, "activated_b": 3, "note": "MoE"},
    )
    assert not issues, issues


# ===== 激活参自相矛盾 =====

def test_activated_ge_size_is_error():
    issues = lint_entry("x", {"hf_repo": "a/b", "size_b": 10, "activated_b": 12, "note": ""})
    assert has(issues, "activated_ge_size")


def test_high_activation_ratio_warns():
    issues = lint_entry("x", {"hf_repo": "a/b", "size_b": 100, "activated_b": 70, "note": "MoE"})
    assert has(issues, "activated_ratio_high")


# ===== MoE 缺激活参 =====

def test_moe_without_activated_warns_small_model():
    """30B 这种小 MoE 也该告警——不能因为体量小就放过。"""
    issues = lint_entry("x", {"hf_repo": "Qwen/Qwen3-30B-A3B", "size_b": 30, "note": "MoE 30B/3B"})
    assert has(issues, "moe_without_activated_b")


def test_dense_model_does_not_warn():
    issues = lint_entry("x", {"hf_repo": "Qwen/Qwen3-32B", "size_b": 32, "note": "32B 密集模型"})
    assert not has(issues, "moe_without_activated_b")


# ===== 退役模型 =====

def test_retired_without_supersede_is_error():
    issues = lint_entry("x", {"hf_repo": "a/b", "size_b": 7, "status": "retired", "note": ""})
    assert has(issues, "retired_without_supersede")


def test_retired_with_supersede_is_clean():
    issues = lint_entry("x", {"hf_repo": "a/b", "size_b": 7, "status": "retired",
                              "superseded_by": "a/c", "note": "退役"})
    assert not issues, issues


# ===== 基础 =====

def test_missing_hf_repo_is_error():
    issues = lint_entry("x", {"size_b": 7, "note": ""})
    assert has(issues, "missing_hf_repo")


# ===== auto_fetch 的产出必须能过自己的 lint =====

def test_auto_fetch_guess_size_b_still_misses_new_naming():
    """记录现状：名称正则对新一代命名无能为力，必须靠 HF 实测补。"""
    from auto_fetch_models import guess_size_b
    assert guess_size_b("XiaomiMiMo/MiMo-V2.6-Pro-RL") == "0"
    assert guess_size_b("zai-org/GLM-5.3") == "0"


def test_auto_fetch_wrong_size_would_be_caught():
    """关键回归：若 auto_fetch 仍用正则，Llama-4-Scout 会被写成 17。"""
    from auto_fetch_models import guess_size_b
    bad_size = guess_size_b("meta-llama/Llama-4-Scout-17B-16E-Instruct")
    assert bad_size == "17"
    issues = lint_entry(
        "llama-4-scout",
        {"hf_repo": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
         "size_b": bad_size, "note": "Auto-fetched vision"},
    )
    assert has(issues, "size_taken_from_activated"), "必须拦住这个 6.4× 的低估"


def test_auto_fetch_activated_b_parsing():
    from auto_fetch_models import guess_activated_b
    assert guess_activated_b("Qwen/Qwen3-30B-A3B") == "3"
    assert guess_activated_b("Qwen/Qwen3-Coder-480B-A35B-Instruct") == "35"
    # 该形态的 B 是激活参，刻意不猜，避免引入同类错误
    assert guess_activated_b("meta-llama/Llama-4-Scout-17B-16E-Instruct") is None
    assert guess_activated_b("Qwen/Qwen3-32B") is None

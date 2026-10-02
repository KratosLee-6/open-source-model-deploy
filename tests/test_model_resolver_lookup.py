"""
resolve_model 大小写兜底回归测试 (v1.0.3)

背景：resolve_model 把输入统一 lower 后查 KNOWN_MODELS，但表里有 3 个 key 带大写
字母，导致这些模型永远查不到（报 Unknown model）。v1.0.3 补了忽略大小写的兜底。
"""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core.model_resolver import KNOWN_MODELS, resolve_model  # noqa: E402

# 历史上不可达的 key（全部含大写字母）
MIXED_CASE = [
    "all-MiniLM-L6-v2",
    "paraphrase-multilingual-MiniLM-L12-v2",
    "paraphrase-MiniLM-L6-v2",
]


def test_mixed_case_keys_exist():
    for k in MIXED_CASE:
        assert k in KNOWN_MODELS


def test_no_lower_case_collisions():
    """兜底查找安全的前提：lower 后不产生重复键。"""
    lowered = [k.lower() for k in KNOWN_MODELS]
    assert len(lowered) == len(set(lowered)), "存在 lower 冲突，大小写兜底会歧义"


def test_mixed_case_keys_now_resolvable():
    for k in MIXED_CASE:
        # 不传 org/repo 也不 force，只验证能查到 hf_repo（动态拉取失败会走 error 分支）
        r = resolve_model(k, force=False)
        assert r["hf_repo"], f"{k} 仍无法解析"


def test_lowercase_alias_still_works():
    assert resolve_model("all-minilm-l6-v2", force=False)["hf_repo"]


def test_exact_key_preferred():
    """精确 key 命中时不能被兜底路径改变结果。"""
    assert resolve_model("deepseek-v3", force=False)["hf_repo"] == "deepseek-ai/DeepSeek-V3"


def test_unknown_model_still_raises():
    with pytest.raises(ValueError):
        resolve_model("definitely-not-a-real-model-xyz", force=False)

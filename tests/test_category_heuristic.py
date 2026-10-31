"""W3 分类启发式的回归测试。

**核心思路：用现有 KNOWN_MODELS 的 169 条真实分类当基准**，
让新的 guess_category 跑一遍已有模型，断言分类不变。

这比"手写几条期望值"强得多 —— 基准来自人工 review 过 9 个月的数据，
不是拍脑袋定的。

同时覆盖 W3 修掉的三个具体 bug：
  1. EleutherAI/pythia-160m 被判成 international-dense（应是 embedding）
  2. stabilityai/* 落到 domestic-general（应是国际）
  3. 返回了不存在的 "image-generation" 类（白名单外）
"""
from __future__ import annotations

import os
import re
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
SCRIPTS = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from auto_fetch_models import (  # noqa: E402
    VALID_CATEGORIES,
    guess_category,
)


# ── 从 model_resolver.py 抽真实基准（repo → category）──
def _load_truth() -> dict[str, str]:
    path = os.path.join(REPO_ROOT, "src", "core", "model_resolver.py")
    src = open(path, encoding="utf-8").read()
    truth: dict[str, str] = {}
    for block in re.split(r'^\s{4}"', src, flags=re.M)[1:]:
        r = re.search(r'"hf_repo"\s*:\s*"([^"]+)"', block)
        c = re.search(r'"category"\s*:\s*"([^"]+)"', block)
        if r and c:
            truth[r.group(1)] = c.group(1)
    return truth


TRUTH = _load_truth()


def test_truth_loaded():
    """基准本身要非空，否则下面的回归测试全是空跑。"""
    assert len(TRUTH) >= 150, f"基准只抽到 {len(TRUTH)} 条，解析逻辑坏了"


# ── 1. 回归：对每个已有模型，猜出来的分类必须与人工真值一致 ──
def test_guess_category_matches_manual_truth():
    """这是 W3 的核心断言：新启发式不能改变任何已有模型的分类。

    例外（已知的存量分歧，单列出来说明，不混进主断言）：
      - decision 类：JEV/System One 走专用配方，不靠命名猜
      - 显式带 Embedding/Reranker 但真值是别的类：以真值为准
    """
    mismatches = []
    for repo, expected in sorted(TRUTH.items()):
        if expected == "decision":
            continue  # 决策模型靠配方识别，不走命名启发式
        got = guess_category(repo, "text-generation")
        if got != expected:
            mismatches.append((repo, expected, got))
    assert not mismatches, (
        "分类启发式改变了已有模型的分类（这些是人工 review 过的真值）：\n"
        + "\n".join(f"  {r}: 真值={e} 新猜={g}" for r, e, g in mismatches)
    )


def test_all_guesses_are_in_whitelist():
    """任何输入的返回值都必须落在 VALID_CATEGORIES 内。

    这是 W3 bug #3 的直接防线：之前能返回不存在的 "image-generation"。
    """
    samples = [
        "EleutherAI/pythia-160m",
        "stabilityai/stable-diffusion-3.5-large",
        "stabilityai/sdxl-turbo",
        "BAAI/bge-reranker-v2-m3",
        "Qwen/Qwen3-Embedding-8B",
        "some-unknown-org/some-random-model",
        "unknown-org/whatever",
        "Qwen/Qwen2.5-Coder-7B-Instruct",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "meta-llama/Llama-3.1-70B",
        "google/gemma-3-4b-it",
    ]
    for repo in samples:
        for tag in ("text-generation", "image-text-to-text",
                    "sentence-similarity", "text-to-image", "text-ranking", ""):
            got = guess_category(repo, tag)
            assert got in VALID_CATEGORIES, (
                f"{repo} (tag={tag!r}) 返回了表外分类 {got!r}"
            )


# ── 2. W3 具体修掉的三个 bug ──
def test_bug_pythia_160m_not_dense():
    """bug #1：EleutherAI/pythia-160m 曾被判成 international-dense。

    160M 的小模型 —— dense 的语义是"需要大机器"，标 dense 会误导部署决策。
    归到 edge / embedding 都对，关键是**不能是 dense**。
    """
    got = guess_category("EleutherAI/pythia-160m", "text-generation")
    assert got != "international-dense", "160M 的模型不该归 dense"
    assert got in VALID_CATEGORIES


def test_bug_stabilityai_is_not_domestic():
    """bug #2：stabilityai/* 曾落到兜底 → domestic-general。

    stabilityai 是国际厂商（图像模型）→ 应归国际，且不是国内通用。
    """
    for repo in ("stabilityai/stable-diffusion-3.5-large",
                 "stabilityai/sdxl-turbo",
                 "stabilityai/stable-diffusion-xl-base-1.0"):
        got = guess_category(repo, "text-generation")
        assert got != "domestic-general", f"{repo} 不该判成国内通用"
        assert got in VALID_CATEGORIES


def test_bug_no_image_generation_category():
    """bug #3：image-generation 类不存在，曾被返回。"""
    assert "image-generation" not in VALID_CATEGORIES
    got = guess_category("stabilityai/stable-diffusion-3.5-large", "text-to-image")
    assert got != "image-generation"
    assert got in VALID_CATEGORIES


# ── 3. 各分类的正例 ──
@pytest.mark.parametrize("repo,expected", [
    # embedding
    ("BAAI/bge-large-zh-v1.5", "embedding"),
    ("Qwen/Qwen3-Embedding-8B", "embedding"),
    ("Alibaba-NLP/gte-multilingual-base", "embedding"),
    ("intfloat/e5-base-v2", "embedding"),
    # reranker
    ("BAAI/bge-reranker-large", "reranker"),
    ("BAAI/bge-reranker-v2-m3", "reranker"),
    # code
    ("Qwen/Qwen2.5-Coder-7B-Instruct", "code"),
    ("deepseek-ai/DeepSeek-Coder-V2-Instruct", "code"),
    ("mistralai/Codestral-22B-v0.1", "code"),
    # vision
    ("Qwen/Qwen2.5-VL-7B-Instruct", "vision"),
    ("OpenGVLab/InternVL3-8B", "vision"),
    # 国内推理
    ("deepseek-ai/DeepSeek-R1", "domestic-reasoning"),
    ("Qwen/QwQ-32B", "domestic-reasoning"),
    ("THUDM/GLM-Z1-32B-0414", "domestic-reasoning"),
    # 国内通用
    ("Qwen/Qwen3-14B", "domestic-general"),
    ("MiniMaxAI/MiniMax-M2.5", "domestic-general"),
    # 国际 edge / dense
    ("meta-llama/Llama-3.2-1B", "international-edge"),
    ("meta-llama/Llama-3.1-8B-Instruct", "international-edge"),
    ("google/gemma-3-4b-it", "international-edge"),
    ("microsoft/Phi-4-mini-instruct", "international-edge"),
    ("meta-llama/Llama-3.1-70B", "international-dense"),
    ("meta-llama/Llama-3.1-405B", "international-dense"),
    ("mistralai/Mistral-Large-Instruct-2407", "international-dense"),
    ("openai/gpt-oss-120b", "international-dense"),
])
def test_positive_cases(repo, expected):
    assert guess_category(repo, "text-generation") == expected


# ── 4. 功能类优先于 namespace ──
def test_functional_class_beats_namespace():
    """BAAI 是国内 namespace，但 bge-* 是 embedding —— 功能优先。"""
    assert guess_category("BAAI/bge-m3", "text-generation") == "embedding"
    assert guess_category("BAAI/bge-reranker-v2-m3", "text-generation") == "reranker"


def test_code_beats_namespace():
    """Qwen 是国内 namespace，Coder 是 code —— 功能优先。"""
    assert guess_category("Qwen/Qwen2.5-Coder-14B-Instruct", "text-generation") == "code"


def test_vision_beats_namespace():
    assert guess_category("Qwen/Qwen3-VL-8B-Instruct", "text-generation") == "vision"


# ── 5. 边界：抠不到参数量时按 edge（保守）──
def test_unknown_namespace_falls_back_safely():
    """未知 namespace → 兜底，且兜底值必须在白名单内。

    兜底给 domestic-general（中性），不给 international-*：
    未知厂商的模型连国内/国际都判断不了，标成国际 edge/dense 是在编造信息。
    """
    got = guess_category("some-org/mystery-model", "text-generation")
    assert got in VALID_CATEGORIES
    assert got == "domestic-general"


def test_known_namespace_without_size_defaults_to_edge():
    """已知国际 namespace 但名字里抠不到参数量 → edge（保守）。"""
    assert guess_category("meta-llama/mystery-model", "text-generation") == "international-edge"

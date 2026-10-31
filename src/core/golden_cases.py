"""golden_cases.py · 决策模型的「已知答案」自检题

`osm-deploy verify` 用这些题判断一个部署**真的能出正确答案**，而不只是
「服务起来了」。

收录原则
--------
1. 只收**真机实测过**的（有输出留证），不抄 model card 的示例
   —— 抄示例只能证明「能返回」，证明不了「答案对」。
2. 每题必须有**客观答案**：合同里确实写了的条款、确实成立的事实。
   不要收「风险等级=中」这种主观判断，那种无法判定对错。
3. 记录实测时的概率，作为 `prob_min` 的下限参考（判分要留余量，
   不同硬件/量化档位会有小幅漂移）。

目前只有 JEV-9B 满足条件（2026-10-31 真机验证）。
其余 11 个模型 `verify` 只做连通性与结构检查，会明确说「答案未验证」。
"""
from __future__ import annotations

from typing import Any, Dict, List

GOLDEN_CASES: Dict[str, Dict[str, Any]] = {
    "autotrust/jev-9b": {
        "verified_at": "2026-10-31",
        "environment": "AutoDL RTX 4080 SUPER 32GB / vllm 0.32.0 / torch 2.13",
        "note": "合同文本是自拟的，两个问题的答案在文本里客观存在，可判定对错",
        "cases": [
            {
                "name": "自动续约条款识别",
                "kind": "noul",
                "state": (
                    "甲方应在合同到期前 30 日书面通知乙方。"
                    "乙方未在期限内通知的，合同自动续期一年。"
                ),
                "question": "是否包含自动续约条款",
                "expect_value": True,
                "expect_prob_min": 0.70,
                "measured_prob": 0.985,
                "why": "文本里明确写了「合同自动续期一年」",
            },
            {
                "name": "违约金条款识别",
                "kind": "noul",
                "state": "任一方违约应向对方支付合同总额 20% 的违约金。",
                "question": "是否约定违约金",
                "expect_value": True,
                "expect_prob_min": 0.70,
                "measured_prob": 0.996,
                "why": "文本里明确写了「20% 的违约金」",
            },
            {
                "name": "否定项不应误判",
                "kind": "noul",
                "state": "本合同经双方签字盖章后生效，有效期为一年。",
                "question": "是否包含保密条款",
                "expect_value": False,
                "expect_prob_min": 0.60,
                "measured_prob": None,
                "why": "文本里完全没有保密相关内容，正确答案是 false",
                "note": "这条是防「模型无脑答 true」的对照题",
            },
        ],
    },
}


def has_golden(hf_repo: str) -> bool:
    return (hf_repo or "").lower() in GOLDEN_CASES


def get_golden(hf_repo: str) -> Dict[str, Any]:
    return GOLDEN_CASES.get((hf_repo or "").lower(), {})


def list_covered() -> List[str]:
    """哪些模型有 golden set（供文档核对）"""
    return sorted(GOLDEN_CASES.keys())

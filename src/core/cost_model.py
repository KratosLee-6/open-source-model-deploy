"""cost_model.py · 真实成本对比：本地一次性投入 vs 云租

设计原则（这是「真实」二字的全部含义）
--------------------------------------
1. **每个价格都有出处和时间**。没有 source / as_of 的数字不许进这个模块。
2. **云租给区间，不给单点**。同一张 4090，AutoDL 现货价 ¥1.88/h、按需价 ¥2.68/h，
   第三方比价样本中位 ¥2.20/h —— 抹成一个数字就是骗人。
3. **显存需求从 vram_requirements 取**，不在这里重算。成本要和「能不能跑」同源。
4. **只算硬件账，并把没算的说清楚**。回本周期回答的是「硬件钱多久靠租省回来」，
   不含运维人力、网络、存储、机房、折旧残值、停机损失。
5. **不替用户做决定**。输出事实和区间，结论留给 `assess` 的调用方。

价格来源（2026-10 采集）
------------------------
云租：
  - AutoDL 价格页（按需价）：RTX 4090 ¥2.68/h · A100 40G ¥3.45/h · A100 80G ¥5.98/h
  - AutoDL 现货/竞价价：RTX 4090 ¥1.88/h 起，A100 80G ¥4.0/h 起（北京时间 0-6 点最低）
  - 第三方 4550 条样本中位价：RTX 4090 ¥2.20/h · A100 ¥7.29/h
  - 阿里云 PAI：A100 80G ¥8–12/h；腾讯云 TI：A100 80G ¥7.5–10/h
本地卡价：2026-08 人工基线（见 hardware_prices.py），加价率与功耗见下表。

⚠️ 价格随供给、机房、促销波动，下单前请以官网为准。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .vram_requirements import suggest_gpu_plan

# ---------------------------------------------------------------------------
# 本地硬件：价格 + 功耗 + 出处
# ---------------------------------------------------------------------------
# power_w 是**整机满载**估算（GPU TDP + 主板/CPU/内存/风扇），不是单卡 TDP
LOCAL_GPU: Dict[str, Dict[str, Any]] = {
    # 消费级 24GB 档
    "RTX 4090": {
        "vram_gb": 24, "price_cny": 14000, "power_w": 550, "tier": "consumer",
        "price_source": "2026-08 国内电商基线（hardware_prices.py）", "price_as_of": "2026-08",
    },
    "RTX 4090D": {
        "vram_gb": 24, "price_cny": 12500, "power_w": 500, "tier": "consumer",
        "price_source": "2026-08 国内电商基线", "price_as_of": "2026-08",
    },
    "RTX 5090": {
        "vram_gb": 32, "price_cny": 17000, "power_w": 650, "tier": "consumer",
        "price_source": "2026-08 国内电商基线", "price_as_of": "2026-08",
    },
    "RTX 3090": {
        "vram_gb": 24, "price_cny": 7000, "power_w": 450, "tier": "consumer",
        "price_source": "2026-08 二手/尾货基线", "price_as_of": "2026-08",
    },
    # 数据中心 80GB 档
    "NVIDIA A100 80G": {
        "vram_gb": 80, "price_cny": 80000, "power_w": 900, "tier": "datacenter",
        "price_source": "2026-08 渠道基线", "price_as_of": "2026-08",
    },
    "NVIDIA H100 80G PCIe": {
        "vram_gb": 80, "price_cny": 225000, "power_w": 1000, "tier": "datacenter",
        "price_source": "2026-08 渠道基线", "price_as_of": "2026-08",
    },
    "NVIDIA H100 SXM": {
        "vram_gb": 80, "price_cny": 250000, "power_w": 1100, "tier": "datacenter",
        "price_source": "2026-08 渠道基线", "price_as_of": "2026-08",
    },
    "NVIDIA H200": {
        "vram_gb": 141, "price_cny": 315000, "power_w": 1200, "tier": "datacenter",
        "price_source": "2026-08 渠道基线", "price_as_of": "2026-08",
    },
    # 国产替代
    "华为昇腾 910B": {
        "vram_gb": 64, "price_cny": 90000, "power_w": 800, "tier": "domestic",
        "price_source": "2026-08 渠道基线", "price_as_of": "2026-08",
    },
}

# ---------------------------------------------------------------------------
# 云租：区间价（低=现货/竞价，高=按需牌价）
# ---------------------------------------------------------------------------
CLOUD_GPU: Dict[str, Dict[str, Dict[str, Any]]] = {
    "AutoDL": {
        "RTX 4090": {
            "spot_low": 1.88, "ondemand_high": 2.68,
            "source": "AutoDL 价格页（按需 ¥2.68/h）+ 现货 ¥1.88/h 起", "as_of": "2026-07",
        },
        "RTX 3090": {
            "spot_low": 1.68, "ondemand_high": 2.20,
            "source": "AutoDL 现货价 ¥1.68/h 起", "as_of": "2026-07",
        },
        "NVIDIA A100 40G": {
            "spot_low": 2.50, "ondemand_high": 3.45,
            "source": "AutoDL 按需 ¥3.45/h", "as_of": "2026-07",
        },
        "NVIDIA A100 80G": {
            "spot_low": 4.00, "ondemand_high": 5.98,
            "source": "AutoDL 按需 ¥5.98/h，现货 ¥4.0/h 起", "as_of": "2026-07",
        },
    },
    "阿里云 PAI": {
        "NVIDIA A100 80G": {
            "spot_low": 8.00, "ondemand_high": 12.00,
            "source": "阿里云 PAI 按需区间", "as_of": "2026-07",
        },
    },
    "腾讯云 TI": {
        "NVIDIA A100 80G": {
            "spot_low": 7.50, "ondemand_high": 10.00,
            "source": "腾讯云 TI 按需区间", "as_of": "2026-07",
        },
    },
}

# 整机加价率：GPU × N → 整机（含主板/CPU/内存/硬盘/电源/机箱）
RIG_MARKUP = 1.3

# 电价（元/度）——中国商业用电常见区间 0.6–1.2，默认取 0.8
DEFAULT_ELECTRICITY_CNY_KWH = 0.8

# 使用时长档位（小时/月）
HOURS_24X7 = 730.0
HOURS_WORKDAY_8H = 8 * 22  # 176


class CostError(ValueError):
    """成本计算前置条件不满足。"""


# ---------------------------------------------------------------------------
# 卡型选择
# ---------------------------------------------------------------------------
def _pick_local_gpu(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """按显存需求选本地卡方案。

    规则（简单但可解释）：
      - 单卡能装下 → 优先 24GB 消费级（个位数 GB 需求）或 80GB（>24GB 需求）
      - 装不下 → 多卡，24GB 卡优先（单位显存更便宜），超过 8 卡改 80GB 卡
    """
    vram = float(plan.get("vram_required_gb") or 0)
    if vram <= 0:
        raise CostError("显存需求为 0，无法计算成本")

    is_moe = bool(plan.get("is_moe"))

    if vram <= 24:
        # 单张消费级即可
        return [{"gpu": "RTX 4090", "count": 1}]
    if vram <= 32:
        return [{"gpu": "RTX 5090", "count": 1}]
    if vram <= 80:
        return [{"gpu": "NVIDIA A100 80G", "count": 1}]

    # 多卡：先试 24GB 卡
    gpus_24 = int(-(-vram // 24))  # ceil
    if gpus_24 <= 8:
        return [{"gpu": "RTX 4090", "count": gpus_24}]

    # 超过 8 张 24GB → 用 80GB 卡
    gpus_80 = int(-(-vram // 80))
    return [{"gpu": "NVIDIA A100 80G", "count": gpus_80}]


def _cloud_candidates(gpu_model: str, count: int) -> List[Dict[str, Any]]:
    """找该卡在哪些平台有报价。没有报价的平台不编。"""
    out: List[Dict[str, Any]] = []
    for platform, table in CLOUD_GPU.items():
        rate = table.get(gpu_model)
        if not rate:
            continue
        out.append({
            "platform": platform,
            "gpu": gpu_model,
            "count": count,
            "spot_low_cny_per_hour": round(rate["spot_low"] * count, 2),
            "ondemand_high_cny_per_hour": round(rate["ondemand_high"] * count, 2),
            "source": rate["source"],
            "as_of": rate["as_of"],
        })
    return out


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------
def compare_cost(
    model_info: Dict[str, Any],
    quant: str = "Q4_K_M",
    *,
    electricity_cny_per_kwh: float = DEFAULT_ELECTRICITY_CNY_KWH,
    hours_per_month: Optional[float] = None,
) -> Dict[str, Any]:
    """算「本地一次性投入 vs 云租月成本」，并给回本周期。

    Args:
        model_info: KNOWN_MODELS 里的 info
        quant: 量化档位（默认 Q4_K_M）
        electricity_cny_per_kwh: 电价（元/度），默认 0.8
        hours_per_month: 只看单一时长时传；不传则同时给 24×7 和 8h×22 两档

    Returns:
        {
          "quant": "Q4_K_M",
          "vram_required_gb": 6.4,
          "is_moe": false,
          "local": {"gpu", "count", "gpu_price_cny", "rig_price_cny",
                    "power_w", "electricity_cny_per_month_24x7",
                    "price_source", "price_as_of"},
          "cloud": [{"platform", "spot_low_cny_per_hour", ...}],
          "breakeven": {"months_24x7": [...], "months_working_hours": [...]},
          "caveats": [...]
        }
    """
    plan = suggest_gpu_plan(model_info, quant=quant)
    vram = float(plan.get("vram_required_gb") or 0)
    choices = _pick_local_gpu(plan)

    # 只算第一种（最优）方案，其余作为备选列出
    primary = choices[0]
    gpu_model = primary["gpu"]
    count = primary["count"]
    spec = LOCAL_GPU.get(gpu_model)
    if spec is None:
        raise CostError(f"本地卡表里没有 {gpu_model} 的价格")

    gpu_total = spec["price_cny"] * count
    rig_total = int(gpu_total * RIG_MARKUP)
    power_w = spec["power_w"] * count
    kwh_per_hour = power_w / 1000.0

    def elec_month(hours: float) -> float:
        return round(kwh_per_hour * hours * electricity_cny_per_kwh, 1)

    cloud = _cloud_candidates(gpu_model, count)

    # 回本周期：本地整机 ÷ 云租月费（按不同时长）
    # 注意方向：云租越贵 → 本地回本越快。所以要同时给 min/max，不能只给一个。
    def breakeven(hours: float) -> List[Dict[str, Any]]:
        out = []
        for c in cloud:
            low = c["spot_low_cny_per_hour"] * hours       # 云租便宜档
            high = c["ondemand_high_cny_per_hour"] * hours  # 云租贵档
            m_cheap_cloud = round(rig_total / low, 1) if low else None   # 云便宜 → 回本慢
            m_expensive_cloud = round(rig_total / high, 1) if high else None  # 云贵 → 回本快
            months = [m for m in (m_cheap_cloud, m_expensive_cloud) if m is not None]
            out.append({
                "platform": c["platform"],
                "cloud_monthly_low_cny": round(low, 0),
                "cloud_monthly_high_cny": round(high, 0),
                "months_min": min(months) if months else None,
                "months_max": max(months) if months else None,
            })
        return out

    hours_list = [hours_per_month] if hours_per_month else [HOURS_24X7, HOURS_WORKDAY_8H]
    result: Dict[str, Any] = {
        "quant": quant,
        "vram_required_gb": vram,
        "is_moe": bool(plan.get("is_moe")),
        "local": {
            "gpu": gpu_model,
            "count": count,
            "gpu_price_cny": spec["price_cny"],
            "gpu_total_cny": gpu_total,
            "rig_price_cny": rig_total,
            "rig_markup": RIG_MARKUP,
            "power_w_full_load": power_w,
            "electricity_cny_per_kwh": electricity_cny_per_kwh,
            "electricity_cny_per_month_24x7": elec_month(HOURS_24X7),
            "electricity_cny_per_month_working": elec_month(HOURS_WORKDAY_8H),
            "price_source": spec["price_source"],
            "price_as_of": spec["price_as_of"],
        },
        "cloud": cloud,
        "alternatives": choices[1:] if len(choices) > 1 else [],
        "breakeven": {},
        "caveats": [
            "只算硬件账：不含运维人力、网络带宽、存储、机房/电费基础建设、折旧残值。",
            "云租价随供给、机房、时段波动（现货价北京时间 0–6 点最低，可比按需低 40–60%），下单前以官网为准。",
            "本地整机按 GPU 价 ×1.3 估算（含主板/CPU/内存/硬盘/电源/机箱），非精确报价。",
            f"电价按 ¥{electricity_cny_per_kwh}/度计，中国商业用电常见区间 ¥0.6–1.2。",
            "回本周期只回答「硬件钱多久靠租省回来」，不等于总拥有成本对比。",
        ],
    }

    if not cloud:
        result["breakeven"] = {"note": f"{gpu_model} 在已知云平台没有公开报价，无法算回本周期"}
        return result

    if hours_per_month:
        result["breakeven"] = {
            "hours_per_month": hours_per_month,
            "items": breakeven(hours_per_month),
        }
    else:
        result["breakeven"] = {
            "hours_24x7": HOURS_24X7,
            "items_24x7": breakeven(HOURS_24X7),
            "hours_working": HOURS_WORKDAY_8H,
            "items_working": breakeven(HOURS_WORKDAY_8H),
        }

    return result


def render_cost(cost: Dict[str, Any]) -> str:
    """把 compare_cost() 的结果渲染成几行（CLI / assess 用）。"""
    loc = cost["local"]
    lines = [
        f"  量化档位 : {cost['quant']}   显存需求 {cost['vram_required_gb']} GB"
        + ("  (MoE 按总参)" if cost["is_moe"] else ""),
        f"  本地方案 : {loc['count']}× {loc['gpu']}",
        f"             单卡 ¥{loc['gpu_price_cny']:,} × {loc['count']}"
        f" = ¥{loc['gpu_total_cny']:,}；整机估 ¥{loc['rig_price_cny']:,}"
        f"（×{loc['rig_markup']}，含主板/CPU/内存/硬盘）",
        f"             满载 {loc['power_w_full_load']} W"
        f"  →  电费 24×7 ¥{loc['electricity_cny_per_month_24x7']:,}/月"
        f" · 8h×22 ¥{loc['electricity_cny_per_month_working']:,}/月",
        f"  价格出处 : {loc['price_source']}",
    ]

    if cost.get("cloud"):
        lines.append("  云租对比 :")
        for c in cost["cloud"]:
            lines.append(
                f"    {c['platform']:12} {c['count']}× {c['gpu']:22}"
                f" ¥{c['spot_low_cny_per_hour']}–{c['ondemand_high_cny_per_hour']}/h"
                f"   （{c['source']}，{c['as_of']}）"
            )

    be = cost.get("breakeven") or {}
    if "items_24x7" in be:
        lines.append("  回本周期 :")
        for label, key in (("24×7 跑", "items_24x7"), ("8h×22 跑", "items_working")):
            for it in be[key]:
                lines.append(
                    f"    {label} → {it['platform']:12}"
                    f" 云租 ¥{it['cloud_monthly_low_cny']:,.0f}–{it['cloud_monthly_high_cny']:,.0f}/月"
                    f"  ·  回本 {it['months_min']}–{it['months_max']} 个月"
                )
    elif "note" in be:
        lines.append(f"  回本周期 : {be['note']}")

    return "\n".join(lines)

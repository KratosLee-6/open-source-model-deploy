"""
硬件报价：消费级 GPU、服务器、云租价
- 内置基准表（每月人工刷新一次）
- 支持扩展：未来可接京东爬虫/云厂商 API
"""
from typing import Dict, List, Any


# 基准表 - 每月手动刷新（README 注明刷新日期）
# 数据格式：[(型号, 显存GB, 单卡参考价(元), 来源, 备注)]
GPU_BASELINE_2026_08: List[Dict[str, Any]] = [
    # 消费级
    {"model": "RTX 4090", "vram_gb": 24, "price_cny": 14000, "tier": "consumer", "note": "性价比首选"},
    {"model": "RTX 4090D", "vram_gb": 24, "price_cny": 12500, "tier": "consumer", "note": "国内合规版"},
    {"model": "RTX 5090", "vram_gb": 32, "price_cny": 17000, "tier": "consumer", "note": "新一代旗舰"},
    {"model": "RTX 5080", "vram_gb": 16, "price_cny": 8500, "tier": "consumer", "note": "中端"},
    # 数据中心
    {"model": "NVIDIA A100 80G", "vram_gb": 80, "price_cny": 80000, "tier": "datacenter", "note": "上一代主力"},
    {"model": "NVIDIA A100 40G", "vram_gb": 40, "price_cny": 55000, "tier": "datacenter", "note": "性价比"},
    {"model": "NVIDIA H100 80G PCIe", "vram_gb": 80, "price_cny": 225000, "tier": "datacenter", "note": "当代旗舰"},
    {"model": "NVIDIA H100 SXM", "vram_gb": 80, "price_cny": 250000, "tier": "datacenter", "note": "NVLink 版"},
    {"model": "NVIDIA H200", "vram_gb": 141, "price_cny": 315000, "tier": "datacenter", "note": "大显存版"},
    # 国产替代
    {"model": "华为昇腾 910B", "vram_gb": 64, "price_cny": 90000, "tier": "domestic", "note": "国产化首选"},
    {"model": "寒武纪 MLU370", "vram_gb": 24, "price_cny": 40000, "tier": "domestic", "note": "推理为主"},
    {"model": "海光 DCU", "vram_gb": 32, "price_cny": 25000, "tier": "domestic", "note": "ROCm 兼容"},
]

CLOUD_RENTAL_BASELINE_2026_08: Dict[str, List[Dict[str, Any]]] = {
    "阿里云": [
        {"gpu": "A100 80G", "monthly_cny": 10000, "note": "单卡"},
        {"gpu": "H100 80G", "monthly_cny": 21500, "note": "单卡"},
    ],
    "腾讯云": [
        {"gpu": "A100 40G", "monthly_cny": 7500, "note": "单卡"},
        {"gpu": "H100 80G", "monthly_cny": 21000, "note": "单卡"},
    ],
    "华为云": [
        {"gpu": "昇腾 910B", "monthly_cny": 7500, "note": "单卡"},
    ],
    "AutoDL": [
        {"gpu": "RTX 4090", "monthly_cny": 2500, "note": "科研友好"},
    ],
}


def find_gpu(model_name: str) -> Dict[str, Any]:
    """按型号查找 GPU 基准价"""
    for gpu in GPU_BASELINE_2026_08:
        if gpu["model"].lower() == model_name.lower():
            return gpu
    return {}


def get_all_gpus_by_tier(tier: str) -> List[Dict[str, Any]]:
    """按档位列出 GPU（consumer / datacenter / domestic）"""
    return [g for g in GPU_BASELINE_2026_08 if g["tier"] == tier]


def estimate_server_cost(gpu_count: int, gpu_model: str, include_other: bool = True) -> int:
    """估算服务器整机成本（含 CPU/内存/硬盘/机箱）

    系数：服务器整机 ≈ 单卡价格 × 卡数 × 1.3（含主板/CPU/内存/硬盘/电源）
    """
    gpu = find_gpu(gpu_model)
    if not gpu:
        return 0
    base = gpu["price_cny"] * gpu_count
    if include_other:
        return int(base * 1.3)
    return base


def estimate_3tier_budget(model_size_b: float, context_k: int = 128) -> Dict[str, int]:
    """根据模型规模估算 3 档预算（入门/标准/高性能）

    Args:
        model_size_b: 模型总参数（B），如 671（B = billion）
        context_k: 上下文长度（K）

    Returns:
        {"entry": ¥, "standard": ¥, "high": ¥}
    """
    # 入门档：单卡 4090 可行需 model_size_b ≤ 13B（量化后 ≤ 10GB）
    if model_size_b <= 13:
        entry = estimate_server_cost(1, "RTX 4090")
    else:
        # 入门档：双卡 4090 或单卡 5090（适合 13B-32B 量化）
        entry = estimate_server_cost(2, "RTX 4090")

    # 标准档：双 4090 或单卡 A100 80G（适合 14B-70B 量化）
    if model_size_b <= 32:
        standard = estimate_server_cost(2, "RTX 4090")
    elif model_size_b <= 70:
        standard = estimate_server_cost(1, "NVIDIA A100 80G")
    else:
        # 70B+ 需 2×A100 或更多
        standard = estimate_server_cost(2, "NVIDIA A100 80G")

    # 高性能档：满血全精度部署
    if model_size_b <= 13:
        # 单卡 H100 已足够
        high = estimate_server_cost(1, "NVIDIA H100 80G PCIe")
    elif model_size_b <= 70:
        # 4×H100 服务器
        high = estimate_server_cost(4, "NVIDIA H100 SXM")
    else:
        # 8×H100 服务器
        high = estimate_server_cost(8, "NVIDIA H100 SXM")

    return {"entry": entry, "standard": standard, "high": high}

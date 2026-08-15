"""
硬件自动检测模块 - 跨平台（macOS / Windows / Linux）
- 自动识别 GPU / CPU / 内存 / 硬盘
- Apple Silicon 通过 system_profiler / sysctl
- NVIDIA 通过 nvidia-smi
- AMD 通过 rocm-smi
- 自动反推可部署模型清单

零依赖：纯标准库 + subprocess
"""
import sys
import os
import platform
import subprocess
import shutil
import re
from typing import Dict, List, Any, Optional


# 常见 GPU 显存速查表（型号 → 显存 GB）
KNOWN_GPU_VRAM = {
    # NVIDIA 消费级
    "rtx 4090": 24, "rtx 4090 d": 24, "rtx 4090d": 24,
    "rtx 4080": 16, "rtx 4080 super": 16,
    "rtx 4070 ti": 12, "rtx 4070": 12, "rtx 4060 ti": 8, "rtx 4060": 8,
    "rtx 5090": 32, "rtx 5080": 16, "rtx 5070 ti": 16, "rtx 5070": 12,
    # NVIDIA 数据中心
    "a100": 80, "a100 80gb": 80, "a100 40gb": 40,
    "h100": 80, "h100 80gb": 80,
    "h200": 141, "h200 141gb": 141,
    "b100": 192, "b200": 192,
    "v100": 32, "v100 32gb": 32,
    "a10": 24, "a40": 48, "l4": 24, "l40": 48, "l40s": 48,
    "t4": 16,
    # AMD
    "mi300x": 192, "mi250x": 128, "mi210": 64,
    "rx 7900 xtx": 24, "rx 7900 xt": 20, "rx 7800 xt": 16,
}


def detect_platform() -> str:
    """返回标准化平台名"""
    p = platform.system().lower()
    if p == "darwin":
        return "macos"
    elif p == "windows":
        return "windows"
    elif p == "linux":
        return "linux"
    return p


def detect_apple_silicon() -> Optional[Dict[str, Any]]:
    """检测 Apple Silicon（统一内存架构）

    返回 {"chip": "M2 Max", "unified_memory_gb": 64, "gpu_cores": 38}
    """
    if detect_platform() != "macos":
        return None

    info = {"chip": None, "unified_memory_gb": 0, "gpu_cores": 0}

    # 检测芯片（sysctl machdep.cpu.brand_string）
    try:
        out = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, timeout=5
        )
        if out.returncode == 0:
            info["chip"] = out.stdout.strip()
    except Exception:
        pass

    # 检测统一内存（system_profiler）
    try:
        out = subprocess.run(
            ["system_profiler", "SPHardwareDataType"],
            capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0:
            m = re.search(r"Memory:\s*(\d+)\s*GB", out.stdout)
            if m:
                info["unified_memory_gb"] = int(m.group(1))
            m = re.search(r"Chipset Model:\s*(\S+)", out.stdout)
            if m and not info["chip"]:
                info["chip"] = m.group(1)
    except Exception:
        pass

    # 检测 GPU 核心数
    try:
        out = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0:
            m = re.search(r"Total Number of Cores:\s*(\d+)", out.stdout)
            if m:
                info["gpu_cores"] = int(m.group(1))
    except Exception:
        pass

    return info


def detect_nvidia_gpus() -> List[Dict[str, Any]]:
    """检测 NVIDIA GPU（需 nvidia-smi）"""
    gpus = []
    if not shutil.which("nvidia-smi"):
        return gpus

    try:
        # -L 列出 GPU，--query-gpu 查详细
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.free,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if out.returncode != 0:
            return gpus

        for line in out.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                idx, name, mem_total, mem_free = parts[:4]
                driver = parts[4] if len(parts) > 4 else "unknown"
                mem_total_gb = int(int(mem_total) / 1024) if mem_total.isdigit() else 0
                mem_free_gb = int(int(mem_free) / 1024) if mem_free.isdigit() else 0
                gpus.append({
                    "index": int(idx),
                    "vendor": "nvidia",
                    "name": name,
                    "vram_total_gb": mem_total_gb,
                    "vram_free_gb": mem_free_gb,
                    "driver_version": driver,
                })
    except Exception:
        pass

    return gpus


def detect_amd_gpus() -> List[Dict[str, Any]]:
    """检测 AMD GPU（需 rocm-smi）"""
    gpus = []
    if not shutil.which("rocm-smi"):
        return gpus

    try:
        out = subprocess.run(
            ["rocm-smi", "--showproductname", "--showmeminfo", "vram"],
            capture_output=True, text=True, timeout=10
        )
        if out.returncode != 0:
            return gpus
        # 简化解析：提取 GPU 名称和显存
        name_match = re.findall(r"Card series:\s*(.+)", out.stdout)
        mem_match = re.findall(r"VRAM Total Memory.*?(\d+)\s*M", out.stdout)
        for i, name in enumerate(name_match):
            vram_gb = int(int(mem_match[i]) / 1024) if i < len(mem_match) else 0
            # 用型号反查显存表
            if vram_gb == 0:
                name_lower = name.lower().strip()
                for k, v in KNOWN_GPU_VRAM.items():
                    if k in name_lower:
                        vram_gb = v
                        break
            gpus.append({
                "index": i,
                "vendor": "amd",
                "name": name.strip(),
                "vram_total_gb": vram_gb,
                "vram_free_gb": 0,
                "driver_version": "rocm",
            })
    except Exception:
        pass

    return gpus


def detect_cpu() -> Dict[str, Any]:
    """检测 CPU 信息"""
    info = {
        "physical_cores": 0,
        "logical_cores": 0,
        "model": platform.processor() or "unknown",
        "arch": platform.machine(),
    }
    try:
        info["logical_cores"] = os.cpu_count() or 0
        # 物理核心数（psutil 标准库替代）
        if hasattr(os, "sched_getaffinity"):
            info["physical_cores"] = len(os.sched_getaffinity(0))
    except Exception:
        pass
    return info


def detect_memory() -> Dict[str, Any]:
    """检测内存（统一方法：读 /proc/meminfo 或调用 wmic）"""
    info = {"total_gb": 0, "available_gb": 0, "type": "unknown"}

    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            for line in lines:
                if line.startswith("MemTotal:"):
                    info["total_gb"] = round(int(line.split()[1]) / 1024 / 1024, 1)
                elif line.startswith("MemAvailable:"):
                    info["available_gb"] = round(int(line.split()[1]) / 1024 / 1024, 1)
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            out = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                capture_output=True, text=True, timeout=5)
            if out.returncode == 0:
                info["total_gb"] = round(int(out.stdout.strip()) / 1024**3, 1)
        except Exception:
            pass
    elif sys.platform == "win32":
        try:
            out = subprocess.run(
                ["wmic", "OS", "get", "TotalVisibleMemorySize", "/value"],
                capture_output=True, text=True, timeout=5
            )
            if out.returncode == 0:
                m = re.search(r"TotalVisibleMemorySize=(\d+)", out.stdout)
                if m:
                    info["total_gb"] = round(int(m.group(1)) / 1024 / 1024, 1)
        except Exception:
            pass

    return info


def detect_disk() -> Dict[str, Any]:
    """检测当前盘剩余空间"""
    info = {"free_gb": 0, "total_gb": 0}
    try:
        stat = shutil.disk_usage(".")
        info["free_gb"] = round(stat.free / 1024**3, 1)
        info["total_gb"] = round(stat.total / 1024**3, 1)
    except Exception:
        pass
    return info


def full_hardware_scan() -> Dict[str, Any]:
    """完整硬件扫描

    Returns:
        {
          "platform": "macos",
          "apple_silicon": {...} | None,
          "nvidia_gpus": [...],
          "amd_gpus": [...],
          "cpu": {...},
          "memory": {...},
          "disk": {...},
          "total_vram_gb": 64,  # 汇总
          "deployable_tier": "standard",
          "recommend_models": [...],
        }
    """
    plat = detect_platform()
    apple = detect_apple_silicon() if plat == "macos" else None
    nvidia = detect_nvidia_gpus()
    amd = detect_amd_gpus()
    cpu = detect_cpu()
    mem = detect_memory()
    disk = detect_disk()

    # 汇总显存
    if apple and apple.get("unified_memory_gb"):
        # Apple Silicon 共享内存（GPU 约可用 75%）
        total_vram_gb = int(apple["unified_memory_gb"] * 0.75)
    else:
        total_vram_gb = sum(g["vram_total_gb"] for g in nvidia + amd)

    # 判断部署档位
    if total_vram_gb >= 160:  # 8×H100 级别
        tier = "ultra"
    elif total_vram_gb >= 80:  # 单 H100 / 双 A100
        tier = "high"
    elif total_vram_gb >= 40:  # 单 A100 80G / 双 4090
        tier = "standard"
    elif total_vram_gb >= 16:  # 单 4090
        tier = "entry"
    elif total_vram_gb >= 8:  # Mac M1/M2 入门
        tier = "edge"
    else:
        tier = "cpu_only"

    return {
        "platform": plat,
        "apple_silicon": apple,
        "nvidia_gpus": nvidia,
        "amd_gpus": amd,
        "cpu": cpu,
        "memory": mem,
        "disk": disk,
        "total_vram_gb": total_vram_gb,
        "deployable_tier": tier,
        "timestamp": _now(),
    }


def _now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def recommend_models_for_hardware(hw_scan: Dict[str, Any], all_models: Dict[str, Dict]) -> List[Dict[str, Any]]:
    """根据硬件扫描结果，反推可部署的模型清单

    Args:
        hw_scan: full_hardware_scan() 输出
        all_models: KNOWN_MODELS 字典

    Returns:
        按适配度排序的模型推荐列表
    """
    total_vram = hw_scan["total_vram_gb"]
    tier = hw_scan["deployable_tier"]
    is_apple = hw_scan.get("apple_silicon") is not None
    has_cuda = len(hw_scan.get("nvidia_gpus", [])) > 0
    has_rocm = len(hw_scan.get("amd_gpus", [])) > 0

    recommendations = []

    for name, info in all_models.items():
        size_b = info.get("size_b", 0)
        activated_b = info.get("activated_b", 0)
        if size_b == 0:
            continue

        # 估算各精度所需显存
        vram_4bit = size_b * 0.6  # GGUF Q4
        vram_8bit = size_b * 1.0
        vram_fp16 = size_b * 2.0

        # MoE 模型用激活参数算
        if activated_b > 0:
            vram_4bit = activated_b * 0.6
            vram_8bit = activated_b * 1.0
            vram_fp16 = activated_b * 2.0

        # 适配度评估（取最大可支持的精度）
        suitable_quant = None  # Q4_K_M
        suitable_fp = None     # Q8_0 或 FP16/BF16
        for label, vram in [
            ("Q4_K_M", vram_4bit),
            ("Q8_0", vram_8bit),
            ("FP16/BF16", vram_fp16),
        ]:
            # 留 20% 余量（KV cache + 系统开销）
            if vram * 1.2 <= total_vram:
                if "Q4" in label:
                    suitable_quant = label
                elif "Q8" in label:
                    suitable_quant = label  # 升级到 Q8
                    suitable_fp = label
                else:  # FP16
                    suitable_quant = label
                    suitable_fp = label

        # Apple Silicon 排除 FP16（统一内存限制）
        if is_apple and suitable_fp == "FP16/BF16":
            suitable_fp = "Q8_0" if suitable_quant == "Q8_0" else None

        # CPU only / 低显存：放宽到内存也算资源
        # CPU 部署可用量化 + 大内存 swap（适合小模型或紧急测试）
        if not suitable_quant and not suitable_fp:
            # CPU 兜底：只要 4bit 量化小于内存的 80%，仍可推荐（慢但能用）
            cpu_memory_gb = hw_scan.get("memory", {}).get("total_gb", 0)
            if cpu_memory_gb > 0 and vram_4bit * 1.2 <= cpu_memory_gb * 0.8:
                suitable_quant = "Q4_K_M（CPU 慢速）"
                if not has_cuda and not has_rocm:
                    suitable_fp = None  # CPU 不推荐 FP16

        # 推理框架适配
        frameworks = []
        if is_apple:
            frameworks.append("llama.cpp（Apple Silicon 优化）")
            frameworks.append("MLX（Apple 推荐）")
            frameworks.append("Ollama")
        elif has_cuda:
            frameworks.append("vLLM（生产推荐）")
            frameworks.append("SGLang")
            frameworks.append("llama.cpp")
            frameworks.append("Ollama")
        elif has_rocm:
            frameworks.append("vLLM（ROCm）")
            frameworks.append("llama.cpp（ROCm）")
        else:
            frameworks.append("llama.cpp（CPU）")
            frameworks.append("Ollama（CPU）")

        recommendations.append({
            "model": name,
            "category": info.get("category"),
            "size_b": size_b,
            "activated_b": activated_b,
            "vram_estimate_4bit_gb": round(vram_4bit, 1),
            "vram_estimate_fp16_gb": round(vram_fp16, 1),
            "deployable_quant": suitable_quant,
            "deployable_precision": suitable_fp,
            "frameworks": frameworks,
            "note": info.get("note", ""),
        })

    # 按"能跑的最大模型优先"排序
    recommendations.sort(key=lambda r: r["vram_estimate_fp16_gb"], reverse=True)
    return recommendations

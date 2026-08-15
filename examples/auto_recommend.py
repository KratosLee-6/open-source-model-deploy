#!/usr/bin/env python3
"""
示例：硬件自动检测 + 智能推荐可部署模型

运行:
    python examples/auto_recommend.py
"""
import sys
sys.path.insert(0, ".")

from src.data_sources.hardware_detect import full_hardware_scan, recommend_models_for_hardware
from src.core.model_resolver import KNOWN_MODELS
from src.core.deployment_generator import generate_deploy_script


def main():
    print("=" * 70)
    print("【本机硬件扫描】")
    print("=" * 70)
    hw = full_hardware_scan()
    print(f"  平台:     {hw['platform']}")
    if hw.get("apple_silicon"):
        a = hw["apple_silicon"]
        print(f"  芯片:     {a['chip']} ({a.get('gpu_cores', '?')} GPU 核)")
        print(f"  统一内存: {a['unified_memory_gb']}GB")
    print(f"  CPU:      {hw['cpu']['model'][:50]} ({hw['cpu']['logical_cores']} 核)")
    print(f"  内存:     {hw['memory']['total_gb']}GB")
    print(f"  硬盘剩余: {hw['disk']['free_gb']}GB")
    print(f"  NVIDIA:   {len(hw['nvidia_gpus'])} 张")
    print(f"  AMD:      {len(hw['amd_gpus'])} 张")
    print(f"  总可用显存: {hw['total_vram_gb']}GB")
    print(f"  部署档位: {hw['deployable_tier']}")

    print("\n" + "=" * 70)
    print("【可部署模型推荐】(按模型规模升序)")
    print("=" * 70)
    recs = recommend_models_for_hardware(hw, KNOWN_MODELS)
    # 按 size 排序（小到大，方便看小机器适配）
    recs.sort(key=lambda r: r["size_b"])

    print(f"\n{'模型':<32} {'规模':<8} {'精度':<22} {'框架':<25}")
    print("-" * 90)
    for r in recs[:15]:
        precision = r["deployable_quant"] or r["deployable_precision"] or "� 不适配"
        frameworks = " / ".join(r["frameworks"][:2])
        print(f"  {r['model']:<30} {r['size_b']:>5}B  {precision:<22} {frameworks}")

    print(f"\n总共 {len(recs)} 个模型可在本机部署")

    # 演示：给 qwen3-32b 生成部署脚本
    if recs:
        target = next((r for r in recs if r["model"] == "qwen3-32b"), None)
        if target:
            # 找到 KNOWN_MODELS info
            model_info = KNOWN_MODELS.get("qwen3-32b", {})
            print("\n" + "=" * 70)
            print("【一键部署脚本示例】qwen3-32b")
            print("=" * 70)
            script = generate_deploy_script("qwen3-32b", model_info, hw, framework="auto")
            print(f"框架: {script['framework']}")
            print(f"\n[安装]")
            print(script["install_cmd"])
            print(f"\n[运行]")
            print(script["run_cmd"])
            if script.get("docker_cmd"):
                print(f"\n[Docker]")
                print(script["docker_cmd"])
            print(f"\n[注意]")
            for n in script["notes"]:
                print(f"  - {n}")


if __name__ == "__main__":
    main()

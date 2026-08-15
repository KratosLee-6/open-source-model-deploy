"""
CLI 入口：python -m src assess <model_name>
"""
import argparse
import json
import sys

from .core.assessor import full_assessment
from .core.model_resolver import extract_params_from_readme


def cmd_assess(args):
    """assess 子命令：跑 5 步鉴别"""
    result = full_assessment(args.model, force=args.force_refresh)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def cmd_list(args):
    """list 子命令：列出所有支持的模型（可按 category 过滤）"""
    from .core.model_resolver import KNOWN_MODELS
    filter_cat = args.category  # domestic-general / domestic-reasoning / international-dense / international-edge
    models = sorted(KNOWN_MODELS.items())

    # 按 category 分组显示
    cats = {}
    for name, info in models:
        cat = info.get("category", "uncategorized")
        cats.setdefault(cat, []).append((name, info))

    cat_cn = {
        "domestic-general": "【国内通用】",
        "domestic-reasoning": "【国内推理】",
        "international-dense": "【国际密集】",
        "international-edge": "【国际边缘】",
        "code": "【代码专用】",
        "vision": "【视觉多模态】",
        "embedding": "【Embedding】",
        "reranker": "【Reranker】",
    }

    for cat, items in sorted(cats.items()):
        if filter_cat and cat != filter_cat:
            continue
        print(f"\n{cat_cn.get(cat, cat)} ({len(items)} 个)")
        print("-" * 80)
        for name, info in items:
            size = info.get("size_b", "?")
            activated = info.get("activated_b")
            size_str = f"{size}B" if not activated else f"{size}B/{activated}B"
            hf_repo = info.get("hf_repo", "?")
            note = info.get("note", "")
            print(f"  {name:<25} {size_str:<10} {hf_repo:<45} {note}")

    print(f"\n总计: {len(models)} 个模型")
    print("使用示例: osm-deploy assess qwen3-32b")


def cmd_detect(args):
    """detect 子命令：自动检测本机硬件 + 推荐可部署模型"""
    from .data_sources.hardware_detect import (
        full_hardware_scan,
        recommend_models_for_hardware,
    )
    from .core.model_resolver import KNOWN_MODELS

    hw = full_hardware_scan()
    print("=" * 70)
    print("【本机硬件扫描】")
    print("=" * 70)
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
    recs.sort(key=lambda r: r["size_b"])

    print(f"\n{'模型':<32} {'规模':<8} {'精度':<22} {'框架':<25}")
    print("-" * 90)
    for r in recs[:15]:
        precision = r["deployable_quant"] or r["deployable_precision"] or "❌ 不适配"
        frameworks = " / ".join(r["frameworks"][:2])
        print(f"  {r['model']:<30} {r['size_b']:>5}B  {precision:<22} {frameworks}")

    print(f"\n总共 {len(recs)} 个模型可在本机部署")


def cmd_deploy(args):
    """deploy 子命令：生成部署脚本"""
    from .core.deployment_generator import generate_deploy_script
    from .data_sources.hardware_detect import full_hardware_scan
    from .core.model_resolver import KNOWN_MODELS

    if args.model not in KNOWN_MODELS:
        print(f"❌ 未知模型: {args.model}")
        print("用 'osm-deploy list' 查看支持的模型")
        return

    hw = full_hardware_scan()
    info = KNOWN_MODELS[args.model]
    framework = args.framework
    script = generate_deploy_script(args.model, info, hw, framework=framework)

    print(f"\n{'=' * 70}")
    print(f"【一键部署脚本】{args.model} ({script['framework']})")
    print(f"{'=' * 70}")
    print(f"\n[安装]")
    print(script["install_cmd"])
    print(f"\n[运行]")
    print(script["run_cmd"])
    if script.get("docker_cmd"):
        print(f"\n[Docker 备选]")
        print(script["docker_cmd"])
    print(f"\n[注意]")
    for n in script["notes"]:
        print(f"  - {n}")


def cmd_resolve(args):
    """resolve 子命令：只解析模型身份"""
    from .core.model_resolver import resolve_model
    result = resolve_model(args.model, force=args.force_refresh)
    # 精简输出
    print(json.dumps({
        "hf_repo": result["hf_repo"],
        "github": f'{result["github_org"]}/{result["github_repo"]}',
        "arxiv_id": result.get("arxiv_id"),
        "gguf_repo": result.get("gguf_repo"),
        "gguf_files_count": len(result.get("gguf_files", [])),
        "readme_chars": len(result.get("readme", "")),
        "has_arxiv": "arxiv_paper" in result,
    }, indent=2, ensure_ascii=False))


def cmd_gguf(args):
    """gguf 子命令：列出仓库 GGUF 文件及大小"""
    from .data_sources.huggingface import fetch_gguf_files, get_llamacpp_command
    files = fetch_gguf_files(args.repo, force=args.force_refresh)
    if not files:
        print(f"No GGUF files found in {args.repo}")
        return
    for f in files:
        marker = "🎯 MAIN" if f["is_main"] else "   proj "
        print(f'{marker}  {f["path"]:<60}  {f["size_gb"]:>6.2f} GB')
    # 列出可用的 llama-server 命令
    main_files = [f for f in files if f["is_main"]]
    print("\n推荐命令（基于 main 模型）:")
    for f in main_files[:5]:
        # 简单抽取 quant label
        import re
        m = re.search(r"(Q\d+_K(?:_[MSXL])?|Q\d+_\d|Q\d+_K|IQ\d+_[A-Z_]+)", f["path"], re.IGNORECASE)
        if m:
            quant = m.group(0)
            print(f"  llama-server -hf {args.repo}:{quant}")


def cmd_budget(args):
    """budget 子命令：按模型规模算 3 档预算"""
    from .data_sources.hardware_prices import estimate_3tier_budget
    budget = estimate_3tier_budget(args.size_b, args.context)
    print(json.dumps(budget, indent=2, ensure_ascii=False))
    print(f"\n模型规模: {args.size_b}B 参数, 上下文 {args.context}K")
    print(f"  入门档:  ¥{budget['entry']:,}")
    print(f"  标准档:  ¥{budget['standard']:,}")
    print(f"  高性能:  ¥{budget['high']:,}")


def cmd_cache_clear(args):
    """cache-clear 子命令：清缓存"""
    from .data_sources.cache import cache_clear
    if args.key:
        cache_clear(args.key)
        print(f"Cleared cache: {args.key}")
    else:
        cache_clear()
        print("Cleared ALL cache")


def main():
    parser = argparse.ArgumentParser(
        prog="open-source-model-deploy",
        description="开源大模型部署可行性鉴别 CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    p_list = sub.add_parser("list", help="列出所有支持的模型")
    p_list.add_argument("--category", help="按分类过滤：domestic-general/domestic-reasoning/international-dense/international-edge/code/vision/embedding/reranker")
    p_list.set_defaults(func=cmd_list)

    # detect
    p_detect = sub.add_parser("detect", help="自动检测本机硬件 + 推荐可部署模型")
    p_detect.set_defaults(func=cmd_detect)

    # deploy
    p_deploy = sub.add_parser("deploy", help="生成一键部署脚本")
    p_deploy.add_argument("model", help="模型名（如 qwen3-32b）")
    p_deploy.add_argument("--framework", default="auto",
                          choices=["auto", "vllm", "sglang", "ollama", "llama.cpp", "transformers"],
                          help="指定部署框架（默认 auto）")
    p_deploy.set_defaults(func=cmd_deploy)

    # assess
    p_assess = sub.add_parser("assess", help="5 步鉴别（模型→配置→部署→预算→报告）")
    p_assess.add_argument("model", help="模型名（如 deepseek-v3 或 org/repo）")
    p_assess.add_argument("--force-refresh", action="store_true", help="跳过缓存，强制刷新")
    p_assess.set_defaults(func=cmd_assess)

    # resolve
    p_resolve = sub.add_parser("resolve", help="只解析模型身份")
    p_resolve.add_argument("model", help="模型名")
    p_resolve.add_argument("--force-refresh", action="store_true")
    p_resolve.set_defaults(func=cmd_resolve)

    # gguf
    p_gguf = sub.add_parser("gguf", help="列出 GGUF 仓库文件")
    p_gguf.add_argument("repo", help="HF 仓库 ID，如 bartowski/Llama-3.2-3B-Instruct-GGUF")
    p_gguf.add_argument("--force-refresh", action="store_true")
    p_gguf.set_defaults(func=cmd_gguf)

    # budget
    p_budget = sub.add_parser("budget", help="按模型规模算 3 档预算")
    p_budget.add_argument("--size-b", type=float, required=True, help="模型总参数（B）")
    p_budget.add_argument("--context", type=int, default=128, help="上下文长度（K），默认 128")
    p_budget.set_defaults(func=cmd_budget)

    # cache-clear
    p_cache = sub.add_parser("cache-clear", help="清缓存")
    p_cache.add_argument("--key", help="指定 key；不传则清全部")
    p_cache.set_defaults(func=cmd_cache_clear)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

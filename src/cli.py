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
    include_retired = getattr(args, "all", False)

    # v1.0.3：退役模型默认不列出，与 list_models MCP 工具、知识库导出保持一致。
    # 此前这里把 retired 也算进"总计"，导致 CLI 说 136 而别处都说 135。
    retired = [(n, i) for n, i in KNOWN_MODELS.items() if i.get("status") == "retired"]
    models = (
        sorted(KNOWN_MODELS.items()) if include_retired
        else sorted((n, i) for n, i in KNOWN_MODELS.items() if i.get("status") != "retired")
    )

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
        "decision": "【决策模型 / System One】",
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
            flag = " [已退役]" if info.get("status") == "retired" else ""
            print(f"  {name:<25} {size_str:<10} {hf_repo:<45} {note}{flag}")

    print(f"\n总计: {len(models)} 个模型")
    if retired and not include_retired:
        for n, i in retired:
            print(f"⚠️ 另有 {len(retired)} 个已退役不计入："
                  f"{n} → {i.get('superseded_by') or '?'}（用 --all 查看）")
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

    # 计数只算「真的能跑」的。v1.0.3 之前这里错用了 len(recs)——那是全库条数，
    # 于是 6GB 显卡也会宣称「136 个模型可部署」，正是这次要消灭的那类误导。
    # 退役模型与 list_models 保持一致：不计入分母，单独提示。
    retired = [r for r in recs if r.get("status") == "retired"]
    live = [r for r in recs if r.get("status") != "retired"]
    runnable = [r for r in live if r.get("deployable_quant") or r.get("deployable_precision")]
    cpu_only = [r for r in runnable if "CPU" in (r.get("deployable_quant") or "")]

    line = f"\n可部署 {len(runnable)} / {len(live)} 个在架模型（其中 {len(cpu_only)} 个仅 CPU 慢速）"
    if retired:
        names = ", ".join(
            f"{r['model']} → {r.get('superseded_by') or '?'}" for r in retired
        )
        line += f"\n⚠️ 另有 {len(retired)} 个已退役不计入：{names}"
    print(line)


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

    # decision 类：先亮接口，再给命令 —— 否则用户不知道起完服务该问什么
    if script.get("decision"):
        form = script.get("form")
        endpoint = script.get("endpoint")
        port = script.get("port")
        if endpoint and port:
            print(f"\n[接口]  {endpoint}   →  http://localhost:{port}{endpoint}")
        elif form == "library":
            print(f"\n[接口]  进程内调用（无 REST 服务）")
        else:
            print(f"\n[接口]  ⚠️ 尚未核实")

    print(f"\n[安装]")
    print(script["install_cmd"])
    print(f"\n[运行]")
    print(script["run_cmd"])
    if script.get("docker_cmd"):
        print(f"\n[Docker 备选]")
        print(script["docker_cmd"])

    # decision 类：健康检查 + 真实请求示例
    if script.get("decision"):
        if script.get("health_cmd"):
            print(f"\n[健康检查]")
            print(script["health_cmd"])
        if script.get("example_curl"):
            print(f"\n[真实请求 · curl]")
            print(script["example_curl"])
        if script.get("example_python"):
            print(f"\n[真实请求 · Python]")
            print(script["example_python"])

    print(f"\n[注意]")
    for n in script["notes"]:
        print(f"  - {n}")


def cmd_ask(args):
    """ask 子命令：向决策模型提问（统一两种接口）"""
    from .core.decision_client import ask, render_answers, DecisionError

    # state
    state = args.state
    if args.state_file:
        if state:
            print("❌ --state 和 --state-file 只能给一个")
            return
        try:
            with open(args.state_file, encoding="utf-8") as f:
                state = f.read()
        except OSError as e:
            print(f"❌ 读不到 {args.state_file}: {e}")
            return
    if not state:
        print("❌ 需要 --state 或 --state-file 提供待判断的材料")
        return

    # 解析 "名称=选项1,选项2" 形式
    def parse_pairs(items, flag):
        out = {}
        for raw in items:
            if "=" not in raw:
                print(f"❌ {flag} 格式应为 \"名称=选项1,选项2\"，收到: {raw!r}")
                return None
            name, opts = raw.split("=", 1)
            vals = [o.strip() for o in opts.split(",") if o.strip()]
            if len(vals) < 2:
                print(f"❌ {flag} {name!r} 至少需要 2 个选项，收到 {len(vals)} 个")
                return None
            out[name.strip()] = vals
        return out

    choice = parse_pairs(args.choice, "--choice")
    if choice is None:
        return
    score = parse_pairs(args.score, "--score")
    if score is None:
        return

    try:
        result = ask(
            args.model,
            state=state,
            noul=args.noul or None,
            choice=choice or None,
            score=score or None,
            base_url=args.base_url,
            timeout=args.timeout,
            dry_run=args.dry_run,
        )
    except DecisionError as e:
        print(f"❌ {e}")
        return

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.dry_run:
        print(f"\n{'=' * 70}")
        print(f"【dry-run】{args.model} — 将发送 {len(result['requests'])} 个请求")
        print(f"{'=' * 70}")
        print(f"接口: {result['endpoint']}  body 格式: {result['body_format']}")
        for i, r in enumerate(result["requests"], 1):
            print(f"\n[{i}] POST {r['url']}")
            print("    " + json.dumps(r["body"], ensure_ascii=False)[:400])
        return

    print(f"\n{'=' * 70}")
    print(f"【决策结果】{args.model}")
    print(f"{'=' * 70}")
    print(render_answers(result))


def cmd_cost(args):
    """cost 子命令：本地一次性投入 vs 云租，含回本周期"""
    from .core.cost_model import compare_cost, render_cost, CostError
    from .core.model_resolver import KNOWN_MODELS

    if args.model not in KNOWN_MODELS:
        print(f"❌ 未知模型: {args.model}")
        print("用 'osm-deploy list' 查看支持的模型")
        return

    try:
        cost = compare_cost(
            KNOWN_MODELS[args.model],
            quant=args.quant,
            electricity_cny_per_kwh=args.electricity,
            hours_per_month=args.hours,
        )
    except CostError as e:
        print(f"❌ {e}")
        return

    if args.json:
        print(json.dumps(cost, indent=2, ensure_ascii=False))
        return

    print(f"\n{'=' * 72}")
    print(f"【成本对比】{args.model}")
    print(f"{'=' * 72}")
    print(render_cost(cost))
    print(f"\n[口径说明]")
    for c in cost.get("caveats", []):
        print(f"  - {c}")


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
    p_list.add_argument("--category", help="按分类过滤：domestic-general/domestic-reasoning/international-dense/international-edge/code/vision/embedding/reranker/decision")
    p_list.add_argument("--all", action="store_true",
                        help="包含已退役模型（默认排除）")
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

    # ask（决策模型统一客户端）
    p_ask = sub.add_parser(
        "ask",
        help="向决策模型提问（noul/choice/score 三原语，统一两种接口）",
        description="System One 决策模型统一调用：不管你用 /v1/decide 还是 "
                    "/v1/systemone 的模型，都走同一套参数。",
    )
    p_ask.add_argument("model", help="决策模型 slug（osm-deploy list --category decision）")
    p_ask.add_argument("--state", help="待判断的材料（文本）")
    p_ask.add_argument("--state-file", help="从文件读材料（与 --state 二选一）")
    p_ask.add_argument("--noul", action="append", default=[],
                       help='是非题，可重复：--noul "是否包含自动续约条款"')
    p_ask.add_argument("--choice", action="append", default=[],
                       help='选择题，可重复：--choice "风险等级=低,中,高"')
    p_ask.add_argument("--score", action="append", default=[],
                       help='打分题，可重复：--score "严重程度=无,轻微,严重"')
    p_ask.add_argument("--base-url", help="覆盖默认地址（默认 http://localhost:<端口>）")
    p_ask.add_argument("--timeout", type=float, default=60.0, help="单次请求超时秒数")
    p_ask.add_argument("--dry-run", action="store_true", help="只显示将发送的请求，不真发")
    p_ask.add_argument("--json", action="store_true", help="输出原始 JSON")
    p_ask.set_defaults(func=cmd_ask)

    # cost（本地 vs 云租成本对比）
    p_cost = sub.add_parser(
        "cost",
        help="本地一次性投入 vs 云租月成本 + 回本周期",
        description="按真实显存需求匹配卡型，算本地整机价与云租月费，给回本周期。"
                    "所有价格带出处，云租给区间（现货/按需）。",
    )
    p_cost.add_argument("model", help="模型名（如 autotrust-jev-9b）")
    p_cost.add_argument("--quant", default="Q4_K_M",
                        choices=["Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0", "FP8", "BF16"],
                        help="量化档位（默认 Q4_K_M）")
    p_cost.add_argument("--hours", type=float, default=None,
                        help="只看单一时长（小时/月）；不传则同时给 24×7 和 8h×22")
    p_cost.add_argument("--electricity", type=float, default=0.8,
                        help="电价（元/度，默认 0.8）")
    p_cost.add_argument("--json", action="store_true", help="输出 JSON")
    p_cost.set_defaults(func=cmd_cost)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

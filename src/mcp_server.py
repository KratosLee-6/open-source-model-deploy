"""
MCP Server 入口 - 让任何 Agent 通过 Model Context Protocol 调用
- 协议：stdio（标准 MCP 通信）
- 工具：assess / list_models / detect_hardware / recommend / deploy_script / cache_clear

启动方式：
    python -m src.mcp_server

配置（在 Claude/Codex 等支持 MCP 的客户端）:
    {
      "mcpServers": {
        "osm-deploy": {
          "command": "python",
          "args": ["-m", "src.mcp_server"]
        }
      }
    }
"""
import sys
import json
import asyncio
from typing import Any

# MCP 是可选依赖；没装也能用 HTTP 模式
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


from .core.assessor import full_assessment
from .core.model_resolver import KNOWN_MODELS
from .core import vram_requirements
from .core.deployment_generator import generate_deploy_script
from .data_sources.hardware_detect import (
    full_hardware_scan,
    recommend_models_for_hardware,
)
from .data_sources.cache import cache_clear as _cache_clear


# MCP 工具定义
TOOLS = [
    {
        "name": "assess_model",
        "description": "5 步鉴别开源大模型部署可行性（模型→配置→部署→预算→报告）。返回结构化 JSON 数据。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "模型名（deepseek-v3 / qwen3-32b / bartowski/Llama-3.2-3B-Instruct-GGUF 等）",
                },
                "force_refresh": {
                    "type": "boolean",
                    "description": "跳过 24h 缓存，强制刷新数据",
                    "default": False,
                },
            },
            "required": ["model"],
        },
    },
    {
        "name": "list_models",
        "description": (
            "列出支持的模型（136 个，分 8 类），每条附结构化显存需求（6 档量化）。"
            "传 max_vram_gb 可直接筛出「这台机器跑得动」的模型。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "过滤分类（domestic-general / domestic-reasoning / international-dense / international-edge / code / vision / embedding / reranker）",
                },
                "max_vram_gb": {
                    "type": "number",
                    "description": "按可用显存筛选，只返回该显存下放得下的模型（如 8 / 12 / 16 / 24）",
                },
                "quant": {
                    "type": "string",
                    "description": "判定 fit 时使用的量化档位",
                    "enum": list(vram_requirements.QUANT_LADDER),
                    "default": "Q4_K_M",
                },
                "include_retired": {
                    "type": "boolean",
                    "description": "是否包含已退役模型（默认排除）",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "detect_hardware",
        "description": "自动检测本机硬件（GPU/CPU/内存/硬盘），并推荐可部署的开源模型清单。",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "generate_deploy_script",
        "description": "为指定模型生成一键部署脚本（vLLM/SGLang/Ollama/llama.cpp）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "模型名",
                },
                "framework": {
                    "type": "string",
                    "description": "指定框架：vllm/sglang/ollama/llama.cpp/transformers/auto",
                    "default": "auto",
                },
            },
            "required": ["model"],
        },
    },
    {
        "name": "clear_cache",
        "description": "清除 24h 智能缓存，强制下次调用拉取最新数据。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "可选，指定某个 key；不传则清全部",
                },
            },
        },
    },
]


def _call_tool(name: str, arguments: dict) -> str:
    """同步执行工具，返回 JSON 字符串"""
    if name == "assess_model":
        result = full_assessment(arguments["model"], force=arguments.get("force_refresh", False))
        return json.dumps(result, ensure_ascii=False, default=str)

    elif name == "list_models":
        cat = arguments.get("category")
        # v1.0.3：支持按「我这台机器能跑什么」筛选，而不只是罗列
        max_vram = arguments.get("max_vram_gb")
        quant = arguments.get("quant", "Q4_K_M")
        include_retired = arguments.get("include_retired", False)

        models = sorted(KNOWN_MODELS.items())
        if cat:
            models = [(n, i) for n, i in models if i.get("category") == cat]

        out = []
        for n, i in models:
            status = i.get("status", "active")
            if status == "retired" and not include_retired:
                continue

            entry = {
                "name": n,
                "category": i.get("category"),
                "size_b": i.get("size_b"),
                "activated_b": i.get("activated_b"),
                "is_moe": vram_requirements.is_moe(i),
                "hf_repo": i.get("hf_repo"),
                "status": status,
                "note": i.get("note"),
            }
            if status == "retired":
                entry["superseded_by"] = i.get("superseded_by")

            # 附结构化显存数据（v1.0.3）——消费端一次拉全，不用逐个 assess
            if i.get("size_b"):
                prof = vram_requirements.model_vram_profile(n, i)
                entry["vram_gb_by_quant"] = prof["vram_gb_by_quant"]
                entry["min_vram"] = prof["min_vram"]
                if max_vram:
                    entry["fit"] = vram_requirements.fit_verdict(
                        vram_requirements.vram_requirement(i, quant=quant)["vram_required_gb"],
                        max_vram,
                    )
                    entry["quant_at_max_vram"] = vram_requirements.best_quant_for_vram(
                        i, max_vram
                    )
            out.append(entry)

        if max_vram:
            # 只保留放得下的（fit != no），并按 Q4 显存从小到大排——先看到能跑的
            out = [e for e in out if e.get("fit") != "no"]
            out.sort(key=lambda e: e.get("min_vram", {}).get("vram_min_gb", 1e9))

        return json.dumps(out, ensure_ascii=False)

    elif name == "detect_hardware":
        hw = full_hardware_scan()
        recs = recommend_models_for_hardware(hw, KNOWN_MODELS)
        # 退役模型不该出现在采购建议里，但保留一个单独的清单供追溯
        active = [r for r in recs if r.get("status") != "retired"]
        retired = [r for r in recs if r.get("status") == "retired"]
        runnable = [r for r in active if r.get("deployable_quant")]
        return json.dumps({
            "hardware": hw,
            "total_vram_gb": hw.get("total_vram_gb"),
            "deployable_tier": hw.get("deployable_tier"),
            "recommendations_count": len(active),
            "runnable_count": len(runnable),
            "top_recommendations": recs[:10],
            "excluded_retired": [
                {"model": r["model"], "superseded_by": r.get("superseded_by")}
                for r in retired
            ],
        }, ensure_ascii=False, default=str)

    elif name == "generate_deploy_script":
        model = arguments["model"]
        if model not in KNOWN_MODELS:
            return json.dumps({"error": f"Unknown model: {model}. Run list_models first."})
        hw = full_hardware_scan()
        framework = arguments.get("framework", "auto")
        info = KNOWN_MODELS[model]
        script = generate_deploy_script(model, info, hw, framework=framework)
        return json.dumps(script, ensure_ascii=False)

    elif name == "clear_cache":
        key = arguments.get("key")
        _cache_clear(key)
        return json.dumps({"cleared": "all" if not key else key})

    return json.dumps({"error": f"Unknown tool: {name}"})


# ============== MCP 模式 ==============

def run_mcp_server():
    """MCP stdio server"""
    if not HAS_MCP:
        print("MCP not installed. Run: pip install mcp", file=sys.stderr)
        print("Or use HTTP mode: python -m src.http_server", file=sys.stderr)
        sys.exit(1)

    app = Server("osm-deploy")

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return [Tool(**t) for t in TOOLS]

    @app.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        result = _call_tool(name, arguments or {})
        return [TextContent(type="text", text=result)]

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(main())


if __name__ == "__main__":
    run_mcp_server()

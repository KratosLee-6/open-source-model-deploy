"""
HTTP API Server - 任何 Agent/工具通过 HTTP 调用
- 跨平台兼容（任何语言都能调）
- 5 个端点：/assess /list /detect /deploy /cache-clear
- 同时支持 MCP（HTTP 桥接模式）

启动：
    pip install fastapi uvicorn
    python -m src.http_server

默认端口 8765
"""
import sys
import json

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def create_app():
    """创建 FastAPI app"""
    if not HAS_FASTAPI:
        print("FastAPI not installed. Run: pip install fastapi uvicorn", file=sys.stderr)
        sys.exit(1)

    app = FastAPI(
        title="osm-deploy API",
        description="开源大模型部署可行性鉴别 HTTP API",
        version="1.0.0",
    )

    # 复用 mcp_server 的 _call_tool
    from .mcp_server import _call_tool

    @app.get("/")
    async def root():
        return {
            "service": "osm-deploy",
            "version": "1.0.0",
            "endpoints": [
                "POST /assess - 5 步鉴别模型",
                "GET /list - 列出所有模型",
                "GET /detect - 硬件检测+推荐",
                "POST /deploy - 生成部署脚本",
                "POST /cache-clear - 清缓存",
            ],
        }

    @app.post("/assess")
    async def assess(body: dict):
        return JSONResponse(
            content=json.loads(_call_tool("assess_model", body))
        )

    @app.get("/list")
    async def list_models(category: str = None):
        args = {"category": category} if category else {}
        return JSONResponse(
            content=json.loads(_call_tool("list_models", args))
        )

    @app.get("/detect")
    async def detect():
        return JSONResponse(
            content=json.loads(_call_tool("detect_hardware", {}))
        )

    @app.post("/deploy")
    async def deploy(body: dict):
        return JSONResponse(
            content=json.loads(_call_tool("generate_deploy_script", body))
        )

    @app.post("/cache-clear")
    async def cache_clear(body: dict = {}):
        return JSONResponse(
            content=json.loads(_call_tool("clear_cache", body))
        )

    return app


def main():
    if not HAS_FASTAPI:
        print("Install: pip install fastapi uvicorn")
        sys.exit(1)
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")


if __name__ == "__main__":
    main()

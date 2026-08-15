"""
HuggingFace Hub API 封装
- 模型元数据（tags、license、参数规模）
- GGUF 仓库文件列表（含精确文件大小）
- 支持 llama.cpp 本地应用模式 URL
文档: https://huggingface.co/docs/hub/api
"""
import urllib.request
import urllib.error
import json
from typing import Any, Dict, List, Optional

from .cache import cached_fetch

HF_API_BASE = "https://huggingface.co/api"
# 国内镜像支持（默认走官方，超时自动 fallback）
HF_MIRRORS = [
    "https://hf-mirror.com/api",  # 国内常用镜像
]
HF_RAW_BASE = "https://huggingface.co"
HF_RAW_MIRRORS = [
    "https://hf-mirror.com",
]


def _http_get_json(url: str, timeout: int = 15) -> Any:
    """带 UA 的 GET 请求，自动尝试镜像 fallback"""
    bases = [HF_API_BASE] + HF_MIRRORS
    last_err = None
    for base in bases:
        try_url = url.replace(HF_API_BASE, base)
        req = urllib.request.Request(try_url, headers={"User-Agent": "open-source-model-deploy/0.2"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            last_err = e
            continue
    raise RuntimeError(f"HF API network error after trying {len(bases)} mirrors: {last_err}")


def fetch_model_metadata(repo_id: str, force: bool = False) -> Dict[str, Any]:
    """拉取 HF 模型元数据

    字段: id, tags, license, downloads, likes, last_modified, ...
    """
    key = f"hf:meta:{repo_id}"
    return cached_fetch(
        key,
        lambda: _http_get_json(f"{HF_API_BASE}/models/{repo_id}"),
        force=force,
    )


def fetch_gguf_files(repo_id: str, force: bool = False) -> List[Dict[str, Any]]:
    """列出仓库内所有 GGUF 文件（含字节大小）

    过滤: type=='file' && path endswith '.gguf'
    排除: mmproj-*.gguf (投影器)
    """
    key = f"hf:gguf:{repo_id}"
    files = cached_fetch(
        key,
        lambda: _http_get_json(
            f"{HF_API_BASE}/models/{repo_id}/tree/main?recursive=true"
        ),
        force=force,
    )
    return [
        {
            "path": f["path"],
            "size_bytes": f.get("size", 0),
            "size_gb": round(f.get("size", 0) / 1024**3, 2),
            "is_main": not f["path"].startswith("mmproj"),
            "is_projector": f["path"].startswith("mmproj"),
        }
        for f in files
        if f.get("type") == "file" and f["path"].endswith(".gguf")
    ]


def fetch_model_readme(repo_id: str, force: bool = False) -> str:
    """拉取模型 README 原文（markdown）"""
    key = f"hf:readme:{repo_id}"
    def _fetch():
        bases = [HF_RAW_BASE] + HF_RAW_MIRRORS
        for base in bases:
            url = f"{base}/{repo_id}/raw/main/README.md"
            req = urllib.request.Request(url, headers={"User-Agent": "open-source-model-deploy/0.2"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.read().decode("utf-8", errors="replace")
            except (urllib.error.HTTPError, urllib.error.URLError):
                continue
        return ""
    return cached_fetch(key, _fetch, force=force)


def get_llamacpp_command(repo_id: str, quant_label: str) -> str:
    """构造 llama.cpp 直接加载命令

    例: llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
    """
    return f"llama-server -hf {repo_id}:{quant_label}"


def get_local_app_url(repo_id: str) -> str:
    """HF llama.cpp 本地应用页 URL（含量化推荐）"""
    return f"https://huggingface.co/{repo_id}?local-app=llama.cpp"


def extract_quant_size_from_name(filename: str) -> Optional[str]:
    """从文件名提取量化标签，如 Q4_K_M、IQ4_XS、Q8_0"""
    import re
    m = re.search(r"(Q\d+_K(?:_[MSXL])?|Q\d+_\d|Q\d+_K|IQ\d+_[A-Z_]+|UD-Q\d+_K_[MSXL])", filename, re.IGNORECASE)
    return m.group(0) if m else None

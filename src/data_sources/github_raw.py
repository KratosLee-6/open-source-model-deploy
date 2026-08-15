"""
GitHub raw 抓取：官方 README、LICENSE、CITATION
"""
import urllib.request
import urllib.error
from typing import Optional

from .cache import cached_fetch


def fetch_raw(url: str, force: bool = False, timeout: int = 20) -> str:
    """拉取 GitHub raw 文件内容

    常见用法:
    - https://raw.githubusercontent.com/deepseek-ai/DeepSeek-V3/main/README.md
    - https://raw.githubusercontent.com/deepseek-ai/DeepSeek-V3/main/LICENSE-MODEL
    """
    key = f"github:{url}"
    def _fetch():
        req = urllib.request.Request(url, headers={"User-Agent": "open-source-model-deploy/0.2"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""
            raise RuntimeError(f"GitHub raw HTTP {e.code}: {url}") from e
    return cached_fetch(key, _fetch, force=force)


def parse_repo_from_url(url: str) -> tuple[str, str]:
    """从 raw URL 解析 (org, repo)，如 deepseek-ai/DeepSeek-V3"""
    import re
    m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/", url)
    if not m:
        raise ValueError(f"Invalid GitHub raw URL: {url}")
    return m.group(1), m.group(2)


def fetch_repo_readme(org: str, repo: str, branch: str = "main", force: bool = False) -> str:
    """便捷方法：抓取仓库 README"""
    return fetch_raw(
        f"https://raw.githubusercontent.com/{org}/{repo}/{branch}/README.md",
        force=force,
    )


def fetch_repo_license(org: str, repo: str, branch: str = "main", force: bool = False) -> Optional[str]:
    """抓取 LICENSE 内容"""
    content = fetch_raw(
        f"https://raw.githubusercontent.com/{org}/{repo}/{branch}/LICENSE",
        force=force,
    )
    return content or None

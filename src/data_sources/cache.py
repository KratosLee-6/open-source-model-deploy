"""
智能缓存层：TTL=24h，避免每次调用都拉网络
- 文件缓存：~/.cache/open-source-model-deploy/{key}.json
- TTL=24h，过期自动重新拉取
- 支持 force_refresh=True 强制刷新
"""
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path.home() / ".cache" / "open-source-model-deploy"
CACHE_TTL = 86400  # 24 hours


def _cache_path(key: str) -> Path:
    """生成缓存文件路径"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    hashed = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{hashed}.json"


def cache_get(key: str, ttl: int = CACHE_TTL) -> Optional[Any]:
    """读取缓存，过期返回 None"""
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data.get("_ts", 0) > ttl:
            return None
        return data.get("value")
    except Exception:
        return None


def cache_set(key: str, value: Any) -> None:
    """写入缓存，带时间戳"""
    path = _cache_path(key)
    path.write_text(
        json.dumps({"_ts": time.time(), "value": value}, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def cache_clear(key: Optional[str] = None) -> None:
    """清除缓存（全部 or 指定 key）"""
    if key is None:
        if CACHE_DIR.exists():
            for p in CACHE_DIR.glob("*.json"):
                p.unlink()
        return
    path = _cache_path(key)
    if path.exists():
        path.unlink()


def cached_fetch(key: str, fetcher, ttl: int = CACHE_TTL, force: bool = False):
    """通用带缓存的拉取逻辑

    Args:
        key: 缓存键（建议含数据源+目标，如 "hf:deepseek-ai/DeepSeek-V3"）
        fetcher: 无参函数，返回原始数据
        ttl: 过期秒数
        force: True 跳过缓存强制刷新
    """
    if not force:
        hit = cache_get(key, ttl)
        if hit is not None:
            return hit
    value = fetcher()
    cache_set(key, value)
    return value

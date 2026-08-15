"""
arXiv API：拉取官方论文
- 论文标题、摘要、作者、PDF URL
文档: https://info.arxiv.org/help/api/basics.html
"""
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from .cache import cached_fetch

ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def search_by_title(title: str, max_results: int = 3, force: bool = False) -> List[Dict[str, Any]]:
    """按标题搜索 arXiv 论文"""
    key = f"arxiv:title:{title}:{max_results}"
    def _fetch():
        params = {
            "search_query": f'ti:"{title}"',
            "max_results": max_results,
            "sortBy": "relevance",
        }
        url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "open-source-model-deploy/0.2"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            root = ET.fromstring(resp.read())
        return _parse_entries(root)
    return cached_fetch(key, _fetch, force=force)


def fetch_by_id(arxiv_id: str, force: bool = False) -> Dict[str, Any]:
    """按 arXiv ID 抓论文"""
    key = f"arxiv:id:{arxiv_id}"
    def _fetch():
        url = f"{ARXIV_API}?id_list={arxiv_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "open-source-model-deploy/0.2"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            root = ET.fromstring(resp.read())
        entries = _parse_entries(root)
        return entries[0] if entries else {}
    return cached_fetch(key, _fetch, force=force)


def _parse_entries(root: ET.Element) -> List[Dict[str, Any]]:
    """解析 arXiv API 返回的 XML"""
    results = []
    for entry in root.findall("atom:entry", NS):
        eid = entry.find("atom:id", NS)
        title = entry.find("atom:title", NS)
        summary = entry.find("atom:summary", NS)
        published = entry.find("atom:published", NS)
        authors = [
            a.find("atom:name", NS).text
            for a in entry.findall("atom:author", NS)
            if a.find("atom:name", NS) is not None
        ]
        # arxiv:primary_category 等扩展
        results.append({
            "id": eid.text.split("/abs/")[-1] if eid is not None else "",
            "url": eid.text if eid is not None else "",
            "title": title.text.strip() if title is not None else "",
            "summary": summary.text.strip() if summary is not None else "",
            "published": published.text if published is not None else "",
            "authors": authors,
        })
    return results

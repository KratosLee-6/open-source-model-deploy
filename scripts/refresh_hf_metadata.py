"""
GitHub Actions Step 1: 刷新 HuggingFace 模型元数据

功能：
1. 从 src/core/model_resolver.py 读 KNOWN_MODELS
2. 对每个模型调 HF API 拉元数据（tags/license/downloads/last_modified/GGUF files）
3. 输出 data/hf-metadata-snapshot.json（保留所有原始字段）
4. 输出 references/hf-models-snapshot.md（人类可读表格）

用法：
  python3 scripts/refresh_hf_metadata.py [--force] [--only=name1,name2]

输出：
  data/hf-metadata-snapshot.json       完整元数据快照
  references/hf-models-snapshot.md     人类可读报告

依赖：仅 Python 标准库
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

# Paths
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_RESOLVER = os.path.join(REPO_ROOT, "src", "core", "model_resolver.py")
DATA_DIR = os.path.join(REPO_ROOT, "data")
REFS_DIR = os.path.join(REPO_ROOT, "references")
SNAPSHOT_JSON = os.path.join(DATA_DIR, "hf-metadata-snapshot.json")
SNAPSHOT_MD = os.path.join(REFS_DIR, "hf-models-snapshot.md")

HF_API_BASE = "https://huggingface.co/api"
HF_MIRROR = "https://hf-mirror.com/api"
TIMEOUT = 20
RATE_LIMIT_SEC = 0.3  # HF API 限速保护


def http_get_json(url: str, timeout: int = TIMEOUT) -> tuple:
    """带镜像 fallback 的 GET。返回 (data, source_url)"""
    bases = [url]
    if HF_API_BASE in url:
        bases.append(url.replace(HF_API_BASE, HF_MIRROR))
    last_err = None
    for try_url in bases:
        req = urllib.request.Request(try_url, headers={"User-Agent": "osm-deploy-gh/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8")), try_url
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            last_err = e
            continue
    return None, str(last_err)


def parse_resolver() -> dict:
    """从 model_resolver.py 提取 KNOWN_MODELS（与 auto_expand_models.py 同样的解析）"""
    with open(MODEL_RESOLVER, encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"KNOWN_MODELS[^=]*=\s*\{(.+?)\n\}\n", content, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    entry_starts = list(re.finditer(r'^\s*"([^"]+)":\s*\{', block, re.MULTILINE))
    result = {}
    for i, em in enumerate(entry_starts):
        name = em.group(1)
        next_start = entry_starts[i + 1].start() if i + 1 < len(entry_starts) else len(block)
        chunk = block[em.end():next_start]
        m_hf = re.search(r'"hf_repo":\s*"([^"]+)"', chunk)
        m_gh = re.search(r'"github":\s*"([^"]+)"', chunk)
        m_cat = re.search(r'"category":\s*"([^"]+)"', chunk)
        m_sz = re.search(r'"size_b":\s*([\d.]+)', chunk)
        m_act = re.search(r'"activated_b":\s*([\d.]+)', chunk)
        m_note = re.search(r'"note":\s*"([^"]+)"', chunk)
        if m_hf:
            result[name] = {
                "hf_repo": m_hf.group(1),
                "github": m_gh.group(1) if m_gh else "",
                "category": m_cat.group(1) if m_cat else "",
                "size_b": float(m_sz.group(1)) if m_sz else 0,
                "activated_b": float(m_act.group(1)) if m_act else None,
                "note": m_note.group(1) if m_note else "",
            }
    return result


def fetch_repo_meta(repo_id: str) -> dict | None:
    """拉 HF 模型元数据"""
    data, _ = http_get_json(f"{HF_API_BASE}/models/{repo_id}")
    return data


def fetch_gguf_files(repo_id: str) -> list:
    """列出 GGUF 文件清单（带字节大小）"""
    data, _ = http_get_json(f"{HF_API_BASE}/models/{repo_id}/tree/main?recursive=true")
    if not isinstance(data, list):
        return []
    return [
        {
            "path": f["path"],
            "size_bytes": f.get("size", 0),
            "size_gb": round(f.get("size", 0) / 1024**3, 2) if f.get("size", 0) else 0,
        }
        for f in data
        if isinstance(f, dict)
        and f.get("type") == "file"
        and f["path"].endswith(".gguf")
        and not f["path"].startswith("mmproj")
    ]


def fetch_recommended_hardware(repo_id: str) -> dict | None:
    """从 HF model card README.md + vLLM recipes 解析"官方推荐硬件"段。

    策略：
      1. 抓主 README.md + inference/README.md（DeepSeek 家族风格）
      2. 找以下关键字：
         - "Hardware Requirements" / "Hardware" / "Prerequisites" 段
         - 提到 H100/H200/A100/RTX/GB200/MI300/vRAM/V100/TPU/节点
         - vLLM recipe（recipes.vllm.ai/<repo>）—— 权威第三方部署文档
    返回精简结构：{
      "official_source": "HF model card" | "inference/README.md" | "vLLM recipe" | None,
      "recommended_gpu": ["GB200", "H200"],   # 提及的 GPU 型号
      "recommended_memory_gb": [...],         # 显存/内存数字
      "recommended_nodes": [...],             # 节点数量
      "raw_excerpt": "...原始段摘录..."
    }
    """
    # 1. 先抓主 README + inference/README
    readme_urls = [
        f"https://huggingface.co/{repo_id}/raw/main/README.md",
        f"https://huggingface.co/{repo_id}/raw/main/inference/README.md",
        f"https://huggingface.co/{repo_id}/raw/main/inference.md",
        f"https://huggingface.co/{repo_id}/raw/main/DEPLOYMENT.md",
    ]
    readme_text = ""
    source = None
    for u in readme_urls:
        bases = [u, u.replace("huggingface.co", "hf-mirror.com")]
        for try_url in bases:
            req = urllib.request.Request(try_url, headers={"User-Agent": "osm-deploy-gh/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    readme_text += "\n\n" + resp.read().decode("utf-8")
                source = u.split("/")[-1]
                break
            except Exception:
                continue
        if readme_text:
            break

    # 2. 抓 vLLM recipe（权威第三方部署文档）—— 给大型 MoE / 闭源/前沿模型很有用
    vllm_recipe_text = ""
    vllm_url = f"https://recipes.vllm.ai/{repo_id}"
    try:
        req = urllib.request.Request(vllm_url, headers={"User-Agent": "osm-deploy-gh/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            vllm_recipe_text = resp.read().decode("utf-8")
        if source is None:
            source = "vLLM recipe"
        else:
            source = f"{source} + vLLM recipe"
    except Exception:
        pass

    combined_text = readme_text + "\n\n" + vllm_recipe_text

    if not combined_text.strip():
        return None

    # 3. 找 hardware 段
    gpu_pat = re.compile(
        r"\b(H100|H200|A100|B200|GB200|MI300(?:X)?|RTX\s?\d{4}|V100|TPU\s?v\d+|H800|L40S|L4)\b"
    )
    # 提取"Hardware"/"Prerequisites"/"Memory"/"Serving" 段
    section_pat = re.compile(
        r"^##\s+([^#\n]+?(?:Hardware|Requirements|Prerequisites|Memory|Serving|Inference|Deployment)[^#\n]*?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    sections = section_pat.split(combined_text)
    # sections = [pre, title1, body1, title2, body2, ...]
    hardware_text = ""
    if len(sections) >= 3:
        for i in range(1, len(sections), 2):
            title = sections[i].strip()
            body = sections[i + 1] if i + 1 < len(sections) else ""
            if any(kw in title.lower() for kw in ["hardware", "prerequisites", "memory", "requirements", "deployment"]):
                hardware_text += f"\n## {title}\n{body[:1500]}"

    # 4. 扫整文抓 GPU 型号（可能 hardware 段没 ## 标记）
    gpus_in_hardware = sorted(set(gpu_pat.findall(hardware_text)))
    gpus_in_full = sorted(set(gpu_pat.findall(combined_text)))

    # 5. 抓显存/内存数字 + 单位（GB/GiB/TB/TiB）
    mem_pat = re.compile(
        r"(\d+(?:\.\d+)?)\s*(GB|GiB|TB|TiB)\b[^.\n]{0,80}?(?:VRAM|memory|HBM|GPU memory)",
        re.IGNORECASE,
    )
    mem_match = mem_pat.findall(combined_text[:5000])

    # 6. 节点数量（如 "8 GPUs" / "1×8 H200"）
    node_pat = re.compile(
        r"(\d+\s*[×x]\s*\d+\s*(?:GPU|H100|H200|A100|GB200|B200|MI300))", re.IGNORECASE
    )
    nodes = node_pat.findall(combined_text[:5000])

    # 7. 抓 vLLM recipe 的 vram_minimum_gb（最直接的官方推荐硬件数字）
    #    注意：vLLM recipe 页面顶部 model description 里的值最权威（页面后部的 JSON 是侧边栏推荐其他模型）
    #    格式可能是：
    #      - <code>vram_minimum_gb: 614</code>      # markdown 转 HTML
    #      - "vram_minimum_gb":614                  # 原始 JSON
    vram_min = None
    if vllm_recipe_text:
        header = vllm_recipe_text[:250000]
        # 宽松匹配：可选引号 + 可选空格
        vram_match = re.search(r'vram_minimum_gb[^0-9]*?(\d+(?:\.\d+)?)', header)
        if vram_match:
            vram_min = float(vram_match.group(1))

    # 8. 抓 vLLM recipe 的硬件推荐段
    vllm_hw_excerpt = ""
    if vllm_recipe_text:
        # 找 "Fills a GB200" / "1×8 H200" / "vram_minimum_gb" 周围上下文
        for kw in ["GB200 NVL4", "H200", "vram_minimum_gb", "Hardware"]:
            idx = vllm_recipe_text.find(kw)
            if idx > 0:
                s = max(0, idx - 100)
                e = min(len(vllm_recipe_text), idx + 400)
                vllm_hw_excerpt += f"\n--- {kw} ---\n{vllm_recipe_text[s:e]}\n"
                break

    return {
        "official_source": source or "unknown",
        "section_count": len(sections) // 2,
        "hardware_section_found": bool(hardware_text),
        "recommended_gpu": gpus_in_hardware if gpus_in_hardware else gpus_in_full[:8],
        "recommended_memory_gb": [f"{n[0]} {n[1]}" for n in mem_match[:3]],
        "recommended_nodes": nodes[:3],
        "vram_minimum_gb": vram_min,  # vLLM recipe 直接给的官方最小显存
        "raw_excerpt": (hardware_text[:500] if hardware_text else vllm_hw_excerpt or "(未找到)"),
    }


def refresh_all(only: list | None = None) -> dict:
    """刷新所有（或指定）模型的元数据"""
    models = parse_resolver()
    if only:
        models = {k: v for k, v in models.items() if k in only}
    print(f"[refresh_hf_metadata] 共 {len(models)} 个模型待刷新")

    snapshot = {
        "snapshot_at": datetime.now().isoformat(timespec="seconds"),
        "snapshot_source": "GitHub Actions / auto refresh",
        "model_count": len(models),
        "models": {},
    }
    ok = 0
    fail = 0
    for i, (name, info) in enumerate(models.items(), 1):
        repo = info["hf_repo"]
        print(f"  [{i:2}/{len(models)}] {name} → {repo}", end=" ... ", flush=True)
        meta = fetch_repo_meta(repo)
        if not meta:
            print("FAILED (network)")
            snapshot["models"][name] = {
                "hf_repo": repo, "error": "fetch failed",
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                **info,
            }
            fail += 1
            time.sleep(RATE_LIMIT_SEC)
            continue
        # 简化字段
        clean = {
            "hf_repo": repo,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "id": meta.get("id"),
            "tags": meta.get("tags", []),
            "license": meta.get("cardData", {}).get("license") or _extract_license(meta),
            "downloads": meta.get("downloads", 0),
            "likes": meta.get("likes", 0),
            "last_modified": meta.get("lastModified"),
            "pipeline_tag": meta.get("pipeline_tag"),
            "gguf_files": fetch_gguf_files(repo)[:10],  # 最多 10 个 GGUF
            **info,  # 保留 model_resolver 的本地元数据
        }
        # 自动解析官方推荐硬件（仅 large 模型 > 30B 拉取，避免小模型浪费时间）
        if (info.get("size_b") or 0) >= 30:
            try:
                rec = fetch_recommended_hardware(repo)
                if rec:
                    clean["recommended_hardware"] = rec
            except Exception as e:
                clean["recommended_hardware"] = {"official_source": "parse failed", "error": str(e)}
        snapshot["models"][name] = clean
        ok += 1
        hw_info = ""
        if "recommended_hardware" in clean and clean["recommended_hardware"].get("recommended_gpu"):
            hw_info = f" [hw: {'/'.join(clean['recommended_hardware']['recommended_gpu'][:2])}]"
        print(f"OK (downloads={clean['downloads']:,}, gguf={len(clean['gguf_files'])}){hw_info}")
        time.sleep(RATE_LIMIT_SEC)

    print(f"\n[refresh_hf_metadata] 完成: {ok} OK, {fail} FAIL")
    return snapshot


def _extract_license(meta: dict) -> str | None:
    """从 tags 提取 license（HF 常见 tag: license:mit / license:apache-2.0 等）"""
    tags = meta.get("tags", [])
    for t in tags:
        if t.startswith("license:"):
            return t.replace("license:", "")
    return None


def write_outputs(snapshot: dict):
    """写 JSON + Markdown 输出"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REFS_DIR, exist_ok=True)

    # 1. JSON（完整快照，给代码用）
    with open(SNAPSHOT_JSON, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"[refresh_hf_metadata] JSON 写入: {SNAPSHOT_JSON}")

    # 2. Markdown 表格（人类可读）
    lines = [
        f"# HF 模型元数据快照 · {snapshot['snapshot_at']}",
        "",
        f"> 自动生成：`python3 scripts/refresh_hf_metadata.py`",
        f"> 数据源：HuggingFace Hub API（自动 fallback hf-mirror.com）",
        f"> 覆盖：{snapshot['model_count']} 个模型",
        "",
        "| 模型 | HF Repo | 类别 | 大小(B) | License | Downloads | Likes | Last Modified | GGUF 数量 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, m in snapshot["models"].items():
        if m.get("error"):
            lines.append(f"| {name} | `{m['hf_repo']}` | {m.get('category','-')} | - | - | **FETCH ERROR** | - | - | - |")
            continue
        lines.append(
            f"| {name} | `{m['hf_repo']}` | {m.get('category','-')} | "
            f"{m.get('size_b','-')} | {m.get('license') or '-'} | "
            f"{m.get('downloads',0):,} | {m.get('likes',0)} | "
            f"{(m.get('last_modified') or '-')[:10]} | {len(m.get('gguf_files',[]))} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 引用方式",
        "",
        "```python",
        "import json",
        f"with open('data/hf-metadata-snapshot.json', encoding='utf-8') as f:",
        "    snapshot = json.load(f)",
        "",
        "# 拿某模型最新下载数",
        "deepseek_v3 = snapshot['models']['deepseek-v3']",
        "print(deepseek_v3['downloads'], deepseek_v3['likes'])",
        "```",
        "",
        "## 自动刷新",
        "",
        "由 `.github/workflows/refresh-models.yml` 每周一北京时间 8:00 自动执行。",
        "也可手动触发：Actions → Refresh Models Data → Run workflow。",
    ])

    with open(SNAPSHOT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[refresh_hf_metadata] Markdown 写入: {SNAPSHOT_MD}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="强制刷新（默认行为，目前没用，留作扩展）")
    parser.add_argument("--only", help="只刷指定模型，逗号分隔")
    args = parser.parse_args()

    only = args.only.split(",") if args.only else None
    snapshot = refresh_all(only)
    write_outputs(snapshot)

    # 退出码
    fail_count = sum(1 for m in snapshot["models"].values() if m.get("error"))
    if fail_count > snapshot["model_count"] / 2:
        print(f"FAIL: 失败率过高 ({fail_count}/{snapshot['model_count']})")
        sys.exit(1)
    print("OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
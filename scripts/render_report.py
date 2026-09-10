"""
GitHub Actions Step 3: 渲染最终部署建议报告

功能：
1. 读 data/hf-metadata-snapshot.json（HF 模型最新元数据）
2. 读 data/gpu-prices-snapshot.json（GPU 最新价格）
3. 综合两者 + src/core/model_resolver.py 的 size_b + activated_b
4. 生成 references/deployment-recommendations-{date}.md（按预算分桶）
5. 覆盖最新版本 references/deployment-recommendations.md

用法：
  python3 scripts/render_report.py [--target=default|consumer-gpu|studio|cloud]

输出：
  references/deployment-recommendations.md          (latest)
  references/deployment-recommendations-{YYYY-MM-DD}.md

依赖：仅 Python 标准库
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
REFS_DIR = os.path.join(REPO_ROOT, "references")
MODEL_RESOLVER = os.path.join(REPO_ROOT, "src", "core", "model_resolver.py")

HF_JSON = os.path.join(DATA_DIR, "hf-metadata-snapshot.json")
GPU_JSON = os.path.join(DATA_DIR, "gpu-prices-snapshot.json")
LATEST_OUT = os.path.join(REFS_DIR, "deployment-recommendations.md")


def parse_resolver() -> dict:
    """提取 KNOWN_MODELS（与 refresh_hf_metadata.py 同样逻辑）"""
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
        m_cat = re.search(r'"category":\s*"([^"]+)"', chunk)
        m_sz = re.search(r'"size_b":\s*([\d.]+)', chunk)
        m_act = re.search(r'"activated_b":\s*([\d.]+)', chunk)
        m_note = re.search(r'"note":\s*"([^"]+)"', chunk)
        if m_hf:
            result[name] = {
                "hf_repo": m_hf.group(1),
                "category": m_cat.group(1) if m_cat else "",
                "size_b": float(m_sz.group(1)) if m_sz else 0,
                "activated_b": float(m_act.group(1)) if m_act else None,
                "note": m_note.group(1) if m_note else "",
            }
    return result


def load_json(path: str, default=None) -> dict:
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def classify_by_size(size_b: float, target: str) -> str:
    """根据 size_b + target 返回档位"""
    if target == "default":  # 笔记本 16GB
        if size_b <= 3:
            return "✓ CPU 即可"
        elif size_b <= 8:
            return "⚠ Q4 量化（4-8GB）"
        else:
            return "❌ 需 GPU"
    elif target == "consumer-gpu":  # RTX 4090 24GB
        if size_b <= 9:
            return f"✓ FP16 ({size_b*2:.0f}GB 1× 4090)"
        elif size_b <= 32:
            return f"⚠ Q4 量化 ({size_b*0.5:.0f}GB 1× 4090)"
        else:
            return "❌ 需云租 H100"
    elif target == "studio":  # 2× 4090 / A100 80G
        if size_b <= 70:
            return f"✓ FP16 ({size_b*2:.0f}GB A100)"
        else:
            return "❌ 需云租"
    elif target == "cloud":
        return f"✓ 云租 ({size_b*2:.0f}GB fp16)"
    return "?"


def recommend_framework(size_b: float, target: str) -> str:
    """推荐框架"""
    if target == "default":
        return "llama.cpp / Ollama" if size_b <= 8 else "vLLM / 云租"
    elif target == "consumer-gpu":
        return "vLLM / llama.cpp"
    elif target == "studio":
        return "vLLM / SGLang"
    else:
        return "vLLM"


def render(models: dict, hf_data: dict, gpu_data: dict, target: str = "default") -> str:
    """渲染 Markdown 报告"""
    scenarios = {
        "default": "常规笔记本 16GB / 无独显",
        "consumer-gpu": "RTX 4090 (24GB)",
        "studio": "2× RTX 4090 / A100 80G",
        "cloud": "云租按量（H100/A100）",
    }
    target_name = scenarios.get(target, target)

    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    hf_at = hf_data.get("snapshot_at", "未知") if hf_data else "未知"
    gpu_at = gpu_data.get("snapshot_at", "未知") if gpu_data else "未知"

    lines = [
        f"# 47 个开源模型部署建议 · {today} 自动生成",
        "",
        f"> **目标场景**: {target_name}",
        f"> **HF 元数据快照**: {hf_at}",
        f"> **GPU 价格快照**: {gpu_at}",
        f"> **生成方式**: GitHub Actions 每周自动跑 (`scripts/render_report.py`)",
        f"> **手动重生成**: `python3 scripts/render_report.py --target={target}`",
        "",
        "---",
        "",
        "## 内存估算公式",
        "",
        "- **fp16** = `2 × size_b` GB",
        "- **Q4 量化** ≈ `0.5 × size_b` GB",
        "- **MoE**: fp16 按 total size 算，推理激活 `activated_b`",
        "",
        "---",
        "",
    ]

    # 按 category 分组
    categories = ["domestic-general", "domestic-reasoning", "code", "vision",
                  "international-dense", "international-edge", "embedding", "reranker"]

    cat_names_zh = {
        "domestic-general": "🟢 国内通用",
        "domestic-reasoning": "🧠 国内推理",
        "code": "💻 代码专用",
        "vision": "👁️ 视觉多模态",
        "international-dense": "🌍 国际密集",
        "international-edge": "⚡ 国际边缘",
        "embedding": "🔢 Embedding",
        "reranker": "📊 Reranker",
    }

    for cat in categories:
        cat_models = [(n, m) for n, m in models.items() if m["category"] == cat]
        if not cat_models:
            continue
        lines.append(f"\n## {cat_names_zh.get(cat, cat)} ({len(cat_models)} 个)\n")
        lines.append("| 模型 | HF Repo | size | Downloads | 档位 | 框架 |")
        lines.append("|---|---|---|---|---|---|")
        for name, m in sorted(cat_models, key=lambda x: x[1]["size_b"]):
            hf = hf_data.get("models", {}).get(name, {}) if hf_data else {}
            downloads = hf.get("downloads", "N/A")
            if isinstance(downloads, int):
                downloads = f"{downloads:,}"
            tier = classify_by_size(m["size_b"], target)
            frame = recommend_framework(m["size_b"], target)
            lines.append(
                f"| {name} | `{m['hf_repo']}` | {m['size_b']}B | {downloads} | {tier} | {frame} |"
            )

    lines.extend([
        "\n---\n",
        "## 🎯 实战推荐组合（按预算）\n",
        "| 预算 | 推荐方案 |",
        "|---|---|",
        "| **0 元**（笔记本）| deepseek-r1-distill-qwen-1.5b + bge-m3 + bge-reranker-v2-m3 |",
        "| **$500-800** | RTX 5060 Ti 16GB（一次性）+ qwen3-8b + deepseek-r1-distill-qwen-14b |",
        "| **$1000-1500** | RTX 5080 16GB（一次性）+ qwen3-32b + qwen2.5-vl-7b |",
        "| **$2000-2500** | RTX 5090 32GB（一次性）+ qwen3-32b FP16 + qwen3-235b Q4 |",
        "| **$150-500/月** | AutoDL RTX 4090 单卡按需 |",
        "| **$3000-7000/月** | AutoDL/A100 80GB 包月 |",
        "| **$7000-30000/月** | 阿里云 GPU gn7/gn8（8× A100/H100）|",
        "",
        "---",
        "",
        f"**快照时间**: {today}",
        f"**下次更新**: 下周一北京时间 8:00",
        "",
        "**数据源**:",
        "- HF 模型元数据：`data/hf-metadata-snapshot.json`",
        "- GPU 价格：`data/gpu-prices-snapshot.json`",
        "- 模型清单：`src/core/model_resolver.py`",
        "",
        "**自动化工作流**: `.github/workflows/refresh-models.yml`",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="default",
                        choices=["default", "consumer-gpu", "studio", "cloud"])
    args = parser.parse_args()

    models = parse_resolver()
    hf_data = load_json(HF_JSON)
    gpu_data = load_json(GPU_JSON)

    if not models:
        print("ERROR: KNOWN_MODELS 解析失败")
        sys.exit(1)

    md = render(models, hf_data, gpu_data, args.target)

    os.makedirs(REFS_DIR, exist_ok=True)
    with open(LATEST_OUT, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[render_report] latest: {LATEST_OUT}")

    # 也存日期版
    dated = os.path.join(REFS_DIR,
                          f"deployment-recommendations-{datetime.now().strftime('%Y-%m-%d')}.md")
    with open(dated, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[render_report] dated: {dated}")

    print("OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
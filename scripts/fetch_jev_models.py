#!/usr/bin/env python3
"""拉 JEV / System One 决策模型的真实 HF 元数据（v1.1.1 集成用）"""
import json
import re
import urllib.request

# slug, hf_repo, github, note
JEV_TARGETS = [
    ("autotrust-jev-9b", "autotrust/JEV-9B", "autotrust/JEV",
     "AutoTrust JEV-9B：Jev 1.13 蒸馏学生模型（Qwen3.5-9B 底座 + LoRA + 24 槽决策头），"
     "Apache-2.0，noul AUROC 0.996，29,955 题留出集上与教师选项一致率 87.5%"),
    ("autotrust-jev-27b", "autotrust/JEV-27B", "autotrust/JEV",
     "AutoTrust JEV-27B：Qwen3.8-27B 底座，6 基准平均 84.07% 反超闭源教师 Jev 1.13（83.85%），"
     "4/6 基准胜出，Apache-2.0，单张 B200 约 140ms/请求"),
    ("autotrust-jev-35b", "autotrust/JEV-35B", "autotrust/JEV",
     "AutoTrust JEV-35B：Qwen3.5-35B-A3B MoE 底座，HF 147 万下载，"
     "已在生产环境跑实时新闻推荐，是本波下载量最大的决策模型"),
    ("cloudflare-clef-27b", "Cloudflare/clef", "cloudflare/clef",
     "Cloudflare Clef 27B：Qwen3.8-27B 底座 + 图像输入（state 可带图），"
     "Ollama 0.35.1 起原生支持 /v1/systemone 接口"),
    ("cloudflare-clef-flash-9b", "Cloudflare/clef-flash", "cloudflare/clef",
     "Cloudflare Clef Flash 9B：Qwen3.5-9B 底座，同架构轻量版，"
     "3090 + Ollama 实测 12.8GB 占用、3 道类型化问题约 220ms"),
    ("convai-laya", "convaiinnovations/laya", "NandhaKishorM/laya",
     "Laya 0.4B：最受欢迎的开源 Jev 对应物，Apache-2.0，RLCD 训练，"
     "约 33ms，pip 可装且自带 MCP extra"),
    ("convai-laya-multilingual", "convaiinnovations/laya-multilingual", "NandhaKishorM/laya",
     "Laya 多语言版 0.3B：支持 100+ 语言，上下文 8k tokens"),
    ("openjev-openjev-27b", "openjev/openjev", "openjev/openjev",
     "OpenJEV 27B：开放权重复刻 TypeSafe /v1/systemone 请求形状，"
     "支持文本/网页/截图三态输入，最多 52 选项，CC BY-NC 4.0"),
    ("juspay-xor-35b", "juspay/xor", "juspay/xor",
     "Juspay XOR 35B：工业级变体，Qwen3.6-35B-A3B 后训练，最多 255 候选，SGLang 部署"),
    ("doofz-thx-01", "doofz/THX-01", "doofz/THX-01",
     "THX-01 0.3B：非自回归 mmBERT 编码器（约 322M），"
     "单次决策约 10ms，多语言（az/en/ru/tr/de），最小可用决策模型"),
    ("mapika-decider-2b", "Mapika/decider-2b", "mapika/decider-2b",
     "Decider 2B：System One 模型类的明确开源复刻，本波使用最广"),
]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "osm/4.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def params(repo):
    try:
        d = get_json(f"https://huggingface.co/api/models/{repo}?expand[]=safetensors")
        st = d.get("safetensors") or {}
        if st.get("total"):
            return round(st["total"] / 1e9, 2)
    except Exception:
        pass
    return None


print("=== JEV 系模型真实元数据 ===\n")
rows = []
for slug, repo, gh, note in JEV_TARGETS:
    try:
        d = get_json(f"https://huggingface.co/api/models/{repo}")
    except Exception as e:
        print(f"  ❌ {repo}: {e}")
        continue
    sz = params(repo)
    dl = d.get("downloads", 0)
    lk = d.get("likes", 0)
    cr = (d.get("createdAt") or "")[:10]
    mod = (d.get("lastModified") or "")[:10]
    lic = ""
    for t in d.get("tags", []):
        if t.startswith("license:"):
            lic = t.split(":", 1)[1]
    pt = d.get("pipeline_tag", "")
    rows.append((slug, repo, gh, sz, dl, lk, cr, mod, lic, pt, note))
    print(f"  {repo}")
    print(f"      size_b={sz}  DL={dl:,}  ♥={lk:,}  created={cr}  mod={mod}  license={lic}  pipeline={pt}")

print(f"\n\n=== 生成条目 ===\n")
blocks = []
for slug, repo, gh, sz, dl, lk, cr, mod, lic, pt, note in rows:
    lines = [
        f'    "{slug}": {{',
        f'        "hf_repo": "{repo}",',
        f'        "github": "{gh}",',
        f'        "category": "international-edge",',
        f'        "size_b": {sz or 0},',
        f'        "note": "{note}（HF {dl/1e6:.2f}M DLs · {lic}）",',
        f'    }},',
    ]
    blocks.append("\n".join(lines))
out = "\n".join(blocks)
print(out)
with open(r"C:\Users\Admin\AppData\Local\Temp\kx-check\jev_models_block.txt", "w", encoding="utf-8") as f:
    f.write(out)
print(f"\n✅ {len(blocks)} 条 JEV 条目已存")

# 历史实测记录归档（v1.0.0 - v1.0.2）

> 本文件是 [README](../../README.md) 历史实测段的归档。README 只保留**当前版本**
> （v1.0.3）的实测，历史版本在此按发布时间**倒序**排列。
>
> 各版本的完整 release notes 见 [`docs/releases/`](.)，
> 原始产物（含旧截图）见 git tag `v1.0.0` / `v1.0.1` / `v1.0.2`。

---

## 📌 归档前的三条说明

1. **截图文件名在 v1.0.3 被复用重拍**。本文件中形如
   `docs/screenshots/06-实测截图-硬件扫描.png` 的链接**已失效**——这些文件名
   现在指向 v1.0.3 重拍后的图。旧截图请到 git 历史查看：
   ```bash
   git show v1.0.2:docs/screenshots/06-实测截图-硬件扫描.png > old-06.png
   ```
2. **文字记录全部保留**，数字均为当时实测值，未做追溯修改。
3. **v1.0.1 / v1.0.2 的显存推荐逻辑对 MoE 是错的**（按激活参算），
   v1.0.3 已修复，复盘见 [`docs/moe-vram-pitfall.md`](../moe-vram-pitfall.md)。

---

### v1.0.2 实测（2026-09-26）— 127 模型 + `auto_fetch` 自动拉取（**历史记录**）

> ⚠️ 本段的截图文件名已被 v1.0.3 复用并**重拍为 v1.0.3 内容**（如
> `06-实测截图-硬件扫描.png` 现在是 v1.0.3 的输出），故此处不再重复贴图，
> 避免同一张图配两个版本说明。v1.0.2 的原始截图已存档于 git 历史
> （tag `v1.0.2`）。

v1.0.2 做的主要是：模型库 94 → 127、新增 `auto_fetch_models.py`、
新增 `auto-fetch-models.yml` 周日自动开 PR 工作流。
首次手动触发 run [#36242423838](https://github.com/KratosLee-6/open-source-model-deploy/actions/runs/36242423838)。

---

**v1.0.2 当时的结论**（历史快照 · 127 模型）：在真实硬件上跑通全集工具链路——
`auto_fetch_models` 自动拉取脚本可独立使用 ✓、GitHub Actions 工作流新增每周自动补模型 PR ✓。

> ⚠️ 当时的显存推荐逻辑对 MoE 是错的（按激活参算），v1.0.3 已修复，
> 复盘见 [docs/moe-vram-pitfall.md](docs/moe-vram-pitfall.md)。

---

### v1.0.1 实测（2026-09-10）— 工具自检 94 模型推荐（**历史快照 · v1.0.2 已替换为 127**）

> ⚠️ **重要区分**：v1.0.1 实测是**工具自身功能验证**——hardware_detect 扫描硬件、auto_expand_models 检查 94 模型清单、按 size_b 推荐部署档位。**没有真实加载模型跑推理**。
> v1.0.0 实测是**真实模型推理**——本地加载 Llama-3.2-1B 跑 API 调用（35.85 tokens/秒）。
> 两者并列保存是**不同维度**的实测记录。

> 📌 **该段为 v1.0.1 (2026-09-10) 历史快照**。**当前最新实测见下方 v1.0.2 段（实测 6-9，127 模型 + auto_fetch 自动拉取）**。

**环境**：Windows 11 / Intel64 8 核 / 15.9GB 内存 / **NVIDIA GeForce GTX 1660 Ti 6GB**
**驱动**：NVIDIA 595.97 / CUDA 13.2
**工具版本**：v1.0.1（GitHub Actions 工作流版 · 已被 v1.0.2 `auto-fetch-models.yml` 替代并增强）

#### 实测 1：硬件扫描

```json
{
  "platform": "windows",
  "cpu": {"logical_cores": 8, "arch": "AMD64"},
  "memory_gb": 15.9,
  "gpu": "NVIDIA GeForce GTX 1660 Ti (6GB VRAM, Driver 595.97)",
  "total_vram_gb": 6,
  "deployable_tier": "cpu_only",
  "timestamp": "2026-09-11 00:53:05"
}
```

![硬件扫描实测](docs/screenshots/06-实测截图-硬件扫描.png)

#### 实测 2（v1.0.0 历史快照）：47 个模型分类清单（8 大类 / 当时 47 个）

| 分类 | 模型数 | 代表模型 |
|------|-------|---------|
| domestic-general（国内通用）| 9 | deepseek-v3, qwen3-235b-a22b, kimi-k2 |
| domestic-reasoning（国内推理）| 10 | deepseek-r1, qwq-32b, deepseek-r1-distill-qwen-* |
| international-dense（国际密集）| 5 | llama-3.1-405b, mistral-large-2 |
| international-edge（国际边缘）| 8 | llama-3.2-1b/3b, llama-3.3-70b, gemma-3-* |
| code（代码专用）| 6 | qwen2.5-coder-32b, codestral-22b |
| vision（视觉多模态）| 5 | qwen2.5-vl-72b, internvl3-78b |
| embedding | 4 | bge-m3, qwen3-embedding-8b |
| reranker | 1 | bge-reranker-v2-m3 |
| **总计 (v1.0.0)** | **47** | **8 大类全覆盖（历史快照）** |

> 📌 当年的 47 模型分类截图已在 v1.0.3 重拍时移除（文件名与 135 模型那张冲突）。
> 原始截图见 git 历史（tag `v1.0.0` / `v1.0.1`）；上表的分类数据保留作历史记录。

#### 实测 3：本地部署推荐（GTX 1660 Ti 6GB）

| 档位 | 显存需求 | 可用模型数 | 推荐 |
|------|---------|-----------|------|
| **consumer-edge** | ≤6GB | 5 个 ✓ | llama-3.2-1b/3b, bge-m3, bge-large-zh-v1.5, bge-reranker-v2-m3 |
| **warn-quant** | 4-8GB（Q4 量化）| 7 个 ⚠ | qwen3-8b, deepseek-r1-distill-qwen-7b, gemma-3-4b |
| **need-gpu** | 16GB+ | 35 个 ❌ | qwen3-32b, deepseek-r1, llama-3.1-70b |

**KX 笔记本 6GB 显存 → 推荐 4 个主力模型**：
- **主力推荐**：qwen3-8b Q4_K_M（4GB，GPU 全速推理）
- **强推理**：deepseek-r1-distill-qwen-7b（3.5GB，强 CoT 能力）
- **多模态**：qwen2.5-vl-7b（3.5GB，图文理解）
- **备用**：llama-3.2-3b（1.5GB，CPU/GPU 都行）

![推荐结果](docs/screenshots/09-实测截图-推荐结果.png)

#### 实测 4：GPU 状态（nvidia-smi）

```
GPU  0  NVIDIA GeForce GTX 1660 Ti   WDDM
Fan  30%   38C    P8  12W / 120W
Memory-Usage  43MiB / 6144MiB
```

![nvidia-smi](docs/screenshots/08-实测截图-nvidia-smi.png)

#### 实测 5：自动刷新工作流（GitHub Actions）

**触发条件**：
- 每周一 UTC 00:00（北京时间 8:00）自动跑
- 修改 `src/core/model_resolver.py` 自动触发
- Actions 页面手动触发

**实测运行**（最近一次 2026-09-10）：
- ✅ 13 个 step 全部成功
- ✅ 自动 commit + 推送
- ✅ 耗时 42 秒

详见 [docs/GITHUB-ACTIONS.md](docs/GITHUB-ACTIONS.md)

---

**结论**：v1.0.1 在真实硬件（GTX 1660 Ti 6GB）上跑通全套工具链路——94 模型清单完整 ✓、硬件扫描准确 ✓、推荐结果按档位分组 ✓、GitHub Actions 工作流每周自动刷新 ✓。

---

### v1.0.0 发布实测（2026-08-15）— 无独显笔记本跑 1B 模型（历史 47 模型清单快照）

**环境**：Windows 11 / AMD64 16 核 / 15.2GB 内存 / 无独显
**模型**：Llama-3.2-1B-Instruct Q4_K_M（770MB）
**引擎**：llama.cpp b10424（CPU 版）

| 指标 | 实测结果 |
|------|---------|
| 模型加载 | ~3 秒 |
| **推理速度** | **35.85 tokens/秒** |
| 响应质量 | 准确生成结构化英文描述 |

**结论**：无独显笔记本也能本地跑 1B 模型，速度远超预期。对比云租 AutoDL 4090 月租 ¥2,500，本机部署**节省 100% 成本 + 数据不出本地**。

详细实测：[examples/real_world_test_windows_no_gpu.md](examples/real_world_test_windows_no_gpu.md)

---

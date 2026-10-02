# MoE 显存踩坑实录：一台 4090 差点被建议去跑 Kimi-K2

> 沉淀时间：2026-10-03 · 对应版本 v1.0.3
> 这是一个**真实发生并已修复**的 bug 复盘。如果你的项目也在做「模型 × 硬件」匹配，这篇能帮你省掉一次线上事故。

---

## 一句话结论

> **MoE 模型的显存必须按「总参数」算，不能按「激活参数」算。**
> 稀疏激活只降低计算量（FLOPs），不降低权重占用的显存。

激活参数是 MoE 的宣传口径（"1 万亿参数但每次只激活 420 亿"），最容易让人误以为显存需求也按激活算。**这是错的。** 所有 expert 权重都必须常驻显存，推理时每个 token 只激活其中少数几个，但没被激活的那些同样占着显存。

---

## 踩坑的经过

v1.0.2 的 `recommend_models_for_hardware` 对 MoE 走的是这条分支：

```python
vram_4bit = size_b * 0.6          # 密集模型
if activated_b > 0:               # ← MoE
    vram_4bit = activated_b * 0.6 # 用激活参算显存
```

看起来是对 MoE 做了优化，实际上差了一个数量级。实测输出（24GB RTX 4090 场景）：

| 模型 | 总参 / 激活 | v1.0.2 算出的显存 | 24GB 卡的判定 | 实际 Q4 需求 |
| --- | --- | ---: | --- | ---: |
| Kimi-K2 | 1000B / 32B | 23.0 GB | `tight` → **建议能跑** | **720 GB** |
| Qwen3-235B-A22B | 235B / 22B | 15.8 GB | `fits` → **建议能跑** | **169 GB** |
| GLM-4.5 | 355B / 32B | 23.0 GB | `tight` → **建议能跑** | **256 GB** |
| DeepSeek-V3 | 671B / 37B | 26.6 GB | `no`（勉强正确） | **483 GB** |
| DeepSeek-R1 | 671B / 37B | 26.6 GB | `no`（勉强正确） | **483 GB** |

注意前三个的判定是 `tight` / `fits`——也就是**明确建议能跑**，而不只是"边缘"。只有 DeepSeek-V3 / R1 因为算出来 26.6GB 刚好超过 24GB 才碰巧判成 `no`。

也就是说，一个准备花两三千块买二手显卡的用户，会被明确告知"这台机器能跑 Kimi-K2"。实际上他要租一个 8×H200 的集群。

**这个错误的隐蔽性在于它对密集模型完全正确。** 95% 的模型没有 `activated_b`，走的是对的分支，测试也全绿——直到有人拿 MoE 模型去核对，才发现整条推荐链路的语义是反的。

---

## 修正

单一修正点：显存按 `size_b`（总参）计算，`activated_b` 只用于计算量和 KV cache 估算。

```python
def resident_params_b(model_info) -> float:
    """权重常驻显存所需的参数量（B）

    无论密集还是 MoE，都返回 **总参数** size_b —— MoE 的 expert 权重同样要常驻。
    这与 activated_b（只影响计算量）的区别是本模块存在的核心原因。
    """
    return float(model_info.get("size_b") or 0)
```

修正后的实际差距：

| 模型 | 总参 | 激活 | 激活比 | Q4 真实需求 | 若误用激活参数 | 差距 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `deepseek-v3` | 671B | 37B | 5.5% | **483.1 GB** | 26.6 GB | 18× |
| `kimi-k2` | 1000B | 32B | 3.2% | **720.0 GB** | 23.0 GB | **31×** |
| `qwen3-235b-a22b` | 235B | 22B | 9.4% | **169.2 GB** | 15.8 GB | 11× |
| `glm-4.5` | 355B | 32B | 9.0% | **255.6 GB** | 23.0 GB | 11× |
| `mimo-v2.6-pro` | 1024.2B | 42B | 4.1% | **737.4 GB** | 30.2 GB | 24× |
| `glm-5.3` | 753.3B | 39B | 5.2% | **542.4 GB** | 28.1 GB | 19× |
| `kimi-k3` | 2779.9B | 119B | 4.3% | **2001.5 GB** | 85.7 GB | 23× |
| `llama-4-scout-17b` | 108.6B | 17B | 15.7% | **78.2 GB** | 12.2 GB | 6× |

激活比越低，错得越离谱——而 MoE 恰恰是激活比最低的那一类（3%~9%）。**这两件事是相关的，不是巧合。**

---

## 第二个坑：反向犯同一个错

修完主 bug 后回头查数据源，发现 `auto_fetch_models.py` 的 `guess_size_b()` 在**反向**犯同一个错误——它纯靠正则从模型名抠数字当总参：

| 模型名 | 正则结果 | 真实总参 | 后果 |
| --- | ---: | ---: | --- |
| `MiMo-V2.6-Pro-RL` | `0` | 1024.2B | 数据全丢 |
| `GLM-5.3` | `0` | 753.3B | 数据全丢 |
| `Kimi-K3` | `0` | 2779.9B | 数据全丢 |
| `Llama-4-Scout-17B-16E` | `17` | 108.6B | **把激活参当总参，低估 6.4×** |

最后一行值得单独说。`Llama-4-Scout-17B-16E` 这个命名里：

- `17B` = **激活**参数量
- `16E` = 专家数
- 总参 = 108.6B

正则只认得 `17B`，于是把它当总参写进库。用户会以为 16GB 卡能跑 Llama 4 Scout，实际 Q4 需要 78GB。**和第一个 bug 同一个根因、方向相反。**

这类命名必须单独处理：

```python
# Qwen 系：<总参>B-A<激活>B  → 两个数字都有明确含义，可直接取
#   Qwen3-30B-A3B            → size 30, activated 3
#   Qwen3-Coder-480B-A35B    → size 480, activated 35
_TOTAL_ACT_RE = r"(\d+(\.\d+)?)[bB][-_]a(\d+(\.\d+)?)[bB]"

# Meta 系：<激活>B-<专家>E  → 那个 B 是激活参，当总参用就错了
#   Llama-4-Scout-17B-16E   → 激活 17B，总参 108.6B
_ACT_EXPERT_RE = r"(\d+(\.\d+)?)[bB][-_](\d+)[eE]\b"
```

最终做法是**不猜**：`size_b` 改从 HF API 的 `safetensors.total` 取（权重元素数，即真实总参），`activated_b` 只认 Qwen 系的明确形态，Meta 系那类宁可留空并报警，也不填一个看起来合理的错值。

```python
url = f"https://huggingface.co/api/models/{repo_id}?expand[]=safetensors"
total = data["safetensors"]["total"]   # 权重元素个数 = 真实参数量
```

---

## 防回归：把判据固化成 lint

光修代码不够——这类错误会从任何入口溜进来（手工录入、自动抓取、模型改名）。所以把判据固化成了 `src/core/model_lint.py`，并在 CI 里作为第一个业务 step 执行：

| 判据 | 级别 | 拦什么 |
|---|---|---|
| `size_b` 缺失或为 0 | ERROR | 新命名抠不到数字，显存算不出来 |
| `size_taken_from_activated` | ERROR | `<激活>B-<专家>E` 形态下把激活参当总参 |
| `name_size_mismatch` | ERROR | 模型名声明的总参与 `size_b` 不符 |
| `activated_ge_size` | ERROR | 激活参 ≥ 总参（两个值填反了） |
| `moe_without_activated_b` | WARN | 标称 MoE 却没记激活参 → `is_moe()` 失真 |
| `expert_moe_activated_unknown` | WARN | `<激活>B-<专家>E` 是 MoE 但激活参未知 |
| `retired_without_supersede` | ERROR | 标记退役却没指向继任模型 |

```bash
python scripts/lint_models.py            # 体检
python scripts/lint_models.py --strict   # WARN 也返回非 0（CI 用）
```

自动抓取的 patch 在输出前会先过这道闸门，ERROR 的候选直接拦下列出原因，不进 patch。

**这个 lint 自己也抓到了一个 bug**：`_TOTAL_ACT_RE` 漏了 `re.I`，而 Qwen 官方命名用的是大写 `A`（`Qwen3-30B-A3B`），导致总参互证规则全程静默失效。是测试逼出来的，不是 code review 能看出来的。

---

## 给其他项目的 checklist

如果你也在做「模型 × 硬件」的匹配判断：

- [ ] MoE 显存按**总参**算，`activated_b` 只用于计算量/KV cache
- [ ] 总参从权威来源取（HF `safetensors.total`、官方模型卡），不要正则抠模型名
- [ ] 认清两种命名形态：`<总参>B-A<激活>B` vs `<激活>B-<专家>E`，后者不能当总参
- [ ] `activated_b` 宁可留空也不要瞎填——留空只是 `is_moe()` 判断失真，填错会让显存估算错一个数量级
- [ ] 把上述判据做成 lint + CI 卡口，别指望 review 能拦住
- [ ] 回归测试要**显式列出每个大型 MoE 在消费级卡上必须是 `no`**，别只测密集模型

最后一条尤其重要：这类 bug 在密集模型上完全不可见，测试覆盖率再高也测不出来，必须显式构造 MoE 样例。

---

## 相关文件

| 文件 | 作用 |
| --- | --- |
| `src/core/vram_requirements.py` | 显存需求的单一可序列化来源 |
| `src/core/model_lint.py` | 模型数据体检判据 |
| `scripts/lint_models.py` | 体检 CLI |
| `data/models-knowledge.json` | 导出契约（MCP / HTTP / 第三方插件消费） |
| `references/vram-requirements.md` | 136 个模型的显存对照表（自动生成） |
| `tests/test_vram_requirements.py` | 20 项，含 MoE 误判回归 |
| `tests/test_model_lint.py` | 22 项，含 4 个真实坏数据回归 |

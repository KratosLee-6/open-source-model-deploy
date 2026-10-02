# XHS / 小红书发布硬约束（沉淀时间：2026-09-26）

> **背景**：KX 9/26 反馈 v1.0.2 XHS 图文文案超字数 260 个（1260 字 vs 1000 字上限）+ 缺 tag + emoji 不达标 —— **这是第 4 次踩同一类坑**（之前 8/16/9/16 已反复强调）。永久存档为仓内文件，下次 XHS 工作直接读这份。

---

## 一、XHS 硬约束（5+5 项硬指标）

### A. 文案硬约束

| # | 指标 | 标准 | 失败后果 |
|---|---|---|---|
| 1 | **标题字数** | ≤ **20 字** | 标题被截断 |
| 2 | **正文 + 标签总字数** | ≤ **1000 字**（XHS OCR 扫的是渲染后 JPG，不是 HTML 源码） | 整篇被限流 |
| 3 | **标签数** | ≤ **10 个** | 标签被忽略 |
| 4 | **emoji 数** | **5-8 个**（正文关键节点 + 标题候选都带） | 0 MD ≠ 0 emoji |
| 5 | **0 联系方式** | 0 QQ/微信/vx/邮箱/网址/二维码/私信 | `含义不明字符串` 直接限流 |

### B. 配图硬约束

| # | 指标 | 标准 |
|---|---|---|
| 6 | **0 emoji** | XHS 配图（HTML+Playwright 渲）禁 emoji —— Playwright Noto Sans SC 不渲染 emoji 字体 |
| 7 | **0 黑底块** | 唯一允许的是 issue-strip（最底部 64px 黑条）；其他任何大面积黑色实心块 ❌ |
| 8 | **0 黄色 + 0 橙色** | Swiss editorial 蓝白主调，黄/橙仅做小标签 |
| 9 | **0 联系方式 / 平台名** | 0 QQ/微信/小红书/抖音/B站/微博/A平台 等 |
| 10 | **edge-to-edge** | Edge headless `--window-size=1080,1440` 渲染；HTML `body { padding: 0 }` —— 不留 32px 画布空白 |

### C. 限流 SOP（来自 `xhs-content-style-match` skill §4）

| # | 违规 | 判定 |
|---|---|---|
| 11 | 含义不明数字串 | `7w+` / `55` / `160万` / `A平台` / `三0天` → 触发 OCR 误判 |
| 12 | 跨平台框架 | `A平台/B平台/C平台` 类词汇必被扫 |
| 13 | 含义不明折扣 | `省 ¥N` / `单独购买合计` → 提示词广告推广 → 拒 |

---

## 二、字数自查（必须独立于 spec.md 跑）

```python
import re
s = open("文案-spec.md", encoding="utf-8").read()
# 找正文块（第一个 ```...```）和标签块（第二个）
blocks = re.findall(r"```\n(.*?)\n```", s, re.S)
body = re.sub(r"\s+", "", blocks[0])               # 正文去空白
tags = re.findall(r"#(\S+)", blocks[1])             # 标签区
n_emoji = len(re.findall(
    r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F900-\U0001F9FF]",
    blocks[0]))

# 5 项硬指标
assert len(body) <= 1000, f"FAIL 正文 {len(body)} > 1000"
total = len(body) + sum(len("#"+t) for t in tags)
assert total <= 1000, f"FAIL 正文+标签 {total} > 1000"
assert len(tags) <= 10, f"FAIL 标签 {len(tags)} > 10"
assert 5 <= n_emoji <= 8, f"FAIL emoji {n_emoji} 不在 5-8 区间"
print(f"✅ PASS: 标题≤20 / 正文+标签={total}≤1000 / 标签={len(tags)}≤10 / emoji={n_emoji}")
```

**约束**：spec.md 末尾**必须有独立自查报告块**（block 3），不被 markdown 装饰污染计数。

### ⚠️ 标题计数必须剥除 markdown 装饰（2026-10-03 补充）

v1.0.3 撰写时踩到：标题写成 `> **24G显卡跑Kimi-K2差31倍**`，直接 `len()` 得 21 字、
误判超限；实际渲染后只有 17 字。**XHS OCR 扫的是渲染结果，markdown 装饰不占字数。**

```python
# ❌ 错：len("**24G显卡跑Kimi-K2差31倍**") = 21
# ✅ 对：剥掉装饰再数
title = re.sub(r"[*_`>#\s]", "", title_raw)
```

标题限 20 字这一项上面的示例代码没覆盖（只查了正文/标签/emoji），
**自查脚本需自己补上标题检查 + 联系方式/平台名扫描**。
参考实现：`E:\工作\KratosLee小红书\06b_开源模型工具-v1.0.3_MoE显存踩坑\_check.py`

---

## 三、第一次做 XHS 内容前的 clarify（必走）

任何 XHS / 公众号 / 视频号内容**第一次生成前**必须 clarify **三个问题**：

1. **这是个人号 / 团队号 / 客户号？**（不要默认填"AI 看世界"团队号）
2. **左下角 issue-strip .left 该填什么？**（KX 个人号 → `KratosLee`，团队号 → `AI 看世界`）
3. **右下角 issue-strip .right 该填什么 tag？**（直接对应文案末尾 tag 区，**不能多也不能少**）

**根因**：之前 4 次踩坑都是"我自动填了'AI 看世界'"（来自 skill 文档默认值），KX 个人小红书工作区却放个人号内容 → **账号错位 + 字数超限双错**。

---

## 四、生成 → 渲染 → 自检 4 步

| 步 | 动作 | 工具 |
|---|---|---|
| 1 | 生成 spec.md（含 4 个独立 ` ``` ` 块：正文 / 标签 / 配图说明 / 自查报告） | write_file |
| 2 | 跑字数 Python 自查（§二） | execute_code |
| 3 | HTML 渲染：HTML `body { padding: 0 }` + Edge headless `--window-size=1080,1440` + `--virtual-time-budget=30000` | terminal |
| 4 | **像素扫描**：4 边空白 ≤ 5 px（避免画布空白）/ blue 2-6% / yellow ≈ 0 / orange ≈ 0 | PIL + vision_analyze |

---

## 五、真实案例（v1.0.2 · 2026-09-26）

✅ PASS 验证（`E:\工作\KratosLee小红书\06_开源模型工具-v1.0.2\文案-spec.md`）：

```
标题：开源大模型自动盘点工具 · v1.0.2
字数：18 字   ✅ ≤20
正文：932 字   ✅ ≤1000
标签：8 个     ✅ ≤10  (#开源大模型 #AI工具 #LLM部署 #HuggingFace #开发者工具 #GitHub #MCP #vllm)
emoji：7 个    ✅ 5-8
正文+标签合计：987 字   ✅ ≤1000
配图：edge-to-edge (1080×1440 · 0 空白边 · 蓝白主调 · issue-strip .left=KratosLee)
```

---

## 六、参考

- Skill: `xhs-content-style-match` (§3 文案硬约束 / §4 限流 SOP / §5 双重扫描)
- Skill: `xhs-social-card` (pitfall #6 Google Fonts CDN 拦截 / #10 viewport = section / #22 撑满整高 / #25 禁大面积黑底块)
- 本次踩坑沉淀：KX 9/26 反馈 "你又忘了，XHS ≤1000 字 + 账号确认" → 写入本文件

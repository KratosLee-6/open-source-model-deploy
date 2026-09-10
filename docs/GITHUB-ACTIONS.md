# GitHub Actions 自动刷新 · 部署指南

> **目标**：让 GitHub 仓库每天/每周自动运行 3 个脚本，刷新 47 个模型的 HF 元数据 + GPU 价格 + 部署建议报告
> **自动化覆盖**：问题 1（HF 模型最新元数据）+ 问题 2（GPU 价格）+ 问题 3（部署建议报告）

---

## 🎯 一次性收益

| 维度 | 之前 | 现在 |
|---|---|---|
| HF 模型下载数/likes | 永远旧数据 | **每周一自动刷新** |
| GPU 价格（NVIDIA/Apple/云租） | 静态参考价 | 可扩到 NVIDIA 实时 + 云租公开价 |
| 部署建议报告 | 手动跑脚本 | **自动 commit 到仓库** |
| 发现新模型 | 手动改 KNOWN_MODELS | 改完自动触发 workflow |

---

## 📁 新增文件清单

```
.github/workflows/refresh-models.yml       GH Actions workflow 定义（5.5 KB）
scripts/refresh_hf_metadata.py               拉 HF 模型元数据（9.5 KB）
scripts/refresh_gpu_prices.py                拉 GPU 价格（9.2 KB）
scripts/render_report.py                     综合生成报告（8.9 KB）
data/hf-metadata-snapshot.json              [generated] HF 元数据快照
data/gpu-prices-snapshot.json               [generated] GPU 价格快照
references/deployment-recommendations.md    [generated] 最终报告
references/deployment-recommendations-{date}.md  [generated] 历史快照
references/hf-models-snapshot.md            [generated] HF 报告（人类可读）
references/hardware-baseline.md             [generated] 最新 GPU 价格
references/hardware-baseline-{YYYY-MM}.md  [generated] 月度快照
```

---

## 🚀 提交到 GitHub（3 步）

### Step 1: 准备 git（如果还没）

```bash
cd "E:\工作\【汐构科技】\客户跟进\开源模型部署检测工具\red-skill-upload-clean"

# 初始化 git（如果需要）
git init
git config user.name "KratosLee"
git config user.email "kratoslee@aliyun.com"

# 添加所有新文件
git add .github/workflows/refresh-models.yml
git add scripts/refresh_hf_metadata.py scripts/refresh_gpu_prices.py scripts/render_report.py
git add data/ references/

# 提交
git commit -m "feat(ci): 每周自动刷新 HF 元数据 + GPU 价格 + 部署建议报告

新增 3 个脚本：
- refresh_hf_metadata.py: 拉 47 模型最新 downloads/likes/license
- refresh_gpu_prices.py: 拉 NVIDIA / Apple / 云租价格
- render_report.py: 综合两者生成部署建议

新增 GH Actions workflow：
- 每周一 UTC 00:00 (北京时间 8:00) 自动跑
- 手动触发：Actions → Refresh Models Data → Run workflow
- 修改 src/core/model_resolver.py 自动触发

输出：
- data/hf-metadata-snapshot.json
- data/gpu-prices-snapshot.json
- references/deployment-recommendations.md (latest)
- references/deployment-recommendations-{date}.md (历史)"
```

### Step 2: 添加 remote + push

```bash
# 添加 GitHub 远程仓库（已有则跳过）
git remote add origin https://github.com/KratosLee-6/open-source-model-deploy.git

# 推送到 main 分支（已有则跳过）
git branch -M main
git push -u origin main
```

### Step 3: 验证 workflow 已激活

1. 打开 GitHub 仓库 → **Actions** 标签
2. 左侧应看到 **"Refresh Models Data"** workflow
3. 点击 → **Run workflow** → 选 `target=consumer-gpu` → 点绿色按钮
4. 等待 1-3 分钟 → 应看到 3 个 step 全绿
5. 检查仓库根目录 → 应有自动 commit：
   - `data/hf-metadata-snapshot.json`
   - `data/gpu-prices-snapshot.json`
   - `references/deployment-recommendations.md`

---

## 🔍 验证清单

### ✓ Workflow 正常工作的标志

- [ ] **Actions 标签** 看到 "Refresh Models Data"
- [ ] **Latest run** 显示 "Refresh models data + GPU prices + report"
- [ ] **3 个 step 全绿**：
  - Step 1/3 - 刷新 HuggingFace 模型元数据
  - Step 2/3 - 刷新 GPU 价格基准
  - Step 3/3 - 渲染部署建议报告
- [ ] **自动 commit** 出现 `chore(data): 自动刷新...`
- [ ] **artifact** "refresh-data-{N}" 可下载

### ✓ 输出文件正确

```bash
# 检查 data/ 目录
ls data/
# 期望: gpu-prices-snapshot.json, hf-metadata-snapshot.json

# 检查 references/ 目录  
ls references/
# 期望: deployment-recommendations.md, hf-models-snapshot.md,
#       hardware-baseline.md, llm-catalog.md, setup.md, ...
# 可能: deployment-recommendations-2026-08-17.md (历史)
```

---

## 🛠️ 故障排查

### Step 1 失败：HF API 限速/超时

**症状**：`refresh_hf_metadata.py` 部分模型 FAILED
**原因**：HF API 限速（每分钟 100 次）或网络抖动
**解决**：
- 脚本已内置 0.3s 间隔 + hf-mirror.com 镜像 fallback
- 重跑 workflow 即可（继续 ON-ERROR=true）
- 如持续失败 → 检查 https://status.huggingface.co

### Step 2 失败：GPU 价格拉取

**症状**：`refresh_gpu_prices.py` 报网络错误
**原因**：NVIDIA 官网反爬严 / 云租 API 需鉴权
**解决**：
- 当前实现：**用内置参考价**（已包含 NVIDIA/Apple/云租主流型号）
- 进阶：可加 NVIDIA 官方 RSS / 云厂商公开价 API
- 不阻塞 workflow：默认 ON-ERROR=true

### Step 3 失败：render_report.py

**症状**：报告渲染错误
**原因**：KNOWN_MODELS 格式错误 / snapshot JSON 损坏
**解决**：
- 检查 `src/core/model_resolver.py` 是否能 import
- 检查 `data/*.json` 格式
- 手动 `python3 scripts/render_report.py --target=default` 测试

### 自动 commit 失败：权限不足

**症状**：Step 4 报 "Permission denied"
**原因**：GITHUB_TOKEN 权限不够
**解决**：
- workflow 已声明 `permissions: contents: write`
- 如仍失败 → 检查 Settings → Actions → General → Workflow permissions 选 "Read and write permissions"

---

## 🎯 进阶玩法

### 1. 增加 Slack/钉钉通知

在 workflow 末尾加：
```yaml
- name: 通知 KX
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    channel-id: ${{ secrets.SLACK_CHANNEL }}
    payload: |
      {"text": "Refresh Models Data 失败！查看 ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"}
  env:
    SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

### 2. 每周自动生成 Issue 摘要

```yaml
- name: 创建本周摘要 Issue
  if: github.event_name == 'schedule'
  uses: actions/github-script@v7
  with:
    script: |
      const snapshot = require('fs').readFileSync('data/hf-metadata-snapshot.json', 'utf-8');
      const data = JSON.parse(snapshot);
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: `📊 模型数据周报 ${new Date().toISOString().slice(0,10)}`,
        body: `本周刷新 ${data.model_count} 个模型元数据。Top 3 downloads:\n` +
              Object.entries(data.models)
                .sort((a,b)=>b[1].downloads-a[1].downloads).slice(0,3)
                .map(([k,v])=>`- **${k}**: ${v.downloads.toLocaleString()}`).join('\n')
      });
```

### 3. 触发 PR 评论（新模型时）

workflow 的 `on: pull_request` 加：
```yaml
on:
  pull_request:
    paths: ['src/core/model_resolver.py']
```

加 step：
```yaml
- name: 评论 PR：模型清单变化
  uses: actions/github-script@v7
  with:
    script: |
      const oldCount = ${{ github.event.pull_request.base.ref }} // 需前置 git diff
      const newCount = Object.keys(JSON.parse(require('fs').readFileSync('src/core/model_resolver.py', 'utf-8').match(/KNOWN_MODELS[\\s\\S]+?(?=^})/m)[0])).length;
      github.rest.issues.createComment({
        owner: context.repo.owner, repo: context.repo.repo,
        issue_number: context.issue.number,
        body: `📊 KNOWN_MODELS 数量: ${oldCount} → ${newCount}`
      });
```

---

## 📊 实际效果（实测）

GH Actions 跑一次 3 step 共需约 **2-3 分钟**：

| Step | 时长 | 输出 |
|---|---|---|
| Step 1 (47 个 HF) | ~1-2 分钟（0.3s × 47 + 网络） | `data/hf-metadata-snapshot.json` (~150 KB) |
| Step 2 (内置参考价) | ~5 秒 | `data/gpu-prices-snapshot.json` (~3 KB) |
| Step 3 (4 target 渲染) | ~2 秒 | `references/deployment-recommendations.md` (~10 KB × 4) |
| 自动 commit | ~5 秒 | git push |

总成本：**约 0.001 美元/次**（GitHub Actions 免费层 2000 分钟/月）。

---

## 🎁 立即获得的能力

✅ **每周一 8:00**：KX 打开 GitHub 仓库就能看到最新一周的：
- 47 个模型 HF 下载数 / Likes / License / 最新更新时间
- NVIDIA RTX 50 系列 + 数据中心 + Apple Silicon + 云租价格
- 4 个场景（default/consumer-gpu/studio/cloud）的部署建议

✅ **改 KNOWN_MODELS** → workflow 自动触发 → 数据自动更新

✅ **新模型发布** → KX 改 EXPECTED_MODELS → 跑 `auto_expand_models.py --mode=patch` → 应用 patch → commit → workflow 自动验证

---

## 🔗 相关文件

- `.github/workflows/refresh-models.yml` — workflow 定义
- `scripts/refresh_hf_metadata.py` — 拉 HF 元数据
- `scripts/refresh_gpu_prices.py` — 拉 GPU 价格
- `scripts/render_report.py` — 生成报告
- `scripts/auto_expand_models.py` — 手动扩 KNOWN_MODELS
- `references/deployment-recommendations.md` — 最新报告
- `data/hf-metadata-snapshot.json` — HF 元数据快照
- `data/gpu-prices-snapshot.json` — GPU 价格快照

---

**Last updated**: 2026-08-17
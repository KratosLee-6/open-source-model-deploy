# Release Checklist · v1.0.3+ 起强制执行

> **背景**：2026-09-26 v1.0.2 发布时漏改了 GitHub repo description / INSTALL.md / topics，导致用户从 GitHub 项目卡片（不是 README）进入仓库看到的还是「47 个开源模型 + 16 核无独显」。KX 反馈：「主仓库的项目介绍没有全文更新到最新版」。
> **目的**：让 v1.0.3+ 起，每次发布前必跑完这张清单，**不留任何「仓库级」过期**。

---

## ✅ Release Checklist（每个版本号前必勾完）

### 1️⃣ 代码与数据（Git tracked）

- [ ] `src/core/model_resolver.py` · `KNOWN_MODELS` 加完目标模型
- [ ] 跑 `python scripts/auto_fetch_models.py --mode=stats` · 候选数合理（业务预期内）
- [ ] 跑 `python scripts/auto_fetch_models.py --mode=patch` · 输出可粘贴
- [ ] 跑 `python scripts/apply_auto_fetch_patch.py` · AST 验证：去重 + 插入 OK
- [ ] AST 语法：`python -c "import ast; ast.parse(open('src/core/model_resolver.py').read())"`
- [ ] 跑 `osm-deploy list` · CLI 输出正确（含新增 slug）
- [ ] 抽 11/11 新模型跑 `osm-deploy assess <slug>` · resolve OK
- [ ] `tests/` 跑过（如果以后加单测）
- [ ] Commit message 写清：`feat(vX.Y.Z): ...` 格式

### 2️⃣ 文档（Git tracked）

- [ ] `README.md` 头部版本号 `vX.Y.Z (YYYY-MM-DD)` 已更新
- [ ] `README.md` 头部模型数（如 127 → 165）已更新
- [ ] `README.md` 「🌟 核心亮点」段反映新特性
- [ ] `README.md`「🏆 真实实测案例」段最新化（去「最新」表述 → 「历史快照」）
- [ ] `SKILL.md` frontmatter `version: X.Y.Z` 已升
- [ ] `SKILL.md` `summary` 数字与 README 一致
- [ ] `INSTALL.md` 第一步 "支持 N 个模型，分 8 类" 同步
- [ ] `INSTALL.md` 第二步示例输出同步到当前真实硬件（CPU 核数 / 显存 / 推荐数）
- [ ] `INSTALL.md` 顶部加 `📌 vX.Y.Z 更新` 标注（让用户一眼看到变化）
- [ ] `docs/releases/vX.Y.Z.md` 创建（必备！）
- [ ] `docs/RELEASE_CHECKLIST.md`（本文件）如有变更同步

### 3️⃣ GitHub 元数据（非 Git tracked · 走 `gh` CLI / REST API）

> ⚠️ **2026-09-26 v1.0.2 实际踩坑章节** — 这些不在 git commit 里，**容易漏**

- [ ] `gh repo edit` description 同步新版本号 + 模型数
  ```bash
  gh repo edit github.com/<owner>/<repo> \
    --description "<一句话描述 · N 个开源模型...>"
  ```
- [ ] `gh repo edit --add-topic ...` 加 topics（如 llm / huggingface / mcp / vllm）
- [ ] 不需要的 topics `--remove-topic` 清掉
- [ ] **验证**：curl GitHub API `/repos/<owner>/<repo>` 看 description/topics 实时生效

### 4️⃣ 截图与可视化

- [ ] `python scripts/regen_screenshots.py` 重生成所有截图
  - 06 / 07-127 / 08 / 09 (实测 5 张)
  - 13 / 14 (auto_fetch stats / patch) — 仅 v1.0.2+ 有
  - 12 (架构图) — 通常不动
  - 07-47 (历史快照) — 保留作 backward-compat
- [ ] `ls -la docs/screenshots/*.png` 看大小合理（30-200 KB）
- [ ] 看 `07-实测截图-127模型分类.png` 最新且字符清晰（v2 修复后 1200×855 px）

### 5️⃣ GitHub Actions

- [ ] `.github/workflows/refresh-models.yml` 现有代码不变
- [ ] `.github/workflows/auto-fetch-models.yml`（v1.0.2+）触发测试过
  ```bash
  gh workflow run auto-fetch-models.yml --repo github.com/<owner>/<repo> \
    -f min_downloads=100000
  gh run list --workflow=auto-fetch-models.yml --limit=3
  # 应该看到 completed · success
  ```

### 6️⃣ Releases & Tags

- [ ] `git tag vX.Y.Z <commit-sha> -f`
- [ ] `git push origin vX.Y.Z --force`
- [ ] `gh release create vX.Y.Z --target main \
       --title "vX.Y.Z · <一句话>" \
       --notes-file docs/releases/vX.Y.Z.md`
- [ ] 已有 release 时：`gh release edit vX.Y.Z --target main`
  （注意：`--target` 必须 branch 名，不能 SHA → 否则 422）
- [ ] `gh release view vX.Y.Z` 核对 title/tag/target

### 7️⃣ 推送与最终验证

- [ ] `git pull --rebase` 拉取 refresh-models.yml 自动跑出的新 commit
- [ ] `git push origin main`
- [ ] `curl raw.githubusercontent.com/<owner>/<repo>/main/README.md` 验证 CDN 最新（5-10 min）
- [ ] `curl https://api.github.com/repos/<owner>/<repo>/commits?per_page=3` 验证 commit 历史
- [ ] `curl https://api.github.com/repos/<owner>/<repo>/git/refs/tags/vX.Y.Z` 验证 tag 指向

---

## 🚨 关键易漏点（来自 v1.0.2 实战）

| 易漏项 | 后果 | 修复办法 |
|---|---|---|
| 漏改 GitHub repo description | 用户搜到仓库看到的还是旧版描述 | `gh repo edit` 走 REST API（不走 git commit） |
| 漏改 INSTALL.md 示例输出 | 用户安装时看到的还是旧硬件描述 | 每次 README 改完顺扫 INSTALL.md |
| 历史段不说「历史快照」 | 用户误以为是「最新」实测 | 加 `**历史快照 · vX.Y.Z 已替换为 N**` 标注 |
| `gh release edit --target` 用 SHA | 422 Validation Failed | 必须用 branch 名 |
| KX 反馈时 raw.githubusercontent.com 缓存 | 反馈"还是旧版"但实际已更新 | wait 5-10 min 再 verify，或 grep curl 加 `?nocache=...` |
| `git push origin main` 前没 `git pull --rebase` | 远端有 `refresh-models` 自动跑出的 commit | 必须先 pull，否则 push 被拒 |
| auto_fetch 跑出 0 candidates | workflow 步直接跳过 | 检查 `steps.stats.outputs.candidates != '0'` 条件 |
| tag 强制 push 后 gh release 还指旧 commit | release 页走老 pointer | release edit `--target main` |

---

## 📝 跑完清单后写一份 wrap report

放到 `docs/releases/vX.Y.Z-wrap.md`，对内沟通：

```markdown
# vX.Y.Z 发布收尾报告 · YYYY-MM-DD

## 实际 vs 计划差异
- 计划: ...
- 实际: ...
- 原因: ...

## 数据
- 模型: N → M
- commits: 3
- new files: X
- workflow runs: #xxx

## KX 反馈（如果有）
- 反馈 1: 修复 → commit XXX
- 反馈 2: 修复 → commit YYY
```

---

## 🔗 相关

- `docs/releases/vX.Y.Z.md` — 单版本详细 release notes
- `scripts/auto_fetch_models.py` — 模型自动拉取脚本（任务 1 的核心）
- `scripts/apply_auto_fetch_patch.py` — workflow 调用的 apply 逻辑
- `scripts/regen_screenshots.py` — 截图重生工具
- `.github/workflows/auto-fetch-models.yml` — 周日自动 PR 工作流
- `.github/workflows/refresh-models.yml` — 周一自动数据快照（不动）

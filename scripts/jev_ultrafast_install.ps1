# ============================================================
# JEV (browser-use/jev-ultrafast) 一键安装脚本（Windows PowerShell）
# 用法：.\scripts\jev_ultrafast_install.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$RepoUrl = "https://ghfast.top/https://github.com/browser-use/jev-ultrafast"
$InstallDir = Join-Path $env:USERPROFILE "jev-ultrafast"

Write-Host "==> 克隆 browser-use/jev-ultrafast 到 $InstallDir" -ForegroundColor Cyan
if (Test-Path $InstallDir) {
    Write-Host "    目录已存在，跳过克隆（pull 一次）" -ForegroundColor Yellow
    & git -C $InstallDir pull --ff-only
} else {
    & git clone $RepoUrl $InstallDir
}

Set-Location $InstallDir
Write-Host "==> 安装依赖（uv 优先，无则 pip）" -ForegroundColor Cyan
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    & uv sync
} else {
    & python -m pip install -e ".[dev]"
}

Write-Host "==> 复制 env 模板" -ForegroundColor Cyan
$EnvExample = Join-Path $InstallDir "templates\..\templates\jev-env.example"
$EnvExample2 = "templates\jev-env.example"
$EnvTarget = Join-Path $InstallDir ".env"

# 本仓库内 templates/jev-env.example 也要复制
$SrcEnv = if (Test-Path $EnvExample2) { $EnvExample2 } elseif (Test-Path "..\templates\jev-env.example") { "..\templates\jev-env.example" } else { $null }

if ($SrcEnv) {
    Copy-Item $SrcEnv $EnvTarget -Force
    Write-Host "    .env 已就绪（请编辑 $EnvTarget 填入 key）" -ForegroundColor Green
} else {
    Write-Host "    找不到 env 模板，跳过（手动从 open-source-model-deploy/templates/jev-env.example 复制）" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ 安装完成" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "  1. 编辑 $EnvTarget 填入 TYPESAFE_API_KEY 和 TEXT_MODEL_API_KEY"
Write-Host "  2. 跑演示：python jev_ultrafast/demo.py"
Write-Host "  3. 跑 Zurich->London 基准：python examples/flights.py"
Write-Host ""
Write-Host "性能预期（基于 docs/performance.md）：" -ForegroundColor Cyan
Write-Host "  Median TypeSafe latency: 178 ms / decision"
Write-Host "  Zurich->London 完成时间: ~7.07 s"
Write-Host ""

# 画宗制片中枢 — 10 窗口并行启动脚本 (PowerShell)
# 用法: .\scripts\launch-swarm.ps1 -Phase 1 -Feature "1.1"

param(
    [Parameter(Mandatory=$true)]
    [int]$Phase,

    [Parameter(Mandatory=$true)]
    [string]$Feature
)

$ErrorActionPreference = "Stop"
$config = Get-Content ".\scripts\swarm-config.json" | ConvertFrom-Json
$repoRoot = $config.project.repo_root
$worktreeBase = $config.project.worktree_base
$systemPrompt = Get-Content ".\scripts\prompts\system-base.md" -Raw

# 找到对应 phase 和 feature
$phase = $config.phases | Where-Object { $_.id -eq "phase-$Phase" }
$feat = $phase.features | Where-Object { $_.id -eq $Feature }

if (-not $feat) {
    Write-Error "功能 $Feature 不存在"
    exit 1
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  画宗制片中枢 — 启动多窗口并行开发" -ForegroundColor Cyan
Write-Host "  功能: $Feature — $($feat.name)" -ForegroundColor Cyan
Write-Host "  Workers: $($feat.workers -join ', ')" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# 创建 worktree 目录
New-Item -ItemType Directory -Force -Path $worktreeBase | Out-Null

# 为每个 worker 启动一个新的 Windows Terminal 标签页
$workers = $feat.workers
$subtasks = $feat.subtasks

foreach ($wid in $workers) {
    $worker = $config.workers | Where-Object { $_.id -eq $wid }
    $subtask = $subtasks.$wid
    $worktreePath = "$worktreeBase\$Feature-$wid"
    $branch = "feature/$Feature-$wid"

    # 创建 worktree
    Write-Host "  创建 Worktree: $wid → $branch" -ForegroundColor Yellow
    git -C $repoRoot worktree add -b $branch $worktreePath HEAD 2>$null
    if ($LASTEXITCODE -ne 0) {
        git -C $repoRoot worktree add $worktreePath $branch 2>$null
    }

    # 构建 prompt
    $prompt = @"
$systemPrompt

---

# 你的角色

Worker ID: $wid
角色名称: $($worker.name)
专长: $($worker.focus)

# 当前任务

## 功能: $Feature — $($feat.name)

**你的具体任务**:
$subtask

## 多智能体协同要求

你**必须**将上述任务拆解为 2-4 个独立子任务，并使用 Agent 工具派出多个子代理并行执行:

1. 分析任务，拆解为可并行的子任务（确保无文件编辑冲突）
2. 同时启动多个子代理，每个负责一个子任务
3. 等待所有子代理完成
4. 集成验证所有改动
5. 运行相关测试确认无破坏

## 完成后

运行验证命令，然后输出:
1. 变更文件清单
2. 验证结果（lint/test）
3. 简要总结做了什么
"@

    # 保存 prompt 到临时文件
    $promptFile = "$worktreeBase\prompt-$wid.md"
    $prompt | Out-File -FilePath $promptFile -Encoding utf8

    # 在新 Windows Terminal 标签页中启动 claude
    $title = "$wid $($worker.name)"

    # 使用 wt (Windows Terminal) 新标签页
    Start-Process wt -ArgumentList @(
        "new-tab",
        "--title", "`"$title`"",
        "--tabColor", "#00B4D8",
        "-d", $worktreePath,
        "cmd", "/k",
        "echo Starting Worker $wid ($($worker.name))... && claude -p `"$(Get-Content $promptFile -Raw)`" --max-turns 50"
    )

    Write-Host "  ✅ Worker $wid ($($worker.name)) 已启动" -ForegroundColor Green
    Start-Sleep -Seconds 2  # 避免同时启动太多进程
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  所有 Workers 已启动！" -ForegroundColor Green
Write-Host "  每个 Worker 在独立的 Windows Terminal 标签页中运行" -ForegroundColor Green
Write-Host "  完成后请运行: python scripts/swarm.py --merge $Feature" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green

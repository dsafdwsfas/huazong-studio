#!/usr/bin/env python3
"""
画宗制片中枢 — Windows 可见窗口启动器
每个 Worker 弹出独立的 cmd.exe 窗口，实时可见输出。
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "swarm-config.json"
PROMPTS_DIR = SCRIPT_DIR / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system-base.md"
WORKTREE_BASE = Path(r"D:\claude\bot-01\workspace\.worktrees")
REPO_ROOT = Path(r"D:\claude\bot-01\workspace\kitsu-frontend")
BAT_DIR = SCRIPT_DIR / "worker-bats"

ROLE_DESCS = {
    "frontend-lead-a": "你是前端主力工程师A，专精 Vue 3 组件开发和页面布局。",
    "frontend-lead-b": "你是前端主力工程师B，专精交互动效、拖拽、Canvas 标注。",
    "backend-lead-a": "你是后端主力工程师A，专精 Flask RESTful API 开发。",
    "backend-lead-b": "你是后端主力工程师B，专精 SQLAlchemy 数据模型和数据库迁移。",
    "integration": "你是集成工程师，负责前后端联调、数据流验证。",
    "testing": "你是测试工程师，负责编写自动化测试、压测脚本。",
    "frontend-support": "你是前端辅助工程师，专精 CSS/SCSS、国际化(i18n)、响应式设计。",
    "backend-support": "你是后端辅助工程师，专精异步任务队列、文件处理。",
    "devops": "你是运维工程师，专精 Docker、CI/CD、部署、监控。",
    "ai-engineer": "你是 AI 工程师，专精 Gemini API 集成、图片分析、风格提取。",
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_system_prompt():
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return ""


def build_prompt(system_prompt, worker, feature, subtask):
    role_desc = ROLE_DESCS.get(worker["role"], "你是开发工程师。")
    return f"""{system_prompt}

---

# 你的角色

{role_desc}

- Worker ID: {worker['id']}
- 角色名称: {worker['name']}
- 专长领域: {worker['focus']}

# 当前任务

## 功能: {feature['id']} — {feature['name']}

**你的具体任务**:
{subtask}

## 多智能体协同要求

你**必须**将上述任务拆解为 2-4 个独立子任务，并使用 Agent 工具派出多个子代理并行执行:

1. 分析任务，拆解为可并行的子任务（确保无文件编辑冲突）
2. 同时启动多个子代理，每个负责一个子任务
3. 等待所有子代理完成
4. 集成验证所有改动
5. 运行相关测试确认无破坏

## 完成后

1. git add 所有改动的文件
2. git commit -m "feat({feature['id']}): {worker['id']} - 描述"
3. 输出变更文件清单和验证结果
"""


def main():
    if len(sys.argv) < 3:
        print("用法: python scripts/launch-windows.py <phase> <feature_id>")
        print("示例: python scripts/launch-windows.py 1 1.1")
        sys.exit(1)

    phase_num = sys.argv[1]
    feature_id = sys.argv[2]
    phase_id = f"phase-{phase_num}"

    config = load_config()
    system_prompt = load_system_prompt()
    workers_map = {w["id"]: w for w in config["workers"]}

    # 找 phase 和 feature
    feature = None
    for p in config["phases"]:
        if p["id"] == phase_id:
            for f in p["features"]:
                if f["id"] == feature_id:
                    feature = f
                    break

    if not feature:
        print(f"错误: 功能 {feature_id} 不存在")
        sys.exit(1)

    worker_ids = feature["workers"]
    subtasks = feature["subtasks"]

    print()
    print("=" * 60)
    print(f"  画宗制片中枢 — 启动 {len(worker_ids)} 个可见窗口")
    print(f"  功能: {feature_id} — {feature['name']}")
    print(f"  Workers: {', '.join(worker_ids)}")
    print("=" * 60)
    print()

    BAT_DIR.mkdir(parents=True, exist_ok=True)
    WORKTREE_BASE.mkdir(parents=True, exist_ok=True)

    for wid in worker_ids:
        worker = workers_map[wid]
        subtask = subtasks.get(wid, "完成分配的任务")
        branch = f"feature/{feature_id}/{wid}"
        wt_path = WORKTREE_BASE / f"{feature_id}-{wid}"

        # 创建 worktree
        if wt_path.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(wt_path)],
                           cwd=str(REPO_ROOT), capture_output=True)
            subprocess.run(["git", "branch", "-D", branch],
                           cwd=str(REPO_ROOT), capture_output=True)

        subprocess.run(["git", "worktree", "add", "-b", branch, str(wt_path), "HEAD"],
                       cwd=str(REPO_ROOT), capture_output=True)
        print(f"  [worktree] {wid} -> {wt_path.name}")

        # 写 prompt 文件
        prompt = build_prompt(system_prompt, worker, feature, subtask)
        prompt_file = BAT_DIR / f"{feature_id}-{wid}-prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")

        # 写 .bat 启动文件
        bat_file = BAT_DIR / f"start-{feature_id}-{wid}.bat"
        bat_content = f"""@echo off
chcp 65001 >nul
title {wid} {worker['name']} ^| {feature_id} {feature['name']}
color 0A
cd /d "{wt_path}"

echo.
echo =========================================
echo   Worker: {wid} - {worker['name']}
echo   Feature: {feature_id} - {feature['name']}
echo   Worktree: {wt_path}
echo   Task: {subtask[:80]}
echo =========================================
echo.
echo Starting claude...
echo.

type "{prompt_file}" | claude -p - --output-format text --max-turns 50 --model sonnet

echo.
echo =========================================
echo   Worker {wid} DONE!
echo =========================================
echo.
pause
"""
        bat_file.write_text(bat_content, encoding="gbk", errors="replace")
        print(f"  [bat]      {bat_file.name}")

    # 生成总启动器 .bat
    master_bat = BAT_DIR / f"START-ALL-{feature_id}.bat"
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        f'echo Starting {len(worker_ids)} workers for feature {feature_id}...',
        "echo.",
    ]
    for wid in worker_ids:
        bat_name = f"start-{feature_id}-{wid}.bat"
        lines.append(f'start "" "{BAT_DIR / bat_name}"')
        lines.append("timeout /t 3 /nobreak >nul")

    lines += [
        "echo.",
        f"echo All {len(worker_ids)} workers launched!",
        "echo.",
        "pause",
    ]
    master_bat.write_text("\r\n".join(lines), encoding="gbk", errors="replace")

    print()
    print("=" * 60)
    print(f"  所有文件已生成！")
    print()
    print(f"  >>> 请双击运行此文件启动所有 Worker:")
    print(f"  {master_bat}")
    print()
    print(f"  或者单独启动某个 Worker:")
    for wid in worker_ids:
        print(f"    {BAT_DIR / f'start-{feature_id}-{wid}.bat'}")
    print()
    print(f"  所有 Worker 完成后运行合并:")
    print(f"    python scripts/merge-visible.py {feature_id}")
    print("=" * 60)

    # 直接用 os.startfile 启动总 bat（这在 Windows 上一定能弹窗）
    print()
    print("  正在启动...")
    os.startfile(str(master_bat))
    print("  ✅ 已启动！请查看弹出的窗口。")


if __name__ == "__main__":
    main()

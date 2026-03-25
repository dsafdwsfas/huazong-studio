#!/usr/bin/env python3
"""
画宗制片中枢 — 可见窗口模式启动器
===================================
每个 Worker 在独立的 Windows Terminal 标签页中运行，实时可见输出。

用法:
  python scripts/launch-visible.py 1 1.1      # 启动 Phase 1 Feature 1.1
  python scripts/launch-visible.py 1 1.1 --dry # 只生成 prompt 文件不启动
"""

import json
import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "swarm-config.json"
PROMPTS_DIR = SCRIPT_DIR / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system-base.md"
WORKTREE_BASE = Path("D:/claude/bot-01/workspace/.worktrees")
REPO_ROOT = Path("D:/claude/bot-01/workspace/kitsu-frontend")
PROMPT_TMP_DIR = SCRIPT_DIR / "worker-prompts"

# Worker 标签页颜色
WORKER_COLORS = {
    "w1":  "#E63946",  # 红 — 前端主力A
    "w2":  "#F4A261",  # 橙 — 前端主力B
    "w3":  "#2A9D8F",  # 绿 — 后端主力A
    "w4":  "#264653",  # 深绿 — 后端主力B
    "w5":  "#E9C46A",  # 金 — 集成
    "w6":  "#606C38",  # 橄榄 — 测试
    "w7":  "#457B9D",  # 蓝 — 前端辅助
    "w8":  "#6D6875",  # 紫灰 — 后端辅助
    "w9":  "#B5838D",  # 玫瑰 — 运维
    "w10": "#7209B7",  # 紫 — AI工程师
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_system_prompt():
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return ""


def build_prompt(system_prompt, worker, feature, subtask):
    role_descs = {
        "frontend-lead-a": "你是前端主力工程师A，专精 Vue 3 组件开发和页面布局。",
        "frontend-lead-b": "你是前端主力工程师B，专精交互动效、拖拽、Canvas 标注。",
        "backend-lead-a": "你是后端主力工程师A，专精 Flask RESTful API 开发。",
        "backend-lead-b": "你是后端主力工程师B，专精 SQLAlchemy 数据模型和数据库迁移。",
        "integration": "你是集成工程师，负责前后端联调、数据流验证、端到端测试。",
        "testing": "你是测试工程师，负责编写自动化测试、压测脚本、质量保障。",
        "frontend-support": "你是前端辅助工程师，专精 CSS/SCSS、国际化(i18n)、响应式设计。",
        "backend-support": "你是后端辅助工程师，专精异步任务队列、文件处理、后台服务。",
        "devops": "你是运维工程师，专精 Docker、CI/CD、部署、监控、数据库运维。",
        "ai-engineer": "你是 AI 工程师，专精 Gemini API 集成、图片分析、风格提取。",
    }

    role_desc = role_descs.get(worker["role"], "你是开发工程师。")

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
3. 输出变更文件清单
4. 输出验证结果（lint/test 是否通过）
"""


def main():
    if len(sys.argv) < 3:
        print("用法: python scripts/launch-visible.py <phase> <feature_id> [--dry]")
        print("示例: python scripts/launch-visible.py 1 1.1")
        sys.exit(1)

    phase_num = sys.argv[1]
    feature_id = sys.argv[2]
    dry_run = "--dry" in sys.argv

    phase_id = f"phase-{phase_num}"
    config = load_config()
    system_prompt = load_system_prompt()

    # 找到 phase 和 feature
    phase = None
    for p in config["phases"]:
        if p["id"] == phase_id:
            phase = p
            break
    if not phase:
        print(f"错误: 阶段 {phase_id} 不存在")
        sys.exit(1)

    feature = None
    for f in phase["features"]:
        if f["id"] == feature_id:
            feature = f
            break
    if not feature:
        print(f"错误: 功能 {feature_id} 不存在")
        sys.exit(1)

    workers_map = {w["id"]: w for w in config["workers"]}
    worker_ids = feature["workers"]
    subtasks = feature["subtasks"]

    print()
    print("━" * 60)
    print(f"  🚀 画宗制片中枢 — 可见窗口模式")
    print(f"  功能: {feature_id} — {feature['name']}")
    print(f"  Workers: {', '.join(worker_ids)}")
    print(f"  模式: {'DRY RUN（只生成文件）' if dry_run else '启动 Windows Terminal 标签页'}")
    print("━" * 60)
    print()

    # 创建 prompt 临时目录
    PROMPT_TMP_DIR.mkdir(parents=True, exist_ok=True)
    WORKTREE_BASE.mkdir(parents=True, exist_ok=True)

    wt_commands = []

    for wid in worker_ids:
        worker = workers_map[wid]
        subtask = subtasks.get(wid, "完成分配的任务")
        branch = f"feature/{feature_id}/{wid}"
        wt_path = WORKTREE_BASE / f"{feature_id}-{wid}"

        # 1. 生成 prompt 文件
        prompt = build_prompt(system_prompt, worker, feature, subtask)
        prompt_file = PROMPT_TMP_DIR / f"{feature_id}-{wid}.md"
        prompt_file.write_text(prompt, encoding="utf-8")
        print(f"  📝 Prompt 已生成: {prompt_file.name}")

        # 2. 创建 worktree
        if wt_path.exists():
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_path)],
                cwd=str(REPO_ROOT), capture_output=True
            )
            subprocess.run(
                ["git", "branch", "-D", branch],
                cwd=str(REPO_ROOT), capture_output=True
            )

        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch, str(wt_path), "HEAD"],
            cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ⚠️  Worktree 创建失败 [{wid}]: {result.stderr.strip()}")
            # 尝试不创建新分支
            subprocess.run(
                ["git", "worktree", "add", str(wt_path), branch],
                cwd=str(REPO_ROOT), capture_output=True
            )

        print(f"  🌿 Worktree: {wt_path.name} → {branch}")

        # 3. 构建 Windows Terminal 命令
        # 用 prompt 文件而不是内联 prompt（避免命令行长度限制）
        prompt_file_win = str(prompt_file).replace("/", "\\")
        wt_path_win = str(wt_path).replace("/", "\\")
        color = WORKER_COLORS.get(wid, "#00B4D8")
        tab_title = f"{wid} {worker['name']} | {feature_id}"

        # claude -p 从文件读取 prompt
        claude_cmd = (
            f'cd /d "{wt_path_win}" && '
            f'echo ========================================= && '
            f'echo   Worker {wid}: {worker["name"]} && '
            f'echo   Feature: {feature_id} - {feature["name"]} && '
            f'echo   Task: {subtask[:60]}... && '
            f'echo ========================================= && '
            f'echo. && '
            f'type "{prompt_file_win}" | claude -p - --output-format text --max-turns 50 --model sonnet && '
            f'echo. && '
            f'echo ========================================= && '
            f'echo   Worker {wid} 完成！请审查代码。 && '
            f'echo ========================================= && '
            f'pause'
        )

        wt_commands.append({
            "wid": wid,
            "title": tab_title,
            "color": color,
            "cmd": claude_cmd,
            "wt_path": wt_path_win,
        })

    if dry_run:
        print()
        print("  DRY RUN 完成。Prompt 文件和 Worktrees 已创建。")
        print(f"  Prompt 目录: {PROMPT_TMP_DIR}")
        print(f"  Worktree 目录: {WORKTREE_BASE}")
        return

    # 4. 启动 Windows Terminal 标签页
    print()
    print("  🖥️  启动 Windows Terminal 标签页...")
    print()

    # 构建 wt.exe 命令 — 所有标签页在一个命令中打开
    # 格式: wt new-tab --title "..." -d "..." cmd /k "..." ; new-tab ...
    wt_args = []

    for i, wc in enumerate(wt_commands):
        if i == 0:
            # 第一个标签页
            wt_args.extend([
                "new-tab",
                "--title", wc["title"],
                "--tabColor", wc["color"],
                "-d", wc["wt_path"],
                "cmd", "/k", wc["cmd"],
            ])
        else:
            # 后续标签页用 ; 分隔
            wt_args.extend([
                ";", "new-tab",
                "--title", wc["title"],
                "--tabColor", wc["color"],
                "-d", wc["wt_path"],
                "cmd", "/k", wc["cmd"],
            ])

    try:
        subprocess.Popen(
            ["wt"] + wt_args,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        time.sleep(2)

        for wc in wt_commands:
            print(f"  ✅ {wc['wid']} ({wc['title']}) — 已启动")

    except FileNotFoundError:
        print("  ⚠️  Windows Terminal (wt.exe) 未找到，降级为 cmd 窗口模式...")
        for wc in wt_commands:
            subprocess.Popen(
                f'start "{wc["title"]}" cmd /k "{wc["cmd"]}"',
                shell=True
            )
            print(f"  ✅ {wc['wid']} — 已在新 cmd 窗口启动")
            time.sleep(1)

    print()
    print("━" * 60)
    print(f"  ✅ {len(wt_commands)} 个 Worker 已在独立标签页启动！")
    print()
    print("  📌 你可以:")
    print("    1. 切换标签页查看每个 Worker 的实时输出")
    print("    2. 所有 Worker 完成后（窗口显示 '按任意键继续'）")
    print("    3. 回到这里运行合并命令:")
    print(f"       python scripts/merge-visible.py {feature_id}")
    print("━" * 60)


if __name__ == "__main__":
    main()

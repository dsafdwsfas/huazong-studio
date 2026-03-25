#!/usr/bin/env python3
"""
画宗制片中枢 — 10 实例 Claude Code 协同开发编排器
====================================================

功能:
1. 读取 swarm-config.json 中的阶段/功能/任务定义
2. 为每个功能创建独立 git worktree
3. 启动多个 claude 实例并行开发
4. 每个实例内部再派多个子代理协同
5. 功能完成后等待用户确认才进入下一个功能
6. 确认后自动合并代码到主分支

用法:
  python scripts/swarm.py                    # 交互式选择阶段和功能
  python scripts/swarm.py --phase 1          # 执行 Phase 1 全部功能
  python scripts/swarm.py --phase 1 --feature 1.1  # 执行指定功能
  python scripts/swarm.py --status           # 查看当前进度
  python scripts/swarm.py --resume           # 从上次中断处继续
"""

import json
import os
import sys
import subprocess
import time
import signal
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "swarm-config.json"
PROGRESS_PATH = SCRIPT_DIR / "swarm-progress.json"
LOGS_DIR = SCRIPT_DIR / "swarm-logs"
PROMPTS_DIR = SCRIPT_DIR / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system-base.md"

# Claude CLI 命令 — Windows 需要 .cmd 扩展名
import platform
if platform.system() == "Windows":
    CLAUDE_CMD = shutil.which("claude.cmd") or shutil.which("claude") or "claude.cmd"
else:
    CLAUDE_CMD = shutil.which("claude") or "claude"

# 颜色
class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def log(msg: str, color: str = ""):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C.DIM}[{ts}]{C.RESET} {color}{msg}{C.RESET}")


def log_ok(msg): log(msg, C.GREEN)
def log_warn(msg): log(msg, C.YELLOW)
def log_err(msg): log(msg, C.RED)
def log_info(msg): log(msg, C.CYAN)
def log_phase(msg): log(msg, f"{C.BOLD}{C.MAGENTA}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 配置加载
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed": [], "current": None, "started_at": None}


def save_progress(progress: dict):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Git Worktree 管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WorktreeManager:
    def __init__(self, config: dict):
        self.repo_root = Path(config["project"]["repo_root"])
        self.worktree_base = Path(config["project"]["worktree_base"])
        self.worktree_base.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, worker_id: str, feature_id: str, branch_name: str) -> Path:
        """为每个 worker 创建独立 worktree"""
        worktree_path = self.worktree_base / f"{feature_id}-{worker_id}"

        # 如果已存在先清理
        if worktree_path.exists():
            self.remove_worktree(worker_id, feature_id)

        # 创建分支和 worktree
        full_branch = f"feature/{branch_name}/{worker_id}"

        # 先确保 develop 分支存在
        subprocess.run(
            ["git", "branch", "develop"],
            cwd=str(self.repo_root),
            capture_output=True
        )

        # 创建 worktree
        result = subprocess.run(
            ["git", "worktree", "add", "-b", full_branch,
             str(worktree_path), "HEAD"],
            cwd=str(self.repo_root),
            capture_output=True, text=True
        )

        if result.returncode != 0:
            # 分支可能已存在，尝试不创建分支
            result = subprocess.run(
                ["git", "worktree", "add", str(worktree_path), full_branch],
                cwd=str(self.repo_root),
                capture_output=True, text=True
            )
            if result.returncode != 0:
                log_err(f"创建 worktree 失败 [{worker_id}]: {result.stderr}")
                return None

        log_ok(f"Worktree 创建成功: {worktree_path.name}")
        return worktree_path

    def remove_worktree(self, worker_id: str, feature_id: str):
        """移除 worktree"""
        worktree_path = self.worktree_base / f"{feature_id}-{worker_id}"
        if worktree_path.exists():
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=str(self.repo_root),
                capture_output=True
            )

    def merge_worktree(self, worker_id: str, feature_id: str, target_branch: str) -> bool:
        """将 worktree 的改动合并到目标分支"""
        worktree_path = self.worktree_base / f"{feature_id}-{worker_id}"
        full_branch = f"feature/{feature_id}-{worker_id.replace('w', 'worker-')}/{worker_id}"

        # 在 worktree 中提交所有改动
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(worktree_path),
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"feat({feature_id}): {worker_id} 完成任务",
             "--allow-empty"],
            cwd=str(worktree_path),
            capture_output=True
        )

        # 合并到目标分支
        result = subprocess.run(
            ["git", "merge", "--no-ff", full_branch,
             "-m", f"merge: {feature_id}/{worker_id} 合并完成"],
            cwd=str(self.repo_root),
            capture_output=True, text=True
        )

        if result.returncode != 0:
            log_warn(f"合并冲突 [{worker_id}]，需手动解决: {result.stderr[:200]}")
            return False

        return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Worker 启动器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WorkerLauncher:
    def __init__(self, config: dict):
        self.config = config
        self.system_prompt = load_system_prompt()
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def build_worker_prompt(self, worker: dict, feature: dict, subtask: str) -> str:
        """为每个 worker 构建专属 prompt"""
        worker_role_desc = {
            "frontend-lead-a": "你是前端主力工程师A，专精 Vue 3 组件开发和页面布局。",
            "frontend-lead-b": "你是前端主力工程师B，专精交互动效、拖拽、Canvas 标注。",
            "backend-lead-a": "你是后端主力工程师A，专精 Flask RESTful API 开发。",
            "backend-lead-b": "你是后端主力工程师B，专精 SQLAlchemy 数据模型和数据库迁移。",
            "integration": "你是集成工程师，负责前后端联调、数据流验证、端到端测试。",
            "testing": "你是测试工程师，负责编写自动化测试、压测脚本、质量保障。",
            "frontend-support": "你是前端辅助工程师，专精 CSS/SCSS、国际化(i18n)、响应式设计。",
            "backend-support": "你是后端辅助工程师，专精异步任务队列、文件处理、后台服务。",
            "devops": "你是运维工程师，专精 Docker、CI/CD、部署、监控、数据库运维。",
            "ai-engineer": "你是 AI 工程师，专精 Gemini API 集成、图片分析、风格提取。"
        }

        role_desc = worker_role_desc.get(worker["role"], "你是开发工程师。")

        prompt = f"""
{self.system_prompt}

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

## 注意事项

- 只修改与你任务相关的文件，不要动其他 worker 负责的部分
- 前端代码在当前目录，后端代码在 ../kitsu-zou/
- 改完后运行 `npm run lint` (前端) 或 `python -m pytest` (后端) 验证
- 提交清晰的 git commit message，格式: feat({feature['id']}): 描述
- 完成后输出变更文件清单和验证结果
"""
        return prompt.strip()

    def launch_worker(self, worker: dict, feature: dict, subtask: str,
                      worktree_path: Path) -> dict:
        """启动一个 claude 实例执行任务"""
        worker_id = worker["id"]
        feature_id = feature["id"]
        log_file = LOGS_DIR / f"{feature_id}-{worker_id}.log"

        prompt = self.build_worker_prompt(worker, feature, subtask)

        log_info(f"启动 Worker {worker_id} ({worker['name']}) → 功能 {feature_id}")

        start_time = time.time()

        try:
            # 使用 claude -p 非交互模式
            # Windows 上必须 shell=True 才能运行 .cmd 文件
            use_shell = platform.system() == "Windows"

            cmd = [CLAUDE_CMD, "-p", prompt,
                   "--output-format", "text",
                   "--max-turns", "50",
                   "--model", "sonnet"]

            result = subprocess.run(
                cmd,
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                timeout=1800,  # 30 分钟超时
                shell=use_shell,
                env={**os.environ, "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}
            )

            elapsed = time.time() - start_time

            # 写日志
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"=== Worker {worker_id} | Feature {feature_id} ===\n")
                f.write(f"Role: {worker['name']}\n")
                f.write(f"Duration: {elapsed:.1f}s\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"\n=== STDOUT ===\n{result.stdout}\n")
                if result.stderr:
                    f.write(f"\n=== STDERR ===\n{result.stderr}\n")

            if result.returncode == 0:
                log_ok(f"Worker {worker_id} 完成 ✓ ({elapsed:.0f}s)")
                return {
                    "worker_id": worker_id,
                    "status": "success",
                    "duration": elapsed,
                    "output": result.stdout[-2000:] if result.stdout else "",
                    "log_file": str(log_file)
                }
            else:
                log_err(f"Worker {worker_id} 失败 ✗ ({elapsed:.0f}s)")
                return {
                    "worker_id": worker_id,
                    "status": "failed",
                    "duration": elapsed,
                    "error": result.stderr[-1000:] if result.stderr else "",
                    "log_file": str(log_file)
                }

        except subprocess.TimeoutExpired:
            log_err(f"Worker {worker_id} 超时 (30分钟)")
            return {
                "worker_id": worker_id,
                "status": "timeout",
                "duration": 1800,
                "log_file": str(log_file)
            }
        except Exception as e:
            log_err(f"Worker {worker_id} 异常: {e}")
            return {
                "worker_id": worker_id,
                "status": "error",
                "error": str(e),
                "log_file": str(log_file)
            }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主编排器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SwarmOrchestrator:
    def __init__(self):
        self.config = load_config()
        self.progress = load_progress()
        self.worktree_mgr = WorktreeManager(self.config)
        self.launcher = WorkerLauncher(self.config)
        self.workers_map = {w["id"]: w for w in self.config["workers"]}

    def get_phase(self, phase_id: str) -> Optional[dict]:
        for p in self.config["phases"]:
            if p["id"] == phase_id:
                return p
        return None

    def get_feature(self, phase: dict, feature_id: str) -> Optional[dict]:
        for f in phase["features"]:
            if f["id"] == feature_id:
                return f
        return None

    def is_completed(self, feature_id: str) -> bool:
        return feature_id in self.progress.get("completed", [])

    def print_banner(self):
        print(f"""
{C.BOLD}{C.CYAN}
  ╔══════════════════════════════════════════════════╗
  ║                                                  ║
  ║   画宗制片中枢 — 多实例协同开发编排器             ║
  ║   HuaZong Studio Swarm Orchestrator              ║
  ║                                                  ║
  ║   10 Workers × N SubAgents = 并行开发            ║
  ║                                                  ║
  ╚══════════════════════════════════════════════════╝
{C.RESET}""")

    def print_status(self):
        """打印当前进度"""
        print(f"\n{C.BOLD}📊 开发进度{C.RESET}\n")
        completed = set(self.progress.get("completed", []))

        for phase in self.config["phases"]:
            phase_features = phase["features"]
            done = sum(1 for f in phase_features if f["id"] in completed)
            total = len(phase_features)
            bar = "█" * done + "░" * (total - done)
            pct = (done / total * 100) if total > 0 else 0

            color = C.GREEN if done == total else (C.YELLOW if done > 0 else C.DIM)
            print(f"  {color}{phase['name']}: [{bar}] {done}/{total} ({pct:.0f}%){C.RESET}")

            for feature in phase_features:
                status = "✅" if feature["id"] in completed else "⏳"
                workers_str = ", ".join(feature["workers"])
                print(f"    {status} {feature['id']} {feature['name']} ({workers_str})")

        print()

    def execute_feature(self, phase: dict, feature: dict) -> bool:
        """执行一个功能：启动多个 worker 并行开发"""
        feature_id = feature["id"]
        feature_name = feature["name"]
        worker_ids = feature["workers"]
        subtasks = feature["subtasks"]

        print(f"""
{C.BOLD}{C.BLUE}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🚀 功能 {feature_id}: {feature_name}
  📋 参与 Workers: {', '.join(worker_ids)}
  🔀 并行度: {len(worker_ids)} 个 Claude 实例
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{C.RESET}""")

        # Step 1: 创建 worktrees
        log_info("Step 1/4: 创建 Git Worktrees...")
        worktrees = {}
        for wid in worker_ids:
            branch_name = f"{feature_id}-{wid}"
            wt_path = self.worktree_mgr.create_worktree(wid, feature_id, branch_name)
            if wt_path:
                worktrees[wid] = wt_path
            else:
                log_err(f"无法为 {wid} 创建 worktree，跳过")

        if not worktrees:
            log_err("所有 worktree 创建失败，终止")
            return False

        # Step 2: 并行启动 workers
        log_info(f"Step 2/4: 启动 {len(worktrees)} 个 Claude 实例并行开发...")
        results = {}

        with ThreadPoolExecutor(max_workers=len(worktrees)) as executor:
            futures = {}
            for wid, wt_path in worktrees.items():
                worker = self.workers_map[wid]
                subtask = subtasks.get(wid, "完成分配的任务")
                future = executor.submit(
                    self.launcher.launch_worker,
                    worker, feature, subtask, wt_path
                )
                futures[future] = wid

            for future in as_completed(futures):
                wid = futures[future]
                try:
                    result = future.result()
                    results[wid] = result
                except Exception as e:
                    results[wid] = {"worker_id": wid, "status": "error", "error": str(e)}

        # Step 3: 汇总结果
        log_info("Step 3/4: 汇总开发结果...")
        self._print_feature_report(feature, results)

        # Step 4: 等待用户确认
        return self._wait_for_confirmation(feature, results)

    def _print_feature_report(self, feature: dict, results: dict):
        """打印功能完成报告"""
        feature_id = feature["id"]
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        total_count = len(results)
        total_duration = sum(r.get("duration", 0) for r in results.values())

        print(f"""
{C.BOLD}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔔 功能 {feature_id} {feature['name']} — 开发完成报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{C.RESET}
  📊 成功率: {success_count}/{total_count}
  ⏱️  总耗时: {total_duration:.0f}s
""")

        for wid, result in results.items():
            worker = self.workers_map.get(wid, {"name": wid})
            status_icon = {
                "success": f"{C.GREEN}✅ 成功{C.RESET}",
                "failed": f"{C.RED}❌ 失败{C.RESET}",
                "timeout": f"{C.YELLOW}⏰ 超时{C.RESET}",
                "error": f"{C.RED}💥 异常{C.RESET}"
            }.get(result["status"], "❓ 未知")

            duration = result.get("duration", 0)
            print(f"  {status_icon} {wid} ({worker['name']}) — {duration:.0f}s")

            if result["status"] == "failed" and "error" in result:
                print(f"       错误: {result['error'][:200]}")

            if "log_file" in result:
                print(f"       日志: {result['log_file']}")

        print()

    def _wait_for_confirmation(self, feature: dict, results: dict) -> bool:
        """等待用户确认"""
        feature_id = feature["id"]
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        total_count = len(results)

        if success_count == 0:
            log_err(f"功能 {feature_id} 全部失败，请检查日志后重试")
            return False

        print(f"""
{C.BOLD}{C.YELLOW}
  ⏸️  等待确认 — 功能 {feature_id}: {feature['name']}

  请审查代码和日志后选择:
    [y/Y] ✅ 确认通过 → 合并代码，进入下一个功能
    [r/R] 🔄 重试     → 重新执行此功能
    [s/S] ⏭️  跳过     → 标记跳过，进入下一个功能
    [q/Q] 🛑 退出     → 保存进度，退出编排器
{C.RESET}""")

        while True:
            try:
                choice = input(f"  {C.BOLD}请选择 [y/r/s/q]: {C.RESET}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return False

            if choice in ("y", "yes"):
                # 合并所有成功的 worktree
                log_info("合并代码到主分支...")
                for wid, result in results.items():
                    if result["status"] == "success":
                        self.worktree_mgr.merge_worktree(wid, feature_id, "develop")

                # 清理 worktrees
                for wid in feature["workers"]:
                    self.worktree_mgr.remove_worktree(wid, feature_id)

                # 记录进度
                self.progress.setdefault("completed", []).append(feature_id)
                save_progress(self.progress)
                log_ok(f"功能 {feature_id} 已确认通过 ✓")
                return True

            elif choice in ("r", "retry"):
                log_warn("将重新执行此功能...")
                # 清理 worktrees
                for wid in feature["workers"]:
                    self.worktree_mgr.remove_worktree(wid, feature_id)
                return None  # 信号: 需要重试

            elif choice in ("s", "skip"):
                log_warn(f"功能 {feature_id} 已跳过")
                for wid in feature["workers"]:
                    self.worktree_mgr.remove_worktree(wid, feature_id)
                return True

            elif choice in ("q", "quit"):
                log_info("保存进度并退出...")
                self.progress["current"] = feature_id
                save_progress(self.progress)
                return False

            else:
                print(f"  无效选择，请输入 y/r/s/q")

    def run_phase(self, phase_id: str, start_feature: Optional[str] = None):
        """执行一个阶段的所有功能"""
        phase = self.get_phase(phase_id)
        if not phase:
            log_err(f"阶段 {phase_id} 不存在")
            return

        log_phase(f"\n{'='*60}")
        log_phase(f"  Phase: {phase['name']}")
        log_phase(f"  功能数: {len(phase['features'])}")
        log_phase(f"{'='*60}\n")

        started = start_feature is None
        for feature in phase["features"]:
            if not started:
                if feature["id"] == start_feature:
                    started = True
                else:
                    continue

            if self.is_completed(feature["id"]):
                log_ok(f"功能 {feature['id']} 已完成，跳过")
                continue

            while True:
                result = self.execute_feature(phase, feature)
                if result is None:
                    # 重试
                    continue
                elif result is False:
                    # 退出
                    return
                else:
                    # 通过，进入下一个
                    break

        log_ok(f"\n🎉 Phase {phase_id} 全部完成！\n")

    def interactive_menu(self):
        """交互式菜单"""
        self.print_banner()
        self.print_status()

        print(f"{C.BOLD}请选择操作:{C.RESET}")
        print(f"  1. 执行 Phase 1 — 基础改造与品牌重塑")
        print(f"  2. 执行 Phase 2 — 分镜管理与标注系统")
        print(f"  3. 执行 Phase 3 — AI 风格引擎与智能资产")
        print(f"  4. 执行 Phase 4 — 永久资产库与智能节点")
        print(f"  5. 从上次中断处继续")
        print(f"  6. 执行指定功能")
        print(f"  7. 重置进度")
        print(f"  0. 退出")
        print()

        try:
            choice = input(f"  {C.BOLD}请选择 [0-7]: {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if choice == "1":
            self.run_phase("phase-1")
        elif choice == "2":
            self.run_phase("phase-2")
        elif choice == "3":
            self.run_phase("phase-3")
        elif choice == "4":
            self.run_phase("phase-4")
        elif choice == "5":
            self.resume()
        elif choice == "6":
            self.run_specific_feature()
        elif choice == "7":
            self.reset_progress()
        elif choice == "0":
            log_info("退出")
        else:
            log_warn("无效选择")

    def resume(self):
        """从上次中断处继续"""
        current = self.progress.get("current")
        if not current:
            log_warn("没有找到中断点，请选择阶段执行")
            return

        # 找到 current 所在的 phase
        for phase in self.config["phases"]:
            for feature in phase["features"]:
                if feature["id"] == current:
                    log_info(f"从 {current} ({feature['name']}) 继续...")
                    self.run_phase(phase["id"], start_feature=current)
                    return

        log_err(f"无法找到功能 {current}")

    def run_specific_feature(self):
        """执行指定功能"""
        feature_id = input(f"  输入功能 ID (如 1.1): ").strip()

        for phase in self.config["phases"]:
            feature = self.get_feature(phase, feature_id)
            if feature:
                result = self.execute_feature(phase, feature)
                return

        log_err(f"功能 {feature_id} 不存在")

    def reset_progress(self):
        """重置进度"""
        confirm = input(f"  {C.RED}确认重置所有进度? [yes/no]: {C.RESET}").strip()
        if confirm == "yes":
            self.progress = {"completed": [], "current": None, "started_at": None}
            save_progress(self.progress)
            log_ok("进度已重置")
        else:
            log_info("已取消")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 快速启动脚本生成器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_launch_scripts():
    """生成各平台启动脚本"""
    config = load_config()

    # 生成 PowerShell 启动脚本（Windows 并行窗口）
    ps_script = SCRIPT_DIR / "launch-swarm.ps1"
    ps_content = '''# 画宗制片中枢 — 10 窗口并行启动脚本 (PowerShell)
# 用法: .\\scripts\\launch-swarm.ps1 -Phase 1 -Feature "1.1"

param(
    [Parameter(Mandatory=$true)]
    [int]$Phase,

    [Parameter(Mandatory=$true)]
    [string]$Feature
)

$ErrorActionPreference = "Stop"
$config = Get-Content ".\\scripts\\swarm-config.json" | ConvertFrom-Json
$repoRoot = $config.project.repo_root
$worktreeBase = $config.project.worktree_base
$systemPrompt = Get-Content ".\\scripts\\prompts\\system-base.md" -Raw

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
    $worktreePath = "$worktreeBase\\$Feature-$wid"
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
    $promptFile = "$worktreeBase\\prompt-$wid.md"
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
'''
    with open(ps_script, "w", encoding="utf-8") as f:
        f.write(ps_content)

    # 生成 Bash 启动脚本（WSL/Linux/Mac）
    bash_script = SCRIPT_DIR / "launch-swarm.sh"
    bash_content = '''#!/usr/bin/env bash
# 画宗制片中枢 — 10 窗口并行启动脚本 (Bash)
# 用法: bash scripts/launch-swarm.sh <phase> <feature_id>
# 示例: bash scripts/launch-swarm.sh 1 1.1

set -euo pipefail

PHASE="${1:?用法: $0 <phase> <feature_id>}"
FEATURE="${2:?用法: $0 <phase> <feature_id>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/swarm-config.json"
SYSTEM_PROMPT="$SCRIPT_DIR/prompts/system-base.md"

# 解析配置
REPO_ROOT=$(python3 -c "
import json
c = json.load(open('$CONFIG'))
print(c['project']['repo_root'])
")
WORKTREE_BASE=$(python3 -c "
import json
c = json.load(open('$CONFIG'))
print(c['project']['worktree_base'])
")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  画宗制片中枢 — 启动多窗口并行开发"
echo "  功能: $FEATURE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

mkdir -p "$WORKTREE_BASE"

# 解析 workers 和 subtasks
WORKERS=$(python3 -c "
import json
c = json.load(open('$CONFIG'))
phase = [p for p in c['phases'] if p['id'] == 'phase-$PHASE'][0]
feat = [f for f in phase['features'] if f['id'] == '$FEATURE'][0]
for wid in feat['workers']:
    worker = [w for w in c['workers'] if w['id'] == wid][0]
    subtask = feat['subtasks'].get(wid, '完成分配的任务')
    # 用 | 分隔字段
    print(f\"{wid}|{worker['name']}|{worker['focus']}|{subtask}\")
")

PIDS=()
LOG_DIR="$SCRIPT_DIR/swarm-logs"
mkdir -p "$LOG_DIR"

while IFS='|' read -r WID WNAME WFOCUS WSUBTASK; do
    WORKTREE_PATH="$WORKTREE_BASE/$FEATURE-$WID"
    BRANCH="feature/$FEATURE-$WID"
    LOG_FILE="$LOG_DIR/$FEATURE-$WID.log"

    # 创建 worktree
    echo "  创建 Worktree: $WID → $BRANCH"
    git -C "$REPO_ROOT" worktree add -b "$BRANCH" "$WORKTREE_PATH" HEAD 2>/dev/null || \
    git -C "$REPO_ROOT" worktree add "$WORKTREE_PATH" "$BRANCH" 2>/dev/null || true

    # 构建 prompt
    SYSTEM_CONTENT=$(cat "$SYSTEM_PROMPT" 2>/dev/null || echo "")
    PROMPT="$SYSTEM_CONTENT

---

# 你的角色
Worker ID: $WID | 角色: $WNAME | 专长: $WFOCUS

# 当前任务
## 功能: $FEATURE

**你的具体任务**: $WSUBTASK

## 多智能体协同要求
你**必须**将任务拆解为 2-4 个独立子任务，使用 Agent 工具派多个子代理并行执行。
完成后输出变更文件清单和验证结果。"

    # 后台启动 claude
    echo "  🚀 启动 Worker $WID ($WNAME)..."
    CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 \
    claude -p "$PROMPT" --output-format text --max-turns 50 --model sonnet \
        > "$LOG_FILE" 2>&1 &
    PIDS+=($!)

    sleep 1

done <<< "$WORKERS"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  所有 Workers 已在后台启动！"
echo "  PID 列表: ${PIDS[*]}"
echo "  日志目录: $LOG_DIR"
echo ""
echo "  监控命令:"
echo "    tail -f $LOG_DIR/$FEATURE-*.log"
echo ""
echo "  等待全部完成:"
echo "    wait ${PIDS[*]}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 等待所有完成
echo ""
echo "⏳ 等待所有 Workers 完成..."
FAILED=0
for PID in "${PIDS[@]}"; do
    if ! wait "$PID"; then
        FAILED=$((FAILED + 1))
    fi
done

echo ""
if [ "$FAILED" -eq 0 ]; then
    echo "✅ 所有 Workers 完成！请审查日志后运行:"
    echo "   python3 scripts/swarm.py --merge $FEATURE"
else
    echo "⚠️  $FAILED 个 Worker 失败，请检查日志:"
    echo "   ls $LOG_DIR/$FEATURE-*.log"
fi
'''
    with open(bash_script, "w", encoding="utf-8", newline="\n") as f:
        f.write(bash_content)

    # 生成合并脚本
    merge_script = SCRIPT_DIR / "merge-feature.sh"
    merge_content = '''#!/usr/bin/env bash
# 合并指定功能的所有 worker 分支
# 用法: bash scripts/merge-feature.sh <feature_id>

FEATURE="${1:?用法: $0 <feature_id>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/swarm-config.json"

REPO_ROOT=$(python3 -c "
import json; c = json.load(open('$CONFIG'))
print(c['project']['repo_root'])
")
WORKTREE_BASE=$(python3 -c "
import json; c = json.load(open('$CONFIG'))
print(c['project']['worktree_base'])
")

WORKERS=$(python3 -c "
import json; c = json.load(open('$CONFIG'))
for p in c['phases']:
    for f in p['features']:
        if f['id'] == '$FEATURE':
            print(' '.join(f['workers']))
            break
")

echo "合并功能 $FEATURE 的所有 worker 分支..."

cd "$REPO_ROOT"

for WID in $WORKERS; do
    BRANCH="feature/$FEATURE-$WID"
    WORKTREE="$WORKTREE_BASE/$FEATURE-$WID"

    if [ -d "$WORKTREE" ]; then
        echo "  合并 $WID ($BRANCH)..."

        # 提交 worktree 中的改动
        git -C "$WORKTREE" add -A 2>/dev/null
        git -C "$WORKTREE" commit -m "feat($FEATURE): $WID 完成任务" --allow-empty 2>/dev/null

        # 合并
        git merge --no-ff "$BRANCH" -m "merge($FEATURE): $WID" 2>/dev/null && \
            echo "    ✅ 合并成功" || \
            echo "    ⚠️  合并冲突，需手动解决"

        # 清理 worktree
        git worktree remove --force "$WORKTREE" 2>/dev/null
    fi
done

echo ""
echo "✅ 功能 $FEATURE 合并完成"
'''
    with open(merge_script, "w", encoding="utf-8", newline="\n") as f:
        f.write(merge_content)

    log_ok("启动脚本已生成:")
    log_info(f"  PowerShell: {ps_script}")
    log_info(f"  Bash:       {bash_script}")
    log_info(f"  合并脚本:   {merge_script}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    import argparse

    parser = argparse.ArgumentParser(description="画宗制片中枢 — 多实例协同开发编排器")
    parser.add_argument("--phase", type=int, help="执行指定阶段 (1-4)")
    parser.add_argument("--feature", type=str, help="执行指定功能 (如 1.1)")
    parser.add_argument("--status", action="store_true", help="查看当前进度")
    parser.add_argument("--resume", action="store_true", help="从上次中断处继续")
    parser.add_argument("--merge", type=str, help="合并指定功能的 worktrees")
    parser.add_argument("--generate-scripts", action="store_true", help="生成启动脚本")
    parser.add_argument("--reset", action="store_true", help="重置进度")

    args = parser.parse_args()

    orchestrator = SwarmOrchestrator()

    if args.generate_scripts:
        generate_launch_scripts()
    elif args.status:
        orchestrator.print_banner()
        orchestrator.print_status()
    elif args.resume:
        orchestrator.print_banner()
        orchestrator.resume()
    elif args.reset:
        orchestrator.reset_progress()
    elif args.phase:
        orchestrator.print_banner()
        phase_id = f"phase-{args.phase}"
        if args.feature:
            # 执行指定功能
            phase = orchestrator.get_phase(phase_id)
            if phase:
                feature = orchestrator.get_feature(phase, args.feature)
                if feature:
                    orchestrator.execute_feature(phase, feature)
                else:
                    log_err(f"功能 {args.feature} 不存在")
            else:
                log_err(f"阶段 {phase_id} 不存在")
        else:
            orchestrator.run_phase(phase_id)
    else:
        orchestrator.interactive_menu()


if __name__ == "__main__":
    main()

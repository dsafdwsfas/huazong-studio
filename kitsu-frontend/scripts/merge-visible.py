#!/usr/bin/env python3
"""
合并所有 Worker 的改动到 develop 分支
用法: python scripts/merge-visible.py <feature_id>
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "swarm-config.json"
REPO_ROOT = Path("D:/claude/bot-01/workspace/kitsu-frontend")
WORKTREE_BASE = Path("D:/claude/bot-01/workspace/.worktrees")
PROGRESS_PATH = SCRIPT_DIR / "swarm-progress.json"


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/merge-visible.py <feature_id>")
        sys.exit(1)

    feature_id = sys.argv[1]

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 找到 feature
    feature = None
    for phase in config["phases"]:
        for f in phase["features"]:
            if f["id"] == feature_id:
                feature = f
                break

    if not feature:
        print(f"错误: 功能 {feature_id} 不存在")
        sys.exit(1)

    print()
    print("━" * 60)
    print(f"  🔀 合并功能 {feature_id}: {feature['name']}")
    print("━" * 60)
    print()

    # 切换到 develop 分支
    subprocess.run(["git", "checkout", "develop"], cwd=str(REPO_ROOT), capture_output=True)

    merged = 0
    failed = 0

    for wid in feature["workers"]:
        branch = f"feature/{feature_id}/{wid}"
        wt_path = WORKTREE_BASE / f"{feature_id}-{wid}"

        # 检查 worktree 是否有改动
        if wt_path.exists():
            # 提交 worktree 中的改动
            subprocess.run(["git", "add", "-A"], cwd=str(wt_path), capture_output=True)
            result = subprocess.run(
                ["git", "diff", "--cached", "--stat"],
                cwd=str(wt_path), capture_output=True, text=True
            )
            has_changes = bool(result.stdout.strip())

            if has_changes:
                subprocess.run(
                    ["git", "commit", "-m", f"feat({feature_id}): {wid} 完成任务"],
                    cwd=str(wt_path), capture_output=True
                )
                print(f"  📦 {wid}: 有改动，已提交")
                print(f"       {result.stdout.strip().split(chr(10))[-1]}")
            else:
                # 检查是否已经有 commit
                log = subprocess.run(
                    ["git", "log", "develop..HEAD", "--oneline"],
                    cwd=str(wt_path), capture_output=True, text=True
                )
                if log.stdout.strip():
                    print(f"  📦 {wid}: 已有提交")
                else:
                    print(f"  ⚪ {wid}: 无改动")
                    continue

        # 合并分支
        result = subprocess.run(
            ["git", "merge", "--no-ff", branch,
             "-m", f"merge({feature_id}): {wid} 合并"],
            cwd=str(REPO_ROOT), capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"  ✅ {wid}: 合并成功")
            merged += 1
        else:
            print(f"  ❌ {wid}: 合并冲突")
            print(f"       {result.stderr.strip()[:200]}")
            # 中止合并
            subprocess.run(["git", "merge", "--abort"], cwd=str(REPO_ROOT), capture_output=True)
            failed += 1

    # 清理 worktrees
    print()
    clean = input("  清理 worktrees? [y/n]: ").strip().lower()
    if clean == "y":
        for wid in feature["workers"]:
            wt_path = WORKTREE_BASE / f"{feature_id}-{wid}"
            branch = f"feature/{feature_id}/{wid}"
            if wt_path.exists():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(wt_path)],
                    cwd=str(REPO_ROOT), capture_output=True
                )
            subprocess.run(
                ["git", "branch", "-D", branch],
                cwd=str(REPO_ROOT), capture_output=True
            )
        print("  🧹 已清理")

    # 更新进度
    if merged > 0:
        progress = {"completed": [], "current": None}
        if PROGRESS_PATH.exists():
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                progress = json.load(f)
        if feature_id not in progress.get("completed", []):
            progress.setdefault("completed", []).append(feature_id)
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)

    print()
    print("━" * 60)
    print(f"  📊 结果: {merged} 成功, {failed} 失败")
    if failed == 0:
        print(f"  ✅ 功能 {feature_id} 合并完成！可以启动下一个功能了。")
    else:
        print(f"  ⚠️  有冲突需要手动解决")
    print("━" * 60)


if __name__ == "__main__":
    main()

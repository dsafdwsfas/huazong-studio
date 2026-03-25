#!/usr/bin/env bash
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
    print(f"{wid}|{worker['name']}|{worker['focus']}|{subtask}")
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
    git -C "$REPO_ROOT" worktree add -b "$BRANCH" "$WORKTREE_PATH" HEAD 2>/dev/null ||     git -C "$REPO_ROOT" worktree add "$WORKTREE_PATH" "$BRANCH" 2>/dev/null || true

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
    CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1     claude -p "$PROMPT" --output-format text --max-turns 50 --model sonnet         > "$LOG_FILE" 2>&1 &
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

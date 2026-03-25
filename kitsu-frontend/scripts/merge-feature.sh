#!/usr/bin/env bash
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
        git merge --no-ff "$BRANCH" -m "merge($FEATURE): $WID" 2>/dev/null &&             echo "    ✅ 合并成功" ||             echo "    ⚠️  合并冲突，需手动解决"

        # 清理 worktree
        git worktree remove --force "$WORKTREE" 2>/dev/null
    fi
done

echo ""
echo "✅ 功能 $FEATURE 合并完成"

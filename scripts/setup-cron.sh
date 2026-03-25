#!/bin/bash
# =============================================
# 画宗制片中枢 — 安装定时备份 Cron Job
# 用法: sudo bash scripts/setup-cron.sh
# =============================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_SCRIPT="$PROJECT_ROOT/scripts/backup-to-cos.sh"
CRON_LOG="/var/log/huazong-backup.log"

# 检查是否 root
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ 请使用 sudo 执行此脚本"
  exit 1
fi

# 确保备份脚本可执行
chmod +x "$BACKUP_SCRIPT"

# Cron 表达式：每天凌晨 3:17 执行（避开整点高峰）
CRON_EXPR="17 3 * * *"
CRON_CMD="cd $PROJECT_ROOT && bash $BACKUP_SCRIPT >> $CRON_LOG 2>&1"
CRON_LINE="$CRON_EXPR $CRON_CMD"
CRON_MARKER="# huazong-backup"

# 检查是否已安装
if crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
  echo "⚠️  Cron job 已存在，更新中..."
  # 移除旧条目
  crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab -
fi

# 安装新 cron job
(crontab -l 2>/dev/null; echo "$CRON_LINE $CRON_MARKER") | crontab -

# 创建日志文件
touch "$CRON_LOG"
chmod 644 "$CRON_LOG"

# 配置 logrotate 防止日志膨胀
cat > /etc/logrotate.d/huazong-backup << 'LOGROTATE'
/var/log/huazong-backup.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    create 644 root root
}
LOGROTATE

echo ""
echo "✅ 定时备份已安装:"
echo "   时间: 每天凌晨 3:17"
echo "   脚本: $BACKUP_SCRIPT"
echo "   日志: $CRON_LOG"
echo ""
echo "当前 crontab:"
crontab -l | grep huazong || true
echo ""
echo "📝 手动测试: bash $BACKUP_SCRIPT"
echo "📝 查看日志: tail -f $CRON_LOG"

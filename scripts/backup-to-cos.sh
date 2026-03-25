#!/bin/bash
# =============================================
# 画宗制片中枢 — 自动备份到腾讯云 COS
# 用法: bash scripts/backup-to-cos.sh
# 功能: 备份 PostgreSQL → gzip → 上传 COS → 清理本地旧备份
# =============================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 加载环境变量
if [ ! -f .env ]; then
  echo "❌ 未找到 .env 文件" >&2
  exit 1
fi
set -a; source .env; set +a

# ---------- 配置 ----------
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_PREFIX=$(date +%Y/%m)
BACKUP_DIR="$PROJECT_ROOT/backups"
BACKUP_FILE="db_${TIMESTAMP}.sql.gz"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"
COS_BACKUP_KEY="backups/${DATE_PREFIX}/${BACKUP_FILE}"
LOCAL_KEEP_DAYS=7
COS_KEEP_DAYS=90
LOG_FILE="$BACKUP_DIR/backup.log"

mkdir -p "$BACKUP_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ---------- Step 1: 备份 PostgreSQL ----------
log "💾 开始备份 PostgreSQL..."
if docker compose exec -T db pg_dump \
  -U "${POSTGRES_USER:-huazong}" \
  "${POSTGRES_DB:-huazong_studio}" \
  --no-owner --no-privileges \
  | gzip > "$BACKUP_PATH"; then
  FILESIZE=$(du -h "$BACKUP_PATH" | cut -f1)
  log "✅ 数据库备份完成: $BACKUP_FILE ($FILESIZE)"
else
  log "❌ 数据库备份失败"
  rm -f "$BACKUP_PATH"
  exit 1
fi

# ---------- Step 2: 上传到 COS ----------
if [ -n "${COS_SECRET_ID:-}" ] && [ "${COS_SECRET_ID:-}" != "your-cos-secret-id" ]; then
  log "☁️  上传到 COS: $COS_BACKUP_KEY ..."

  # 使用 coscli 上传（如果已安装）
  if command -v coscli &>/dev/null; then
    BUCKET="${COS_BUCKET_FILES:-huazong-files-1250000000}"
    if coscli cp "$BACKUP_PATH" "cos://${BUCKET}/${COS_BACKUP_KEY}" \
      --secret-id "$COS_SECRET_ID" \
      --secret-key "$COS_SECRET_KEY" \
      --region "${COS_REGION:-ap-beijing}" 2>>"$LOG_FILE"; then
      log "✅ COS 上传成功: cos://${BUCKET}/${COS_BACKUP_KEY}"
    else
      log "⚠️  coscli 上传失败，尝试 curl 方式..."
      upload_with_curl
    fi
  else
    upload_with_curl
  fi
else
  log "⏭️  COS 未配置，仅保留本地备份"
fi

# curl 上传函数（使用 COS PUT Object + 签名）
upload_with_curl() {
  # 简化版：通过 Docker 容器内 Python COS SDK 上传
  log "📦 使用 Python COS SDK 上传..."
  docker compose exec -T api python3 -c "
import os, sys
try:
    from qcloud_cos import CosConfig, CosS3Client

    config = CosConfig(
        Region=os.environ.get('COS_REGION', 'ap-beijing'),
        SecretId=os.environ['COS_SECRET_ID'],
        SecretKey=os.environ['COS_SECRET_KEY'],
    )
    client = CosS3Client(config)
    bucket = os.environ.get('COS_BUCKET_FILES', 'huazong-files-1250000000')

    # 从 stdin 读取不可行，改用容器可访问的路径
    print('SDK_READY')
except Exception as e:
    print(f'SDK_ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>>"$LOG_FILE"

  # 通过 docker cp + 容器内上传
  CONTAINER_NAME=$(docker compose ps -q api)
  if [ -n "$CONTAINER_NAME" ]; then
    docker cp "$BACKUP_PATH" "$CONTAINER_NAME:/tmp/$BACKUP_FILE"
    docker compose exec -T api python3 -c "
import os
from qcloud_cos import CosConfig, CosS3Client

config = CosConfig(
    Region=os.environ.get('COS_REGION', 'ap-beijing'),
    SecretId=os.environ['COS_SECRET_ID'],
    SecretKey=os.environ['COS_SECRET_KEY'],
)
client = CosS3Client(config)
bucket = os.environ.get('COS_BUCKET_FILES', 'huazong-files-1250000000')
key = '${COS_BACKUP_KEY}'

with open('/tmp/${BACKUP_FILE}', 'rb') as f:
    client.put_object(Bucket=bucket, Body=f, Key=key)
print(f'Uploaded to cos://{bucket}/{key}')

os.remove('/tmp/${BACKUP_FILE}')
" 2>>"$LOG_FILE" && log "✅ COS 上传成功" || log "⚠️  COS 上传失败，仅保留本地备份"
  else
    log "⚠️  找不到 API 容器，跳过 COS 上传"
  fi
}

# ---------- Step 3: 清理本地旧备份 ----------
DELETED_LOCAL=$(find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +${LOCAL_KEEP_DAYS} -delete -print 2>/dev/null | wc -l)
if [ "$DELETED_LOCAL" -gt 0 ]; then
  log "🧹 清理本地 ${LOCAL_KEEP_DAYS} 天前的备份: ${DELETED_LOCAL} 个文件"
fi

# ---------- Step 4: 清理 COS 旧备份（可选） ----------
if [ -n "${COS_SECRET_ID:-}" ] && [ "${COS_SECRET_ID:-}" != "your-cos-secret-id" ] && command -v coscli &>/dev/null; then
  CUTOFF_DATE=$(date -d "-${COS_KEEP_DAYS} days" +%Y%m%d 2>/dev/null || date -v-${COS_KEEP_DAYS}d +%Y%m%d 2>/dev/null || echo "")
  if [ -n "$CUTOFF_DATE" ]; then
    log "🧹 COS 旧备份清理: 保留最近 ${COS_KEEP_DAYS} 天"
    # COS 清理通过生命周期规则更好，这里只记录日志
    log "💡 建议在 COS 控制台配置生命周期规则自动清理 backups/ 前缀下 ${COS_KEEP_DAYS} 天前的文件"
  fi
fi

# ---------- 汇总 ----------
log "📊 备份汇总:"
log "   本地备份数: $(ls "$BACKUP_DIR"/db_*.sql.gz 2>/dev/null | wc -l)"
log "   本地占用: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)"
log "✅ 备份任务完成"

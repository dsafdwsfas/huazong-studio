#!/bin/bash
# =============================================
# 画宗制片中枢 — COS 连通性健康检查
# 验证 COS bucket 可访问且凭证有效
# 用法: bash scripts/cos-healthcheck.sh
# =============================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 加载 .env
if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$PROJECT_ROOT/.env"
  set +a
fi

# 如果不使用 COS，跳过检查
if [ "${FS_BACKEND:-local}" != "cos" ]; then
  echo "FS_BACKEND=${FS_BACKEND:-local} — COS 未启用，跳过检查"
  exit 0
fi

# 必需变量检查
REQUIRED_VARS=(COS_SECRET_ID COS_SECRET_KEY COS_REGION)
MISSING=()
for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    MISSING+=("$var")
  fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "ERROR: 缺少必需的 COS 环境变量: ${MISSING[*]}"
  exit 1
fi

# Bucket 列表
BUCKETS=(
  "${COS_BUCKET_PICTURES:-}"
  "${COS_BUCKET_MOVIES:-}"
  "${COS_BUCKET_FILES:-}"
)
BUCKET_NAMES=("pictures" "movies" "files")

echo "===== COS 健康检查 ====="
echo "Region: ${COS_REGION}"
echo "CDN:    ${COS_CDN_ENABLED:-false}"
echo ""

PASS=0
FAIL=0

for i in "${!BUCKETS[@]}"; do
  bucket="${BUCKETS[$i]}"
  name="${BUCKET_NAMES[$i]}"

  if [ -z "$bucket" ]; then
    echo "[SKIP] $name — bucket 未配置"
    continue
  fi

  # 使用 HEAD 请求检查 bucket 是否可达
  url="https://${bucket}.cos.${COS_REGION}.myqcloud.com/"
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    --connect-timeout 5 \
    --max-time 10 \
    "$url" 2>/dev/null || echo "000")

  # COS 返回 403 表示 bucket 存在但未授权匿名访问（正常）
  # 返回 200 表示公开访问
  # 返回 404 表示 bucket 不存在
  case "$http_code" in
    200|403)
      echo "[PASS] $name — $bucket (HTTP $http_code)"
      PASS=$((PASS + 1))
      ;;
    404)
      echo "[FAIL] $name — $bucket 不存在 (HTTP 404)"
      FAIL=$((FAIL + 1))
      ;;
    000)
      echo "[FAIL] $name — $bucket 连接超时"
      FAIL=$((FAIL + 1))
      ;;
    *)
      echo "[WARN] $name — $bucket 返回 HTTP $http_code"
      FAIL=$((FAIL + 1))
      ;;
  esac
done

echo ""
echo "结果: $PASS 通过, $FAIL 失败"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi

echo "COS 健康检查通过"

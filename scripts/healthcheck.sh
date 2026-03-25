#!/bin/bash
# =============================================
# 画宗制片中枢 — 服务健康检查
# 用于部署后验证 + 定时监控（可配合 crontab 使用）
# 用法: bash scripts/healthcheck.sh
# =============================================

set -e

check_service() {
  local name=$1
  local url=$2
  local expected=$3

  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
  if [ "$status" = "$expected" ]; then
    echo "✅ $name: HTTP $status"
    return 0
  else
    echo "❌ $name: HTTP $status (期望 $expected)"
    return 1
  fi
}

echo "🏥 画宗制片中枢健康检查"
echo "========================"
FAILS=0

check_service "Nginx (前端)" "http://localhost" "200" || ((FAILS++))
check_service "API 服务" "http://localhost/api/status" "200" || ((FAILS++))
check_service "Meilisearch" "http://localhost:7700/health" "200" || ((FAILS++))

# 检查 Redis 连通性
echo ""
echo "--- Redis ---"
if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
  echo "✅ Redis: PONG"
else
  echo "❌ Redis: 无响应"
  ((FAILS++))
fi

# 检查容器状态
echo ""
echo "--- 容器状态 ---"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
if [ $FAILS -gt 0 ]; then
  echo "⚠️  $FAILS 个服务异常"
  exit 1
else
  echo "✅ 所有服务正常"
fi

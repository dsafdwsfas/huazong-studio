#!/bin/bash
# =============================================
# 画宗制片中枢 — 腾讯云一键部署脚本
# 用法: bash scripts/deploy.sh [up|down|restart|logs|status|backup|update]
# =============================================

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 加载 .env（用于 backup 命令读取变量）
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

case "${1:-up}" in
  up)
    if [ ! -f .env ]; then
      echo "❌ 未找到 .env 文件，请先复制 .env.example 并填写配置"
      echo "   cp .env.example .env && vim .env"
      exit 1
    fi
    # 首次部署：如果没有 active-nginx.conf，用 HTTP-only 版本
    if [ ! -f "$PROJECT_ROOT/nginx/active-nginx.conf" ]; then
      echo "📝 首次部署，使用 HTTP-only 配置（之后运行 setup-ssl.sh 启用 HTTPS）"
      cp "$PROJECT_ROOT/nginx/nginx-http-only.conf" "$PROJECT_ROOT/nginx/active-nginx.conf"
    fi
    echo "🚀 启动画宗制片中枢..."
    docker compose up -d --build
    echo "⏳ 等待服务就绪..."
    sleep 10
    docker compose ps
    echo ""
    # COS 连通性检查（仅在 FS_BACKEND=cos 时执行）
    if [ "${FS_BACKEND:-local}" = "cos" ]; then
      echo "☁️  验证 COS 连通性..."
      if bash "$PROJECT_ROOT/scripts/cos-healthcheck.sh"; then
        echo "✅ COS 连通性正常"
      else
        echo "⚠️  COS 连通性检查失败，请检查 COS 配置"
        echo "   服务已启动，但文件存储可能无法正常工作"
      fi
      echo ""
    fi
    echo "✅ 部署完成！访问: http://${SERVER_NAME:-localhost}"
    ;;
  down)
    echo "🛑 停止所有服务..."
    docker compose down
    ;;
  restart)
    echo "🔄 重启所有服务..."
    docker compose restart
    ;;
  logs)
    docker compose logs -f ${2:-}
    ;;
  status)
    docker compose ps
    echo ""
    echo "--- 磁盘使用 ---"
    docker system df
    ;;
  backup)
    echo "💾 备份数据库..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="$PROJECT_ROOT/backups"
    mkdir -p "$BACKUP_DIR"
    docker compose exec -T db pg_dump -U "${POSTGRES_USER:-huazong}" "${POSTGRES_DB:-huazong_studio}" | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"
    echo "✅ 备份已保存: $BACKUP_DIR/db_$TIMESTAMP.sql.gz"
    # 清理 30 天前的旧备份
    find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete 2>/dev/null || true
    echo "🧹 已清理 30 天前的旧备份"
    ;;
  update)
    echo "📦 更新并重新部署..."
    git pull
    docker compose up -d --build
    echo "⏳ 等待服务就绪..."
    sleep 10
    docker compose ps
    # COS 连通性检查（仅在 FS_BACKEND=cos 时执行）
    if [ "${FS_BACKEND:-local}" = "cos" ]; then
      echo "☁️  验证 COS 连通性..."
      bash "$PROJECT_ROOT/scripts/cos-healthcheck.sh" || echo "⚠️  COS 连通性检查失败"
    fi
    echo "✅ 更新完成"
    ;;
  *)
    echo "画宗制片中枢 — 部署管理工具"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  up       启动所有服务（默认）"
    echo "  down     停止所有服务"
    echo "  restart  重启所有服务"
    echo "  logs     查看日志（可选服务名: logs api）"
    echo "  status   查看服务状态和磁盘使用"
    echo "  backup   备份 PostgreSQL 数据库"
    echo "  update   拉取最新代码并重新部署"
    exit 1
    ;;
esac

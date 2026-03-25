#!/bin/bash
# =============================================
# 画宗制片中枢 — 从零到上线一键部署
# 在全新 Ubuntu 服务器上运行：
#   curl -fsSL https://raw.githubusercontent.com/dsafdwsfas/huazong-studio/main/scripts/full-deploy.sh | sudo bash
# 或者已克隆后：
#   sudo bash scripts/full-deploy.sh
# =============================================

set -euo pipefail

REPO_URL="https://github.com/dsafdwsfas/huazong-studio.git"
INSTALL_DIR="/opt/huazong"
DOMAIN=""
EMAIL=""

echo "=========================================="
echo "  画宗制片中枢 — 一键部署"
echo "  目标: 2C2G Ubuntu CVM"
echo "=========================================="
echo ""

# ---- 交互式收集配置 ----
read -rp "📌 域名（如 studio.huazong.com，回车跳过用 IP 访问）: " DOMAIN
read -rp "📧 管理员邮箱（用于 HTTPS 证书和通知）: " EMAIL

if [ -z "$EMAIL" ]; then
  EMAIL="admin@huazong.com"
fi

echo ""
echo "📋 部署配置:"
echo "   仓库: $REPO_URL"
echo "   目录: $INSTALL_DIR"
echo "   域名: ${DOMAIN:-无（HTTP 直接 IP 访问）}"
echo "   邮箱: $EMAIL"
echo ""
read -rp "确认开始？(y/N) " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
  echo "已取消。"
  exit 0
fi

# ========== Step 1: 系统初始化 ==========
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [1/6] 系统初始化"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Swap
if ! swapon --show | grep -q '/swapfile'; then
  echo "📦 配置 Swap 2G..."
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl -w vm.swappiness=10 > /dev/null
  grep -q 'vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf
  echo "  ✅ Swap 2G"
else
  echo "  ⏭️  Swap 已存在"
fi

# Docker
if ! command -v docker &>/dev/null; then
  echo "🐳 安装 Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
  echo "  ✅ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+')"
else
  echo "  ⏭️  Docker $(docker --version | grep -oP '\d+\.\d+\.\d+')"
fi

# Tools
echo "🔧 安装基础工具..."
apt-get update -qq
apt-get install -y --no-install-recommends git curl certbot > /dev/null 2>&1
echo "  ✅ git, curl, certbot"

# Firewall
if command -v ufw &>/dev/null; then
  ufw allow 22/tcp > /dev/null 2>&1
  ufw allow 80/tcp > /dev/null 2>&1
  ufw allow 443/tcp > /dev/null 2>&1
  ufw --force enable > /dev/null 2>&1
  echo "  ✅ 防火墙: 22/80/443"
fi

# ========== Step 2: 拉取代码 ==========
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [2/6] 拉取代码"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "📦 更新已有代码..."
  cd "$INSTALL_DIR"
  git pull origin main
else
  echo "📦 克隆仓库..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi
echo "  ✅ 代码就绪: $INSTALL_DIR"

# ========== Step 3: 生成 .env ==========
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [3/6] 生成配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$INSTALL_DIR/.env" ]; then
  echo "  ⏭️  .env 已存在，跳过生成"
else
  # 生成随机密码
  DB_PASS=$(openssl rand -hex 16)
  SECRET=$(openssl rand -hex 32)
  JWT_SECRET=$(openssl rand -hex 32)

  cat > "$INSTALL_DIR/.env" << ENVEOF
# ===== 自动生成于 $(date '+%Y-%m-%d %H:%M:%S') =====

# PostgreSQL
POSTGRES_USER=huazong
POSTGRES_PASSWORD=$DB_PASS
POSTGRES_DB=huazong_studio

# Redis
KV_HOST=redis
KV_PORT=6379

# MeiliSearch (2C2G 已禁用)
INDEXER_HOST=
INDEXER_PORT=
INDEXER_KEY=

# Events
EVENT_STREAM_HOST=events
EVENT_STREAM_PORT=5001

# Flask
SECRET_KEY=$SECRET
JWT_SECRET_KEY=$JWT_SECRET

# 文件存储
PREVIEW_FOLDER=/opt/zou/previews
TMP_DIR=/opt/zou/tmp

# Gunicorn (2C2G 优化)
GUNICORN_WORKERS=2
GUNICORN_LOG_LEVEL=info

# Nginx
SERVER_NAME=${DOMAIN:-_}

# COS (暂用本地存储，后续可改)
FS_BACKEND=local
COS_SECRET_ID=
COS_SECRET_KEY=
COS_REGION=ap-beijing
COS_BUCKET_PICTURES=
COS_BUCKET_MOVIES=
COS_BUCKET_FILES=
COS_CDN_DOMAIN=
COS_CDN_ENABLED=false
COS_PRESIGN_EXPIRED=3600
COS_CI_ENABLED=false
ENVEOF

  echo "  ✅ .env 已生成（密码已随机化）"
  echo "  📝 数据库密码: $DB_PASS"
  echo "  📝 请记录以上密码！"
fi

# ========== Step 4: 启动服务 ==========
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [4/6] 启动服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$INSTALL_DIR"

# 首次部署用 HTTP-only nginx 配置
if [ ! -f "$INSTALL_DIR/nginx/active-nginx.conf" ]; then
  cp "$INSTALL_DIR/nginx/nginx-http-only.conf" "$INSTALL_DIR/nginx/active-nginx.conf"
  echo "  📝 使用 HTTP-only 配置（HTTPS 稍后配置）"
fi

echo "🚀 构建并启动容器（首次约 5-10 分钟）..."
docker compose up -d --build 2>&1 | tail -5

echo "⏳ 等待服务就绪..."
sleep 15

# 检查服务状态
echo ""
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker compose ps
echo ""

# 健康检查
API_STATUS=$(curl -s -o /dev/null -w '%{http_code}' http://localhost/api/status 2>/dev/null || echo "000")
if [ "$API_STATUS" = "200" ] || [ "$API_STATUS" = "401" ]; then
  echo "  ✅ API 服务正常 (HTTP $API_STATUS)"
else
  echo "  ⚠️  API 返回 HTTP $API_STATUS，可能还在启动中"
  echo "  💡 查看日志: cd $INSTALL_DIR && docker compose logs api"
fi

# ========== Step 5: HTTPS ==========
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [5/6] HTTPS 配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "_" ]; then
  echo "🔒 为 $DOMAIN 申请 SSL 证书..."
  if bash "$INSTALL_DIR/scripts/setup-ssl.sh" "$DOMAIN" "$EMAIL" 2>&1; then
    echo "  ✅ HTTPS 已启用"
  else
    echo "  ⚠️  SSL 配置失败，请确认："
    echo "     1. 域名 $DOMAIN 已解析到本服务器 IP"
    echo "     2. 端口 80/443 已开放"
    echo "     3. 稍后手动运行: bash scripts/setup-ssl.sh $DOMAIN $EMAIL"
  fi
else
  echo "  ⏭️  未配置域名，跳过 HTTPS"
  echo "  💡 后续配置: bash scripts/setup-ssl.sh your-domain.com your@email.com"
fi

# ========== Step 6: 定时备份 ==========
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [6/6] 定时备份"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

chmod +x "$INSTALL_DIR/scripts/backup-to-cos.sh"
chmod +x "$INSTALL_DIR/scripts/setup-cron.sh"
bash "$INSTALL_DIR/scripts/setup-cron.sh" 2>&1
echo "  ✅ 每日 3:17 自动备份"

# ========== 完成 ==========
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "  🎉 画宗制片中枢部署完成！"
echo "=========================================="
echo ""
echo "  访问地址:"
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "_" ]; then
  echo "    🌐 https://$DOMAIN"
fi
echo "    🌐 http://$SERVER_IP"
echo ""
echo "  默认管理员:"
echo "    账号: admin@huazong-studio.com"
echo "    密码: default"
echo "    ⚠️  首次登录请立即修改密码！"
echo ""
echo "  运维命令:"
echo "    cd $INSTALL_DIR"
echo "    bash scripts/deploy.sh status    # 查看状态"
echo "    bash scripts/deploy.sh logs      # 查看日志"
echo "    bash scripts/deploy.sh restart   # 重启服务"
echo "    bash scripts/deploy.sh backup    # 手动备份"
echo ""
echo "  内存使用:"
free -h | head -2
echo ""
echo "=========================================="

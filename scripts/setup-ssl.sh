#!/bin/bash
# =============================================
# 画宗制片中枢 — SSL 证书申请 + HTTPS 启用
# 用法: sudo bash scripts/setup-ssl.sh <域名> <邮箱>
# 示例: sudo bash scripts/setup-ssl.sh studio.huazong.com admin@huazong.com
# =============================================

set -e

DOMAIN="${1:?用法: $0 <域名> <邮箱>}"
EMAIL="${2:?用法: $0 <域名> <邮箱>}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT_NAME="huazong"

echo "=========================================="
echo "  画宗制片中枢 — HTTPS 配置"
echo "  域名: $DOMAIN"
echo "  邮箱: $EMAIL"
echo "=========================================="

# ---- 1. 检查前置条件 ----
echo ""
echo "🔍 [1/5] 检查前置条件..."

if ! command -v certbot &>/dev/null; then
  echo "  安装 certbot..."
  apt-get update -qq && apt-get install -y certbot > /dev/null 2>&1
fi
echo "  ✅ certbot 就绪"

if ! docker compose -f "$PROJECT_ROOT/docker-compose.yml" ps --format json 2>/dev/null | grep -q 'nginx'; then
  echo "  ❌ Nginx 容器未运行，请先 bash scripts/deploy.sh up"
  exit 1
fi
echo "  ✅ Nginx 容器运行中"

# ---- 2. 确保使用 HTTP-only 配置（certbot 验证需要 80 端口可访问）----
echo ""
echo "📝 [2/5] 切换到 HTTP-only 配置..."

cp "$PROJECT_ROOT/nginx/nginx-http-only.conf" "$PROJECT_ROOT/nginx/active-nginx.conf"
docker compose -f "$PROJECT_ROOT/docker-compose.yml" exec nginx nginx -s reload 2>/dev/null || \
  docker compose -f "$PROJECT_ROOT/docker-compose.yml" restart nginx
sleep 2
echo "  ✅ Nginx 已切换到 HTTP-only 模式"

# ---- 3. 获取 certbot webroot 路径并申请证书 ----
echo ""
echo "🔐 [3/5] 申请 Let's Encrypt 证书..."

# 找到 certbot-webroot 卷的实际挂载路径
WEBROOT=$(docker compose -f "$PROJECT_ROOT/docker-compose.yml" exec nginx \
  df /var/www/certbot 2>/dev/null | tail -1 | awk '{print $NF}')

# 获取 certbot 卷的宿主机路径
CERTBOT_WEBROOT_VOL=$(docker volume inspect "$(basename "$PROJECT_ROOT")_certbot-webroot" \
  --format '{{ .Mountpoint }}' 2>/dev/null || echo "")
CERTBOT_ETC_VOL=$(docker volume inspect "$(basename "$PROJECT_ROOT")_certbot-etc" \
  --format '{{ .Mountpoint }}' 2>/dev/null || echo "")

if [ -z "$CERTBOT_WEBROOT_VOL" ]; then
  # 回退: 用 docker inspect 获取
  NGINX_CONTAINER=$(docker compose -f "$PROJECT_ROOT/docker-compose.yml" ps -q nginx)
  CERTBOT_WEBROOT_VOL=$(docker inspect "$NGINX_CONTAINER" \
    --format '{{ range .Mounts }}{{ if eq .Destination "/var/www/certbot" }}{{ .Source }}{{ end }}{{ end }}')
  CERTBOT_ETC_VOL=$(docker inspect "$NGINX_CONTAINER" \
    --format '{{ range .Mounts }}{{ if eq .Destination "/etc/letsencrypt" }}{{ .Source }}{{ end }}{{ end }}')
fi

echo "  Webroot: $CERTBOT_WEBROOT_VOL"
echo "  Cert目录: $CERTBOT_ETC_VOL"

certbot certonly \
  --webroot \
  --webroot-path "$CERTBOT_WEBROOT_VOL" \
  --config-dir "$CERTBOT_ETC_VOL" \
  --cert-name "$CERT_NAME" \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive

echo "  ✅ 证书已申请成功"

# ---- 4. 切换到 HTTPS 配置 ----
echo ""
echo "🔒 [4/5] 启用 HTTPS..."

# 更新 nginx.conf 中的 server_name
sed "s/server_name _;/server_name $DOMAIN;/g" \
  "$PROJECT_ROOT/nginx/nginx.conf" > "$PROJECT_ROOT/nginx/active-nginx.conf"

docker compose -f "$PROJECT_ROOT/docker-compose.yml" exec nginx nginx -s reload 2>/dev/null || \
  docker compose -f "$PROJECT_ROOT/docker-compose.yml" restart nginx
sleep 2
echo "  ✅ HTTPS 已启用"

# ---- 5. 设置自动续签 cron ----
echo ""
echo "⏰ [5/5] 配置证书自动续签..."

RENEW_CMD="certbot renew --config-dir $CERTBOT_ETC_VOL --quiet && docker compose -f $PROJECT_ROOT/docker-compose.yml exec -T nginx nginx -s reload"
CRON_LINE="0 3 * * * $RENEW_CMD"

# 添加到 crontab（幂等）
(crontab -l 2>/dev/null | grep -v 'certbot renew' ; echo "$CRON_LINE") | crontab -
echo "  ✅ 每日凌晨 3 点自动续签"

# ---- 完成 ----
echo ""
echo "=========================================="
echo "  ✅ HTTPS 配置完成！"
echo ""
echo "  🌐 https://$DOMAIN"
echo ""
echo "  证书信息:"
certbot certificates --config-dir "$CERTBOT_ETC_VOL" --cert-name "$CERT_NAME" 2>/dev/null | grep -E 'Domain|Expiry' || true
echo ""
echo "  自动续签: 每日 03:00 检查"
echo "=========================================="

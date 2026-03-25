#!/bin/bash
# =============================================
# 画宗制片中枢 — 腾讯云 CVM 初始化脚本
# 用法: sudo bash scripts/server-init.sh
# 适用: Ubuntu 20.04/22.04/24.04, 2C2G
# =============================================

set -e

echo "=========================================="
echo "  画宗制片中枢 — 服务器初始化"
echo "  目标: 2C2G Ubuntu CVM"
echo "=========================================="

# ---- 1. Swap 2G ----
echo ""
echo "📦 [1/4] 配置 Swap 2G..."

if swapon --show | grep -q '/swapfile'; then
  echo "  ⏭️  Swap 已存在，跳过"
  swapon --show
else
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile

  # 持久化到 fstab
  if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
  fi

  # 调优 swappiness — 低值让内核尽量用物理内存，只在真正紧张时用 swap
  sysctl vm.swappiness=10
  if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
  fi

  # 调优 vfs_cache_pressure — 降低内核回收 inode/dentry 缓存的倾向
  sysctl vm.vfs_cache_pressure=50
  if ! grep -q 'vm.vfs_cache_pressure' /etc/sysctl.conf; then
    echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf
  fi

  echo "  ✅ Swap 2G 已启用"
  swapon --show
fi

# ---- 2. Docker ----
echo ""
echo "🐳 [2/4] 安装 Docker..."

if command -v docker &>/dev/null; then
  echo "  ⏭️  Docker 已安装: $(docker --version)"
else
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
  echo "  ✅ Docker 已安装: $(docker --version)"
fi

# 当前用户加入 docker 组（非 root 时生效）
if [ -n "$SUDO_USER" ]; then
  usermod -aG docker "$SUDO_USER"
  echo "  ✅ 用户 $SUDO_USER 已加入 docker 组（需重新登录生效）"
fi

# ---- 3. 基础工具 ----
echo ""
echo "🔧 [3/4] 安装基础工具..."

apt-get update -qq
apt-get install -y --no-install-recommends \
  git \
  curl \
  htop \
  vim \
  unzip \
  certbot \
  > /dev/null 2>&1

echo "  ✅ git, curl, htop, vim, certbot 已安装"

# ---- 4. 防火墙 ----
echo ""
echo "🔒 [4/4] 配置防火墙..."

if command -v ufw &>/dev/null; then
  ufw allow 22/tcp   comment 'SSH'       > /dev/null 2>&1
  ufw allow 80/tcp   comment 'HTTP'      > /dev/null 2>&1
  ufw allow 443/tcp  comment 'HTTPS'     > /dev/null 2>&1
  ufw --force enable > /dev/null 2>&1
  echo "  ✅ UFW 已启用: SSH(22) + HTTP(80) + HTTPS(443)"
else
  echo "  ⏭️  UFW 未安装，请在腾讯云安全组中放行 22/80/443 端口"
fi

# ---- 完成 ----
echo ""
echo "=========================================="
echo "  ✅ 服务器初始化完成！"
echo ""
echo "  内存状态:"
free -h
echo ""
echo "  下一步:"
echo "  1. cd /opt/huazong"
echo "  2. cp .env.example .env && vim .env"
echo "  3. bash scripts/deploy.sh up"
echo "=========================================="

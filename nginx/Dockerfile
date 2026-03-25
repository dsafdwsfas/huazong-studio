# 轻量 Nginx — 直接使用预构建的前端产物（2C2G 无法跑 npm build）
FROM nginx:1.27-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy frontend build output（本地构建后推到仓库）
COPY kitsu-frontend/dist /var/www/html

# Create certbot webroot directory
RUN mkdir -p /var/www/certbot

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]

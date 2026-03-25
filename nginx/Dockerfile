# Stage 1: Build frontend
FROM node:20-alpine AS builder

WORKDIR /app

COPY kitsu-frontend/package.json kitsu-frontend/package-lock.json* ./
RUN npm ci

COPY kitsu-frontend/ ./
RUN npm run build

# Stage 2: Nginx with built frontend
FROM nginx:1.27-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config（首次用 HTTP-only，setup-ssl.sh 申请证书后切换）
COPY nginx/nginx-http-only.conf /etc/nginx/conf.d/default.conf

# Copy frontend build output
COPY --from=builder /app/dist /var/www/html

# Create certbot webroot directory
RUN mkdir -p /var/www/certbot

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]

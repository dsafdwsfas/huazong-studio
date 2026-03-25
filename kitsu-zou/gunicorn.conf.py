"""
Gunicorn configuration for Zou API server.

Used by: docker-entrypoint.sh "api" role
Serves: zou.app:app on port 5000

2C2G 轻量化配置：
- workers 默认 2（原 4），可通过 GUNICORN_WORKERS 环境变量覆盖
- max_requests 降到 500 加速 worker 回收，防止内存泄漏
- graceful_timeout 缩短，减少停机时间
"""

import os

# Server socket
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5000")

# Worker processes — 2C2G 推荐 2 个 worker
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "gevent"
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "100"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 5

# Worker recycling — 更积极回收防止内存泄漏
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "500"))
max_requests_jitter = 50

# Preload app for faster worker startup and shared memory
preload_app = True

# Logging
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

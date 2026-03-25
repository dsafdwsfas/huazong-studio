"""
Gunicorn configuration for Zou Event Stream server (SocketIO/WebSocket).

Used by: docker-entrypoint.sh "events" role
Serves: zou.event_stream:app on port 5001
"""

import os

# Server socket
bind = os.getenv("GUNICORN_EVENTS_BIND", "0.0.0.0:5001")

# Worker processes — SocketIO requires a single worker
workers = 1
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"

# Timeouts — WebSocket long-lived connections need generous timeout
timeout = 300
keepalive = 65

# Logging
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

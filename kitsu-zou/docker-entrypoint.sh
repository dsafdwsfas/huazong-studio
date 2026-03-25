#!/bin/bash
# newline: lf — this file MUST use Unix line endings (LF), not CRLF
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT:-5432}..."
until pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USERNAME"; do
  sleep 2
done
echo "PostgreSQL is ready."

# Wait for Redis to be ready
echo "Waiting for Redis at ${KV_HOST}:${KV_PORT:-6379}..."
until redis-cli -h "$KV_HOST" -p "${KV_PORT:-6379}" ping 2>/dev/null | grep -q PONG; do
  sleep 2
done
echo "Redis is ready."

# Start the appropriate service based on the role argument
case "$1" in
  "api")
    echo "Initializing database..."
    zou init-db || true
    zou init-data || true
    echo "Starting API server on port 5000..."
    exec gunicorn -c /etc/gunicorn.conf.py zou.app:app
    ;;
  "events")
    echo "Starting Event Stream server on port 5001..."
    exec gunicorn -c /etc/gunicorn-events.conf.py zou.event_stream:app
    ;;
  "worker")
    echo "Starting background task worker..."
    exec rq worker -c zou.app.config
    ;;
  *)
    exec "$@"
    ;;
esac

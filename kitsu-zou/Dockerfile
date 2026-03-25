FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    imagemagick \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/zou

# Copy source code
COPY . .

# Install Python package
RUN pip install --no-cache-dir -e .

# Install pg_isready and redis-cli for health checks in entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy Gunicorn configs
COPY gunicorn.conf.py /etc/gunicorn.conf.py
COPY gunicorn-events.conf.py /etc/gunicorn-events.conf.py

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create storage directories
RUN mkdir -p /opt/zou/previews /opt/zou/tmp

EXPOSE 5000 5001

ENTRYPOINT ["docker-entrypoint.sh"]

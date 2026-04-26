# ---- EventFlow AI — Cloud Run Dockerfile ----
# Multi-stage build for efficient deployment

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app.py config.py gemini_engine.py simulator.py rewards.py ./
COPY templates/ templates/
COPY static/ static/

# Cloud Run provides PORT env var (default 8080)
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE ${PORT}

# Use gunicorn for production
CMD exec gunicorn --bind :${PORT} --workers 1 --threads 4 --timeout 120 app:app

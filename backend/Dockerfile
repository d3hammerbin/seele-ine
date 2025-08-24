# =============================================================================
# SEELE-E Backend Dockerfile
# Multi-stage build for development and production
# =============================================================================

# Base image with Python 3.11
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libopencv-dev \
    tesseract-ocr \
    tesseract-ocr-spa \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Development stage
# =============================================================================
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black isort flake8

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads temp credentials logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "main.py"]

# =============================================================================
# Production stage
# =============================================================================
FROM base AS production

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads temp credentials logs

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command with Gunicorn
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]

# =============================================================================
# Worker stage for background tasks
# =============================================================================
FROM base AS worker

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads temp credentials logs

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check for worker (check Redis connection)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import redis; r=redis.Redis(host='redis'); r.ping()" || exit 1

# Start worker process
CMD ["python", "-m", "app.infrastructure.worker"]

# =============================================================================
# Scheduler stage for scheduled tasks
# =============================================================================
FROM base AS scheduler

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads temp credentials logs backups

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check for scheduler (check Redis connection)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import redis; r=redis.Redis(host='redis'); r.ping()" || exit 1

# Start scheduler process
CMD ["python", "-m", "app.infrastructure.scheduler"]
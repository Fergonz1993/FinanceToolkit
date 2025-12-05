# Dockerfile for FinanceToolkit API deployment to Google Cloud Run

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml /app/pyproject.toml

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[infra]"

# Copy the entire project
COPY . /app/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with gunicorn + uvicorn worker for better concurrency
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8080", "infrastructure.api:app"]


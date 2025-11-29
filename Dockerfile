# Dockerfile for FinanceToolkit API deployment to Google Cloud Run

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY api/requirements.txt /app/api/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# Copy the entire project (needed for my_finance_layer and config)
COPY . /app/

# Set Python path to include project root
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Run the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]


# Backend Dockerfile for Google Cloud Run
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run sets PORT environment variable (default 8080)
ENV PORT=8080

# Expose the port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# Run the application with uvicorn
# Cloud Run requires listening on 0.0.0.0 and the PORT env variable
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}

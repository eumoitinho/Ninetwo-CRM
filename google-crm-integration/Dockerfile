# Dockerfile for Google CRM Integration

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
# Note: Environment variables are provided by Railway, not from .env file

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Railway will provide PORT via environment variable)
EXPOSE 8080

# Run the application (PORT will be provided by Railway or default to 8080)
# Railway automatically handles health checks using the /health endpoint
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"

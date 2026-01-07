# ModPlayer Dockerfile
# Supports both SQLite (single container) and PostgreSQL (multi-container)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data and cache
RUN mkdir -p /app/data /app/cache/modules /app/logs && \
    chmod -R 755 /app/data /app/cache /app/logs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    DATABASE_PATH=/app/data/database.db

# Initialize database and run application
CMD ["sh", "-c", "python init_db.py && gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app"]

# UTJFC Backend Dockerfile for AWS Elastic Beanstalk
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=80

# Install system dependencies for image processing and security
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libheif-dev \
        libde265-dev \
        libx265-dev \
        pkg-config \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/uploads

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Run the FastAPI application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80", "--workers", "1"]

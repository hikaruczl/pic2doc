# Dockerfile for OCR Backend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (mirror for faster build)
RUN sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources || true && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        poppler-utils \
        libpq-dev \
        gcc \
        libffi-dev \
        libssl-dev \
        libjpeg62-turbo-dev \
        libtiff5-dev \
        libopenjp2-7-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libwebp-dev \
        tk-dev \
        tcl-dev \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Configure faster PyPI mirror and timeout
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
    PIP_TRUSTED_HOST=mirrors.aliyun.com \
    PIP_DEFAULT_TIMEOUT=120

# Copy requirements first for better caching
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads output logs

# Expose backend port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "web.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

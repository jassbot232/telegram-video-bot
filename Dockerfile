FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies including FFmpeg and other required tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    ghostscript \
    poppler-utils \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp_files \
    && chmod 755 temp_files

# Create a non-root user for security
RUN groupadd -r botuser && useradd -r -g botuser botuser \
    && chown -R botuser:botuser /app
USER botuser

# Expose port (if needed for webhooks)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run the bot
CMD ["python", "bot.py"]

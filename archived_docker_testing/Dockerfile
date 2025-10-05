FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Clean up Python cache files that might cause import conflicts
RUN find . -type f -name "*.pyc" -delete && \
    find . -type d -name "__pycache__" -exec rm -rf {} + || true

# Create necessary directories with proper permissions
RUN mkdir -p /app/test_output /app/temp_files /app/storage /app/logs /app/trash/tmp && \
    chmod -R 777 /app/test_output /app/temp_files /app/storage /app/logs /app/trash/tmp

# Set environment variables for testing
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ANTHROPIC_API_KEY=""
ENV OPENAI_API_KEY=""

# Set up non-interactive environment for CLI tests
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Run tests by default
CMD ["python", "-m", "pytest", "-v", "--tb=short"]

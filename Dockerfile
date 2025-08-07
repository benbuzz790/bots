FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the entire project
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Set up environment variables
ENV ANTHROPIC_API_KEY=""
ENV OPENAI_API_KEY=""
# Create directories with full write permissions for tests
RUN mkdir -p /app/test_output /app/temp_files /app/storage /app/logs && \
    chmod -R 777 /app/test_output /app/temp_files /app/storage /app/logs && \
    chmod -R 755 /app

# Ensure the app directory is writable for test file creation
RUN chmod -R 755 /app && \
    find /app -type d -exec chmod 755 {} \; && \
    find /app -type f -exec chmod 644 {} \;


# Run tests by default
CMD ["python", "-m", "pytest", "-v"]

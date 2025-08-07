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


# Run tests by default
CMD ["python", "-m", "pytest", "-v"]

#!/bin/bash

# Build the Docker image
echo "Building test container..."
docker build -t pytest-container .

# Run tests in container
echo "Running tests in isolated container..."
docker run --rm -it --memory=2g --cpus=2 \
  -v "$(pwd)/test_output:/app/test_output" \
  -v "$(pwd)/temp_files:/app/temp_files" \
  -v "$(pwd)/storage:/app/storage" \
  -v "$(pwd)/logs:/app/logs" pytest-container

# Optional: Run with specific pytest args
# docker run --rm -it pytest-container python -m pytest "$@"

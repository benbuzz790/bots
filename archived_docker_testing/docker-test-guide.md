# Docker Test Guide - Safe Pytest Execution

This guide shows you how to run your pytest suite in a Docker container to prevent system crashes and provide complete isolation.

## Step 1: Install Docker Desktop (Windows)

1. Download Docker Desktop from: <https://www.docker.com/products/docker-desktop/>
2. Run the installer and follow the setup wizard
3. Restart your computer when prompted
4. Launch Docker Desktop and wait for it to start
5. Verify installation by opening PowerShell and running:

   ```powershell
   docker --version
   ```

## Step 2: Files Created for You

Your project now has these Docker-related files:

- **`Dockerfile`** - Defines the container environment
- **`run_tests_docker.bat`** - Windows batch script to run tests
- **`run_tests_docker.sh`** - Linux/Mac script (for reference)

## Step 3: Running Tests in Docker

### Option A: Use the Batch Script (Easiest)

1. Open File Explorer and navigate to your project folder
2. Double-click `run_tests_docker.bat`
3. A command window will open, build the container, and run your tests
4. Press any key when done to close the window

### Option B: Manual Commands

Open PowerShell in your project directory and run:

```powershell
# Build the container (first time only, or when dependencies change)
docker build -t pytest-container .

# Run all tests
docker run --rm -it pytest-container

# Run specific tests with options
docker run --rm -it pytest-container python -m pytest tests/test_basic.py -v

# Run with resource limits (safer)
docker run --rm -it --memory=2g --cpus=2 pytest-container
```

## Step 4: Understanding What Happens

1. **Build Phase**: Docker creates a container with Python 3.12 and your project
2. **Test Phase**: Tests run inside the isolated container
3. **Cleanup**: Container is automatically deleted when tests finish
4. **Safety**: If tests crash, only the container crashes - your system stays safe

## Common Commands

```powershell
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# Remove the test image (to rebuild from scratch)
docker rmi pytest-container

# Clean up all unused Docker resources
docker system prune
```

## Troubleshooting

**"docker: command not found"**

- Docker Desktop isn't installed or running
- Restart Docker Desktop and wait for it to fully start

**"Cannot connect to Docker daemon"**

- Docker Desktop isn't running
- Check the system tray for Docker icon

**Tests fail in container but work locally**

- Check if you have local environment variables or files not copied to container
- Add any missing files to the Dockerfile COPY commands

**Container builds slowly**

- First build takes time to download Python image
- Subsequent builds are much faster due to Docker caching

## Environment Variables Setup

Your tests may need API keys or other environment variables. Here's how to set them up:

1. **Edit the `.env` file** in your project root:

   ```
   ANTHROPIC_API_KEY=your_actual_anthropic_key_here
   OPENAI_API_KEY=your_actual_openai_key_here
   ```

2. **Environment variables are automatically passed** to the Docker container when you run:
   - `.\run_tests_docker.bat`
   - `pytest --use-docker` (automatic with `--use-docker` flag)
   - Manual: `docker run --rm --env-file .env pytest-container`

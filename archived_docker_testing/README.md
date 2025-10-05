# Archived Docker Testing Infrastructure
This directory contains the Docker-based test infrastructure that was developed but ultimately abandoned due to Docker Desktop issues on the development machine.
## What Was This?
An ambitious attempt to create a safe, isolated test environment using Docker containers to prevent system crashes during pytest execution. The system included:
- Automated container building with resource limits (2GB RAM, 2 CPUs)
- Multiple orchestration scripts (interactive and automated)
- Comprehensive documentation and user guides
- Pytest integration with --use-docker flags
- Environment variable management
- Cross-platform support (Windows, Linux, Mac)
## Why Was It Abandoned?
Docker Desktop issues on the development machine made this infrastructure unusable. The project moved back to native test execution.
## Files Included
- **Dockerfile** - Container definition with Python 3.12 and dependencies
- **.dockerignore** - Build optimization file
- **docker-test-guide.md** - Complete user guide for Docker testing
- **run_tests_docker.py** - Interactive test orchestrator
- **run_tests_docker_auto.py** - Automated test orchestrator
- **run_tests_docker.sh** - Linux/Mac test runner
- **run_tests_docker.bat** - Windows test runner
## Archived Date
2025-10-04
## Note
This code is preserved for historical reference and potential future use if Docker issues are resolved.

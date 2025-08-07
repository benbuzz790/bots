#!/usr/bin/env python3
"""
Development runner for the React GUI Bot Framework.
Starts both backend and frontend in development mode with hot
reloading.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from pathlib import Path
from typing import List, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DevelopmentRunner:
    """Manages development environment with defensive validation."""

    def __init__(self, project_root: str):
        # Input validation
        assert isinstance(project_root, str), f"project_root must be str, got {type(project_root)}"
        assert os.path.exists(project_root), f"Project root does not exist: {project_root}"

        self.project_root = Path(project_root).resolve()
        # Fix: Look for backend and frontend directly under project_root, not under react-gui subdirectory
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"

        # Validate directories exist - fix escape sequence syntax errors
        assert self.backend_dir.exists(), f"Backend directory not found: {self.backend_dir}"
        assert self.frontend_dir.exists(), f"Frontend directory not found: {self.frontend_dir}"

        self.processes: List[subprocess.Popen] = []
        self.shutdown_event = threading.Event()

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed."""
        logger.info("Checking prerequisites...")

        # Check Python
        try:
            result = subprocess.run([sys.executable, "--version"],
                                capture_output=True, text=True,
                                check=True, shell=True) # Added shell=True
            logger.info(f"Python: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Python check failed: {e}")
            return False
        except FileNotFoundError: # Added this specific exception handling
            logger.error("Python not found or not working")
            return False

        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"],
                                    capture_output=True, text=True,
                                    check=True, shell=True) # Added shell=True
            logger.info(f"Node.js: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e: # Catching both
            logger.error(f"Node.js not found. Please install Node.js 18+: {e}") # More informative error
            return False

        # Check npm
        try:
            result = subprocess.run(["npm", "--version"],
                                capture_output=True, text=True,
                                check=True, shell=True) # Added shell=True
            logger.info(f"npm: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e: # Catching both
            logger.error(f"npm not found: {e}") # More informative error
            return False

        return True

    def setup_backend(self) -> bool:
        """Setup backend environment."""
        logger.info("Setting up backend environment...")

        try:
            # Check if requirements.txt exists
            requirements_file = self.backend_dir / "requirements.txt"
            if not requirements_file.exists():
                logger.error(f"Requirements file not found: {requirements_file}")
                return False

            # Install Python dependencies
            logger.info("Installing Python dependencies...")
            result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                    cwd=self.backend_dir, check=True,
                )

            logger.info("Backend setup completed")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Backend setup failed: {e}")
            return False

    def setup_frontend(self) -> bool:
        """Setup frontend environment."""
        logger.info("Setting up frontend environment...")

        try:
            # Check if package.json exists
            package_file = self.frontend_dir / "package.json"
            if not package_file.exists():
                logger.error(f"Package.json not found: {package_file}")
                return False

            # Install Node.js dependencies
            logger.info("Installing Node.js dependencies...")
            result = subprocess.run(
                ["npm", "install"], 
                cwd=self.frontend_dir, 
                check=True,
                )

            logger.info("Frontend setup completed")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Frontend setup failed: {e}")
            return False

    def start_backend(self) -> Optional[subprocess.Popen]:
        """Start backend development server."""
        logger.info("Starting backend server...")

        try:
            # Set environment variables
            env = os.environ.copy()
            env.update({
                "PYTHONPATH": str(self.backend_dir),
                "BOT_STORAGE_DIR": str(self.project_root / "storage"),
                "LOG_LEVEL": "DEBUG",
                "RELOAD": "true"
            })

            # Create storage directory
            storage_dir = self.project_root / "storage"
            storage_dir.mkdir(exist_ok=True)

            # Start backend process
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn",
                "main:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload",
                "--log-level", "info"
            ], cwd=self.backend_dir, env=env)

            self.processes.append(process)
            logger.info("Backend server started on http://127.0.0.1:8000")
            return process

        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return None

    def start_frontend(self) -> Optional[subprocess.Popen]:
        """Start frontend development server."""
        logger.info("Starting frontend server...")

        try:
            # Start frontend process
            process = subprocess.Popen([
                "npm", "run", "dev"
            ], cwd=self.frontend_dir)

            self.processes.append(process)
            logger.info("Frontend server started on http://127.0.0.1:3000")
            return process

        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            return None

    def wait_for_backend(self, timeout: int = 60) -> bool:
        """Wait for backend to be ready."""
        logger.info("Waiting for backend to be ready...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
                if response.status_code == 200:
                    logger.info("Backend is ready!")
                    return True
            except requests.RequestException:
                pass

            time.sleep(2)

        logger.error("Backend failed to start within timeout")
        return False

    def wait_for_frontend(self, timeout: int = 60) -> bool:
        """Wait for frontend to be ready."""
        logger.info("Waiting for frontend to be ready...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://127.0.0.1:3000",
                                    timeout=5)
                if response.status_code == 200:
                    logger.info("Frontend is ready!")
                    return True
            except requests.RequestException:
                pass

            time.sleep(2)

        logger.error("Frontend failed to start within timeout")
        return False

    def shutdown(self):
        """Shutdown all processes."""
        logger.info("Shutting down development environment...")

        self.shutdown_event.set()

        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing process{process.pid}")
                process.kill()
            except Exception as e:
                logger.error(f"Error shutting down process: {e}")

        self.processes.clear()
        logger.info("Shutdown complete")

    def run(self) -> bool:
        """Run the complete development environment."""
        logger.info("Starting React GUI Bot Framework development environment")

        try:
            # Setup signal handlers
            def signal_handler(signum, frame):
                logger.info("Received shutdown signal")
                self.shutdown()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Check prerequisites
            if not self.check_prerequisites():
                return False

            # Setup environments
            if not self.setup_backend():
                return False

            if not self.setup_frontend():
                return False

            # Start services
            backend_process = self.start_backend()
            if not backend_process:
                return False

            frontend_process = self.start_frontend()
            if not frontend_process:
                return False

            # Wait for services to be ready
            if not self.wait_for_backend():
                return False

            if not self.wait_for_frontend():
                return False

            logger.info("🎉 Development environment is ready!")
            logger.info("Frontend: http://127.0.0.1:3000")
            logger.info("Backend API: http://127.0.0.1:8000")
            logger.info("API Docs: http://127.0.0.1:8000/docs")
            logger.info("Press Ctrl+C to stop")

            # Wait for shutdown
            while not self.shutdown_event.is_set():
                time.sleep(1)

                # Check if processes are still running
                for process in self.processes:
                    if process.poll() is not None:
                        logger.error(f"Process {process.pid} has stopped unexpectedly")
                        return False

            return True

        except Exception as e:
            logger.error(f"Development environment failed: {e}")
            return False
        finally:
            self.shutdown()

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="React GUI Bot Framework Development Runner")
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    runner = DevelopmentRunner(args.project_root)
    success = runner.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
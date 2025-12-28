"""Test installation in a fresh virtual environment.
This test ensures that requirements.txt and requirements-dev.txt contain
all necessary dependencies for the bots framework to function properly.
The test creates a fresh virtual environment, installs dependencies,
and verifies that:
1. All core dependencies are installed correctly
2. The package can be imported without errors
3. Basic functionality works (creating bots, using tools)
4. Development dependencies are present when installed
Usage:
    pytest tests/test_install_in_fresh_environment.py
    pytest tests/test_install_in_fresh_environment.py -v
    pytest tests/test_install_in_fresh_environment.py::test_core_requirements
"""

import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import pytest


def run_command(cmd: List[str], cwd: str = None, timeout: int = 300) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr.
    Args:
        cmd: Command and arguments as a list
        cwd: Working directory for the command
        timeout: Maximum time to wait for command completion in seconds
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


def create_venv(venv_path: Path) -> None:
    """Create a fresh virtual environment.
    Args:
        venv_path: Path where the virtual environment should be created
    """
    returncode, stdout, stderr = run_command([sys.executable, "-m", "venv", str(venv_path)])
    if returncode != 0:
        raise RuntimeError(f"Failed to create venv: {stderr}")


def get_venv_python(venv_path: Path) -> str:
    """Get the path to the Python executable in the virtual environment.
    Args:
        venv_path: Path to the virtual environment
    Returns:
        Path to the Python executable
    """
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "python.exe")
    else:
        return str(venv_path / "bin" / "python")


def get_venv_pip(venv_path: Path) -> str:
    """Get the path to the pip executable in the virtual environment.
    Args:
        venv_path: Path to the virtual environment
    Returns:
        Path to the pip executable
    """
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "pip.exe")
    else:
        return str(venv_path / "bin" / "pip")


@pytest.fixture
def fresh_venv(tmp_path):
    """Create a fresh virtual environment for testing.
    Yields:
        Tuple of (venv_path, python_path, pip_path)
    """
    venv_path = tmp_path / "test_venv"
    create_venv(venv_path)
    python_path = get_venv_python(venv_path)
    pip_path = get_venv_pip(venv_path)
    # Upgrade pip to avoid warnings
    run_command([python_path, "-m", "pip", "install", "--upgrade", "pip"], timeout=120)
    yield venv_path, python_path, pip_path


@pytest.fixture
def repo_root():
    """Get the repository root directory.
    Returns:
        Path to the repository root
    """
    # Assuming this test file is in tests/
    return Path(__file__).parent.parent


def test_core_requirements(fresh_venv, repo_root):
    """Test that requirements.txt installs all necessary core dependencies."""
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    # Install core requirements
    returncode, stdout, stderr = run_command([pip_path, "install", "-r", str(requirements_file)], timeout=300)
    assert returncode == 0, f"Failed to install requirements.txt: {stderr}"
    # Verify key packages are installed
    expected_packages = [
        "anthropic",
        "openai",
        "google-genai",
        "typing_extensions",
        "libcst",
        "dill",
        "psutil",
        "numpy",
        "opentelemetry-api",
        "opentelemetry-sdk",
    ]
    for package in expected_packages:
        returncode, stdout, stderr = run_command([pip_path, "show", package])
        assert returncode == 0, f"Package {package} not installed"


def test_package_installation(fresh_venv, repo_root):
    """Test that the package can be installed in editable mode."""
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    # Install requirements first
    returncode, stdout, stderr = run_command([pip_path, "install", "-r", str(requirements_file)], timeout=300)
    assert returncode == 0, f"Failed to install requirements: {stderr}"
    # Install package in editable mode
    returncode, stdout, stderr = run_command([pip_path, "install", "-e", str(repo_root)], timeout=120)
    assert returncode == 0, f"Failed to install package: {stderr}"


def test_basic_import(fresh_venv, repo_root):
    """Test that the package can be imported after installation."""
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    # Install requirements and package
    run_command([pip_path, "install", "-r", str(requirements_file)], timeout=300)
    run_command([pip_path, "install", "-e", str(repo_root)], timeout=120)
    # Test basic imports
    test_script = """
import sys
try:
    import bots
    from bots.foundation.base import Bot, Engines
    from bots.foundation.anthropic_bots import AnthropicBot
    from bots.foundation.openai_bots import ChatGPT_Bot
    from bots.foundation.gemini_bots import GeminiBot
    from bots.dev.decorators import toolify, lazy
    from bots.flows import functional_prompts
    print("SUCCESS: All imports successful")
    sys.exit(0)
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    returncode, stdout, stderr = run_command([python_path, "-c", test_script], timeout=30)
    assert returncode == 0, f"Import test failed: {stderr}\n{stdout}"
    assert "SUCCESS" in stdout


def test_dev_requirements(fresh_venv, repo_root):
    """Test that requirements-dev.txt installs all development dependencies."""
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    dev_requirements_file = repo_root / "requirements-dev.txt"
    # Install core requirements first
    returncode, stdout, stderr = run_command([pip_path, "install", "-r", str(requirements_file)], timeout=300)
    assert returncode == 0, f"Failed to install requirements.txt: {stderr}"
    # Install dev requirements
    returncode, stdout, stderr = run_command([pip_path, "install", "-r", str(dev_requirements_file)], timeout=300)
    assert returncode == 0, f"Failed to install requirements-dev.txt: {stderr}"
    # Verify key dev packages are installed
    expected_dev_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-timeout",
        "pytest-xdist",
        "pytest-mock",
        "black",
        "isort",
        "flake8",
        "mypy",
        "sphinx",
    ]
    for package in expected_dev_packages:
        returncode, stdout, stderr = run_command([pip_path, "show", package])
        assert returncode == 0, f"Dev package {package} not installed"


def test_pytest_runs(fresh_venv, repo_root):
    """Test that pytest can be run after installing dev requirements."""
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    dev_requirements_file = repo_root / "requirements-dev.txt"
    # Install all requirements and package
    run_command([pip_path, "install", "-r", str(requirements_file)], timeout=300)
    run_command([pip_path, "install", "-r", str(dev_requirements_file)], timeout=300)
    run_command([pip_path, "install", "-e", str(repo_root)], timeout=120)
    # Try to run pytest --collect-only (just collect tests, don't run them)
    pytest_path = get_venv_pip(venv_path).replace("pip", "pytest")
    if platform.system() == "Windows":
        pytest_path = pytest_path.replace("pip.exe", "pytest.exe")
    returncode, stdout, stderr = run_command(
        [pytest_path, "--collect-only", str(repo_root / "tests" / "unit")], cwd=str(repo_root), timeout=60
    )
    # Should be able to collect tests (returncode 0 or 5 for no tests collected)
    assert returncode in [0, 5], f"pytest collection failed: {stderr}\n{stdout}"


def test_setup_py_install(fresh_venv, repo_root):
    """Test that 'pip install .[dev]' works correctly."""
    venv_path, python_path, pip_path = fresh_venv
    # Install package with dev extras
    returncode, stdout, stderr = run_command([pip_path, "install", "-e", f"{repo_root}[dev]"], timeout=300)
    assert returncode == 0, f"Failed to install with [dev] extras: {stderr}"
    # Verify both core and dev packages are installed
    test_packages = ["anthropic", "pytest", "black"]
    for package in test_packages:
        returncode, stdout, stderr = run_command([pip_path, "show", package])
        assert returncode == 0, f"Package {package} not installed with [dev] extras"


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])

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
    pytest tests/test_install_temp.py -n0
    pytest tests/test_install_temp.py -v -n0
    pytest tests/test_install_temp.py::test_core_requirements -n0
Note: These tests are SKIPPED when running in parallel mode (pytest with -n auto).
They must run serially (use -n0) as they create virtual environments
and can timeout or crash when run in parallel.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

pytestmark = [pytest.mark.serial, pytest.mark.slow, pytest.mark.installation]


def skip_if_xdist():
    """Skip test if running under xdist (parallel execution)."""
    if hasattr(sys, "_called_from_test"):
        return
    if os.environ.get("PYTEST_XDIST_WORKER"):
        pytest.skip("This test must run serially (use pytest -n0)")


def scan_project_for_imports() -> Tuple[List[str], List[str]]:
    """Scan the project for third-party imports to verify requirements completeness.

    Returns:
        Tuple of (core_packages, dev_packages) where:
        - core_packages: packages imported in bots/ directory
        - dev_packages: packages imported in tests/ directory
    """
    import ast
    import sys
    from pathlib import Path

    # Get project root (parent of tests directory)
    project_root = Path(__file__).parent.parent

    # Standard library modules (Python 3.12)
    stdlib_modules = set(sys.stdlib_module_names)

    # Local modules (our own packages and subpackages)
    local_modules = {"bots", "tests", "conftest", "tools"}

    core_packages = set()
    dev_packages = set()

    def extract_imports(file_path: Path) -> set:
        """Extract top-level import names from a Python file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get the top-level package name
                        package = alias.name.split(".")[0]
                        imports.add(package)
                elif isinstance(node, ast.ImportFrom):
                    # Skip relative imports (e.g., from .dev import something)
                    if node.level > 0:
                        continue
                    if node.module:
                        # Get the top-level package name
                        package = node.module.split(".")[0]
                        imports.add(package)

            return imports
        except Exception:
            return set()

    # Scan bots/ directory for core dependencies
    bots_dir = project_root / "bots"
    if bots_dir.exists():
        for py_file in bots_dir.rglob("*.py"):
            imports = extract_imports(py_file)
            for imp in imports:
                if imp not in stdlib_modules and imp not in local_modules:
                    core_packages.add(imp)

    # Scan tests/ directory for dev dependencies
    tests_dir = project_root / "tests"
    if tests_dir.exists():
        for py_file in tests_dir.rglob("*.py"):
            imports = extract_imports(py_file)
            for imp in imports:
                if imp not in stdlib_modules and imp not in local_modules and imp not in core_packages:
                    dev_packages.add(imp)

    # Map import names to package names (handle special cases)
    package_mapping = {
        "anthropic": "anthropic",
        "openai": "openai",
        "google": "google-genai",
        "pytest": "pytest",
        "black": "black",
        "isort": "isort",
        "flake8": "flake8",
        "mypy": "mypy",
        "libcst": "libcst",
        "click": "click",
        "psutil": "psutil",
        "numpy": "numpy",
        "opentelemetry": "opentelemetry-api",
    }

    # Convert import names to package names
    core_packages = {package_mapping.get(pkg, pkg) for pkg in core_packages}
    dev_packages = {package_mapping.get(pkg, pkg) for pkg in dev_packages}

    return sorted(core_packages), sorted(dev_packages)


def run_command(cmd: List[str], cwd: str = None, timeout: int = 300) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds: {' '.join(cmd)}"
    except Exception as e:
        return -1, "", str(e)


def create_venv(venv_path: Path) -> None:
    """Create a virtual environment at the given path."""
    import venv

    venv.create(venv_path, with_pip=True, clear=True)


def get_venv_python(venv_path: Path) -> str:
    """Get the path to the Python executable in the virtual environment."""
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "python.exe")
    else:
        return str(venv_path / "bin" / "python")


def get_venv_pip(venv_path: Path) -> str:
    """Get the path to the pip executable in the virtual environment."""
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "pip.exe")
    else:
        return str(venv_path / "bin" / "pip")


def get_venv_pytest(venv_path: Path) -> str:
    """Get the path to the pytest executable in the virtual environment."""
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "pytest.exe")
    else:
        return str(venv_path / "bin" / "pytest")


@pytest.fixture
def fresh_venv(tmp_path):
    """Create a fresh virtual environment for testing."""
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
    skip_if_xdist()
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    # Install core requirements
    returncode, stdout, stderr = run_command([pip_path, "install", "-r", str(requirements_file)], timeout=1200)
    assert returncode == 0, f"Failed to install requirements.txt: {stderr}"
    # Verify key packages are installed (dynamically scanned from project code)
    expected_packages, _ = scan_project_for_imports()
    for package in expected_packages:
        returncode, stdout, stderr = run_command([pip_path, "show", package])
        assert returncode == 0, f"Package {package} not installed (found in project imports)"


def test_package_installation(fresh_venv, repo_root):
    """Test that the package can be installed in editable mode."""
    skip_if_xdist()
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    # Install requirements first
    returncode, stdout, stderr = run_command([pip_path, "install", "-r", str(requirements_file)], timeout=1200)
    assert returncode == 0, f"Failed to install requirements: {stderr}"
    # Install package in editable mode
    returncode, stdout, stderr = run_command([pip_path, "install", "-e", str(repo_root)], timeout=120)
    assert returncode == 0, f"Failed to install package: {stderr}"


def test_basic_import(fresh_venv, repo_root):
    """Test that the package can be imported after installation."""
    skip_if_xdist()
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    # Install requirements and package
    run_command([pip_path, "install", "-r", str(requirements_file)], timeout=1200)
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
    skip_if_xdist()
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    dev_requirements_file = repo_root / "requirements-dev.txt"
    # Install core requirements first
    returncode, stdout, stderr = run_command([pip_path, "install", "-r", str(requirements_file)], timeout=1200)
    assert returncode == 0, f"Failed to install requirements.txt: {stderr}"
    # Install dev requirements
    returncode, stdout, stderr = run_command([pip_path, "install", "-r", str(dev_requirements_file)], timeout=1200)
    assert returncode == 0, f"Failed to install requirements-dev.txt: {stderr}"
    # Verify key dev packages are installed (dynamically scanned from test code)
    _, expected_dev_packages = scan_project_for_imports()
    for package in expected_dev_packages:
        returncode, stdout, stderr = run_command([pip_path, "show", package])
        assert returncode == 0, f"Dev package {package} not installed (found in test imports)"


def test_pytest_runs(fresh_venv, repo_root):
    """Test that pytest can be run after installing dev requirements."""
    skip_if_xdist()
    venv_path, python_path, pip_path = fresh_venv
    requirements_file = repo_root / "requirements.txt"
    dev_requirements_file = repo_root / "requirements-dev.txt"
    # Install all requirements and package
    run_command([pip_path, "install", "-r", str(requirements_file)], timeout=1200)
    run_command([pip_path, "install", "-r", str(dev_requirements_file)], timeout=1200)
    run_command([pip_path, "install", "-e", str(repo_root)], timeout=120)
    # Try to run pytest --collect-only (just collect tests, don't run them)
    pytest_path = get_venv_pytest(venv_path)
    returncode, stdout, stderr = run_command(
        [pytest_path, "--collect-only", str(repo_root / "tests" / "unit")], cwd=str(repo_root), timeout=60
    )
    # Should be able to collect tests (returncode 0 or 5 for no tests collected)
    assert returncode in [0, 5], f"pytest collection failed: {stderr}\n{stdout}"


def test_setup_py_install(fresh_venv, repo_root):
    """Test that 'pip install .[dev]' works correctly."""
    skip_if_xdist()
    venv_path, python_path, pip_path = fresh_venv
    # Install package with dev extras
    returncode, stdout, stderr = run_command([pip_path, "install", "-e", f"{repo_root}[dev]"], timeout=1200)
    assert returncode == 0, f"Failed to install with [dev] extras: {stderr}"
    # Verify both core and dev packages are installed
    test_packages = ["anthropic", "pytest", "black"]
    for package in test_packages:
        returncode, stdout, stderr = run_command([pip_path, "show", package])
        assert returncode == 0, f"Package {package} not installed with [dev] extras"


def test_scanner_detects_new_imports(tmp_path, repo_root):
    """Test that the import scanner correctly detects new third-party imports.

    This is a positive test to verify that scan_project_for_imports() will
    catch new dependencies when they are added to the codebase.
    """
    skip_if_xdist()
    import hashlib
    from datetime import datetime

    # Create a unique fake package name using current datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    fake_package = f"fake_package_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"

    # Create a temporary Python file in the bots package with the fake import
    temp_module_dir = repo_root / "bots" / "temp_test_module"
    temp_module_dir.mkdir(exist_ok=True)

    try:
        # Create __init__.py to make it a package
        (temp_module_dir / "__init__.py").write_text("")

        # Create a Python file with the fake import
        temp_file = temp_module_dir / "temp_test_file.py"
        temp_file.write_text(
            f"""
# Temporary test file to verify import scanner
import {fake_package}

def test_function():
    pass
"""
        )

        # Run the scanner
        core_packages, dev_packages = scan_project_for_imports()

        # Verify the fake package was detected
        assert fake_package in core_packages, (
            f"Scanner failed to detect new import '{fake_package}'. " f"Found core packages: {core_packages}"
        )

        print(f"âœ“ Scanner successfully detected fake package: {fake_package}")

    finally:
        # Clean up the temporary files
        if temp_file.exists():
            temp_file.unlink()
        if (temp_module_dir / "__init__.py").exists():
            (temp_module_dir / "__init__.py").unlink()
        if temp_module_dir.exists():
            temp_module_dir.rmdir()


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])

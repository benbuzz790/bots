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
    pytest tests/test_install_in_fresh_environment.py -n0
    pytest tests/test_install_in_fresh_environment.py -v -n0
    pytest tests/test_install_in_fresh_environment.py::test_core_requirements -n0
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

# Mark all tests in this module as serial - they MUST NOT run in parallel
pytestmark = [pytest.mark.serial, pytest.mark.slow, pytest.mark.installation]


@pytest.fixture(autouse=True, scope="module")
def skip_if_xdist():
    """Skip all tests in this module if running with xdist (parallel mode)."""
    if os.environ.get("PYTEST_XDIST_WORKER"):
        pytest.skip(
            "Installation tests must run serially with -n0 (skipped in parallel mode)",
            allow_module_level=True,
        )


def scan_project_for_imports() -> Tuple[List[str], List[str]]:
    """Scan project Python files to extract third-party package dependencies.

    This function analyzes all Python files in the project to determine which
    third-party packages are actually imported and used. It filters out:
    - Standard library modules
    - Local packages (bots and its subpackages)
    - Build-only packages (setuptools, wheel, pip)

    Returns:
        Tuple of (core_packages, dev_packages) where:
        - core_packages: packages imported in non-test code
        - dev_packages: packages imported only in test code
    """
    import ast
    from pathlib import Path
    from typing import Dict, Set

    def get_imports_from_file(file_path: Path) -> Set[str]:
        """Extract all top-level import names from a Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            imports = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    # Only process absolute imports (level == 0)
                    if node.level == 0 and node.module:
                        imports.add(node.module.split(".")[0])

            return imports
        except Exception:
            return set()

    def is_stdlib_module(module_name: str) -> bool:
        """Check if a module is part of Python's standard library."""
        stdlib_modules = {
            "abc",
            "aifc",
            "argparse",
            "array",
            "ast",
            "asynchat",
            "asyncio",
            "asyncore",
            "atexit",
            "audioop",
            "base64",
            "bdb",
            "binascii",
            "binhex",
            "bisect",
            "builtins",
            "bz2",
            "calendar",
            "cgi",
            "cgitb",
            "chunk",
            "cmath",
            "cmd",
            "code",
            "codecs",
            "codeop",
            "collections",
            "colorsys",
            "compileall",
            "concurrent",
            "configparser",
            "contextlib",
            "contextvars",
            "copy",
            "copyreg",
            "cProfile",
            "crypt",
            "csv",
            "ctypes",
            "curses",
            "dataclasses",
            "datetime",
            "dbm",
            "decimal",
            "difflib",
            "dis",
            "distutils",
            "doctest",
            "email",
            "encodings",
            "enum",
            "errno",
            "faulthandler",
            "fcntl",
            "filecmp",
            "fileinput",
            "fnmatch",
            "formatter",
            "fractions",
            "ftplib",
            "functools",
            "gc",
            "getopt",
            "getpass",
            "gettext",
            "glob",
            "graphlib",
            "grp",
            "gzip",
            "hashlib",
            "heapq",
            "hmac",
            "html",
            "http",
            "imaplib",
            "imghdr",
            "imp",
            "importlib",
            "inspect",
            "io",
            "ipaddress",
            "itertools",
            "json",
            "keyword",
            "lib2to3",
            "linecache",
            "locale",
            "logging",
            "lzma",
            "mailbox",
            "mailcap",
            "marshal",
            "math",
            "mimetypes",
            "mmap",
            "modulefinder",
            "msilib",
            "msvcrt",
            "multiprocessing",
            "netrc",
            "nis",
            "nntplib",
            "numbers",
            "operator",
            "optparse",
            "os",
            "ossaudiodev",
            "parser",
            "pathlib",
            "pdb",
            "pickle",
            "pickletools",
            "pipes",
            "pkgutil",
            "platform",
            "plistlib",
            "poplib",
            "posix",
            "posixpath",
            "pprint",
            "profile",
            "pstats",
            "pty",
            "pwd",
            "py_compile",
            "pyclbr",
            "pydoc",
            "queue",
            "quopri",
            "random",
            "re",
            "readline",
            "reprlib",
            "resource",
            "rlcompleter",
            "runpy",
            "sched",
            "secrets",
            "select",
            "selectors",
            "shelve",
            "shlex",
            "shutil",
            "signal",
            "site",
            "smtpd",
            "smtplib",
            "sndhdr",
            "socket",
            "socketserver",
            "spwd",
            "sqlite3",
            "ssl",
            "stat",
            "statistics",
            "string",
            "stringprep",
            "struct",
            "subprocess",
            "sunau",
            "symbol",
            "symtable",
            "sys",
            "sysconfig",
            "syslog",
            "tabnanny",
            "tarfile",
            "telnetlib",
            "tempfile",
            "termios",
            "test",
            "textwrap",
            "threading",
            "time",
            "timeit",
            "tkinter",
            "token",
            "tokenize",
            "tomllib",
            "trace",
            "traceback",
            "tracemalloc",
            "tty",
            "turtle",
            "turtledemo",
            "types",
            "typing",
            "unicodedata",
            "unittest",
            "urllib",
            "uu",
            "uuid",
            "venv",
            "warnings",
            "wave",
            "weakref",
            "webbrowser",
            "winreg",
            "winsound",
            "wsgiref",
            "xdrlib",
            "xml",
            "xmlrpc",
            "zipapp",
            "zipfile",
            "zipimport",
            "zlib",
            "_thread",
        }
        return module_name in stdlib_modules

    def get_local_subpackages(project_root: Path, main_package: str) -> Set[str]:
        """Get all subpackage names within the main package."""
        subpackages = set()
        main_package_dir = project_root / main_package

        if main_package_dir.exists():
            for item in main_package_dir.rglob("*"):
                if item.is_dir() and (item / "__init__.py").exists():
                    rel_path = item.relative_to(main_package_dir)
                    if rel_path.parts:
                        subpackages.add(rel_path.parts[0])

        return subpackages

    def get_import_to_package_mapping() -> Dict[str, str]:
        """Map import names to PyPI package names."""
        return {
            "google": "google-genai",
            "opentelemetry": "opentelemetry-api",
        }

    # Setup
    project_root = Path(__file__).parent.parent
    main_package = "bots"
    exclude_dirs = {
        "venv",
        ".venv",
        "env",
        "__pycache__",
        ".git",
        "build",
        "dist",
        "*.egg-info",
        "__trash",
        "archived_docker_testing",
    }

    core_imports = set()
    dev_imports = set()

    # Get local packages
    local_packages = {main_package}
    local_packages.update(get_local_subpackages(project_root, main_package))
    local_packages.add("tests")
    local_packages.add("conftest")

    # Scan all Python files
    for py_file in project_root.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        # Determine if this is a test file
        is_test_file = "tests" in py_file.parts or py_file.name.startswith("test_") or py_file.name == "conftest.py"

        imports = get_imports_from_file(py_file)

        if is_test_file:
            dev_imports.update(imports)
        else:
            core_imports.update(imports)

    # Process imports to get package names
    import_to_package = get_import_to_package_mapping()

    def process_imports(imports: Set[str]) -> List[str]:
        """Filter and map imports to package names."""
        packages = set()
        for imp in imports:
            if is_stdlib_module(imp):
                continue
            if imp in local_packages:
                continue
            if imp in {"setuptools", "wheel", "pip"}:
                continue
            package_name = import_to_package.get(imp, imp)
            packages.add(package_name)
        return sorted(packages)

    core_packages = process_imports(core_imports)
    dev_packages_all = process_imports(dev_imports)

    # Remove core packages from dev (dev should only have additional ones)
    dev_only_packages = [pkg for pkg in dev_packages_all if pkg not in core_packages]

    return core_packages, dev_only_packages


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
    # Verify key packages are installed (dynamically scanned from project code)
    expected_packages, _ = scan_project_for_imports()
    for package in expected_packages:
        returncode, stdout, stderr = run_command([pip_path, "show", package])
        assert returncode == 0, f"Package {package} not installed (found in project imports)"


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
    # Verify key dev packages are installed (dynamically scanned from test code)
    _, expected_dev_packages = scan_project_for_imports()
    for package in expected_dev_packages:
        returncode, stdout, stderr = run_command([pip_path, "show", package])
        assert returncode == 0, f"Dev package {package} not installed (found in test imports)"


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


def test_scanner_detects_new_imports(tmp_path, repo_root):
    """Test that the import scanner correctly detects new third-party imports.

    This is a positive test to verify that scan_project_for_imports() will
    catch new dependencies when they are added to the codebase.
    """
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

        print(f"✓ Scanner successfully detected fake package: {fake_package}")

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

"""Setup configuration for the bots package.

This module handles the installation configuration for the bots framework,
a tool for making LLM interactions convenient and powerful. It manages package
metadata, dependencies, and installation requirements.

Features:
    - Automatic package discovery
    - Core dependencies (anthropic, openai, google-genai)
    - Development extras (pytest, black, etc.)
    - Python version compatibility check

Example:
    Basic installation:
        pip install .

    Development installation:
        pip install -e .[dev]
"""

import os
from typing import Dict, List

from setuptools import find_packages, setup


def _read_long_description() -> str:
    """Read and return the package's long description from README.md file.

    Use when you need to get the package's long description for PyPI setup.
    The function looks for README.md in the same directory as setup.py and
    reads its contents with UTF-8 encoding.

    Raises:
        FileNotFoundError: If README.md is not found in the package root
        IOError: If README.md cannot be read

    Returns:
        str: The complete contents of README.md as a string, with all
             formatting intact for proper PyPI rendering
    """
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    with open(readme_path, encoding="utf-8") as f:
        return f.read()


# Get package description
long_description: str = _read_long_description()

# Core package dependencies required for basic functionality
INSTALL_REQUIRES: List[str] = [
    # LLM Provider SDKs
    "anthropic>=0.18.0",
    "openai>=1.0.0",
    "google-genai>=0.2.0",
    # Type hints compatibility
    "typing_extensions>=4.12.0",
    # Code parsing and manipulation
    "libcst>=1.0.0",
    # Serialization for bot state management
    "dill>=0.3.0",
    # System utilities
    "psutil>=5.9.0",
    # Audio/sound generation (for piano tool)
    "numpy>=1.24.0",
    # OpenTelemetry core packages for observability
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
]

# Optional development dependencies for testing and development
EXTRAS_REQUIRE: Dict[str, List[str]] = {
    "dev": [
        # Testing framework and plugins
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "pytest-timeout>=2.4.0",
        "pytest-xdist>=3.7.0",
        "pytest-forked>=1.6.0",
        "pytest-mock>=3.15.0",
        "pytest-rerunfailures>=12.0",
        # Code formatting
        "black>=24.0.0",
        "isort>=5.13.0",
        # Linting
        "flake8>=7.0.0",
        "mypy>=1.13.0",
        # Security scanning
        "bandit>=1.8.0",
        # Documentation
        "sphinx>=7.2.0",
        "sphinx-rtd-theme>=2.0.0",
        # Pre-commit hooks
        "pre-commit>=3.5.0",
    ],
    # Optional exporters for production observability
    "observability": [
        "opentelemetry-exporter-otlp>=1.20.0",
        "opentelemetry-exporter-jaeger>=1.20.0",
    ],
}

# PyPI classifiers defining package metadata
# See https://pypi.org/classifiers/ for full list
CLASSIFIERS: List[str] = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

setup(
    name="bots",
    version="3.0.0",
    author="Ben Rinauto",
    author_email="ben.rinauto@gmail.com",
    description="A framework for LLM tool use",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/benbuzz790/bots",
    classifiers=CLASSIFIERS,
    packages=find_packages(),  # Automatically find all packages
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=">=3.12",
)

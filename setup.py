"""Setup configuration for the bots package.

This module handles the installation configuration for the bots framework,
a tool for making LLM interactions convenient and powerful. It manages package
metadata, dependencies, and installation requirements.

Features:
    - Automatic package discovery
    - Core dependencies (anthropic, openai)
    - Development extras (pytest)
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
    # Required for Claude LLM integration
    "anthropic",
    # Required for GPT LLM integration
    "openai",
    # Required for Python 3.6+ type hint compatibility
    "typing_extensions",
]

# Optional development dependencies for testing and development
EXTRAS_REQUIRE: Dict[str, List[str]] = {
    # Testing framework for running the test suite
    "dev": ["pytest"],
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
    version="2.0.0",
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

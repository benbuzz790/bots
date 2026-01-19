"""File utilities for the bots framework.

This module provides utilities for file operations with proper encoding handling.
"""

from pathlib import Path
from typing import Union


def append_text_file(filepath: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
    """Append text to a file with proper encoding (BOM-free).

    Args:
        filepath: Path to the file
        content: Text content to append
        encoding: Text encoding (default: utf-8)
    """
    filepath = Path(filepath)

    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Append to file with specified encoding
    with open(filepath, "a", encoding=encoding) as f:
        f.write(content)


def write_text_file(filepath: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
    """Write text to a file with proper encoding (BOM-free).

    Args:
        filepath: Path to the file
        content: Text content to write
        encoding: Text encoding (default: utf-8)
    """
    filepath = Path(filepath)

    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write to file with specified encoding
    with open(filepath, "w", encoding=encoding) as f:
        f.write(content)


def read_text_file(filepath: Union[str, Path], encoding: str = "utf-8") -> str:
    """Read text from a file with proper encoding.

    Args:
        filepath: Path to the file
        encoding: Text encoding (default: utf-8)

    Returns:
        File content as string
    """
    filepath = Path(filepath)

    with open(filepath, "r", encoding=encoding) as f:
        return f.read()

"""Unicode handling utilities for CI environments."""

import os
import sys
from typing import Any


def ensure_utf8_encoding():
    """Ensure proper UTF-8 encoding for the current environment.
    This function sets up UTF-8 encoding to prevent Unicode errors
    in CI environments, particularly on Windows runners.
    """
    # Set UTF-8 encoding for stdout/stderr
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    # Set environment variables for UTF-8
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")


def clean_unicode_string(text: Any) -> str:
    """Clean a string of problematic Unicode characters.
    Args:
        text: Input that may contain BOMs or other problematic characters
    Returns:
        Cleaned string safe for ASCII encoding contexts
    """
    if not isinstance(text, str):
        text = str(text)
    # Remove BOM and other problematic characters
    cleaned = text.encode("utf-8", errors="ignore").decode("utf-8")
    # Remove BOM specifically
    cleaned = cleaned.lstrip("\ufeff")
    # Strip whitespace
    cleaned = cleaned.strip()
    return cleaned


def clean_dict_strings(data: Any) -> Any:
    """Recursively clean all strings in a dictionary or list.
    Args:
        data: Dictionary, list, or other data structure to clean
    Returns:
        Cleaned data structure with all strings processed
    """
    if isinstance(data, dict):
        return {clean_unicode_string(k): clean_dict_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_dict_strings(item) for item in data]
    elif isinstance(data, str):
        return clean_unicode_string(data)
    else:
        return data


# Ensure UTF-8 encoding is set up when module is imported
ensure_utf8_encoding()

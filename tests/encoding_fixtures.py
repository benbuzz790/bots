"""Shared fixtures and utilities for encoding/unicode tests.
This module provides common test data and helper functions for testing
unicode handling, encoding issues, and mojibake prevention across the codebase.
"""

import tempfile
from pathlib import Path
from typing import List

import pytest

# Standard unicode test strings used across all encoding tests
UNICODE_TEST_STRINGS = {
    "emoji_checkmark": "✅",
    "emoji_cross": "❌",
    "emoji_warning": "⚠️",
    "emoji_party": "🎉",
    "emoji_memo": "📝",
    "emoji_wrench": "🔧",
    "chinese": "中文测试",
    "arabic": "العربية",
    "mixed": "✅ Test 中文 🎉 العربية ❌",
    "long_unicode": "✅" * 100,
    "problematic_cp437": "Γ£à",  # What ✅ looks like when decoded as CP437
}


def assert_no_mojibake(text: str, expected_chars: List[str]) -> None:
    """Assert that text contains expected unicode characters without mojibake.
    This function checks that:
    1. All expected unicode characters are present in the text
    2. No mojibake artifacts are present (e.g., Γ£à instead of ✅)
    Args:
        text: The text to check for proper unicode encoding
        expected_chars: List of unicode characters that should be present
    Raises:
        AssertionError: If expected chars are missing or mojibake is detected
    Example:
        >>> assert_no_mojibake("Status: ✅", ['✅'])
        >>> assert_no_mojibake("Γ£à", ['✅'])  # Raises AssertionError
    """
    for char in expected_chars:
        assert char in text, (
            f"Expected unicode character '{char}' not found in text. " f"Text may have mojibake. Got: {text!r}"
        )
    # Check for common mojibake patterns
    mojibake_patterns = ["Γ£à", "â", "Ã", "Â"]
    for pattern in mojibake_patterns:
        if pattern in text and pattern not in expected_chars:
            raise AssertionError(f"Mojibake pattern '{pattern}' detected in text: {text!r}")


def create_temp_unicode_file(content: str, encoding: str = "utf-8", suffix: str = ".txt") -> Path:
    """Create a temporary file with unicode content.
    Args:
        content: Unicode content to write to file
        encoding: File encoding to use (default: utf-8)
        suffix: File suffix (default: .txt)
    Returns:
        Path to the created temporary file
    Note:
        Caller is responsible for cleaning up the file.
    Example:
        >>> path = create_temp_unicode_file("Test ✅")
        >>> with open(path, 'r', encoding='utf-8') as f:
        ...     assert '✅' in f.read()
    """
    fd, path = tempfile.mkstemp(suffix=suffix, text=True)
    try:
        with open(fd, "w", encoding=encoding) as f:
            f.write(content)
    except Exception:
        import os

        os.close(fd)
        raise
    return Path(path)


def mock_powershell_output(unicode_text: str, use_utf8: bool = True) -> str:
    """Simulate PowerShell output with or without UTF-8 encoding.
    This function simulates what happens when PowerShell outputs unicode text:
    - With UTF-8: Text is properly encoded and readable
    - Without UTF-8: Text is encoded as CP437, causing mojibake
    Args:
        unicode_text: The unicode text to process
        use_utf8: If True, simulate UTF-8 encoding; if False, simulate CP437
    Returns:
        The text as it would appear from PowerShell output
    Example:
        >>> mock_powershell_output("✅", use_utf8=True)
        '✅'
        >>> mock_powershell_output("✅", use_utf8=False)
        'Γ£à'  # Mojibake!
    """
    if use_utf8:
        return unicode_text
    else:
        # Simulate CP437 encoding issue
        try:
            # Encode as UTF-8, then decode as CP437 (causes mojibake)
            return unicode_text.encode("utf-8").decode("cp437", errors="replace")
        except Exception:
            return unicode_text.replace("✅", "Γ£à").replace("❌", "?").replace("⚠️", "?")


@pytest.fixture
def unicode_test_strings():
    """Pytest fixture providing standard unicode test strings."""
    return UNICODE_TEST_STRINGS.copy()


@pytest.fixture
def temp_unicode_file(tmp_path):
    """Pytest fixture for creating temporary unicode files.
    Returns a function that creates temp files in the pytest tmp_path.
    """

    def _create_file(content: str, encoding: str = "utf-8", filename: str = "test.txt"):
        file_path = tmp_path / filename
        file_path.write_text(content, encoding=encoding)
        return file_path

    return _create_file


@pytest.fixture
def unicode_filename(tmp_path):
    """Pytest fixture for creating files with unicode filenames."""

    def _create_unicode_file(filename: str, content: str = "test"):
        file_path = tmp_path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return _create_unicode_file

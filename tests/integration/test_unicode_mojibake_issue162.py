"""
Test for Issue #162: Mojibake and Unicode character issues in PowerShell output.

This test reproduces the issue where Unicode characters (arrows, emoji) get mangled
during PowerShell output capture and file writing operations.
"""

import os
import tempfile

from bots.tools.terminal_tools import execute_powershell


def test_unicode_in_powershell_output():
    """Test that Unicode characters are preserved in PowerShell output."""
    # Test various Unicode characters that have been reported as problematic
    test_cases = [
        ("arrow", "→", "Right arrow"),
        ("checkmark", "✅", "Check mark emoji"),
        ("cross", "❌", "Cross mark emoji"),
        ("bullet", "•", "Bullet point"),
        ("ellipsis", "…", "Horizontal ellipsis"),
    ]

    for name, char, description in test_cases:
        # Execute PowerShell command that outputs Unicode
        result = execute_powershell(f'Write-Output "{char}"')

        print("\n{description} ({name}):")
        print(f"  Expected: {char}")
        print(f"  Got: {result.strip()}")
        print(f"  Bytes: {result.strip().encode('utf-8')}")

        # Check if the character is preserved
        assert char in result, f"Unicode character {description} ({char}) was mangled in output. Got: {result}"


def test_unicode_in_file_operations():
    """Test that Unicode characters are preserved when writing to files via PowerShell."""
    test_char = "→"

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "unicode_test.txt")

        # Write Unicode to file via PowerShell
        write_cmd = f'Set-Content -Path "{test_file}" -Value "{test_char}" -Encoding UTF8'
        execute_powershell(write_cmd)

        # Read back via PowerShell
        read_cmd = f'Get-Content -Path "{test_file}" -Encoding UTF8'
        result = execute_powershell(read_cmd)

        print("\nFile write/read test:")
        print(f"  Expected: {test_char}")
        print(f"  Got: {result.strip()}")

        # Also read directly with Python to verify
        with open(test_file, "r", encoding="utf-8") as f:
            python_result = f.read().strip()

        print(f"  Python read: {python_result}")

        assert test_char in result, f"Unicode character was mangled in file operations. Got: {result}"
        assert test_char in python_result, f"Unicode character was mangled in file. Got: {python_result}"


def test_unicode_echo_command():
    """Test Unicode preservation with echo command."""
    test_string = "Test → with ✅ emoji ❌"

    result = execute_powershell(f'echo "{test_string}"')

    print("\nEcho test:")
    print(f"  Expected: {test_string}")
    print(f"  Got: {result.strip()}")

    # Check each Unicode character
    assert "→" in result, "Arrow character was mangled"
    assert "✅" in result, "Checkmark emoji was mangled"
    assert "❌" in result, "Cross emoji was mangled"


if __name__ == "__main__":
    print("Testing Unicode preservation in PowerShell output...")
    print("=" * 70)

    try:
        test_unicode_in_powershell_output()
        print("\n✅ test_unicode_in_powershell_output PASSED")
    except AssertionError:
        print("\n❌ test_unicode_in_powershell_output FAILED: {e}")

    try:
        test_unicode_in_file_operations()
        print("\n✅ test_unicode_in_file_operations PASSED")
    except AssertionError:
        print("\n❌ test_unicode_in_file_operations FAILED: {e}")

    try:
        test_unicode_echo_command()
        print("\n✅ test_unicode_echo_command PASSED")
    except AssertionError:
        print("\n❌ test_unicode_echo_command FAILED: {e}")

import os
import tempfile

from bots.tools.code_tools import view
from bots.tools.terminal_tools import execute_powershell


def test_powershell_unicode_output():
    """Test that PowerShell output preserves Unicode characters."""
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
        stripped_result = result.strip()

        print(f"\n{description} ({name}):")
        print(f"  Expected: {char}")
        print(f"  Got: {stripped_result}")
        print(f"  Bytes: {stripped_result.encode('utf-8')}")

        # Check if the character is preserved
        assert char in result, f"Unicode character {description} ({char}) was mangled in output. Got: {result}"


def test_unicode_in_file_operations():
    """Test that Unicode characters are preserved when writing to files via PowerShell."""
    test_char = "→"

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "unicode_test.txt")

        # Write Unicode via PowerShell
        write_cmd = f'Set-Content -Path "{test_file}" -Value "{test_char}" -Encoding UTF8'
        _ = execute_powershell(write_cmd)

        # Read back with view tool
        result = view(test_file)
        stripped_result = result.strip()

        print("\nFile write/read test:")
        print(f"  Expected: {test_char}")
        print(f"  Got: {stripped_result}")

        # Also read directly with Python to verify
        with open(test_file, "r", encoding="utf-8") as f:
            python_result = f.read().strip()
        print(f"  Python read: {python_result}")

        assert test_char in result, f"Unicode character was mangled in file operations. Got: {result}"


def test_powershell_echo():
    """Test PowerShell echo command with Unicode."""
    test_char = "✅"

    result = execute_powershell(f'echo "{test_char}"')
    stripped_result = result.strip()

    print("\nEcho test:")
    print(f"  Expected: {test_char}")
    print(f"  Got: {stripped_result}")

    assert test_char in result, f"Unicode character was mangled. Got: {result}"


def test_powershell_echo_to_file():
    """Test PowerShell echo redirection with Unicode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "echo_test.txt")
        test_chars = "→ ✅ ❌"

        # Use echo with redirection
        cmd = f'echo "{test_chars}" > "{test_file}"'
        _ = execute_powershell(cmd)

        # Read back
        result = view(test_file)

        print("\nEcho redirection - View result:")
        print(result)

        # Check for mojibake
        if "â†" in result or "âœ…" in result:
            print("\n❌ MOJIBAKE in echo redirection!")
            raise AssertionError("Mojibake detected in echo redirection")


if __name__ == "__main__":
    try:
        test_powershell_unicode_output()
        print("\n✓ test_powershell_unicode_output passed")
    except AssertionError:
        print("\n✗ test_powershell_unicode_output FAILED")
        raise

    try:
        test_unicode_in_file_operations()
        print("\n✓ test_unicode_in_file_operations passed")
    except AssertionError:
        print("\n✗ test_unicode_in_file_operations FAILED")
        raise

    try:
        test_powershell_echo()
        print("\n✓ test_powershell_echo passed")
    except AssertionError:
        print("\n✗ test_powershell_echo_to_file FAILED")
        raise

    try:
        test_powershell_echo_to_file()
        print("\n✓ test_powershell_echo_to_file passed")
    except AssertionError:
        print("\n✗ test_powershell_echo_to_file FAILED")
        raise

    print("\n✓ All tests passed!")

"""
Test for Issue #162: Reproduce actual mojibake in bot file operations.
"""

import os
import tempfile

from bots.tools.code_tools import view
from bots.tools.terminal_tools import execute_powershell


def test_bot_file_write_with_unicode():
    """Test if bot file operations preserve Unicode when writing via PowerShell."""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "bot_unicode_test.md")

        # Simulate bot writing a file with Unicode via PowerShell
        content = "# Test File\n\nArrow: → \nCheckmark: ✅\nCross: ❌"

        # Write using PowerShell (as bot would)
        escaped_content = content.replace('"', '`"').replace("\n", "`n")
        write_cmd = f'Set-Content -Path "{test_file}" -Value "{escaped_content}" -Encoding UTF8'
        _ = execute_powershell(write_cmd)

        print("\nWrite result: {result}")

        # Read back with view tool (as bot would)
        view_result = view(test_file)

        print("\nView result:")
        print(view_result)

        # Check for mojibake patterns
        mojibake_patterns = [
            ("â†", "→"),  # Arrow mojibake
            ("âœ…", "✅"),  # Checkmark mojibake
            ("â^]Œ", "❌"),  # Cross mojibake
        ]

        has_mojibake = False
        for pattern, original in mojibake_patterns:
            if pattern in view_result:
                print("\n❌ MOJIBAKE DETECTED: '{original}' became '{pattern}'")
                has_mojibake = True

        # Check if Unicode is preserved
        assert "→" in view_result, "Arrow not found in view result"
        assert "✅" in view_result, "Checkmark not found in view result"
        assert "❌" in view_result, "Cross not found in view result"

        if has_mojibake:
            raise AssertionError("Mojibake detected in file operations")


def test_direct_python_file_write():
    """Test Python file writing with Unicode (control test)."""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "python_unicode_test.md")

        content = "# Test File\n\nArrow: → \nCheckmark: ✅\nCross: ❌"

        # Write directly with Python
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Read back with view tool
        view_result = view(test_file)

        print("\nDirect Python write - View result:")
        print(view_result)

        # Check if Unicode is preserved
        assert "→" in view_result, "Arrow not found"
        assert "✅" in view_result, "Checkmark not found"
        assert "❌" in view_result, "Cross not found"


def test_powershell_echo_to_file():
    """Test PowerShell echo redirection with Unicode."""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "echo_test.txt")

        # Use echo with redirection
        cmd = f'echo "Arrow: → Checkmark: ✅" > "{test_file}"'
        execute_powershell(cmd)

        # Read back
        view_result = view(test_file)

        print("\nEcho redirection - View result:")
        print(view_result)

        # Check for mojibake
        if "â†" in view_result or "âœ…" in view_result:
            print("\n❌ MOJIBAKE in echo redirection!")
            raise AssertionError("Mojibake detected in echo redirection")


if __name__ == "__main__":
    print("Testing actual bot file operations with Unicode...")
    print("=" * 70)

    try:
        test_bot_file_write_with_unicode()
        print("\n✅ test_bot_file_write_with_unicode PASSED")
    except AssertionError:
        print("\n❌ test_bot_file_write_with_unicode FAILED: {e}")
    except Exception:
        print("\n❌ test_bot_file_write_with_unicode ERROR: {e}")

    try:
        test_direct_python_file_write()
        print("\n✅ test_direct_python_file_write PASSED")
    except AssertionError:
        print("\n❌ test_direct_python_file_write FAILED: {e}")

    try:
        test_powershell_echo_to_file()
        print("\n✅ test_powershell_echo_to_file PASSED")
    except AssertionError:
        print("\n❌ test_powershell_echo_to_file FAILED: {e}")

import os
import tempfile

from bots.tools.code_tools import view
from bots.tools.terminal_tools import execute_powershell


def test_bot_unicode_workflow():
    """Test the full workflow: PowerShell write -> view tool read."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "unicode_test.md")
        content = "# Test File\n\nArrow: → \nCheckmark: ✅\nCross: ❌"

        # Write using PowerShell (as bot would)
        escaped_content = content.replace('"', '`"').replace("\n", "`n")
        write_cmd = f'Set-Content -Path "{test_file}" -Value "{escaped_content}" -Encoding UTF8'
        result = execute_powershell(write_cmd)

        print(f"\nWrite result: {result}")

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
                print(f"\n❌ MOJIBAKE DETECTED: '{original}' became '{pattern}'")
                has_mojibake = True

        # Check if Unicode is preserved
        assert "→" in view_result, "Arrow not found in view result"
        assert "✅" in view_result, "Checkmark not found in view result"
        assert "❌" in view_result, "Cross not found in view result"

        if has_mojibake:
            raise AssertionError("Mojibake detected in file operations")

        print("\n✓ Unicode preserved correctly through PowerShell write and view read")


def test_direct_python_write():
    """Test direct Python file write -> view tool read."""
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

        # Use PowerShell echo with redirection
        echo_cmd = f'echo "Arrow: → Checkmark: ✅" | Out-File -FilePath "{test_file}" -Encoding UTF8'
        execute_powershell(echo_cmd)

        # Read back
        view_result = view(test_file)

        print("\nEcho redirection - View result:")
        print(view_result)

        # Check for mojibake
        if "â†" in view_result or "âœ…" in view_result:
            print("\n❌ MOJIBAKE in echo redirection!")
            raise AssertionError("Mojibake detected in echo redirection")


if __name__ == "__main__":
    try:
        test_bot_unicode_workflow()
        print("\n✓ test_bot_unicode_workflow passed")
    except AssertionError:
        print("\n✗ test_bot_unicode_workflow failed")

    try:
        test_direct_python_write()
        print("\n✓ test_direct_python_write passed")
    except AssertionError:
        print("\n✗ test_direct_python_write failed")

    try:
        test_powershell_echo_to_file()
        print("\n✓ test_powershell_echo_to_file passed")
    except AssertionError:
        print("\n✗ test_powershell_echo_to_file failed")

    print("\nAll tests completed!")
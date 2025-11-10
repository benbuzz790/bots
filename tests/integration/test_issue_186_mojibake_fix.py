"""
Test for Issue #186: Verify mojibake fix with chcp 65001
"""

import os
import tempfile

from bots.tools.terminal_tools import execute_powershell


def test_unicode_checkmark_no_mojibake():
    """Test that Unicode checkmark is preserved (not mojibake)."""
    result = execute_powershell('Write-Output "✓"')
    # Should contain the correct checkmark
    assert "✓" in result, f"Checkmark not found. Got: {result}"
    # Should NOT contain mojibake version
    assert "╬ô┬ú├┤" not in result, f"Mojibake detected! Got: {result}"
    print("✓ Test passed. Output: " + result)


def test_unicode_various_characters():
    """Test various Unicode characters that commonly cause mojibake."""
    test_cases = [
        ("✓", "checkmark", "╬ô┬ú├┤"),
        ("✔", "check mark emoji", "╬ô┬ú├┤"),
        ("→", "right arrow", "╬ô┬ó├óΓé¼ "),
        ("•", "bullet", "╬ô┬ó├óΓÇÜ┬¼├é┬ó"),
        ("…", "ellipsis", "╬ô┬ó├óΓÇÜ┬¼├é┬ª"),
    ]
    for char, description, mojibake in test_cases:
        result = execute_powershell(f'Write-Output "{char}"')
        # Check correct character is present
        assert char in result, f"{description} ({char}) not found. Got: {result}"
        # Check mojibake is NOT present
        assert mojibake not in result, f"Mojibake for {description} detected! Got: {result}"
        print(f"✓ {description} ({char}) preserved correctly")


def test_unicode_in_multiline_output():
    """Test Unicode in more complex output scenarios."""
    script = """
    Write-Output "Test Results:"
    Write-Output "  ✓ All tests passed"
    Write-Output "  → Next steps"
    Write-Output "  • Item 1"
    Write-Output "  • Item 2"
    """
    result = execute_powershell(script)
    # Check all Unicode characters are preserved
    assert "✓" in result, "Checkmark missing"
    assert "→" in result, "Arrow missing"
    assert "•" in result, "Bullet missing"
    # Check no mojibake
    assert "╬ô┬ú├┤" not in result, "Checkmark mojibake detected"
    assert "╬ô┬ó├óΓé¼ " not in result, "Arrow mojibake detected"
    assert "╬ô┬ó├óΓÇÜ┬¼├é┬ó" not in result, "Bullet mojibake detected"
    print("✓ Multiline output test passed")


def test_unicode_in_file_write_and_read():
    """Test Unicode preservation through file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "unicode_test.txt")
        # Write Unicode via PowerShell
        write_cmd = f'Set-Content -Path "{test_file}" -Value "✓ Test passed" -Encoding UTF8'
        execute_powershell(write_cmd)
        # Read back via PowerShell
        read_cmd = f'Get-Content -Path "{test_file}"'
        result = execute_powershell(read_cmd)
        # Check Unicode is preserved
        assert "✓" in result, f"Checkmark not preserved through file. Got: {result}"
        assert "╬ô┬ú├┤" not in result, f"Mojibake in file operations! Got: {result}"
        print("✓ File write/read test passed")


if __name__ == "__main__":
    print("Running Issue #186 mojibake fix tests...\n")
    test_unicode_checkmark_no_mojibake()
    test_unicode_various_characters()
    test_unicode_in_multiline_output()
    test_unicode_in_file_write_and_read()
    print("\n✓ All tests passed!")

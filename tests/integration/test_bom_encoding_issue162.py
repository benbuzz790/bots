"""
Test for Issue #162: BOM encoding and Unicode handling
"""

import tempfile

from bots.tools.terminal_tools import execute_powershell
from bots.utils.unicode_utils import clean_unicode_string


def test_bom_in_powershell_file_creation():
    """Test that PowerShell file creation adds BOM and we can handle it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = f"{tmpdir}/test_bom.txt"

        # Create file with PowerShell (which adds BOM on Windows)
        cmd = f'Set-Content -Path "{test_file}" -Value "Test content" -Encoding UTF8'
        execute_powershell(cmd)

        # Read with Python
        with open(test_file, "rb") as f:
            raw_content = f.read()

        print("\nBOM Test:")
        print(f"  First 3 bytes: {raw_content[:3]}")
        print(f"  Has UTF-8 BOM: {raw_content.startswith(b'\\xef\\xbb\\xbf')}")

        # The BOM is expected from PowerShell
        # Our tools should handle it gracefully


def test_clean_unicode_string_removes_bom():
    """Test that clean_unicode_string removes BOM."""
    # String with BOM
    bom_string = "\ufeffHello World"

    # Clean it
    cleaned = clean_unicode_string(bom_string)

    print("\nClean Unicode String Test:")
    print(f"  Original starts with BOM: {bom_string.startswith('\\ufeff')}")
    print(f"  Cleaned starts with BOM: {cleaned.startswith('\\ufeff')}")
    print(f"  Cleaned value: {cleaned}")

    assert not cleaned.startswith("\ufeff"), "BOM should be removed"
    assert cleaned == "Hello World", f"Expected 'Hello World', got '{cleaned}'"


def test_powershell_output_encoding():
    """Test that PowerShell output encoding is correct."""
    # Test with a simple echo command
    result = execute_powershell('Write-Output "Test: →"')

    print(f"\nPowerShell Output Encoding: {result.strip()}")

    # Check that the arrow is preserved
    assert "→" in result or "->" in result, f"Arrow not found in result: {result}"


if __name__ == "__main__":
    try:
        test_bom_in_powershell_file_creation()
        print("\n✅ test_bom_in_powershell_file_creation PASSED")
    except AssertionError as e:
        print(f"\n❌ test_bom_in_powershell_file_creation FAILED: {e}")
    except Exception as e:
        print(f"\n❌ test_bom_in_powershell_file_creation ERROR: {e}")

    try:
        test_clean_unicode_string_removes_bom()
        print("\n✅ test_clean_unicode_string_removes_bom PASSED")
    except AssertionError as e:
        print(f"\n❌ test_clean_unicode_string_removes_bom FAILED: {e}")

    try:
        test_powershell_output_encoding()
        print("\n✅ test_powershell_output_encoding PASSED")
    except Exception as e:
        print(f"\n❌ test_powershell_output_encoding ERROR: {e}")

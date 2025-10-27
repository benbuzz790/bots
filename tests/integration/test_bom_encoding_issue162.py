"""
Extended test for Issue #162: BOM and encoding issues.
"""

import codecs
import os
import tempfile

from bots.tools.terminal_tools import execute_powershell
from bots.utils.unicode_utils import clean_unicode_string


def test_bom_in_powershell_file_creation():
    """Test if PowerShell creates files with BOM."""
    test_char = "→"

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "bom_test.txt")

        # Write Unicode to file via PowerShell with UTF8 encoding
        write_cmd = f'Set-Content -Path "{test_file}" -Value "{test_char}" -Encoding UTF8'
        execute_powershell(write_cmd)

        # Read raw bytes
        with open(test_file, "rb") as f:
            raw_bytes = f.read()

        print("\nBOM Test:")
        print(f"  Raw bytes: {raw_bytes}")
        print(f"  First 3 bytes: {raw_bytes[:3]}")
        print(f"  Has UTF-8 BOM: {raw_bytes.startswith(codecs.BOM_UTF8)}")

        # Read with Python UTF-8
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"  Content with utf-8: '{content}'")
        print(f"  First char code: {ord(content[0]) if content else 'empty'}")

        # Read with Python UTF-8-sig (BOM aware)
        with open(test_file, "r", encoding="utf-8-sig") as f:
            content_sig = f.read()
        print(f"  Content with utf-8-sig: '{content_sig}'")

        # Test clean_unicode_string
        cleaned = clean_unicode_string(content)
        print(f"  After clean_unicode_string: '{cleaned}'")

        assert raw_bytes.startswith(codecs.BOM_UTF8), "PowerShell UTF8 encoding adds BOM"


def test_clean_unicode_string_removes_bom():
    """Test that clean_unicode_string properly removes BOM."""
    # String with BOM
    bom_string = "\ufeff→ test"

    print("\nClean Unicode String Test:")
    print(f"  Input: '{bom_string}'")
    print(f"  Input bytes: {bom_string.encode('utf-8')}")

    cleaned = clean_unicode_string(bom_string)
    print(f"  Output: '{cleaned}'")
    print(f"  Output bytes: {cleaned.encode('utf-8')}")

    assert not cleaned.startswith("\ufeff"), "BOM should be removed"
    assert "→" in cleaned, "Unicode character should be preserved"


def test_powershell_output_encoding():
    """Test PowerShell output encoding directly."""
    # Test what encoding PowerShell actually uses
    result = execute_powershell("[System.Console]::OutputEncoding.EncodingName")
    print("\nPowerShell Output Encoding: {result.strip()}")

    result = execute_powershell("$OutputEncoding.EncodingName")
    print(f"PowerShell $OutputEncoding: {result.strip()}")

    # Test chcp (code page)
    result = execute_powershell("chcp")
    print(f"Code page: {result.strip()}")


if __name__ == "__main__":
    print("Testing BOM and encoding issues...")
    print("=" * 70)

    try:
        test_bom_in_powershell_file_creation()
        print("\n✅ test_bom_in_powershell_file_creation PASSED")
    except AssertionError:
        print("\n❌ test_bom_in_powershell_file_creation FAILED: {e}")
    except Exception:
        print("\n❌ test_bom_in_powershell_file_creation ERROR: {e}")

    try:
        test_clean_unicode_string_removes_bom()
        print("\n✅ test_clean_unicode_string_removes_bom PASSED")
    except AssertionError:
        print("\n❌ test_clean_unicode_string_removes_bom FAILED: {e}")

    try:
        test_powershell_output_encoding()
        print("\n✅ test_powershell_output_encoding PASSED")
    except Exception:
        print("\n❌ test_powershell_output_encoding ERROR: {e}")

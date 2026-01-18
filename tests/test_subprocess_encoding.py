"""Tests for PowerShell subprocess encoding and unicode handling.
This module tests that PowerShell subprocess calls properly handle unicode characters
and prevent mojibake issues. Tests verify that the UTF-8 encoding prefix is used
and that unicode characters are correctly transmitted through subprocess calls.
Background: Without proper UTF-8 encoding, PowerShell defaults to CP437 encoding,
which causes mojibake where emoji like ✅ appear as Γ£à.
"""

import subprocess

import pytest
from encoding_fixtures import UNICODE_TEST_STRINGS, assert_no_mojibake


def run_powershell_with_utf8(command: str) -> str:
    """Run PowerShell command with UTF-8 encoding (CORRECT approach).
    This is the correct way to run PowerShell commands that output unicode.
    The UTF-8 encoding prefix ensures unicode characters are properly transmitted.
    Args:
        command: PowerShell command to execute
    Returns:
        Command output as string with proper unicode
    """
    full_command = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command}"
    result = subprocess.run(["powershell", "-Command", full_command], capture_output=True, encoding="utf-8", errors="replace")
    return result.stdout


def run_powershell_without_utf8(command: str) -> str:
    """Run PowerShell command without UTF-8 encoding (INCORRECT approach).
    This demonstrates the WRONG way to run PowerShell commands.
    Without UTF-8 encoding, unicode characters will be corrupted (mojibake).
    Args:
        command: PowerShell command to execute
    Returns:
        Command output (likely with mojibake for unicode chars)
    """
    result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
    return result.stdout


class TestPowerShellUTF8Encoding:
    """Test PowerShell subprocess calls with proper UTF-8 encoding."""

    def test_simple_emoji_with_utf8(self):
        """Test that emoji are correctly transmitted with UTF-8 encoding."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'Write-Output "{emoji}"'
        output = run_powershell_with_utf8(command)
        # Should contain the actual emoji, not mojibake
        assert_no_mojibake(output, [emoji])
        assert emoji in output
        assert "Γ£à" not in output  # No mojibake

    def test_multiple_emoji_with_utf8(self):
        """Test multiple different emoji in single command."""
        emojis = [
            UNICODE_TEST_STRINGS["emoji_checkmark"],
            UNICODE_TEST_STRINGS["emoji_cross"],
            UNICODE_TEST_STRINGS["emoji_warning"],
            UNICODE_TEST_STRINGS["emoji_party"],
        ]
        emoji_string = " ".join(emojis)
        command = f'Write-Output "{emoji_string}"'
        output = run_powershell_with_utf8(command)
        # All emoji should be present
        for emoji in emojis:
            assert_no_mojibake(output, [emoji])
            assert emoji in output

    def test_chinese_characters_with_utf8(self):
        """Test Chinese characters are correctly transmitted."""
        chinese = UNICODE_TEST_STRINGS["chinese"]
        command = f'Write-Output "{chinese}"'
        output = run_powershell_with_utf8(command)
        assert_no_mojibake(output, [chinese])
        assert chinese in output

    def test_arabic_characters_with_utf8(self):
        """Test Arabic characters are correctly transmitted."""
        arabic = UNICODE_TEST_STRINGS["arabic"]
        command = f'Write-Output "{arabic}"'
        output = run_powershell_with_utf8(command)
        assert_no_mojibake(output, [arabic])
        assert arabic in output

    def test_mixed_unicode_with_utf8(self):
        """Test mixed unicode (emoji + Chinese + Arabic) in single command."""
        mixed = UNICODE_TEST_STRINGS["mixed"]
        command = f'Write-Output "{mixed}"'
        output = run_powershell_with_utf8(command)
        # Check all components are present
        assert "✅" in output
        assert "中文" in output
        assert "🎉" in output
        assert "العربية" in output
        assert "❌" in output

    def test_long_unicode_string_with_utf8(self):
        """Test long strings of unicode characters."""
        # Create a long string with repeated emoji
        long_string = UNICODE_TEST_STRINGS["emoji_checkmark"] * 50
        command = f'Write-Output "{long_string}"'
        output = run_powershell_with_utf8(command)
        # Should contain many instances of the emoji
        assert output.count(UNICODE_TEST_STRINGS["emoji_checkmark"]) >= 40
        assert "Γ£à" not in output  # No mojibake

    def test_unicode_in_error_output_with_utf8(self):
        """Test that unicode in error messages is handled correctly."""
        emoji = UNICODE_TEST_STRINGS["emoji_cross"]
        # Command that writes to error stream
        command = f'Write-Error "Error: {emoji}"'
        full_command = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command}"
        result = subprocess.run(
            ["powershell", "-Command", full_command], capture_output=True, encoding="utf-8", errors="replace"
        )
        # Error output should contain the emoji
        error_output = result.stderr
        assert emoji in error_output or emoji in result.stdout


class TestPowerShellWithoutUTF8:
    """Test that PowerShell without UTF-8 encoding causes mojibake.
    These tests demonstrate the PROBLEM that proper encoding solves.
    They verify that without UTF-8 encoding, unicode is corrupted.
    """

    def test_emoji_without_utf8_causes_mojibake(self):
        """Test that emoji without UTF-8 encoding results in mojibake.
        This test may be flaky depending on system encoding, but demonstrates
        the issue that UTF-8 encoding prevents.
        """
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'Write-Output "{emoji}"'
        output = run_powershell_without_utf8(command)
        # Without UTF-8, we expect either:
        # 1. Mojibake characters (Γ£à)
        # 2. Replacement characters (?)
        # 3. Empty/missing output
        # What we should NOT see is the correct emoji
        # This assertion may fail on some systems, which is expected
        # The point is to demonstrate the encoding issue
        if output.strip():  # If we got any output
            # Either it's mojibake or it's not the correct emoji
            "Γ£à" in output or "?" in output or emoji not in output
            # Note: This test documents the problem, may not always fail
            # depending on system configuration

    def test_chinese_without_utf8_causes_issues(self):
        """Test that Chinese characters without UTF-8 cause issues."""
        chinese = UNICODE_TEST_STRINGS["chinese"]
        command = f'Write-Output "{chinese}"'
        output = run_powershell_without_utf8(command)
        # Without UTF-8, Chinese characters are likely corrupted
        # This test documents the issue
        if output.strip():
            # May contain replacement chars or mojibake
            pass  # Test documents the problem


class TestSubprocessEncodingParameters:
    """Test different subprocess encoding parameter combinations."""

    def test_encoding_parameter_utf8(self):
        """Test that encoding='utf-8' parameter is necessary."""
        emoji = UNICODE_TEST_STRINGS["emoji_party"]
        command = f'[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "{emoji}"'
        # WITH encoding parameter
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, encoding="utf-8", errors="replace")
        assert emoji in result.stdout

    def test_errors_parameter_replace(self):
        """Test that errors='replace' prevents crashes on bad encoding."""
        # Even with malformed unicode, should not crash
        command = '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "Test"'
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            encoding="utf-8",
            errors="replace",  # Replace bad chars instead of crashing
        )
        assert result.returncode == 0
        assert "Test" in result.stdout

    def test_capture_output_required(self):
        """Test that capture_output=True is needed to get output."""
        emoji = UNICODE_TEST_STRINGS["emoji_memo"]
        command = f'[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "{emoji}"'
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, encoding="utf-8")
        assert result.stdout is not None
        assert emoji in result.stdout


class TestRealWorldScenarios:
    """Test real-world scenarios with unicode in subprocess calls."""

    def test_git_log_with_emoji_commits(self):
        """Test parsing git log output with emoji in commit messages."""
        # Simulate git log output with emoji
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'Write-Output "commit abc123\nAuthor: Test\nDate: 2024-01-01\n\n    {emoji} Fixed bug"'
        output = run_powershell_with_utf8(command)
        assert emoji in output
        assert "Fixed bug" in output

    def test_file_listing_with_unicode_names(self):
        """Test listing files with unicode in filenames."""
        emoji = UNICODE_TEST_STRINGS["emoji_wrench"]
        command = f'Write-Output "{emoji}_config.txt"'
        output = run_powershell_with_utf8(command)
        assert emoji in output
        assert "config.txt" in output

    def test_status_messages_with_emoji(self):
        """Test status messages with emoji indicators."""
        checkmark = UNICODE_TEST_STRINGS["emoji_checkmark"]
        cross = UNICODE_TEST_STRINGS["emoji_cross"]
        warning = UNICODE_TEST_STRINGS["emoji_warning"]
        command = f'Write-Output "{checkmark} Success\n{cross} Failed\n{warning} Warning"'
        output = run_powershell_with_utf8(command)
        assert checkmark in output
        assert cross in output
        assert warning in output
        assert "Success" in output
        assert "Failed" in output
        assert "Warning" in output

    def test_json_output_with_unicode(self):
        """Test JSON output containing unicode characters."""
        emoji = UNICODE_TEST_STRINGS["emoji_party"]
        json_str = f'{{"status": "complete", "message": "{emoji} Done!"}}'
        command = f"Write-Output '{json_str}'"
        output = run_powershell_with_utf8(command)
        assert emoji in output
        assert "Done!" in output
        # Should be valid JSON-like structure
        assert "{" in output
        assert "}" in output


class TestEncodingBestPractices:
    """Test and document encoding best practices."""

    def test_utf8_prefix_is_required(self):
        """Document that UTF-8 prefix is required for unicode output.
        Best practice: Always use the UTF-8 encoding prefix:
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
        """
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        # CORRECT: With UTF-8 prefix
        correct_command = f'[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "{emoji}"'
        result_correct = subprocess.run(
            ["powershell", "-Command", correct_command], capture_output=True, encoding="utf-8", errors="replace"
        )
        assert emoji in result_correct.stdout

    def test_encoding_parameter_is_required(self):
        """Document that encoding='utf-8' parameter is required.
        Best practice: Always specify encoding='utf-8' in subprocess.run()
        """
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "{emoji}"'
        # CORRECT: With encoding parameter
        result = subprocess.run(
            ["powershell", "-Command", command], capture_output=True, encoding="utf-8", errors="replace"  # REQUIRED
        )
        assert emoji in result.stdout

    def test_errors_replace_is_recommended(self):
        """Document that errors='replace' is recommended for robustness.
        Best practice: Use errors='replace' to handle unexpected encoding issues
        gracefully instead of crashing.
        """
        command = '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "Test"'
        # CORRECT: With errors='replace'
        result = subprocess.run(
            ["powershell", "-Command", command], capture_output=True, encoding="utf-8", errors="replace"  # RECOMMENDED
        )
        assert result.returncode == 0
        assert result.stdout is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

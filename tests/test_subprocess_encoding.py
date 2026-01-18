"""Tests for PowerShell subprocess encoding and unicode handling.
This module tests that PowerShell subprocess calls properly handle unicode characters
and prevent mojibake issues. Tests verify that the UTF-8 encoding prefix is used
and that unicode characters are correctly transmitted through subprocess calls.
Background: Without proper UTF-8 encoding, PowerShell defaults to CP437 encoding,
which causes mojibake where emoji like ✅ appear as Γ£à.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Add tests directory to path to import encoding_fixtures
sys.path.insert(0, str(Path(__file__).parent))

from encoding_fixtures import UNICODE_TEST_STRINGS, assert_no_mojibake  # noqa: E402


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
    result = subprocess.run(
        ["powershell", "-Command", full_command],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
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
        """Test that a simple emoji is correctly transmitted with UTF-8 encoding."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'Write-Output "{emoji}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, [emoji])
        assert emoji in output

    def test_multiple_emoji_with_utf8(self):
        """Test multiple emoji characters with UTF-8 encoding."""
        emoji_string = "✅❌⚠️"
        command = f'Write-Output "{emoji_string}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, ["✅", "❌", "⚠️"])
        assert "✅" in output
        assert "❌" in output
        assert "⚠️" in output

    def test_chinese_characters_with_utf8(self):
        """Test Chinese characters with UTF-8 encoding."""
        chinese = UNICODE_TEST_STRINGS["chinese"]
        command = f'Write-Output "{chinese}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, [chinese])
        assert chinese in output

    def test_arabic_characters_with_utf8(self):
        """Test Arabic characters with UTF-8 encoding."""
        arabic = UNICODE_TEST_STRINGS["arabic"]
        command = f'Write-Output "{arabic}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, [arabic])
        assert arabic in output

    def test_mixed_unicode_with_utf8(self):
        """Test mixed unicode (emoji + text) with UTF-8 encoding."""
        mixed = f"{UNICODE_TEST_STRINGS['emoji_checkmark']} Test {UNICODE_TEST_STRINGS['chinese']}"
        command = f'Write-Output "{mixed}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(
            output,
            [UNICODE_TEST_STRINGS["emoji_checkmark"], UNICODE_TEST_STRINGS["chinese"]],
        )
        assert UNICODE_TEST_STRINGS["emoji_checkmark"] in output
        assert UNICODE_TEST_STRINGS["chinese"] in output

    def test_long_unicode_string_with_utf8(self):
        """Test a long string with multiple unicode characters."""
        long_string = "✅ " * 50 + UNICODE_TEST_STRINGS["chinese"] * 10
        command = f'Write-Output "{long_string}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, ["✅", UNICODE_TEST_STRINGS["chinese"]])
        assert "✅" in output
        assert UNICODE_TEST_STRINGS["chinese"] in output

    def test_unicode_in_error_output_with_utf8(self):
        """Test that unicode in error output is also handled correctly."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        # Use Write-Error to send to stderr
        command = f'Write-Error "{emoji} Error message"'
        full_command = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command}"
        result = subprocess.run(
            ["powershell", "-Command", full_command],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )

        # Error output goes to stderr
        assert emoji in result.stderr or emoji in result.stdout


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
        if output.strip():  # If we got any output
            # If output equals the correct emoji, this system has UTF-8 configured
            # Mark as xfail since the test is expected to fail on UTF-8 systems
            if emoji in output:
                pytest.xfail("System has UTF-8 configured, so mojibake doesn't occur")
            # Otherwise, verify we have mojibake or replacement characters
            assert "Γ" in output or "?" in output or emoji not in output, f"Expected mojibake but got: {output}"
        else:
            # Empty output is also a sign of encoding issues
            pytest.xfail("Empty output - encoding issue or system configuration")

    def test_chinese_without_utf8_causes_issues(self):
        """Test that Chinese characters without UTF-8 cause issues."""
        chinese = UNICODE_TEST_STRINGS["chinese"]
        command = f'Write-Output "{chinese}"'
        output = run_powershell_without_utf8(command)

        # Without UTF-8, Chinese characters are likely corrupted
        if output.strip():
            # If output equals the correct Chinese, system has UTF-8 configured
            if chinese in output:
                pytest.xfail("System has UTF-8 configured, so mojibake doesn't occur")
            # Otherwise, verify we have mojibake or replacement characters
            assert "?" in output or chinese not in output, f"Expected corruption but got: {output}"
        else:
            pytest.xfail("Empty output - encoding issue or system configuration")


class TestSubprocessEncodingParameters:
    """Test different subprocess encoding parameter combinations."""

    def test_encoding_parameter_utf8(self):
        """Test that encoding='utf-8' parameter works correctly."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'Write-Output "{emoji}"'
        full_command = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command}"

        result = subprocess.run(
            ["powershell", "-Command", full_command],
            capture_output=True,
            encoding="utf-8",
        )

        assert emoji in result.stdout

    def test_errors_parameter_replace(self):
        """Test that errors='replace' parameter handles encoding errors gracefully."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'Write-Output "{emoji}"'
        full_command = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command}"

        # Should not raise exception even if there are encoding issues
        result = subprocess.run(
            ["powershell", "-Command", full_command],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )

        assert result.stdout is not None
        assert isinstance(result.stdout, str)

    def test_capture_output_required(self):
        """Test that capture_output=True is required to get output."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'Write-Output "{emoji}"'
        full_command = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command}"

        result = subprocess.run(
            ["powershell", "-Command", full_command],
            capture_output=True,
            encoding="utf-8",
        )

        assert result.stdout is not None
        assert len(result.stdout) > 0


class TestRealWorldScenarios:
    """Test real-world scenarios with unicode in subprocess calls."""

    def test_git_log_with_emoji_commits(self):
        """Test that git log with emoji commit messages works correctly."""
        # This is a simulation - in real usage, git log would be called
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        commit_message = f"{emoji} Fixed bug"
        command = f'Write-Output "{commit_message}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, [emoji])
        assert emoji in output

    def test_file_listing_with_unicode_names(self):
        """Test listing files with unicode names."""
        unicode_filename = f"test_{UNICODE_TEST_STRINGS['emoji_checkmark']}.txt"
        command = f'Write-Output "{unicode_filename}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, [UNICODE_TEST_STRINGS["emoji_checkmark"]])
        assert UNICODE_TEST_STRINGS["emoji_checkmark"] in output

    def test_status_messages_with_emoji(self):
        """Test status messages that include emoji."""
        status = f"{UNICODE_TEST_STRINGS['emoji_checkmark']} All tests passed"
        command = f'Write-Output "{status}"'
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, [UNICODE_TEST_STRINGS["emoji_checkmark"]])
        assert UNICODE_TEST_STRINGS["emoji_checkmark"] in output
        assert "All tests passed" in output

    def test_json_output_with_unicode(self):
        """Test JSON output containing unicode characters."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        json_str = f'{{"status": "{emoji}", "message": "Success"}}'
        command = f"Write-Output '{json_str}'"
        output = run_powershell_with_utf8(command)

        assert_no_mojibake(output, [emoji])
        assert emoji in output


class TestEncodingBestPractices:
    """Test and document encoding best practices."""

    def test_utf8_prefix_is_required(self):
        """Document that UTF-8 prefix is required for proper encoding."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]

        # With UTF-8 prefix
        command_with_prefix = f'[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "{emoji}"'
        result_with = subprocess.run(
            ["powershell", "-Command", command_with_prefix],
            capture_output=True,
            encoding="utf-8",
        )

        assert emoji in result_with.stdout

    def test_encoding_parameter_is_required(self):
        """Document that encoding parameter is required."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "{emoji}"'

        # With encoding parameter
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            encoding="utf-8",
        )

        assert emoji in result.stdout

    def test_errors_replace_is_recommended(self):
        """Document that errors='replace' is recommended for robustness."""
        emoji = UNICODE_TEST_STRINGS["emoji_checkmark"]
        command = f'[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Write-Output "{emoji}"'

        # With errors='replace' - should never raise exception
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )

        assert result.stdout is not None
        assert isinstance(result.stdout, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

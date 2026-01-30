"""Tests for @toolify decorator auto-truncation functionality.

This module tests the automatic truncation feature in the @toolify decorator
that prevents context overload from very long tool outputs.

Tests cover:
- Normal-sized outputs (no truncation)
- Outputs exceeding threshold (truncation applied)
- Configuration via environment variables
- Edge cases (empty strings, None, exact threshold)
- Different output types (strings, JSON, etc.)
"""

import os
import unittest

import pytest

from bots.dev.decorators import _convert_tool_output, toolify


class TestToolifyTruncation(unittest.TestCase):
    """Test automatic truncation in @toolify decorator."""

    def setUp(self):
        """Save original environment variables."""
        self.original_env = {
            "TOOLIFY_TRUNCATE_ENABLED": os.environ.get("TOOLIFY_TRUNCATE_ENABLED"),
            "TOOLIFY_TRUNCATE_THRESHOLD": os.environ.get("TOOLIFY_TRUNCATE_THRESHOLD"),
            "TOOLIFY_TRUNCATE_PRESERVE": os.environ.get("TOOLIFY_TRUNCATE_PRESERVE"),
        }

    def tearDown(self):
        """Restore original environment variables."""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_short_output_not_truncated(self):
        """Test that outputs below threshold are not truncated."""
        short_text = "This is a short output"
        result = _convert_tool_output(short_text)

        self.assertEqual(result, short_text)
        self.assertNotIn("truncated", result)

    def test_long_output_truncated_with_default_settings(self):
        """Test that long outputs are truncated with default settings."""
        # Create output longer than default threshold (5000 chars)
        long_text = "A" * 6000
        result = _convert_tool_output(long_text)

        # Should be truncated
        self.assertLess(len(result), len(long_text))
        self.assertIn("truncated from middle to save you from context overload", result)

        # Should preserve start and end (default 2000 chars each)
        self.assertTrue(result.startswith("A" * 100))  # Check first 100 chars
        self.assertTrue(result.endswith("A" * 100))  # Check last 100 chars

    def test_truncation_preserves_start_and_end(self):
        """Test that truncation preserves specified amount from start and end."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "1000"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "100"

        # Create text with identifiable start and end
        long_text = "START" + ("X" * 1000) + "END"
        result = _convert_tool_output(long_text)

        # Should contain start and end
        self.assertIn("START", result)
        self.assertIn("END", result)
        self.assertIn("truncated", result)

    def test_truncation_can_be_disabled(self):
        """Test that truncation can be disabled via environment variable."""
        os.environ["TOOLIFY_TRUNCATE_ENABLED"] = "false"

        long_text = "A" * 10000
        result = _convert_tool_output(long_text)

        # Should NOT be truncated
        self.assertEqual(result, long_text)
        self.assertNotIn("truncated", result)

    def test_custom_threshold(self):
        """Test custom truncation threshold."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "500"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "100"

        # Text just over custom threshold
        text = "B" * 600
        result = _convert_tool_output(text)

        # Should be truncated
        self.assertIn("truncated", result)
        self.assertLess(len(result), len(text))

    def test_output_at_exact_threshold_not_truncated(self):
        """Test that output exactly at threshold is not truncated."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "1000"

        text = "C" * 1000
        result = _convert_tool_output(text)

        # Should NOT be truncated (not exceeding threshold)
        self.assertEqual(result, text)
        self.assertNotIn("truncated", result)

    def test_none_result_not_truncated(self):
        """Test that None results are handled correctly."""
        result = _convert_tool_output(None)

        self.assertEqual(result, "Tool execution completed without errors")
        self.assertNotIn("truncated", result)

    def test_empty_string_not_truncated(self):
        """Test that empty strings are not truncated."""
        result = _convert_tool_output("")

        self.assertEqual(result, "")
        self.assertNotIn("truncated", result)

    def test_json_output_truncation(self):
        """Test that JSON outputs are truncated correctly."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "500"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "100"

        # Create large dict that will serialize to long JSON
        large_dict = {f"key_{i}": f"value_{i}" * 50 for i in range(100)}
        result = _convert_tool_output(large_dict)

        # Should be truncated
        self.assertIn("truncated", result)

    def test_list_output_truncation(self):
        """Test that list outputs are truncated correctly."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "500"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "100"

        # Create large list
        large_list = [f"item_{i}" * 10 for i in range(100)]
        result = _convert_tool_output(large_list)

        # Should be truncated
        self.assertIn("truncated", result)

    def test_invalid_env_values_use_defaults(self):
        """Test that invalid environment values fall back to defaults."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "not_a_number"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "also_not_a_number"

        long_text = "D" * 6000
        result = _convert_tool_output(long_text)

        # Should still truncate using defaults
        self.assertIn("truncated", result)
        self.assertLess(len(result), len(long_text))

    def test_toolify_decorator_with_truncation(self):
        """Test that @toolify decorator applies truncation to tool outputs."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "500"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "100"

        @toolify()
        def long_output_tool() -> str:
            """A tool that returns a very long output."""
            return "E" * 1000

        result = long_output_tool()

        # Should be truncated
        self.assertIn("truncated", result)
        self.assertLess(len(result), 1000)

    def test_toolify_decorator_normal_output_unchanged(self):
        """Test that @toolify decorator doesn't affect normal-sized outputs."""

        @toolify()
        def normal_output_tool() -> str:
            """A tool that returns a normal output."""
            return "Normal output"

        result = normal_output_tool()

        # Should NOT be truncated
        self.assertEqual(result, "Normal output")
        self.assertNotIn("truncated", result)

    def test_truncation_message_format(self):
        """Test that truncation message has correct format."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "500"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "100"

        long_text = "F" * 1000
        result = _convert_tool_output(long_text)

        # Check for specific truncation message
        expected_message = "(tool result truncated from middle to save you from context overload)"
        self.assertIn(expected_message, result)

    def test_truncation_with_multiline_output(self):
        """Test truncation works correctly with multiline outputs."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "500"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "100"

        # Create multiline output
        lines = [f"Line {i}: " + ("X" * 50) for i in range(50)]
        long_text = "\n".join(lines)
        result = _convert_tool_output(long_text)

        # Should be truncated
        self.assertIn("truncated", result)
        self.assertLess(len(result), len(long_text))

    def test_preserve_amount_larger_than_threshold(self):
        """Test edge case where preserve amount is larger than threshold."""
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "500"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "1000"  # Larger than threshold

        long_text = "G" * 600
        result = _convert_tool_output(long_text)

        # Should still handle gracefully (will preserve more than threshold allows)
        self.assertIn("truncated", result)


class TestToolifyTruncationIntegration(unittest.TestCase):
    """Integration tests for truncation with various tool scenarios."""

    def setUp(self):
        """Save original environment variables."""
        self.original_env = {
            "TOOLIFY_TRUNCATE_ENABLED": os.environ.get("TOOLIFY_TRUNCATE_ENABLED"),
            "TOOLIFY_TRUNCATE_THRESHOLD": os.environ.get("TOOLIFY_TRUNCATE_THRESHOLD"),
            "TOOLIFY_TRUNCATE_PRESERVE": os.environ.get("TOOLIFY_TRUNCATE_PRESERVE"),
        }
        # Set test configuration
        os.environ["TOOLIFY_TRUNCATE_THRESHOLD"] = "500"
        os.environ["TOOLIFY_TRUNCATE_PRESERVE"] = "100"

    def tearDown(self):
        """Restore original environment variables."""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_file_reading_tool_truncation(self):
        """Test truncation for a tool that reads large files."""

        @toolify("Read a file and return its contents")
        def read_large_file(filename: str) -> str:
            """Simulate reading a large file."""
            return "FILE_CONTENT\n" * 100  # Large file content

        result = read_large_file("test.txt")

        # Should be truncated
        self.assertIn("truncated", result)
        self.assertIn("FILE_CONTENT", result)  # Should preserve some content

    def test_code_analysis_tool_truncation(self):
        """Test truncation for a tool that returns code analysis."""

        @toolify("Analyze code and return results")
        def analyze_code(code: str) -> dict:
            """Simulate code analysis with large results."""
            return {
                "functions": [f"function_{i}" for i in range(100)],
                "classes": [f"class_{i}" for i in range(100)],
                "issues": [f"issue_{i}: " + ("X" * 50) for i in range(50)],
            }

        result = analyze_code("some code")

        # Should be truncated
        self.assertIn("truncated", result)

    def test_error_messages_not_truncated(self):
        """Test that error messages are typically short and not truncated."""

        @toolify()
        def failing_tool() -> str:
            """A tool that returns an error."""
            return "Tool Failed: Something went wrong"

        result = failing_tool()

        # Should NOT be truncated (error messages are typically short)
        self.assertEqual(result, "Tool Failed: Something went wrong")
        self.assertNotIn("truncated", result)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

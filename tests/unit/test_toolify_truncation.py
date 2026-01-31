"""Tests for @toolify decorator auto-truncation functionality.
This module tests the automatic truncation feature in the @toolify decorator
that prevents context overload from very long tool outputs.
Tests cover:
- Normal-sized outputs (no truncation)
- Outputs exceeding threshold (truncation applied)
- Edge cases (empty strings, None, exact threshold)
- Different output types (strings, JSON, etc.)
"""

import unittest

from bots.dev.decorators import _convert_tool_output, toolify


class TestToolifyTruncation(unittest.TestCase):
    """Test automatic truncation in @toolify decorator."""

    def test_short_output_not_truncated(self):
        """Test that outputs below threshold are not truncated."""
        short_text = "This is a short output"
        result = _convert_tool_output(short_text)
        self.assertEqual(result, short_text)
        self.assertNotIn("truncated", result)

    def test_long_output_truncated_with_default_settings(self):
        """Test that long outputs are truncated with default settings (5000 char threshold)."""
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
        """Test that truncation preserves 2000 chars from start and end."""
        # Create text with identifiable start and end
        long_text = "START" + ("X" * 6000) + "END"
        result = _convert_tool_output(long_text)
        # Should contain start and end
        self.assertIn("START", result)
        self.assertIn("END", result)
        self.assertIn("truncated", result)

    def test_output_at_exact_threshold_not_truncated(self):
        """Test that output exactly at threshold (5000) is not truncated."""
        text = "C" * 5000
        result = _convert_tool_output(text)
        # Should NOT be truncated (not exceeding threshold)
        self.assertEqual(result, text)
        self.assertNotIn("truncated", result)

    def test_output_just_over_threshold_is_truncated(self):
        """Test that output just over threshold (5001) is truncated."""
        text = "D" * 5001
        result = _convert_tool_output(text)
        # Should be truncated
        self.assertIn("truncated", result)
        self.assertLess(len(result), len(text))

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
        # Create large dict that will serialize to long JSON (> 5000 chars)
        large_dict = {f"key_{i}": f"value_{i}" * 50 for i in range(100)}
        result = _convert_tool_output(large_dict)
        # Should be truncated
        self.assertIn("truncated", result)

    def test_list_output_truncation(self):
        """Test that list outputs are truncated correctly."""
        # Create large list (> 5000 chars when serialized)
        large_list = [f"item_{i}" * 10 for i in range(100)]
        result = _convert_tool_output(large_list)
        # Should be truncated
        self.assertIn("truncated", result)

    def test_toolify_decorator_with_truncation(self):
        """Test that @toolify decorator applies truncation to tool outputs."""

        @toolify()
        def long_output_tool() -> str:
            """A tool that returns a very long output."""
            return "E" * 6000

        result = long_output_tool()
        # Should be truncated
        self.assertIn("truncated", result)
        self.assertLess(len(result), 6000)

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
        long_text = "F" * 6000
        result = _convert_tool_output(long_text)
        # Check for specific truncation message
        expected_message = "(tool result truncated from middle to save you from context overload)"
        self.assertIn(expected_message, result)

    def test_truncation_with_multiline_output(self):
        """Test truncation works correctly with multiline outputs."""
        # Create multiline output (> 5000 chars)
        lines = [f"Line {i}: " + ("X" * 50) for i in range(100)]
        long_text = "\n".join(lines)
        result = _convert_tool_output(long_text)
        # Should be truncated
        self.assertIn("truncated", result)
        self.assertLess(len(result), len(long_text))

    def test_integer_output(self):
        """Test that integer outputs work correctly."""
        result = _convert_tool_output(42)
        self.assertEqual(result, "42")

    def test_float_output(self):
        """Test that float outputs work correctly."""
        result = _convert_tool_output(3.14159)
        self.assertEqual(result, "3.14159")

    def test_boolean_output(self):
        """Test that boolean outputs work correctly."""
        result = _convert_tool_output(True)
        self.assertEqual(result, "True")


class TestToolifyTruncationIntegration(unittest.TestCase):
    """Integration tests for truncation with various tool scenarios."""

    def test_file_reading_tool_simulation(self):
        """Test truncation with simulated file reading tool."""

        @toolify("Read file contents")
        def read_file(content: str) -> str:
            """Simulate reading a large file."""
            return content

        # Simulate large file content
        large_content = "Line\n" * 2000  # ~10000 chars
        result = read_file(large_content)
        # Should be truncated
        self.assertIn("truncated", result)

    def test_api_response_tool_simulation(self):
        """Test truncation with simulated API response tool."""

        @toolify("Fetch API data")
        def fetch_data() -> dict:
            """Simulate fetching large API response."""
            return {"data": [{"id": i, "value": "x" * 100} for i in range(100)]}

        result = fetch_data()
        # Should be truncated
        self.assertIn("truncated", result)

    def test_code_analysis_tool_simulation(self):
        """Test truncation with simulated code analysis tool."""

        @toolify("Analyze code")
        def analyze_code() -> str:
            """Simulate code analysis with long output."""
            return "\n".join([f"Function {i}: " + ("details " * 50) for i in range(100)])

        result = analyze_code()
        # Should be truncated
        self.assertIn("truncated", result)

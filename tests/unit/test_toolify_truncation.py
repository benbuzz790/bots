"""Tests for @toolify decorator auto-truncation functionality.
This module tests the automatic truncation feature in the @toolify decorator
that prevents context overload from pathological cases with extremely large outputs.
Tests cover:
- Normal-sized outputs (no truncation)
- Outputs exceeding threshold (truncation applied)
- Edge cases (empty strings, None, exact threshold)
- Different output types (strings, JSON, etc.)
"""
import unittest
import pytest
from bots.dev.decorators import _convert_tool_output, toolify
class TestToolifyTruncation(unittest.TestCase):
    """Test automatic truncation in @toolify decorator."""
    def test_short_output_not_truncated(self):
        """Test that outputs below threshold are not truncated."""
        short_text = "This is a short output"
        result = _convert_tool_output(short_text)
        self.assertEqual(result, short_text)
        self.assertNotIn("truncated", result)
    def test_normal_large_output_not_truncated(self):
        """Test that even large outputs (e.g., 50k chars) are not truncated."""
        # 50k characters - well below the 500k threshold
        large_text = "A" * 50000
        result = _convert_tool_output(large_text)
        # Should NOT be truncated
        self.assertEqual(result, large_text)
        self.assertNotIn("truncated", result)
    def test_very_large_output_not_truncated(self):
        """Test that very large outputs (e.g., 400k chars) are still not truncated."""
        # 400k characters - still below the 500k threshold
        very_large_text = "B" * 400000
        result = _convert_tool_output(very_large_text)
        # Should NOT be truncated
        self.assertEqual(result, very_large_text)
        self.assertNotIn("truncated", result)
    def test_pathological_output_truncated(self):
        """Test that pathological outputs (> 500k chars) are truncated."""
        # Create output longer than threshold (500k chars)
        pathological_text = "C" * 600000
        result = _convert_tool_output(pathological_text)
        # Should be truncated
        self.assertLess(len(result), len(pathological_text))
        self.assertIn("truncated from middle to save you from context overload", result)
        # Should preserve start and end (100k chars each)
        self.assertTrue(result.startswith("C" * 1000))  # Check first 1000 chars
        self.assertTrue(result.endswith("C" * 1000))  # Check last 1000 chars
    def test_truncation_preserves_start_and_end(self):
        """Test that truncation preserves 100k chars from start and end."""
        # Create text with identifiable start and end
        pathological_text = "START" + ("X" * 600000) + "END"
        result = _convert_tool_output(pathological_text)
        # Should contain start and end
        self.assertIn("START", result)
        self.assertIn("END", result)
        self.assertIn("truncated", result)
    def test_output_at_exact_threshold_not_truncated(self):
        """Test that output exactly at threshold (500k) is not truncated."""
        text = "D" * 500000
        result = _convert_tool_output(text)
        # Should NOT be truncated (not exceeding threshold)
        self.assertEqual(result, text)
        self.assertNotIn("truncated", result)
    def test_output_just_over_threshold_is_truncated(self):
        """Test that output just over threshold (500,001) is truncated."""
        text = "E" * 500001
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
        """Test that extremely large JSON outputs are truncated correctly."""
        # Create massive dict that will serialize to > 500k chars
        large_dict = {f"key_{i}": f"value_{i}" * 1000 for i in range(1000)}
        result = _convert_tool_output(large_dict)
        # Should be truncated
        self.assertIn("truncated", result)
    def test_toolify_decorator_with_truncation(self):
        """Test that @toolify decorator applies truncation to pathological outputs."""
        @toolify()
        def pathological_output_tool() -> str:
            """A tool that returns a pathologically large output."""
            return "F" * 600000
        result = pathological_output_tool()
        # Should be truncated
        self.assertIn("truncated", result)
        self.assertLess(len(result), 600000)
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
    def test_toolify_decorator_large_but_reasonable_output_unchanged(self):
        """Test that @toolify decorator doesn't affect large but reasonable outputs."""
        @toolify()
        def large_output_tool() -> str:
            """A tool that returns a large but reasonable output."""
            return "G" * 100000  # 100k chars - well below threshold
        result = large_output_tool()
        # Should NOT be truncated
        self.assertEqual(result, "G" * 100000)
        self.assertNotIn("truncated", result)
    def test_truncation_message_format(self):
        """Test that truncation message has correct format."""
        pathological_text = "H" * 600000
        result = _convert_tool_output(pathological_text)
        # Check for specific truncation message
        expected_message = "(tool result truncated from middle to save you from context overload)"
        self.assertIn(expected_message, result)
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
    def test_massive_file_reading_simulation(self):
        """Test truncation with simulated massive file reading."""
        @toolify("Read file contents")
        def read_file(content: str) -> str:
            """Simulate reading a massive file."""
            return content
        # Simulate massive file content (> 500k chars)
        massive_content = "Line\n" * 100000  # ~500k chars
        result = read_file(massive_content)
        # Should be truncated
        self.assertIn("truncated", result)
    def test_normal_file_reading_not_truncated(self):
        """Test that normal file reading is not affected."""
        @toolify("Read file contents")
        def read_file(content: str) -> str:
            """Simulate reading a normal file."""
            return content
        # Normal file content (10k chars)
        normal_content = "Line\n" * 2000
        result = read_file(normal_content)
        # Should NOT be truncated
        self.assertEqual(result, normal_content)
        self.assertNotIn("truncated", result)
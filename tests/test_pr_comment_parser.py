"""Tests for PR comment parser utility."""

import tempfile
import unittest
from unittest.mock import patch

from bots.dev.pr_comment_parser import (
    extract_coderabbit_prompts,
    is_outdated,
    parse_pr_comments,
    save_coderabbit_prompts,
)


class TestPRCommentParser(unittest.TestCase):
    """Test cases for PR comment parser."""

    def test_extract_coderabbit_prompts_valid(self):
        """Test extracting a valid CodeRabbit prompt."""
        comment_body = """
Some review comment here.

<summary>🤖 Prompt for AI Agents</summary>
```
In tests/test_save_load_anthropic.py around lines 1043-1044, the two print
statements use redundant f-strings with no interpolations which triggers Ruff
F541; remove the leading f prefix from both print calls.
```

More text after.
"""
        result = extract_coderabbit_prompts(comment_body)
        self.assertIsNotNone(result)
        self.assertIn("tests/test_save_load_anthropic.py", result)
        self.assertIn("F541", result)

    def test_extract_coderabbit_prompts_none(self):
        """Test extracting from comment without CodeRabbit prompt."""
        comment_body = "Just a regular comment without AI prompts."
        result = extract_coderabbit_prompts(comment_body)
        self.assertIsNone(result)

    def test_extract_coderabbit_prompts_multiline(self):
        """Test extracting multiline prompt."""
        comment_body = """
<summary>🤖 Prompt for AI Agents</summary>
```
Line 1 of prompt
Line 2 of prompt
Line 3 of prompt
```
"""
        result = extract_coderabbit_prompts(comment_body)
        self.assertIsNotNone(result)
        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)
        self.assertIn("Line 3", result)

    def test_is_outdated_field(self):
        """Test checking outdated status from field."""
        comment = {"outdated": True, "body": "Some comment"}
        self.assertTrue(is_outdated(comment))

        comment = {"outdated": False, "body": "Some comment"}
        self.assertFalse(is_outdated(comment))

    def test_is_outdated_markers(self):
        """Test checking outdated status from body markers."""
        comment = {"body": "This is [outdated] comment"}
        self.assertTrue(is_outdated(comment))

        comment = {"body": "This is ~~outdated~~ comment"}
        self.assertTrue(is_outdated(comment))

        comment = {"body": "This is a current comment"}
        self.assertFalse(is_outdated(comment))

    @patch("bots.dev.pr_comment_parser.get_pr_review_comments")
    @patch("bots.dev.pr_comment_parser.get_pr_comments")
    def test_parse_pr_comments_filter_coderabbit(self, mock_get_comments, mock_get_review_comments):
        """Test parsing with CodeRabbit filter."""
        mock_get_review_comments.return_value = []
        mock_get_comments.return_value = [
            {
                "author": {"login": "coderabbitai"},
                "body": """
<summary>🤖 Prompt for AI Agents</summary>
```
Test prompt
```
""",
                "createdAt": "2024-01-01T00:00:00Z",
                "url": "https://github.com/test/pr/1",
            },
            {
                "author": {"login": "human_user"},
                "body": "Regular comment",
                "createdAt": "2024-01-01T00:00:00Z",
                "url": "https://github.com/test/pr/2",
            },
        ]

        result = parse_pr_comments(123, "owner/repo", filter_coderabbit=True, include_review_comments=False)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["author"], "coderabbitai")
        self.assertIsNotNone(result[0]["ai_prompt"])

    @patch("bots.dev.pr_comment_parser.get_pr_review_comments")
    @patch("bots.dev.pr_comment_parser.get_pr_comments")
    def test_parse_pr_comments_exclude_outdated(self, mock_get_comments, mock_get_review_comments):
        """Test parsing with outdated exclusion."""
        mock_get_review_comments.return_value = []
        mock_get_comments.return_value = [
            {
                "author": {"login": "coderabbitai"},
                "body": """
<summary>🤖 Prompt for AI Agents</summary>
```
Current prompt
```
""",
                "outdated": False,
                "createdAt": "2024-01-01T00:00:00Z",
                "url": "https://github.com/test/pr/1",
            },
            {
                "author": {"login": "coderabbitai"},
                "body": """
<summary>🤖 Prompt for AI Agents</summary>
```
Outdated prompt
```
""",
                "outdated": True,
                "createdAt": "2024-01-01T00:00:00Z",
                "url": "https://github.com/test/pr/2",
            },
        ]

        result = parse_pr_comments(
            123, "owner/repo", filter_coderabbit=True, exclude_outdated=True, include_review_comments=False
        )
        self.assertEqual(len(result), 1)
        self.assertIn("Current prompt", result[0]["ai_prompt"])

    @patch("bots.dev.pr_comment_parser.get_pr_review_comments")
    @patch("bots.dev.pr_comment_parser.get_pr_comments")
    def test_save_coderabbit_prompts(self, mock_get_comments, mock_get_review_comments):
        """Test saving CodeRabbit prompts to file."""
        mock_get_comments.return_value = [
            {
                "author": {"login": "coderabbitai"},
                "body": """
<summary>🤖 Prompt for AI Agents</summary>
```
First prompt
```
""",
                "createdAt": "2024-01-01T00:00:00Z",
                "url": "https://github.com/test/pr/1",
            },
            {
                "author": {"login": "coderabbitai"},
                "body": """
<summary>🤖 Prompt for AI Agents</summary>
```
Second prompt
```
""",
                "createdAt": "2024-01-01T00:00:00Z",
                "url": "https://github.com/test/pr/2",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_file = f.name

        try:
            count = save_coderabbit_prompts(123, "owner/repo", temp_file)
            self.assertEqual(count, 2)

            with open(temp_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("First prompt", content)
                self.assertIn("Second prompt", content)
                self.assertIn("=== CodeRabbit Prompt #1 ===", content)
                self.assertIn("=== CodeRabbit Prompt #2 ===", content)
        finally:
            import os

            if os.path.exists(temp_file):
                os.remove(temp_file)


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest

from bots.tools.code_tools import view, view_dir


def create_temp_file(content):
    """Helper function to create a temporary file with given content."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestCodeTools(unittest.TestCase):
    def setUp(self):
        from tests.conftest import get_unique_filename

        self.temp_dir = os.path.join(tempfile.gettempdir(), get_unique_filename("benbuzz790_private_tests_temp"))
        os.makedirs(self.temp_dir, exist_ok=True)
        self.temp_file = os.path.join(self.temp_dir, get_unique_filename("test_file", "txt"))
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n" "Line 6\nLine 7\nLine 8\nLine 9\nLine 10\n"
        with open(self.temp_file, "w", encoding="utf-8") as f:
            f.write(content)

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_view_full_file(self):
        """Test viewing entire file (default behavior)."""
        result = view(self.temp_file)
        expected = "1:Line 1\n2:Line 2\n3:Line 3\n4:Line 4\n5:Line 5\n" "6:Line 6\n7:Line 7\n8:Line 8\n9:Line 9\n10:Line 10"
        self.assertEqual(result, expected)

    def test_view_with_start_line(self):
        """Test viewing file starting from a specific line."""
        result = view(self.temp_file, start_line=3)
        expected = "3:Line 3\n4:Line 4\n5:Line 5\n6:Line 6\n" "7:Line 7\n8:Line 8\n9:Line 9\n10:Line 10"
        self.assertEqual(result, expected)

    def test_view_with_end_line(self):
        """Test viewing file up to a specific line."""
        result = view(self.temp_file, end_line=5)
        expected = "1:Line 1\n2:Line 2\n3:Line 3\n4:Line 4\n5:Line 5"
        self.assertEqual(result, expected)

    def test_view_with_start_and_end_line(self):
        """Test viewing file with both start and end line specified."""
        result = view(self.temp_file, start_line=3, end_line=7)
        expected = "3:Line 3\n4:Line 4\n5:Line 5\n6:Line 6\n7:Line 7"
        self.assertEqual(result, expected)

    def test_view_with_string_match(self):
        """Test viewing lines around a string match."""
        # Create a file with some specific content for string matching
        content = "First line\nSecond line\nImportant function here\n" "Fourth line\nFifth line\nSixth line\n"
        test_file = create_temp_file(content)
        try:
            result = view(test_file, around_str_match="Important function", dist_from_match=1)
            # Should show line 2, 3, and 4 (1 line before and after match)
            expected = "2:Second line\n3:Important function here\n4:Fourth line"
            self.assertEqual(result, expected)
        finally:
            os.remove(test_file)

    def test_view_with_string_match_custom_distance(self):
        """Test viewing lines around a string match with custom distance."""
        content = "Line 1\nLine 2\nLine 3\nTarget line here\n" "Line 5\nLine 6\nLine 7\nLine 8\n"
        test_file = create_temp_file(content)
        try:
            result = view(test_file, around_str_match="Target line", dist_from_match=2)
            # Should show lines 2-6 (2 lines before and after the match)
            expected = "2:Line 2\n3:Line 3\n4:Target line here\n" "5:Line 5\n6:Line 6"
            self.assertEqual(result, expected)
        finally:
            os.remove(test_file)

    def test_view_with_multiple_string_matches(self):
        """Test viewing lines around multiple string matches."""
        content = "Line 1\nmatch here\nLine 3\nLine 4\nLine 5\n" "Another match here\nLine 7\nLine 8\n"
        test_file = create_temp_file(content)
        try:
            result = view(test_file, around_str_match="match here", dist_from_match=1)
            # Should show context around both matches with gaps indicated
            self.assertIn("1:Line 1", result)
            self.assertIn("2:match here", result)
            self.assertIn("3:Line 3", result)
            self.assertIn("5:Line 5", result)
            self.assertIn("6:Another match here", result)
            self.assertIn("7:Line 7", result)
            self.assertIn("...", result)  # Gap separator should be present
        finally:
            os.remove(test_file)

    def test_view_string_match_no_results(self):
        """Test string match with no matching lines."""
        result = view(self.temp_file, around_str_match="Nonexistent text")
        expected = "No matches found for 'Nonexistent text'"
        self.assertEqual(result, expected)

    def test_view_invalid_start_line(self):
        """Test error handling for invalid start_line."""
        result = view(self.temp_file, start_line=100)
        self.assertIn("Error: start_line (100) exceeds file length", result)

    def test_view_boundary_conditions(self):
        """Test boundary conditions for line ranges."""
        # Test start_line = 1, end_line = 1 (single line)
        result = view(self.temp_file, start_line=1, end_line=1)
        expected = "1:Line 1"
        self.assertEqual(result, expected)
        # Test last line only
        result = view(self.temp_file, start_line=10, end_line=10)
        expected = "10:Line 10"
        self.assertEqual(result, expected)

    def test_view_string_match_at_file_boundaries(self):
        """Test string matching at the beginning and end of file."""
        content = "First match\nMiddle line\nLast match\n"
        test_file = create_temp_file(content)
        try:
            # Test match at beginning
            result = view(test_file, around_str_match="First match", dist_from_match=1)
            expected = "1:First match\n2:Middle line"
            self.assertEqual(result, expected)
            # Test match at end
            result = view(test_file, around_str_match="Last match", dist_from_match=1)
            expected = "2:Middle line\n3:Last match"
            self.assertEqual(result, expected)
        finally:
            os.remove(test_file)


if __name__ == "__main__":
    unittest.main()


class TestViewDir(unittest.TestCase):
    def setUp(self):

        self.temp_dir = os.path.join("benbuzz790", "private_tests", "view_dir_test")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.files = {
            "test1.py": 'print("test1")',
            "test2.txt": "test2 content",
            "test3.md": "# test3 header",
            "test4.json": '{"test": 4}',
            "test5.pyc": "compiled python",
            "subdir/test6.py": 'print("test6")',
        }
        for path, content in self.files.items():
            full_path = os.path.join(self.temp_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_specific_extensions(self):
        """Test view_dir with specific file extensions"""
        result = view_dir(self.temp_dir, target_extensions="['py', 'txt']")
        self.assertIn("test1.py", result)
        self.assertIn("test2.txt", result)
        self.assertNotIn("test3.md", result)
        self.assertNotIn("test4.json", result)

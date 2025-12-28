import os
import tempfile
import unittest

from bots.tools.python_edit import python_edit


class TestNonPyFileWrite(unittest.TestCase):
    """Test suite for python_edit handling of non-.py files."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_new_txt_file(self):
        """Test that python_edit writes a new .txt file with a warning."""
        file_path = "test_file.txt"
        content = "This is a text file\nWith multiple lines\n"

        result = python_edit(file_path, content)

        # Check that the file was created
        self.assertTrue(os.path.exists(file_path))

        # Check that the content was written correctly
        with open(file_path, "r", encoding="utf-8") as f:
            actual_content = f.read()
        self.assertEqual(actual_content, content)

        # Check that the result contains a warning (but don't check exact message)
        self.assertIn("WARNING", result)
        self.assertIn(file_path, result)

    def test_write_new_md_file(self):
        """Test that python_edit writes a new .md file with a warning."""
        file_path = "README.md"
        content = "# Test README\n\nThis is a markdown file.\n"

        result = python_edit(file_path, content)

        # Check that the file was created
        self.assertTrue(os.path.exists(file_path))

        # Check that the content was written correctly
        with open(file_path, "r", encoding="utf-8") as f:
            actual_content = f.read()
        self.assertEqual(actual_content, content)

        # Check that the result indicates success
        self.assertIn("WARNING", result)

    def test_write_new_json_file(self):
        """Test that python_edit writes a new .json file with a warning."""
        file_path = "config.json"
        content = '{\n  "key": "value",\n  "number": 42\n}\n'

        result = python_edit(file_path, content)

        # Check that the file was created
        self.assertTrue(os.path.exists(file_path))

        # Check that the content was written correctly
        with open(file_path, "r", encoding="utf-8") as f:
            actual_content = f.read()
        self.assertEqual(actual_content, content)

        # Check that the result contains a warning
        self.assertIn("WARNING", result)

    def test_write_new_file_in_subdirectory(self):
        """Test that python_edit creates subdirectories when writing non-.py files."""
        file_path = "subdir/nested/test.txt"
        content = "Nested file content\n"

        result = python_edit(file_path, content)

        # Check that the directories and file were created
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(os.path.isdir("subdir"))
        self.assertTrue(os.path.isdir("subdir/nested"))

        # Check that the content was written correctly
        with open(file_path, "r", encoding="utf-8") as f:
            actual_content = f.read()
        self.assertEqual(actual_content, content)

        # Check that the result contains a warning
        self.assertIn("WARNING", result)

    def test_existing_non_py_file_returns_error(self):
        """Test that python_edit returns an error for existing non-.py files."""
        file_path = "existing.txt"

        # Create the file first
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Original content\n")

        # Try to edit it
        result = python_edit(file_path, "New content\n")

        # Should return an error
        self.assertIn("Tool Failed", result)
        self.assertIn("must end with .py", result)

        # Original content should be unchanged
        with open(file_path, "r", encoding="utf-8") as f:
            actual_content = f.read()
        self.assertEqual(actual_content, "Original content\n")

    def test_non_py_file_with_scope_returns_error(self):
        """Test that python_edit returns an error when trying to use scope with non-.py files."""
        file_path = "test.txt::SomeScope"
        content = "Content\n"

        result = python_edit(file_path, content)

        # Should return an error
        self.assertIn("Tool Failed", result)
        self.assertIn("must end with .py", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

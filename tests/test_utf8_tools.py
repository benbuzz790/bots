import os
import sys
import unittest
from bots.tools import utf8_tools

class DetailedTestCase(unittest.TestCase):
    def assertEqualDetailed(self, first, second, msg=None):
        try:
            self.assertEqual(first, second, msg)
        except AssertionError as e:
            raise AssertionError(f"\nAssertion Error: {str(e)}\n")

    def assertFileContentEqual(self, file_path, expected_content, msg=None):
        with open(file_path, 'r') as f:
            actual_content = f.read()
        self.assertEqualDetailed(actual_content, expected_content, msg)

class TestUTF8Tools(DetailedTestCase):

    def setUp(self):
        self.test_file = 'test_file.txt'
        with open(self.test_file, 'w') as f:
            f.write('# Original content\n')

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_write(self):
        new_content = '# New content'
        utf8_tools.overwrite(self.test_file, new_content)
        self.assertFileContentEqual(self.test_file, new_content, 'Write failed')

    def test_replace(self):
        initial_content = "old_string = 'value'"
        utf8_tools.overwrite(self.test_file, initial_content)
        utf8_tools.replace(self.test_file, 'old_string', 'new_string')
        self.assertFileContentEqual(self.test_file, "new_string = 'value'", 'Replace failed')

    def test_append(self):
        initial_content = "# Initial content\n"
        append_content = "# Appended content\n"
        utf8_tools.overwrite(self.test_file, initial_content)
        utf8_tools.append(self.test_file, append_content)
        self.assertFileContentEqual(self.test_file, initial_content + append_content, 'Append failed')

    def test_prepend(self):
        initial_content = "# Initial content\n"
        prepend_content = "# Prepended content\n"
        utf8_tools.overwrite(self.test_file, initial_content)
        utf8_tools.prepend(self.test_file, prepend_content)
        self.assertFileContentEqual(self.test_file, prepend_content + initial_content, 'Prepend failed')

    def test_read_file(self):
        content = "Test content"
        with open(self.test_file, 'w') as f:
            f.write(content)
        
        read_content = utf8_tools.read_file(self.test_file)
        self.assertEqual(read_content, content)

    def test_delete_match(self):
        initial_content = """
# Keep this line
# Delete this line
# Keep this line too
"""
        expected_content = """
# Keep this line
# Keep this line too
"""
        utf8_tools.overwrite(self.test_file, initial_content)
        utf8_tools.delete_match(self.test_file, 'Delete this line')
        self.assertFileContentEqual(self.test_file, expected_content, 'Delete match failed')

if __name__ == '__main__':
    unittest.main()
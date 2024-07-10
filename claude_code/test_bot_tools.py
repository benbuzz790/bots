
from bot_tools import rewrite, insert_after, paste_over, append_to_file, prepend_to_file
import unittest
import os

class TestBotTools(unittest.TestCase):
    def setUp(self):
        self.test_file = 'claude_code/test_bot_tools_file.txt'

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_rewrite(self):
        content = "Hello, World!"
        rewrite(self.test_file, content)
        with open(self.test_file, 'r') as file:
            self.assertEqual(file.read(), content)

    def test_insert_after(self):
        initial_content = "Line 1\nLine 2\nLine 3"
        rewrite(self.test_file, initial_content)
        insert_after(self.test_file, "Line 2", "Inserted Line")
        with open(self.test_file, 'r') as file:
            self.assertEqual(file.read(), "Line 1\nLine 2\nInserted Line\nLine 3")

    def test_paste_over(self):
        initial_content = "Hello, World!"
        rewrite(self.test_file, initial_content)
        paste_over(self.test_file, "World", "Universe")
        with open(self.test_file, 'r') as file:
            self.assertEqual(file.read(), "Hello, Universe!")

    def test_append_to_file(self):
        initial_content = "Initial content\n"
        rewrite(self.test_file, initial_content)
        append_to_file(self.test_file, "Appended content")
        with open(self.test_file, 'r') as file:
            self.assertEqual(file.read(), initial_content + "Appended content")

    def test_prepend_to_file(self):
        initial_content = "Initial content\n"
        rewrite(self.test_file, initial_content)
        prepend_to_file(self.test_file, "Prepended content\n")
        with open(self.test_file, 'r') as file:
            self.assertEqual(file.read(), "Prepended content\n" + initial_content)

if __name__ == '__main__':
    unittest.main()

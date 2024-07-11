
import importlib
import bot_tools
importlib.reload(bot_tools)
import unittest
import os

class TestBotTools(unittest.TestCase):
    def setUp(self):
        self.test_file = 'test_file.txt'
        with open(self.test_file, 'w') as f:
            f.write("Original content\n")

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_rewrite(self):
        new_content = "New content"
        bot_tools.rewrite(self.test_file, new_content)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), new_content)

    def test_insert_after(self):
        bot_tools.insert_after(self.test_file, "Original", " inserted")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Original inserted content\n")

    def test_replace(self):
        bot_tools.replace(self.test_file, "Original", "Replaced")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Replaced content\n")

    def test_append(self):
        bot_tools.append(self.test_file, "Appended content")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Original content\nAppended content")

    def test_prepend(self):
        bot_tools.prepend(self.test_file, "Prepended content\n")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Prepended content\nOriginal content\n")

    def test_delete_match(self):
        with open(self.test_file, 'w') as f:
            f.write("Keep this\nDelete me\nKeep this too\nAlso DELETE\n")
        bot_tools.delete_match(self.test_file, "Delete")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Keep this\nKeep this too\n")

    def test_overwrite_function(self):
        with open(self.test_file, 'w') as f:
            f.write("def old_function():\n    pass\n\nother code")
        new_function = "def old_function():\n    print('New implementation')\n"
        bot_tools.overwrite_function(self.test_file, "old_function", new_function)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), new_function.rstrip() + "\nother code")

    def test_overwrite_class(self):
        with open(self.test_file, 'w') as f:
            f.write("class OldClass:\n    pass\n\nother code")
        new_class = "class OldClass:\n    def new_method(self):\n        pass\n"
        bot_tools.overwrite_class(self.test_file, "OldClass", new_class)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), new_class.rstrip() + "\nother code")

if __name__ == '__main__':
    unittest.main(argv=[''], exit=False)

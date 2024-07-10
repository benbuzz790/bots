
import unittest
import os
import sys
import shutil
import time
from parameterized import parameterized

# Add the parent directory to sys.path to import bot_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bot_tools

class TestBotTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = 'test_bot_tools_dir'
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_file = os.path.join(self.test_dir, 'test_file.txt')
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_rewrite(self):
        """Test the rewrite function to ensure it correctly overwrites file content."""
        content = "Test content"
        bot_tools.rewrite(self.test_file, content)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), content)
    
    @parameterized.expand([
        ("middle", "Line 1\nLine 2\nLine 3", "Line 2", "New Line", "Line 1\nLine 2\nNew Line\nLine 3"),
        ("beginning", "Line 1\nLine 2\nLine 3", "Line 1", "New Line", "Line 1\nNew Line\nLine 2\nLine 3"),
        ("end", "Line 1\nLine 2\nLine 3", "Line 3", "New Line", "Line 1\nLine 2\nLine 3\nNew Line"),
    ])
    def test_insert_after(self, name, initial_content, target, insert_content, expected):
        """Test the insert_after function with various scenarios."""
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.insert_after(self.test_file, target, insert_content)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), expected)
    
    @parameterized.expand([
        ("middle", "This is a test sentence.", "test", "sample", "This is a sample sentence."),
        ("beginning", "test at the start", "test", "Check", "Check at the start"),
        ("end", "End with a test", "test", "trial", "End with a trial"),
    ])
    def test_paste_over(self, name, initial_content, target, paste_content, expected):
        """Test the paste_over function with various scenarios."""
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.paste_over(self.test_file, target, paste_content)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), expected)
    
    def test_find_function_definition(self):
        """Test the find_function_definition function to ensure it correctly locates a function."""
        content = "def test_function():\n    pass\n\ndef another_function():\n    pass"
        bot_tools.rewrite(self.test_file, content)
        line_number, definition = bot_tools.find_function_definition(self.test_file, "test_function")
        self.assertEqual(line_number, 1)
        self.assertEqual(definition, "def test_function():\n    pass")
    
    def test_replace_function_definition(self):
        """Test the replace_function_definition function to ensure it correctly replaces a function."""
        content = "def test_function():\n    pass\n\ndef another_function():\n    pass"
        bot_tools.rewrite(self.test_file, content)
        new_definition = "def test_function():\n    return 'New implementation'"
        bot_tools.replace_function_definition(self.test_file, "test_function", new_definition)
        with open(self.test_file, 'r') as f:
            self.assertIn(new_definition, f.read())
    
    def test_append_to_file(self):
        """Test the append_to_file function to ensure it correctly appends content."""
        initial_content = "Initial content\n"
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.append_to_file(self.test_file, "Appended content")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), initial_content + "Appended content")
    
    def test_prepend_to_file(self):
        """Test the prepend_to_file function to ensure it correctly prepends content."""
        initial_content = "Initial content\n"
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.prepend_to_file(self.test_file, "Prepended content\n")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Prepended content\n" + initial_content)
    
    def test_create_directory(self):
        """Test the create_directory function to ensure it creates a directory."""
        new_dir = os.path.join(self.test_dir, 'new_directory')
        bot_tools.create_directory(new_dir)
        self.assertTrue(os.path.exists(new_dir))
    
    
    def test_error_handling(self):
        """Test error handling for various functions."""
        non_existent_file = os.path.join(self.test_dir, 'non_existent.txt')
        
        with self.assertRaises(FileNotFoundError):
            bot_tools.insert_after(non_existent_file, "target", "content")
        
        with self.assertRaises(FileNotFoundError):
            bot_tools.paste_over(non_existent_file, "target", "content")
        
        # Test for a function that doesn't exist
        line_number, definition = bot_tools.find_function_definition(self.test_file, "non_existent_function")
        self.assertIsNone(line_number)
        self.assertIsNone(definition)
        definition = bot_tools.find_function_definition(self.test_file, "non_existent_function")
        self.assertIsNone(line_number)
        self.assertIsNone(definition)
    
    def test_edge_cases(self):
        """Test edge cases for various functions."""
        # Empty file
        bot_tools.rewrite(self.test_file, "")
        bot_tools.insert_after(self.test_file, "non-existent", "content")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "")
        
        # Very long content
        long_content = "a" * 1000000
        bot_tools.rewrite(self.test_file, long_content)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), long_content)
    
    def test_performance(self):
        """Simple performance test for rewrite function with a large file."""
        large_content = "Large content\n" * 100000
        start_time = time.time()
        bot_tools.rewrite(self.test_file, large_content)
        end_time = time.time()
        self.assertLess(end_time - start_time, 5, "Rewriting large file took too long")

if __name__ == '__main__':
    unittest.main()

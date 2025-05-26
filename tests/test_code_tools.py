import unittest
import textwrap
import os
import tempfile
from bots.tools.code_tools import read_file, diff_edit, view_dir

def create_temp_file(content):
    """Helper function to create a temporary file with given content."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

class TestCodeTools(unittest.TestCase):

    def setUp(self):
        self.temp_dir = os.path.join('benbuzz790', 'private_tests', 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.temp_file = os.path.join(self.temp_dir, 'test_file.txt')
        content = 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n'
        with open(self.temp_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def tearDown(self):
        os.remove(self.temp_file)
        os.rmdir(self.temp_dir)

    def test_view(self):
        result = read_file(self.temp_file)
        expected = '1:Line 1\n2:Line 2\n3:Line 3\n4:Line 4\n5:Line 5'
        self.assertEqual(result, expected)

    def test_basic_replacement(self):
        """Test basic single-line replacement."""
        initial_content = textwrap.dedent('\n        def hello():\n            print("Hello")\n            return True\n    ').lstrip()
        diff_spec = textwrap.dedent('\n        -    print("Hello")\n        +    print("Hello, World!")\n    ').lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent('\n            def hello():\n                print("Hello, World!")\n                return True\n        ').lstrip()
            self.assertEqual(new_content, expected)
        finally:
            os.remove(file_path)

    def test_multi_line_replacement(self):
        """Test replacing multiple consecutive lines."""
        initial_content = textwrap.dedent('\n        def complex_function():\n            x = 1\n            y = 2\n            z = 3\n            return x + y + z\n    ').lstrip()
        diff_spec = textwrap.dedent('\n        -    x = 1\n        -    y = 2\n        -    z = 3\n        +    total = 6\n    ').lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent('\n            def complex_function():\n                total = 6\n                return x + y + z\n        ').lstrip()
            self.assertEqual(new_content, expected)
        finally:
            os.remove(file_path)

    def test_indentation_preservation(self):
        """Test that indentation is properly preserved."""
        initial_content = textwrap.dedent('\n        class MyClass:\n            def method(self):\n                if True:\n                    print("old")\n                    return None\n    ').lstrip()
        diff_spec = textwrap.dedent('\n        -            print("old")\n        +            print("new")\n    ').lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent('\n            class MyClass:\n                def method(self):\n                    if True:\n                        print("new")\n                        return None\n        ').lstrip()
            self.assertEqual(new_content, expected)
        finally:
            os.remove(file_path)

    def test_multiple_changes(self):
        """Test multiple separate changes in the same file."""
        initial_content = textwrap.dedent('\n        def first():\n            return 1\n\n        def second():\n            return 2\n\n        def third():\n            return 3\n    ').lstrip()
        diff_spec = textwrap.dedent('\n        -    return 1\n        +    return "one"\n\n        -    return 2\n        +    return "two"\n    ').lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent('\n            def first():\n                return "one"\n\n            def second():\n                return "two"\n\n            def third():\n                return 3\n        ').lstrip()
            self.assertEqual(new_content, expected)
        finally:
            os.remove(file_path)

    def test_no_match(self):
        """Test handling of changes that don't match the file content."""
        initial_content = textwrap.dedent('\n        def hello():\n            print("Hello")\n    ').lstrip()
        diff_spec = textwrap.dedent('\n        -    print("Nonexistent")\n        +    print("New")\n    ').lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Failed to apply', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            self.assertEqual(new_content, initial_content)
        finally:
            os.remove(file_path)

    def test_empty_diff(self):
        """Test handling of empty diff specification."""
        initial_content = "print('test')\n"
        diff_spec = ''
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertTrue('No changes' in result or 'Failed' in result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            self.assertEqual(new_content, initial_content)
        finally:
            os.remove(file_path)

    def test_create_new_file(self):
        """Test that diff_edit creates a new file if it doesn't exist."""
        new_file = os.path.join(self.temp_dir, 'new_file.py')
        if os.path.exists(new_file):
            os.remove(new_file)
        diff_spec = textwrap.dedent('\n        +def hello():\n        +    print("Hello, World!")\n    ').lstrip()
        try:
            result = diff_edit(new_file, diff_spec)
            self.assertIn('Successfully', result)
            self.assertTrue(os.path.exists(new_file))
            with open(new_file, 'r', encoding='utf-8') as f:
                content = f.read()
            expected = textwrap.dedent('\n            def hello():\n                print("Hello, World!")\n        ').lstrip()
            self.assertEqual(content, expected)
        finally:
            if os.path.exists(new_file):
                os.remove(new_file)

    def test_create_new_file_empty_diff(self):
        """Test that diff_edit creates an empty file when given empty diff spec."""
        new_file = os.path.join(self.temp_dir, 'empty_file.py')
        if os.path.exists(new_file):
            os.remove(new_file)
        result = diff_edit(new_file, '')
        try:
            self.assertIn('No changes', result)
            self.assertTrue(os.path.exists(new_file))
            with open(new_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertEqual(content, '')
        finally:
            if os.path.exists(new_file):
                os.remove(new_file)

    def test_create_new_file_multiple_changes(self):
        """Test that diff_edit can create a new file with multiple changes."""
        new_file = os.path.join(self.temp_dir, 'multi_change_file.py')
        if os.path.exists(new_file):
            os.remove(new_file)
        diff_spec = textwrap.dedent('\n            +def add(a, b):\n            +    return a + b\n\n            +def subtract(a, b):\n            +    return a - b\n            ')
        try:
            result = diff_edit(new_file, diff_spec)
            self.assertIn('Successfully', result)
            self.assertTrue(os.path.exists(new_file))
            with open(new_file, 'r', encoding='utf-8') as f:
                content = f.read()
            expected = textwrap.dedent('\n            def add(a, b):\n                return a + b\n            def subtract(a, b):\n                return a - b\n        ').lstrip()
            self.assertEqual(content, expected)
        finally:
            if os.path.exists(new_file):
                os.remove(new_file)
if __name__ == '__main__':
    unittest.main()

class TestViewDir(unittest.TestCase):

    def setUp(self):
        self.temp_dir = os.path.join('benbuzz790', 'private_tests', 'view_dir_test')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.files = {'test1.py': 'print("test1")', 'test2.txt': 'test2 content', 'test3.md': '# test3 header', 'test4.json': '{"test": 4}', 'test5.pyc': 'compiled python', 'subdir/test6.py': 'print("test6")'}
        for path, content in self.files.items():
            full_path = os.path.join(self.temp_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_specific_extensions(self):
        """Test view_dir with specific file extensions"""
        result = view_dir(self.temp_dir, target_extensions="['py', 'txt']")
        self.assertIn('test1.py', result)
        self.assertIn('test2.txt', result)
        self.assertNotIn('test3.md', result)
        self.assertNotIn('test4.json', result)

    def test_wildcard_all(self):
        """Test view_dir with wildcard '*' to show all files"""
        result = view_dir(self.temp_dir, target_extensions="['*']")
        print(f"\nDirectory contents:\n{result}")  # Debug output
        for filename in ['test1.py', 'test2.txt', 'test3.md', 'test4.json', 'test5.pyc']:
            self.assertIn(filename, result)

    def test_wildcard_pattern(self):
        """Test view_dir with wildcard pattern '*.py'"""
        result = view_dir(self.temp_dir, target_extensions="['*.py']")
        self.assertIn('test1.py', result)
        self.assertIn('test6.py', result)
        self.assertNotIn('test2.txt', result)
        self.assertNotIn('test5.pyc', result)

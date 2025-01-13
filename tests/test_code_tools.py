import unittest
import textwrap
import os
import tempfile
from bots.tools.code_tools import view, diff_edit


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
        result = view(self.temp_file)
        expected = '1: Line 1\n2: Line 2\n3: Line 3\n4: Line 4\n5: Line 5'
        self.assertEqual(result, expected)

    def test_basic_replacement(self):
        """Test basic single-line replacement."""
        initial_content = textwrap.dedent(
            """
        def hello():
            print("Hello")
            return True
    """
            ).lstrip()
        diff_spec = textwrap.dedent(
            """
        -    print("Hello")
        +    print("Hello, World!")
    """
            ).lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent(
                """
            def hello():
                print("Hello, World!")
                return True
        """
                ).lstrip()
            self.assertEqual(new_content, expected)
        finally:
            os.remove(file_path)

    def test_multi_line_replacement(self):
        """Test replacing multiple consecutive lines."""
        initial_content = textwrap.dedent(
            """
        def complex_function():
            x = 1
            y = 2
            z = 3
            return x + y + z
    """
            ).lstrip()
        diff_spec = textwrap.dedent(
            """
        -    x = 1
        -    y = 2
        -    z = 3
        +    total = 6
    """
            ).lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent(
                """
            def complex_function():
                total = 6
                return x + y + z
        """
                ).lstrip()
            self.assertEqual(new_content, expected)
        finally:
            os.remove(file_path)

    def test_indentation_preservation(self):
        """Test that indentation is properly preserved."""
        initial_content = textwrap.dedent(
            """
        class MyClass:
            def method(self):
                if True:
                    print("old")
                    return None
    """
            ).lstrip()
        diff_spec = textwrap.dedent(
            """
        -            print("old")
        +            print("new")
    """
            ).lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent(
                """
            class MyClass:
                def method(self):
                    if True:
                        print("new")
                        return None
        """
                ).lstrip()
            self.assertEqual(new_content, expected)
        finally:
            os.remove(file_path)

    def test_multiple_changes(self):
        """Test multiple separate changes in the same file."""
        initial_content = textwrap.dedent(
            """
        def first():
            return 1

        def second():
            return 2

        def third():
            return 3
    """
            ).lstrip()
        diff_spec = textwrap.dedent(
            """
        -    return 1
        +    return "one"

        -    return 2
        +    return "two"
    """
            ).lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent(
                """
            def first():
                return "one"

            def second():
                return "two"

            def third():
                return 3
        """
                ).lstrip()
            self.assertEqual(new_content, expected)
        finally:
            os.remove(file_path)

    def test_no_match(self):
        """Test handling of changes that don't match the file content."""
        initial_content = textwrap.dedent(
            """
        def hello():
            print("Hello")
    """
            ).lstrip()
        diff_spec = textwrap.dedent(
            """
        -    print("Nonexistent")
        +    print("New")
    """
            ).lstrip()
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Failed to apply', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            self.assertEqual(new_content, initial_content)
        finally:
            os.remove(file_path)

    def test_line_number_insertion(self):
        """Test inserting content at a specific line number."""
        initial_content = textwrap.dedent("""
            def test_function():
                x = 1
                z = 3
                return x + z
        """).lstrip()
        
        diff_spec = textwrap.dedent("""
            -2
            +    y = 2
        """).lstrip()
        
        file_path = create_temp_file(initial_content)
        try:
            result = diff_edit(file_path, diff_spec)
            self.assertIn('Successfully', result)
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            expected = textwrap.dedent("""
                def test_function():
                    x = 1
                    y = 2
                    z = 3
                    return x + z
            """).lstrip()
            self.assertEqual(new_content, expected)
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


if __name__ == '__main__':
    unittest.main()

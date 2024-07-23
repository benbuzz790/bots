
import unittest
import os
import sys
import traceback
import tempfile
import shutil
#import concurrent.futures
import time
import csv
import json
import platform
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.auto_terminal as auto_terminal

class DetailedTestCase(unittest.TestCase):
    def assertEqualWithDetails(self, first, second, msg=None):
        try:
            self.assertEqual(first, second, msg)
        except AssertionError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            frame = exc_traceback.tb_frame.f_back
            
            if frame:
                local_vars = frame.f_locals.copy()
                local_vars.pop('self', None)
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "\nLocal variables:\n"
                for key, value in local_vars.items():
                    error_message += f"{key} = {repr(value)}\n"
                error_message += "\nTraceback:\n"
                error_message += ''.join(traceback.format_tb(exc_traceback))
            else:
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "Unable to retrieve local variables.\n"
                error_message += "\nTraceback:\n"
                error_message += ''.join(traceback.format_tb(exc_traceback))
            
            raise AssertionError(error_message)

class TestCodey(DetailedTestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(os.getcwd(), 'tests')
        cls.test_file = os.path.join(cls.test_dir, "test_file.py")

    def setUp(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    @patch('builtins.input')
    def test_file_creation(self, mock_input):
        mock_input.side_effect = [
            f"Create a file named {self.test_file} with content 'Test content'",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        self.assertEqualWithDetails(os.path.exists(self.test_file), True, "File was not created")
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails(content.strip(), "Test content", "File content does not match")

    @patch('builtins.input')
    def test_file_read(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write("Test content for reading")
        mock_input.side_effect = [
            f"Read and return the content of the file {self.test_file}",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        self.assertEqualWithDetails("Test content for reading" in output, True, "File content not read correctly")

    @patch('builtins.input')
    def test_file_update(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write("Original content")
        mock_input.side_effect = [
            f"Update the content of {self.test_file} to 'Updated content'",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails(content.strip(), "Updated content", "File content not updated correctly")

    @patch('builtins.input')
    def test_file_delete(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write("Content to be deleted")
        mock_input.side_effect = [
            f"Delete the file {self.test_file}",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        self.assertEqualWithDetails(os.path.exists(self.test_file), False, "File was not deleted")

    @patch('builtins.input')
    def test_file_size(self, mock_input):
        content = "Test content" * 1000
        with open(self.test_file, 'w') as file:
            file.write(content)
        mock_input.side_effect = [
            f"Get the size of {self.test_file} in bytes",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        self.assertEqualWithDetails(str(len(content)) in output, True, "File size in bytes not found")

    @patch('builtins.input')
    def test_file_modification_time(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write("Test content")
        current_time = time.time()
        mock_input.side_effect = [
            f"Get the modification time of {self.test_file}",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        self.assertEqualWithDetails("modification time" in output.lower(), True, "File modification time retrieval failed")

    ''' Bad test. Success critiera not reliable
    # @patch('builtins.input')
    # def test_file_comparison(self, mock_input):
    #     file1 = os.path.join(self.test_dir, "file1.txt")
    #     file2 = os.path.join(self.test_dir, "file2.txt")
    #     with open(file1, 'w') as f:
    #         f.write("Test content")
    #     with open(file2, 'w') as f:
    #         f.write("Test content")
    #     mock_input.side_effect = [
    #         f"Compare the contents of {file1} and {file2}",
    #         '/exit'
    #     ]

    #     with StringIO() as buf, redirect_stdout(buf):
    #         with self.assertRaises(SystemExit):
    #             auto_terminal.main()
    #         output = buf.getvalue()

    #     self.assertEqualWithDetails(any(word in output.lower() for word in ["identical", "same", "equal"]), True, "File comparison failed")
    '''
    
    """ Not yet supported (i.e. i don't know what I'm doing)
    @patch('builtins.input')
    def test_concurrent_file_operations(self, mock_input):
        def write_file(content):
            mock_input.side_effect = [
                f"Append '{content}' to {self.test_file}",
                '/exit'
            ]
            with StringIO() as buf, redirect_stdout(buf):
                with self.assertRaises(SystemExit):
                    auto_terminal.main()
                return buf.getvalue()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_file, f"Content {i}") for i in range(5)]
            execution_results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqualWithDetails(all("appended" in result.lower() for result in execution_results), True, "Concurrent write operations failed")
        
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails(len(content.split("Content")) > 1, True, "Concurrent file operations failed")
    """

    """ Bad test. Success Criteria not reliable
    # @patch('builtins.input')
    # def test_error_handling_nonexistent_file(self, mock_input):
    #     nonexistent_file = os.path.join(self.test_dir, "nonexistent.txt")
    #     mock_input.side_effect = [
    #         f"Read the contents of {nonexistent_file}",
    #         '/exit'
    #     ]

    #     with StringIO() as buf, redirect_stdout(buf):
    #         with self.assertRaises(SystemExit):
    #             auto_terminal.main()
    #         output = buf.getvalue()

    #     self.assertEqualWithDetails(any(phrase in output.lower() for phrase in ["not found", "does not exist", "unable to read"]), True, "Error handling for nonexistent file failed")
    """
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    @patch('builtins.input')
    def test_replace_function(self, mock_input):
        initial_content = '''
def old_function():
    print("This is the old function")

print("Some other code")
'''
        with open(self.test_file, 'w') as file:
            file.write(initial_content)

        mock_input.side_effect = [
            f"Replace the function 'old_function' in {self.test_file} with a new function that prints 'This is the new function'",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        with open(self.test_file, 'r') as file:
            content = file.read()

        self.assertEqualWithDetails("def old_function():" in content, True, "Function name was changed")
        self.assertEqualWithDetails("This is the new function" in content, True, "New function content not found")
        self.assertEqualWithDetails("This is the old function" in content, False, "Old function content still present")
        self.assertEqualWithDetails("Some other code" in content, True, "Other code was affected")

    @patch('builtins.input')
    def test_replace_class(self, mock_input):
        initial_content = '''
class OldClass:
    def __init__(self):
        print("This is the old class")

print("Some other code")
'''
        with open(self.test_file, 'w') as file:
            file.write(initial_content)

        mock_input.side_effect = [
            f"Replace the class 'OldClass' in {self.test_file} with 'NewClass' that has a method printing 'This is the new class'",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        with open(self.test_file, 'r') as file:
            content = file.read()

        self.assertEqualWithDetails("class OldClass:" not in content, True, f"OldClass still present:\n{content}\n")
        self.assertEqualWithDetails("This is the new class" in content, True, "New class content not found:\n{content}\n")
        self.assertEqualWithDetails("This is the old class" not in content, True, "Old class content still present:\n{content}\n")
        self.assertEqualWithDetails("Some other code" in content, True, "Other code was affected:\n{content}\n")

    @patch('builtins.input')
    def test_insert_method_in_class(self, mock_input):
        initial_content = '''
class TestClass:
    def __init__(self):
        pass

    def existing_method(self):
        pass

print("Some other code")
'''
        with open(self.test_file, 'w') as file:
            file.write(initial_content)

        mock_input.side_effect = [
            f"Insert a new method 'new_method' in the class 'TestClass' in {self.test_file} that prints 'This is a new method'",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        with open(self.test_file, 'r') as file:
            content = file.read()

        self.assertEqualWithDetails("def new_method(self):" in content, True, f"New method not inserted:\n{content}\n")
        self.assertEqualWithDetails("This is a new method" in content, True, f"New method content not found:\n{content}\n")
        self.assertEqualWithDetails("def existing_method(self):" in content, True, f"Existing method was affected:\n{content}\n")
        self.assertEqualWithDetails("Some other code" in content, True, f"Other code was affected:\n{content}\n")

    @unittest.skip(reason="Not Implemented")
    @patch('builtins.input')
    def test_modify_nested_structure(self, mock_input):
        initial_content = '''
def outer_function():
    def inner_function():
        print("This is the inner function")
    
    inner_function()

print("Some other code")
'''
        with open(self.test_file, 'w') as file:
            file.write(initial_content)

        mock_input.side_effect = [
            f"Modify the inner_function inside outer_function in {self.test_file} to print 'This is the modified inner function'",
            '/exit'
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                auto_terminal.main()
            output = buf.getvalue()

        with open(self.test_file, 'r') as file:
            content = file.read()

        self.assertEqualWithDetails("This is the modified inner function" in content, True, "Inner function not modified:\n{content}\n")
        self.assertEqualWithDetails("This is the inner function" in content, False, "Old inner function content still present:\n{content}\n")
        self.assertEqualWithDetails("def outer_function():" in content, True, "Outer function affected:\n{content}\n")
        self.assertEqualWithDetails("Some other code" in content, True, "Other code was affected:\n{content}\n")

if __name__ == '__main__':
    unittest.main()
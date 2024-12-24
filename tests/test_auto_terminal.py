import unittest
import os
import sys
import traceback
import time
import concurrent
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout
import bots.dev.auto_terminal as start


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
                error_message = f'\nAssertion Error: {str(e)}\n'
                error_message += '\nLocal variables:\n'
                for key, value in local_vars.items():
                    error_message += f'{key} = {repr(value)}\n'
                error_message += '\nTraceback:\n'
                error_message += ''.join(traceback.format_tb(exc_traceback))
            else:
                error_message = f'\nAssertion Error: {str(e)}\n'
                error_message += 'Unable to retrieve local variables.\n'
                error_message += '\nTraceback:\n'
                error_message += ''.join(traceback.format_tb(exc_traceback))
            raise AssertionError(error_message)


class TestCodey(DetailedTestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.join(os.getcwd(), 'tests')
        cls.test_file = os.path.join(cls.test_dir, 'test_file.py')

    def setUp(self):
        if not os.path.exists(self.test_file):
            open(self.test_file, 'w').close()
        else:
            open(self.test_file, 'w').close()

    @patch('builtins.input')
    def test_down_navigation_single_path(self, mock_input):
        mock_input.side_effect = ['Hello', '/up', '/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertEqualWithDetails(os.path.exists(self.test_file), True,
            'File was not created')
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails(content.strip(), 'Test content',
            'File content does not match')

    @patch('builtins.input')
    def test_file_read(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write('Test content for reading')
        mock_input.side_effect = [
            f'Read and return the content of the file {self.test_file}',
            '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertEqualWithDetails('Test content for reading' in output, 
            True, 'File content not read correctly')

    @patch('builtins.input')
    def test_file_update(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write('Original content')
        mock_input.side_effect = [
            f"Update the content of {self.test_file} to 'Updated content'",
            '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails(content.strip(), 'Updated content',
            'File content not updated correctly')

    @unittest.skip(
        'bots sometimes refuse to delete things without more context')
    @patch('builtins.input')
    def test_file_delete(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write('Content to be deleted')
        mock_input.side_effect = [f'Delete the file {self.test_file}', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertEqualWithDetails(os.path.exists(self.test_file), False,
            'File was not deleted')

    @patch('builtins.input')
    def test_file_size(self, mock_input):
        content = 'Test content' * 1000
        with open(self.test_file, 'w') as file:
            file.write(content)
        mock_input.side_effect = [f'Get the size of {self.test_file} in bytes',
            '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertEqualWithDetails(str(len(content)) in output, True,
            'File size in bytes not found')

    @patch('builtins.input')
    def test_file_modification_time(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write('Test content')
        current_time = time.time()
        mock_input.side_effect = [
            f'Get the modification time of {self.test_file}', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertEqualWithDetails('modification time' in output.lower(), 
            True, 'File modification time retrieval failed')

    @unittest.skip(reason='Not Implemented')
    @patch('builtins.input')
    def test_concurrent_file_operations(self, mock_input):

        def write_file(content):
            mock_input.side_effect = [f"Append '{content}' to {self.test_file}"
                , '/exit']
            with StringIO() as buf, redirect_stdout(buf):
                with self.assertRaises(SystemExit):
                    start.main()
                return buf.getvalue()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_file, f'Content {i}') for i in
                range(5)]
            execution_results = [f.result() for f in concurrent.futures.
                as_completed(futures)]
        self.assertEqualWithDetails(all('appended' in result.lower() for
            result in execution_results), True,
            'Concurrent write operations failed')
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails(len(content.split('Content')) > 1, True,
            'Concurrent file operations failed')

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_file):
            os.remove(cls.test_file)

    @patch('builtins.input')
    def test_replace_function(self, mock_input):
        initial_content = """
def old_function():
    print("This is the old function")

print("Some other code")
"""
        with open(self.test_file, 'w') as file:
            file.write(initial_content)
        mock_input.side_effect = [
            f"Replace the function 'old_function' in {self.test_file} with a new function that prints 'This is the new function'"
            , '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails('def old_function():' in content, True,
            'Function name was changed')
        self.assertEqualWithDetails('This is the new function' in content, 
            True, 'New function content not found')
        self.assertEqualWithDetails('This is the old function' in content, 
            False, 'Old function content still present')
        self.assertEqualWithDetails('Some other code' in content, True,
            'Other code was affected')

    @patch('builtins.input')
    def test_replace_class(self, mock_input):
        initial_content = """
class OldClass:
    def __init__(self):
        print("This is the old class")

print("Some other code")
"""
        with open(self.test_file, 'w') as file:
            file.write(initial_content)
        mock_input.side_effect = [
            f"Replace the class 'OldClass' in {self.test_file} with 'NewClass' that has a method printing 'This is the new class'"
            , '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails('class OldClass:' not in content, True,
            f"""OldClass still present:
{content}
""")
        self.assertEqualWithDetails('This is the new class' in content, 
            True, """New class content not found:
{content}
""")
        self.assertEqualWithDetails('This is the old class' not in content,
            True, """Old class content still present:
{content}
""")
        self.assertEqualWithDetails('Some other code' in content, True,
            """Other code was affected:
{content}
""")

    @patch('builtins.input')
    def test_insert_method_in_class(self, mock_input):
        initial_content = """
class TestClass:
    def __init__(self):
        pass

    def existing_method(self):
        pass

print("Some other code")
"""
        with open(self.test_file, 'w') as file:
            file.write(initial_content)
        mock_input.side_effect = [
            f"Insert a new method 'new_method' in the class 'TestClass' in {self.test_file} that prints 'This is a new method'"
            , '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails('def new_method(self):' in content, 
            True, f"""New method not inserted:
{content}
""")
        self.assertEqualWithDetails('This is a new method' in content, True,
            f"""New method content not found:
{content}
""")
        self.assertEqualWithDetails('def existing_method(self):' in content,
            True, f"""Existing method was affected:
{content}
""")
        self.assertEqualWithDetails('Some other code' in content, True,
            f"""Other code was affected:
{content}
""")

    @unittest.skip(reason='Not Implemented')
    @patch('builtins.input')
    def test_modify_nested_structure(self, mock_input):
        initial_content = """
def outer_function():
    def inner_function():
        print("This is the inner function")
    
    inner_function()

print("Some other code")
"""
        with open(self.test_file, 'w') as file:
            file.write(initial_content)
        mock_input.side_effect = [
            f"Modify the inner_function inside outer_function in {self.test_file} to print 'This is the modified inner function'"
            , '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails('This is the modified inner function' in
            content, True, """Inner function not modified:
{content}
""")
        self.assertEqualWithDetails('This is the inner function' in content,
            False, """Old inner function content still present:
{content}
""")
        self.assertEqualWithDetails('def outer_function():' in content, 
            True, """Outer function affected:
{content}
""")
        self.assertEqualWithDetails('Some other code' in content, True,
            """Other code was affected:
{content}
""")

class TestConversationNavigation(DetailedTestCase):

    def setUp(self):
        self.bot = start.initialize_bot()
        # Create a simple conversation tree manually
        from bots.foundation.base import ConversationNode
        root = ConversationNode(role='user', content='Write functions')
        response1 = ConversationNode(role='assistant', content='Here is function 1')
        response2 = ConversationNode(role='assistant', content='Here is function 2')
        response3 = ConversationNode(role='assistant', content='Here is function 3')
        
        # Link them up
        root.replies = [response1, response2, response3]
        response1.parent = root
        response2.parent = root
        response3.parent = root
        
        # Set the bot's current conversation to the first response
        self.bot.conversation = response1

    @patch('builtins.input')
    def test_up_navigation(self, mock_input):
        mock_input.side_effect = ['/up', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main(self.bot)
            output = buf.getvalue()
        self.assertTrue('Moving up conversation tree' in output or
            "At root - can't go up" in output)

    @patch('builtins.input')
    def test_down_navigation_single_path(self, mock_input):
        mock_input.side_effect = ['/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main(self.bot)
            output = buf.getvalue()
        self.assertTrue('Moving down conversation tree' in output or
            "At leaf - can't go down" in output)

    @patch('builtins.input')
    def test_down_navigation_multiple_paths(self, mock_input):
        mock_input.side_effect = ['/up', '0', '/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main(self.bot)
            output = buf.getvalue()
        self.assertTrue('Reply index' in output or
            'Moving down conversation tree' in output or
            "At leaf - can't go down" in output)

    @patch('builtins.input')
    def test_left_right_navigation(self, mock_input):
        mock_input.side_effect = ['/right', '/left', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main(self.bot)
            output = buf.getvalue()
        self.assertTrue('Moving' in output or
            'Conversation has no siblings at this point' in output)


if __name__ == '__main__':
    unittest.main()
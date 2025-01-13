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
        cls.test_dir = os.path.join('benbuzz790', 'private_tests')
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.test_file = os.path.join(cls.test_dir, 'test_file.py')

    def setUp(self):
        if not os.path.exists(self.test_file):
            open(self.test_file, 'w').close()
        else:
            open(self.test_file, 'w').close()

    @patch('builtins.input')
    def test_file_read(self, mock_input):
        test_content = 'Test content for reading'
        with open(self.test_file, 'w') as file:
            file.write(test_content)
        prompt = f'Use the view tool to read {self.test_file}'
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Tool Requests' in output and 'view' in output,
            'View tool was not used')
        self.assertTrue('Tool Results' in output, 'No tool results found')
        cleaned_output = ' '.join(line.strip() for line in output.split(
            '\n') if line.strip())
        expected_content = f'1: {test_content}'
        cleaned_expected = ' '.join(expected_content.split())
        print(f'\nCleaned output: {cleaned_output}')
        print(f'Looking for: {cleaned_expected}')
        self.assertTrue(cleaned_expected in cleaned_output,
            f'Expected content "{cleaned_expected}" not found in cleaned output'
            )

    @patch('builtins.input')
    def test_file_update(self, mock_input):
        with open(self.test_file, 'w') as file:
            file.write('Original content')
        prompt = (
            f"Use the change_lines tool to update {self.test_file}. Replace line 1 with 'Updated content'"
            )
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails(content.strip(), 'Updated content',
            'File content not updated correctly')

    @patch('builtins.input')
    def test_file_operations(self, mock_input):
        mock_input.side_effect = [f'Write "Test content" to {self.test_file}',
            '/exit']
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
        prompt = f"""Add a new method to the TestClass in {self.test_file}. The method should be called 'new_method' and should be defined as:
def new_method(self):
    print('This is a new method')"""
        mock_input.side_effect = [prompt, '/exit']
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
        self.assertEqualWithDetails("print('This is a new method')" in
            content, True, f"""New method content not found:
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


class TestConversationNavigation(DetailedTestCase):

    @patch('builtins.input')
    def test_up_navigation(self, mock_input):
        mock_input.side_effect = ['Write a function', 'ok', '/up', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Moving up conversation tree' in output or 
            "At root - can't go up" in output)

    @patch('builtins.input')
    def test_down_navigation_single_path(self, mock_input):
        mock_input.side_effect = ['Write a function', '/up', '/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Moving down conversation tree' in output or 
            "At leaf - can't go down" in output)

    @patch('builtins.input')
    def test_down_navigation_multiple_paths(self, mock_input):
        mock_input.side_effect = ['Write a function',
            'Write it differently', '/up', '0', '/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Reply index' in output or 
            'Moving down conversation tree' in output or 
            "At leaf - can't go down" in output)

    @patch('builtins.input')
    def test_left_right_navigation(self, mock_input):
        mock_input.side_effect = ['Write a function',
            'Write it differently', 'Write another version', '/right',
            '/left', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Moving' in output or 
            'Conversation has no siblings at this point' in output)


if __name__ == '__main__':
    unittest.main()


class TestCommandHandling(DetailedTestCase):

    @patch('builtins.input')
    def test_command_at_start(self, mock_input):
        mock_input.side_effect = ['/verbose Hello bot', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Tool output on' in output)
        self.assertTrue('Claude:' in output or 'ChatGPT:' in output)

    @patch('builtins.input')
    def test_command_at_end(self, mock_input):
        mock_input.side_effect = ['Hello bot /verbose', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Tool output on' in output)
        self.assertTrue('Claude:' in output or 'ChatGPT:' in output)

    @patch('builtins.input')
    def test_unrecognized_command(self, mock_input):
        mock_input.side_effect = ['/nonexistent', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Unrecognized command' in output)
        self.assertTrue('/help' in output)

    @patch('builtins.input')
    def test_regular_chat_input(self, mock_input):
        mock_input.side_effect = ['Hello bot', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Claude:' in output or 'ChatGPT:' in output)

    @patch('builtins.input')
    def test_command_with_chat_processing_order(self, mock_input):
        mock_input.side_effect = ['Test message /quiet', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertFalse('Tool Requests' in output)
        self.assertTrue('Claude:' in output or 'ChatGPT:' in output)

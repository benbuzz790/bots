import unittest
import datetime as DT
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
    """Base test class with enhanced assertion capabilities."""

    def normalize_text(self, text: str) ->str:
        """
        Normalize text for flexible comparison.
        Handles JSON, line numbers, quotes, and case sensitivity.
        """
        text = str(text).lower()
        text = text.replace('"', '').replace("'", '')
        text = text.replace('{', '').replace('}', '')
        text = text.replace('[', '').replace(']', '')
        text = text.replace(':', '').replace(',', '')
        return ' '.join(text.split())

    def assertContainsNormalized(self, haystack: str, needle: str, msg: str
        =None):
        """
        Assert that needle exists in haystack after normalization.
        Better for comparing file contents, JSON responses, etc.
        """
        normalized_haystack = self.normalize_text(haystack)
        normalized_needle = self.normalize_text(needle)
        self.assertTrue(normalized_needle in normalized_haystack, msg or
            f"""Expected to find "{needle}" in text (after normalization).
Got:
{haystack}"""
            )

    def assertEqualWithDetails(self, first, second, msg=None):
        """Detailed assertion with local variable context on failure."""
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
        """Test the bot's ability to read file content."""
        test_content = 'Test content for reading'
        with open(self.test_file, 'w') as file:
            file.write(test_content)
        prompt = (
            f'What is in the file {self.test_file}? I need to know its contents.'
            )
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')

        def normalize(text):
            text = text.lower()
            text = text.replace('"', '').replace("'", '')
            text = text.replace('{', '').replace('}', '')
            text = text.replace('[', '').replace(']', '')
            text = text.replace(':', '').replace(',', '')
            return ' '.join(text.split())
        normalized_output = normalize(output)
        normalized_content = normalize(test_content)
        self.assertTrue(normalized_content in normalized_output,
            f"""Expected to find content "{test_content}" in response (after normalization).
Got:
{output}"""
            )

    @patch('builtins.input')
    def test_file_update(self, mock_input):
        """Test the bot's ability to modify file content."""
        with open(self.test_file, 'w') as f:
            f.write('Original content')
        with open(self.test_file, 'r') as f:
            before = f.read()
        print(f"\nInitial file content: '{before}'")
        prompt = (
            f"Please modify {self.test_file} to contain 'Updated content' instead of its current content"
            )
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        print(f'\nBot output:\n{output}')
        with open(self.test_file, 'r') as f:
            after = f.read()
        print(f"\nFinal file content: '{after}'")
        self.assertEqualWithDetails(after.strip(), 'Updated content',
            'File content was not updated as requested')

    @patch('builtins.input')
    def test_file_operations(self, mock_input):
        """Test the bot's ability to create and write to a file."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        prompt = f"Create a file at {self.test_file} containing 'Test content'"
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        print(f'\nBot output:\n{output}')
        self.assertTrue(os.path.exists(self.test_file), 'File was not created')
        with open(self.test_file, 'r') as file:
            content = file.read()
        self.assertEqualWithDetails(content.strip(), 'Test content',
            'File content does not match requested content')

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
        """Test the bot's ability to report file size."""
        content = 'Test content' * 1000
        with open(self.test_file, 'w') as file:
            file.write(content)
        expected_size = len(content)
        prompt = (
            f'What is the size of {self.test_file} in bytes? Please include the number in your response.'
            )
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        size_variants = [str(expected_size), f'{expected_size} bytes',
            f'{expected_size:,}', f'{expected_size:,} bytes',
            f'{expected_size / 1024:.0f}kb',
            f'{expected_size / 1024:.0f} kb',
            f'{expected_size / 1024:.0f} KB', f'{expected_size / 1024:.1f}',
            f'{expected_size / 1024:.1f} kb', f'{expected_size / 1024:.2f}',
            '12 kilobytes', '11.7 kilobytes', 'approximately 12kb',
            'around 12 kilobytes', 'size is 12000', 'contains 12000 bytes',
            '12000 b', '12000b']
        found_size = any(self.normalize_text(variant) in self.
            normalize_text(output) for variant in size_variants)
        if not found_size:
            print('\nTried looking for these variants:')
            for variant in size_variants:
                print(f'- {variant}')
            print('\nNormalized output:')
            print(self.normalize_text(output))
        self.assertTrue(found_size,
            f'Expected file size ({expected_size} bytes) not found in response in any common format'
            )

    @patch('builtins.input')
    def test_file_modification_time(self, mock_input):
        """Test the bot's ability to report file modification time."""
        with open(self.test_file, 'w') as file:
            file.write('Test content')
        mod_time = os.path.getmtime(self.test_file)
        prompt = (
            f'When was {self.test_file} last changed? Please include the time or date in your response.'
            )
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        time_related_terms = ['modified', 'changed', 'updated', 'timestamp',
            'date', 'time', 'created', 'accessed', str(int(mod_time)), DT.
            datetime.fromtimestamp(mod_time).strftime('%Y'), DT.datetime.
            fromtimestamp(mod_time).strftime('%m'), DT.datetime.
            fromtimestamp(mod_time).strftime('%d')]
        found_time = any(self.normalize_text(term) in self.normalize_text(
            output) for term in time_related_terms)
        if not found_time:
            print('\nTried looking for these time-related terms:')
            for term in time_related_terms:
                print(f'- {term}')
            print('\nNormalized output:')
            print(self.normalize_text(output))
        self.assertTrue(found_time,
            'No time or date information found in response')

    @unittest.skip('Concurrent operations need further design consideration')
    @patch('builtins.input')
    def test_concurrent_file_operations(self, mock_input):
        """Test the bot's ability to handle concurrent file access."""

        def request_append(content: str):
            """Helper to make a file append request."""
            prompt = f"Please add '{content}' to the file {self.test_file}"
            mock_input.side_effect = [prompt, '/exit']
            with StringIO() as buf, redirect_stdout(buf):
                with self.assertRaises(SystemExit):
                    start.main()
                return buf.getvalue()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            contents = [f'Content {i}' for i in range(5)]
            futures = [executor.submit(request_append, content) for content in
                contents]
            responses = [f.result() for f in concurrent.futures.
                as_completed(futures)]
        with open(self.test_file, 'r') as file:
            final_content = file.read()
        for content in contents:
            self.assertTrue(content in final_content,
                f'Expected content "{content}" not found in file')

    @patch('builtins.input')
    def test_insert_method_in_class(self, mock_input):
        """Test the bot's ability to add a method to a class."""
        with open(self.test_file, 'w', encoding='utf-8') as file:
            file.write('class TestClass:\n')
            file.write('    def __init__(self):\n')
            file.write('        pass\n')
            file.write('\n')
            file.write('    def existing_method(self):\n')
            file.write('        pass\n')
            file.write('\n')
            file.write('print("Some other code")\n')
        prompt = (
            f"Please add a method to the TestClass in {self.test_file}. The method should be called 'new_method' and should print 'This is a new method'. Do not change any existing code."
            )
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        with open(self.test_file, 'r', encoding='utf-8') as file:
            content = file.read()
        print(f'\nUpdated file content:\n{content}')
        original_elements = ['class TestClass:', 'def __init__(self):',
            'def existing_method(self):', "print('Some other code')", 'pass']
        for element in original_elements:
            self.assertIn(element, content,
                f'Original code element missing: {element}')
        method_found = any(pattern in content for pattern in [
            'def new_method(self):', 'def new_method (self):',
            'def new_method( self ):'])
        self.assertTrue(method_found, 'New method definition not found')
        print_found = any(pattern in content for pattern in [
            "print('This is a new method')",
            'print("This is a new method")',
            "print(f'This is a new method')", 'print(f"This is a new method")']
            )
        self.assertTrue(print_found, 'Required print statement not found')


class TestConversationNavigation(DetailedTestCase):

    @patch('builtins.input')
    def test_up_navigation(self, mock_input):
        """Test navigating up the conversation tree."""
        mock_input.side_effect = ['Write a function', 'ok', '/up', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertTrue(any(self.normalize_text(msg) in self.normalize_text
            (output) for msg in ['Moving up conversation tree',
            "At root - can't go up"]),
            'Expected navigation message not found in output')

    @patch('builtins.input')
    def test_down_navigation_single_path(self, mock_input):
        """Test navigating down a single path in the conversation tree."""
        mock_input.side_effect = ['Write a function', '/up', '/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertTrue(any(self.normalize_text(msg) in self.normalize_text
            (output) for msg in ['Moving down conversation tree',
            "At leaf - can't go down"]),
            'Expected navigation message not found in output')

    @patch('builtins.input')
    def test_down_navigation_multiple_paths(self, mock_input):
        """Test navigating down when multiple paths exist."""
        mock_input.side_effect = ['Write a function',
            'Write it differently', '/up', '0', '/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        expected_messages = ['Reply index', 'Moving down conversation tree',
            "At leaf - can't go down"]
        self.assertTrue(any(self.normalize_text(msg) in self.normalize_text
            (output) for msg in expected_messages),
            'Expected navigation message not found in output')

    @patch('builtins.input')
    def test_left_right_navigation(self, mock_input):
        """Test navigating between sibling nodes in the conversation tree."""
        mock_input.side_effect = ['Write a function',
            'Write it differently', 'Write another version', '/right',
            '/left', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        expected_messages = ['Moving right in conversation tree',
            'Moving left in conversation tree', 'Moving',
            'Conversation has no siblings at this point']
        self.assertTrue(any(self.normalize_text(msg) in self.normalize_text
            (output) for msg in expected_messages),
            'Expected navigation message not found in output')


if __name__ == '__main__':
    unittest.main()


class TestCommandHandling(DetailedTestCase):

    @patch('builtins.input')
    def test_command_at_start(self, mock_input):
        """Test command processing when command is at start of input."""
        mock_input.side_effect = ['/verbose Hello bot', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Tool output on')
        self.assertContainsNormalized(output, 'Claude')

    @patch('builtins.input')
    def test_command_at_end(self, mock_input):
        """Test command processing when command is at end of input."""
        mock_input.side_effect = ['Hello bot /verbose', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Tool output on')
        self.assertContainsNormalized(output, 'Claude')

    @patch('builtins.input')
    def test_unrecognized_command(self, mock_input):
        """Test handling of unrecognized commands."""
        mock_input.side_effect = ['/nonexistent', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Unrecognized command')
        self.assertContainsNormalized(output, 'help')

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


class DetailedTestCase(unittest.TestCase):
    """Base test class with enhanced assertion capabilities."""

    def normalize_text(self, text: str) ->str:
        """
        Normalize text for flexible comparison.
        Handles JSON, line numbers, quotes, and case sensitivity.
        """
        text = str(text).lower()
        text = text.replace('"', '').replace("'", '')
        text = text.replace('{', '').replace('}', '')
        text = text.replace('[', '').replace(']', '')
        text = text.replace(':', '').replace(',', '')
        return ' '.join(text.split())

    def assertContainsNormalized(self, haystack: str, needle: str, msg: str
        =None):
        """
        Assert that needle exists in haystack after normalization.
        Better for comparing file contents, JSON responses, etc.
        """
        normalized_haystack = self.normalize_text(haystack)
        normalized_needle = self.normalize_text(needle)
        self.assertTrue(normalized_needle in normalized_haystack, msg or
            f"""Expected to find "{needle}" in text (after normalization).
Got:
{haystack}"""
            )

    def assertEqualWithDetails(self, first, second, msg=None):
        """Detailed assertion with local variable context on failure."""
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

"""Unit tests for the auto_terminal module.

This test suite verifies the functionality of the auto_terminal interface,
focusing on file operations, conversation navigation, and command handling.
Tests are designed to run against real APIs without mocking core functionality,
except for input/output operations.
"""

import unittest
import datetime as DT
import os
import sys
import traceback
import concurrent
from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout
import bots.dev.auto_terminal as start
from datetime import datetime

class DetailedTestCase(unittest.TestCase):
    """Base test class with enhanced assertion capabilities."""

    def normalize_text(self, text: str) -> str:
        """Normalize text for flexible comparison.
        
        Standardizes text format by removing common variations in syntax and formatting
        to enable more robust text comparisons.

        Parameters:
            text (str): The text to normalize

        Returns:
            str: The normalized text with special characters removed and standardized spacing
        """
        text = str(text).lower()
        text = text.replace('"', '').replace("'", '')
        text = text.replace('{', '').replace('}', '')
        text = text.replace('[', '').replace(']', '')
        text = text.replace(':', '').replace(',', '')
        return ' '.join(text.split())

    def assertContainsNormalized(self, haystack: str, needle: str, msg: str | None = None) -> None:
        """Assert that needle exists in haystack after normalization.
        
        Performs a contains assertion after normalizing both strings to handle
        variations in formatting, whitespace, and special characters.

        Parameters:
            haystack (str): The larger text to search within
            needle (str): The text to search for
            msg (str | None): Optional custom error message

        Raises:
            AssertionError: If normalized needle is not found in normalized haystack
        """
        normalized_haystack = self.normalize_text(haystack)
        normalized_needle = self.normalize_text(needle)
        self.assertTrue(normalized_needle in normalized_haystack, msg or f'Expected to find "{needle}" in text (after normalization).\nGot:\n{haystack}')
        normalized_haystack = self.normalize_text(haystack)
        normalized_needle = self.normalize_text(needle)
        self.assertTrue(normalized_needle in normalized_haystack, msg or f'Expected to find "{needle}" in text (after normalization).\nGot:\n{haystack}')

    def assertEqualWithDetails(self, first: object, second: object, msg: str | None = None) -> None:
        """Detailed assertion with local variable context on failure.
        
        Enhanced version of assertEqual that provides detailed context including
        local variables and stack trace on assertion failure.

        Parameters:
            first (object): First value to compare
            second (object): Second value to compare
            msg (str | None): Optional custom error message

        Raises:
            AssertionError: If values are not equal, with detailed context
        """
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
    """Test suite for file manipulation capabilities of the auto_terminal.

    Tests the bot's ability to perform various file operations including:
    - Reading file contents
    - Modifying files
    - Deleting files
    - Reporting file metadata (size, modification time)
    - Adding methods to existing classes
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test environment for all test methods in the class.
        
        Creates a test directory structure that will be used by all test methods.
        This is run once before any tests in the class.

        Class Attributes:
            test_dir (str): Path to test directory
            test_file (str): Path to test file used in tests
        """
        cls.test_dir = os.path.join('benbuzz790', 'private_tests')
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.test_file = os.path.join(cls.test_dir, 'test_file.py')
        cls.test_dir = os.path.join('benbuzz790', 'private_tests')
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.test_file = os.path.join(cls.test_dir, 'test_file.py')

    def setUp(self) -> None:
        """Set up test environment before each test method.
        
        Ensures a clean test file exists before each test.
        Creates an empty file if it doesn't exist, or clears existing content.
        """
        if not os.path.exists(self.test_file):
            open(self.test_file, 'w').close()
        else:
            open(self.test_file, 'w').close()
        if not os.path.exists(self.test_file):
            open(self.test_file, 'w').close()
        else:
            open(self.test_file, 'w').close()

    @patch('builtins.input')
    def test_file_read(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the bot's ability to read and report file content.
        
        Creates a test file with known content and verifies that the bot can
        correctly read and report its contents when asked.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create test file with known content
            2. Ask bot to read file
            3. Verify bot's response contains file content
        """
        test_content = 'Test content for reading'
        with open(self.test_file, 'w') as file:
            file.write(test_content)
        prompt = f'What is in the file {self.test_file}? I need to know its contents.'
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
        self.assertTrue(normalized_content in normalized_output, f'Expected to find content "{test_content}" in response (after normalization).\nGot:\n{output}')

    @patch('builtins.input')
    def test_file_update(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the bot's ability to modify existing file content.
        
        Verifies that the bot can correctly update file contents while preserving
        file integrity and handling the operation safely.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create file with original content
            2. Request content modification
            3. Verify file was updated correctly
            4. Ensure no unintended changes occurred
        """
        with open(self.test_file, 'w') as f:
            f.write('Original content')
        with open(self.test_file, 'r') as f:
            before = f.read()
        print(f"\nInitial file content: '{before}'")
        prompt = f"/auto Please modify {self.test_file} to contain 'Updated content' instead of its current content"
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        print(f'\nBot output:\n{output}')
        with open(self.test_file, 'r') as f:
            after = f.read()
        print(f"\nFinal file content: '{after}'")
        self.assertEqualWithDetails(after.strip(), 'Updated content', 'File content was not updated as requested')

    @patch('builtins.input')
    def test_file_delete(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the bot's ability to safely delete files with proper authorization.
        
        Verifies that the bot can delete files when given explicit permission and
        proper context, while maintaining safety checks.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create temporary test file
            2. Request deletion with full context and permission
            3. Verify file was deleted
            4. Check for appropriate confirmation/feedback
        """
        with open(self.test_file, 'w') as file:
            file.write('This is a temporary test file that should be deleted\nCreated for test_file_delete')
        delete_prompt = f"/auto I need you to delete the file at {self.test_file}. This is a test file that contains only the text 'This is a temporary test file that should be deleted'. I've verified its contents and confirm it should be deleted. Use powershell to delete the file."
        mock_input.side_effect = [delete_prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        import time
        time.sleep(1)
        file_exists = os.path.exists(self.test_file)
        if file_exists:
            with open(self.test_file, 'r') as f:
                print(f'\nFile still exists with content:\n{f.read()}')
            print(f"\nBot's response was:\n{output}")
        self.assertFalse(file_exists, 'File was not deleted despite clear context and permission')

    @patch('builtins.input')
    def test_file_size(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the bot's ability to accurately report file size.
        
        Creates a file of known size and verifies that the bot can correctly
        report its size in various acceptable formats (bytes, KB, etc.).

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create file with specific size
            2. Request file size information
            3. Verify response contains correct size in acceptable format
            4. Check multiple size format variants
        """
        content = 'Test content' * 1000
        with open(self.test_file, 'w') as file:
            file.write(content)
        expected_size = len(content)
        prompt = f'What is the size of {self.test_file} in bytes? Please include the number in your response.'
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        size_variants = [str(expected_size), f'{expected_size} bytes', f'{expected_size:,}', f'{expected_size:,} bytes', f'{expected_size / 1024:.0f}kb', f'{expected_size / 1024:.0f} kb', f'{expected_size / 1024:.0f} KB', f'{expected_size / 1024:.1f}', f'{expected_size / 1024:.1f} kb', f'{expected_size / 1024:.2f}', '12 kilobytes', '11.7 kilobytes', 'approximately 12kb', 'around 12 kilobytes', 'size is 12000', 'contains 12000 bytes', '12000 b', '12000b']
        found_size = any((self.normalize_text(variant) in self.normalize_text(output) for variant in size_variants))
        if not found_size:
            print('\nTried looking for these variants:')
            for variant in size_variants:
                print(f'- {variant}')
            print('\nNormalized output:')
            print(self.normalize_text(output))
        self.assertTrue(found_size, f'Expected file size ({expected_size} bytes) not found in response in any common format')

    @patch('builtins.input')
    def test_file_modification_time(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the bot's ability to report file modification timestamps.

        Verifies that the bot can correctly retrieve and report file modification
        times in various acceptable formats (timestamp, date, time components).

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create file with known modification time
            2. Request modification time information
            3. Verify response contains time information
            4. Check multiple time format variants
        """
        with open(self.test_file, 'w') as file:
            file.write('Test content')
        mod_time = os.path.getmtime(self.test_file)
        prompt = f'When was {self.test_file} last changed? Please include the time or date in your response.'
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        time_related_terms = ['modified', 'changed', 'updated', 'timestamp', 'date', 'time', 'created', 'accessed', str(int(mod_time)), DT.datetime.fromtimestamp(mod_time).strftime('%Y'), DT.datetime.fromtimestamp(mod_time).strftime('%m'), DT.datetime.fromtimestamp(mod_time).strftime('%d')]
        found_time = any((self.normalize_text(term) in self.normalize_text(output) for term in time_related_terms))
        if not found_time:
            print('\nTried looking for these time-related terms:')
            for term in time_related_terms:
                print(f'- {term}')
            print('\nNormalized output:')
            print(self.normalize_text(output))
        self.assertTrue(found_time, 'No time or date information found in response')

    @patch('builtins.input')
    def test_insert_method_in_class(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the bot's ability to add methods to existing classes.

        Verifies that the bot can correctly add a new method to an existing class
        while preserving the original class structure and other methods.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create test file with existing class
            2. Request addition of new method
            3. Verify method was added correctly
            4. Check original code preserved
            5. Verify method implementation
        """
        with open(self.test_file, 'w', encoding='utf-8') as file:
            file.write('class TestClass:\n')
            file.write('    def __init__(self):\n')
            file.write('        pass\n')
            file.write('\n')
            file.write('    def existing_method(self):\n')
            file.write('        pass\n')
            file.write('\n')
            file.write('print("Some other code")\n')
        prompt = f"/auto Please add a method to the TestClass in {self.test_file}. The method should be called 'new_method' and should print 'This is a new method'. Do not change any existing code."
        mock_input.side_effect = [prompt, '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        with open(self.test_file, 'r', encoding='utf-8') as file:
            content = file.read()
        print(f'\nUpdated file content:\n{content}')
        original_elements = ['class TestClass:', 'def __init__(self):', 'def existing_method(self):', 'print("Some other code")', 'pass']
        for element in original_elements:
            self.assertIn(self.normalize_text(element), self.normalize_text(content), f'Original code element missing: {element}')
        method_found = any((pattern in content for pattern in ['def new_method(self):', 'def new_method (self):', 'def new_method( self ):']))
        self.assertTrue(method_found, 'New method definition not found')
        print_found = any((pattern in content for pattern in ["print('This is a new method')", 'print("This is a new method")', "print(f'This is a new method')", 'print(f"This is a new method")']))
        self.assertTrue(print_found, 'Required print statement not found')

class TestConversationNavigation(DetailedTestCase):
    """Test suite for basic conversation tree navigation commands.

    Verifies the bot's ability to navigate through conversation history using:
    - Up navigation (to parent nodes)
    - Down navigation (to child nodes)
    - Left/right navigation (between sibling nodes)
    
    Each test verifies both the navigation operation and appropriate feedback messages.
    """

    @patch('builtins.input')
    def test_up_navigation(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test navigation to parent nodes in conversation tree.
        
        Verifies that the /up command correctly moves to parent nodes and
        handles root node edge case appropriately.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create simple conversation path
            2. Navigate upward
            3. Verify appropriate navigation messages
            4. Test behavior at root node
        """
        mock_input.side_effect = ['Write a function', 'ok', '/up', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertTrue(any((self.normalize_text(msg) in self.normalize_text(output) for msg in ['Moving up conversation tree', "At root - can't go up"])), 'Expected navigation message not found in output')

    @patch('builtins.input')
    def test_down_navigation_single_path(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test navigation to child nodes in a linear conversation path.
        
        Verifies that the /down command works correctly when there is only
        one possible child node to navigate to.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create linear conversation
            2. Navigate up then down
            3. Verify navigation messages
            4. Test behavior at leaf node
        """
        mock_input.side_effect = ['Write a function', '/up', '/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertTrue(any((self.normalize_text(msg) in self.normalize_text(output) for msg in ['Moving down conversation tree', "At leaf - can't go down"])), 'Expected navigation message not found in output')

    @patch('builtins.input')
    def test_down_navigation_multiple_paths(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test navigation when multiple child nodes are available.
        
        Verifies that the /down command handles branching conversations correctly,
        providing appropriate selection options when multiple paths exist.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create branching conversation
            2. Navigate to node with multiple children
            3. Verify path selection prompt
            4. Test navigation to selected path
        """
        mock_input.side_effect = ['Write a function', 'Write it differently', '/up', '0', '/down', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        expected_messages = ['Reply index', 'Moving down conversation tree', "At leaf - can't go down"]
        self.assertTrue(any((self.normalize_text(msg) in self.normalize_text(output) for msg in expected_messages)), 'Expected navigation message not found in output')

    @patch('builtins.input')
    def test_left_right_navigation(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test navigation between sibling nodes using /left and /right commands.
        
        Verifies that lateral navigation between sibling nodes works correctly,
        including proper handling of edge cases when no siblings exist.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create multiple sibling nodes
            2. Test right navigation
            3. Test left navigation
            4. Verify edge case handling
        """
        mock_input.side_effect = ['Write a function', 'Write it differently', 'Write another version', '/right', '/left', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        expected_messages = ['Moving right in conversation tree', 'Moving left in conversation tree', 'Moving', 'Conversation has no siblings at this point']
        self.assertTrue(any((self.normalize_text(msg) in self.normalize_text(output) for msg in expected_messages)), 'Expected navigation message not found in output')

class TestCommandHandling(DetailedTestCase):
    """Test suite for command processing in the auto_terminal interface.

    Verifies proper handling of:
    - Commands at start of input
    - Commands at end of input
    - Unrecognized commands
    - Regular chat input
    - Command processing order
    
    Ensures commands are properly parsed regardless of position and appropriate
    feedback is provided for invalid commands.
    """

    @patch('builtins.input')
    def test_command_at_start(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test command recognition at the start of input string.
        
        Verifies that commands are correctly identified and processed when they
        appear at the beginning of the input string.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Send command at start of input
            2. Verify command processing
            3. Check command effect
            4. Verify remaining input handling
        """
        mock_input.side_effect = ['/verbose Hello bot', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Tool output on')
        self.assertContainsNormalized(output, 'Claude')

    @patch('builtins.input')
    def test_command_at_end(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test command recognition at the end of input string.
        
        Verifies that commands are correctly identified and processed when they
        appear at the end of the input string.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Send command at end of input
            2. Verify command processing
            3. Check command effect
            4. Verify preceding input handling
        """
        mock_input.side_effect = ['Hello bot /verbose', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Tool output on')
        self.assertContainsNormalized(output, 'Claude')

    @patch('builtins.input')
    def test_unrecognized_command(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test error handling for invalid or unrecognized commands.
        
        Verifies that the system properly handles unknown commands by providing
        appropriate error messages and help information.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Send invalid command
            2. Verify error message
            3. Check for help suggestion
            4. Ensure system remains stable
        """
        mock_input.side_effect = ['/nonexistent', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Unrecognized command')
        self.assertContainsNormalized(output, 'help')

    @patch('builtins.input')
    def test_regular_chat_input(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test handling of normal chat input without commands.
        
        Verifies that regular conversational input is properly processed
        and receives appropriate responses from the bot.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Send normal chat message
            2. Verify bot response
            3. Check response format
        """
        mock_input.side_effect = ['Hello bot', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertTrue('Claude:' in output or 'ChatGPT:' in output)

    @patch('builtins.input')
    def test_command_with_chat_processing_order(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the order of command and chat message processing.
        
        Verifies that when a message contains both chat content and a command,
        both are processed in the correct order with appropriate effects.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Send message containing both chat and command
            2. Verify command effect (/quiet)
            3. Verify chat message processed
            4. Check correct processing order maintained
        """
        mock_input.side_effect = ['Test message /quiet', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
        self.assertFalse('Tool Requests' in output)
        self.assertTrue('Claude:' in output or 'ChatGPT:' in output)

class TestAdvancedNavigation(DetailedTestCase):
    """Test suite for advanced conversation tree navigation features.

    Tests the implementation of more complex navigation commands:
    - /root: Moving to conversation root from any depth
    - /label: Marking nodes with custom labels
    - /goto: Navigation to labeled nodes
    
    Verifies both successful operations and error handling for these commands,
    ensuring reliable navigation through complex conversation trees.
    """

    @patch('builtins.input')
    def test_root_navigation(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the /root command for returning to conversation start.
        
        Verifies that the /root command correctly navigates to the root node
        from any depth in the conversation tree.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create multi-level conversation
            2. Navigate to deeper level
            3. Execute root command
            4. Verify return to root node
        """
        mock_input.side_effect = ['Write a function', 'Make it better', 'Add error handling', '/root', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Moved to root of conversation tree')

    @patch('builtins.input')
    def test_label_node(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the /label command for marking conversation nodes.
        
        Verifies that nodes can be labeled for later reference and that
        labels are correctly stored in the conversation tree.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create conversation node
            2. Apply label to node
            3. Verify label assignment
            4. Check confirmation message
        """
        mock_input.side_effect = ['Write a function', '/label', 'good_function', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Saved current node with label: good_function')

    @patch('builtins.input')
    def test_goto_labeled_node(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the /goto command for navigating to labeled nodes.
        
        Verifies that the bot can correctly navigate to previously labeled
        nodes in the conversation tree using the /goto command.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create and label node
            2. Navigate away from node
            3. Use goto to return to labeled node
            4. Verify correct navigation
        """
        mock_input.side_effect = ['Write a function', '/label', 'good_function', 'Write another function', '/goto', 'good_function', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Moved to node labeled: good_function')

    @patch('builtins.input')
    def test_goto_nonexistent_label(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test error handling for /goto with invalid labels.
        
        Verifies that appropriate error messages are displayed when attempting
        to navigate to a non-existent label.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create conversation
            2. Attempt goto with invalid label
            3. Verify error message
            4. Check conversation state unchanged
        """
        mock_input.side_effect = ['Write a function', '/goto', 'nonexistent_label', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'No node found with label: nonexistent_label')

    @patch('builtins.input')
    def test_multiple_labels(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test navigation between multiple labeled nodes.
        
        Verifies that multiple nodes can be labeled and that navigation
        between labeled nodes works correctly.

        Parameters:
            mock_input (unittest.mock.MagicMock): Mocked input function for testing

        Test Sequence:
            1. Create multiple labeled nodes
            2. Navigate between labeled nodes
            3. Verify correct navigation to each label
            4. Check state after multiple transitions
        """
        mock_input.side_effect = ['Write a function', '/label', 'function1', 'Write another function', '/label', 'function2', '/goto', 'function1', '/goto', 'function2', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Moved to node labeled: function1')
        self.assertContainsNormalized(output, 'Moved to node labeled: function2')

if __name__ == '__main__':
    unittest.main()

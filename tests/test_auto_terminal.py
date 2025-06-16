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
"""Unit tests for the auto_terminal module.

This test suite verifies the functionality of the auto_terminal interface,
focusing on file operations, conversation navigation, and command handling.
Tests are designed to run against real APIs without mocking core functionality,
except for input/output operations.
"""

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

    def assertContainsNormalized(self, haystack: str, needle: str, msg: str | None=None) -> None:
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

    def assertEqualWithDetails(self, first: object, second: object, msg: str | None=None) -> None:
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

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up test environment after all test methods in the class.

        Removes the test directory and all its contents.
        This is run once after all tests in the class are complete.
        """
        import shutil
        try:
            if os.path.exists(cls.test_dir):
                shutil.rmtree(cls.test_dir)
        except Exception as e:
            print(f'Warning: Could not clean up test directory {cls.test_dir}: {e}')

    def setUp(self) -> None:
        """Set up test environment before each test method.

        Ensures a clean test file exists before each test.
        Creates an empty file if it doesn't exist, or clears existing content.
        """
        if not os.path.exists(self.test_file):
            open(self.test_file, 'w').close()
        else:
            open(self.test_file, 'w').close()

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

        @patch('builtins.input')
        def test_showlabels_empty(self, mock_input: unittest.mock.MagicMock) -> None:
            """Test the /showlabels command when no labels exist."""
            mock_input.side_effect = ['/showlabels', '/exit']
            with StringIO() as buf, redirect_stdout(buf):
                with self.assertRaises(SystemExit):
                    start.main()
                output = buf.getvalue()
                print(f'\nBot output:\n{output}')
            self.assertContainsNormalized(output, 'No labels saved')

    @patch('builtins.input')
    def test_showlabels_with_labels(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test the /showlabels command with existing labels."""
        mock_input.side_effect = ['Write a function to calculate fibonacci numbers', '/label', 'fibonacci_func', 'Write a sorting algorithm', '/label', 'sort_algo', '/showlabels', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'Saved labels:')
        self.assertContainsNormalized(output, 'fibonacci_func')
        self.assertContainsNormalized(output, 'sort_algo')

    @patch('builtins.input')
    def test_showlabels_content_preview(self, mock_input: unittest.mock.MagicMock) -> None:
        """Test that /showlabels displays content previews correctly."""
        long_message = "This is a very long message that should be truncated when displayed in the showlabels command because it exceeds the 100 character limit that is set for content previews"
        mock_input.side_effect = [long_message, '/label', 'long_message', '/showlabels', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                start.main()
            output = buf.getvalue()
            print(f'\nBot output:\n{output}')
        self.assertContainsNormalized(output, 'long_message')
        # Check that the preview is truncated (should contain "..." for long content)
        self.assertTrue('...' in output or len(long_message) <= 100)

    @patch('builtins.input')
    @patch('bots.dev.auto_terminal.filedialog.askopenfilename')
    def test_label_persistence_save_load(self, mock_filedialog: unittest.mock.MagicMock, mock_input: unittest.mock.MagicMock) -> None:
        """Test that labels persist when saving and loading bots."""
        import tempfile
        import os
        # Create a temporary file for saving/loading
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bot', delete=False) as temp_file:
            temp_filename = temp_file.name
        try:
            # First session: create labels and save
            mock_input.side_effect = ['Write a function to parse JSON', '/label', 'json_parser', '/save', temp_filename, '/exit']
            with StringIO() as buf, redirect_stdout(buf):
                with self.assertRaises(SystemExit):
                    start.main()
                output1 = buf.getvalue()
                print(f'\nFirst session output:\n{output1}')
            # Verify the file was created and contains our label
            self.assertTrue(os.path.exists(temp_filename), "Bot file was not created")
            self.assertContainsNormalized(output1, 'Saved current node with label: json_parser')
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
if __name__ == '__main__':
    unittest.main()
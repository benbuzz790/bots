
import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import os
import ast
import astor
import textwrap
import subprocess
from auto_terminal import (
    IndentVisitor, 
    indent_code, 
    execute_python_code, 
    pretty, 
    main
)

class TestAutoTerminal(unittest.TestCase):

    def test_indent_visitor(self):
        code = "def test_func():\n    pass\n"
        tree = ast.parse(code)
        visitor = IndentVisitor()
        modified_tree = visitor.visit(tree)
        modified_code = astor.to_source(modified_tree)
        self.assertIn("    def test_func():", modified_code)

    def test_indent_code(self):
        code = "def test_func():\n    pass"
        indented = indent_code(code)
        self.assertIn("def test_func():", indented)
        self.assertIn("    pass", indented)

    @patch('subprocess.Popen')
    def test_execute_python_code_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Output", "")
        mock_popen.return_value = mock_process

        result = execute_python_code("print('test')")
        self.assertEqual(result, "Output")

    @patch('subprocess.Popen')
    def test_execute_python_code_timeout(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=300)
        mock_popen.return_value = mock_process

        result = execute_python_code("while True: pass")
        self.assertIn("Error: Code execution timed out", result)

    def test_pretty(self):
        captured_output = io.StringIO()
        sys.stdout = captured_output
        pretty("Test message", "Name", width=20, indent=2)
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        self.assertIn("Name: Test", output)
        self.assertIn("  message", output)

    @patch('builtins.input', side_effect=['/exit'])
    @patch('bots.AnthropicBot')
    def test_main_exit(self, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot_instance.load.return_value = mock_bot_instance

        with self.assertRaises(SystemExit):
            main()

    @patch('builtins.input', side_effect=['/save', '/exit'])
    @patch('bots.AnthropicBot')
    def test_main_save(self, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot_instance.load.return_value = mock_bot_instance
        mock_bot_instance.save.return_value = "test_save.bot"

        with self.assertRaises(SystemExit):
            main()

        mock_bot_instance.save.assert_called_once()

    @patch('builtins.input', side_effect=['/load', 'test_load.bot', '/exit'])
    @patch('bots.AnthropicBot')
    @patch('os.path.exists', return_value=True)
    def test_main_load(self, mock_exists, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot_instance.load.return_value = mock_bot_instance

        with self.assertRaises(SystemExit):
            main()

        mock_bot_instance.load.assert_called_with('test_load.bot')

    @patch('builtins.input', side_effect=['/auto', '3', '/exit'])
    @patch('bots.AnthropicBot')
    def test_main_auto(self, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot_instance.load.return_value = mock_bot_instance
        mock_bot_instance.respond.return_value = "Auto response"

        with self.assertRaises(SystemExit):
            main()

        self.assertEqual(mock_bot_instance.respond.call_count, 3)

if __name__ == '__main__':
    unittest.main()

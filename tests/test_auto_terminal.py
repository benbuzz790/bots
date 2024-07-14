import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import patch, MagicMock
import ast
import subprocess
import src.bots as bots
from src.auto_terminal import (
    IndentVisitor, 
    indent_code, 
    execute_python_code, 
    pretty, 
    main
)

class TestAutoTerminal(unittest.TestCase):
    def test_indent_visitor(self):
        code = """
def outer_function():
    print('Outer function')
    if True:
        print('Inside if')
        for i in range(3):
            print(f'Loop {i}')
    def inner_function():
        print('Inner function')
        while True:
            print('Inside while')
            break
    inner_function()
    """
        indented = indent_code(code)
        
        # Test if the indented code compiles
        try:
            ast.parse(indented)
        except SyntaxError as e:
            self.fail(f"Indented code failed to compile: {e}")
        
        # Optionally, you can also compile the code to check for any errors
        try:
            compile(indented, '<string>', 'exec')
        except Exception as e:
            self.fail(f"Compiled code raised an exception: {e}")
        
        # If we've reached this point, the test passes
        self.assertTrue(True)
    
    def test_indent_code(self):
        code = "def test_func():\n    pass"
        indented = indent_code(code)
        self.assertIn("def test_func():", indented)
        self.assertIn("    pass", indented)

    @patch('subprocess.Popen')
    def test_execute_python_code_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Output from complex code", "")
        mock_popen.return_value = mock_process

        complex_code = """
def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n-1)

class MathOperations:
    def __init__(self):
        self.pi = 3.14159

    def circle_area(self, radius):
        return self.pi * radius ** 2

# Main execution
if __name__ == '__main__':
    # Test factorial
    for i in range(5):
        print(f"Factorial of {i} is {factorial(i)}")
    
    # Test circle area
    math_ops = MathOperations()
    radii = [1, 2, 3, 4, 5]
    for r in radii:
        area = math_ops.circle_area(r)
        print(f"Area of circle with radius {r} is {area:.2f}")

    # List comprehension and lambda function
    squares = [x**2 for x in range(10) if x % 2 == 0]
    print("Squares of even numbers:", squares)

    # Using map and filter
    numbers = list(range(-5, 6))
    positive_numbers = list(filter(lambda x: x > 0, numbers))
    squared_positives = list(map(lambda x: x**2, positive_numbers))
    print("Squared positive numbers:", squared_positives)
    """

        result = execute_python_code(complex_code)
        self.assertEqual(result, "Output from complex code")

        # Check if Popen was called with the right arguments
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        self.assertEqual(call_args[0], 'python')
        self.assertTrue(call_args[1].endswith('temp_script.py'))

    @patch('subprocess.Popen')
    def test_execute_python_code_timeout(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=300)
        mock_popen.return_value = mock_process

        result = execute_python_code("while True: pass")
        self.assertIn("Error: Code execution timed out", result)
    
    @patch('builtins.input', side_effect=['/exit'])
    @patch('src.bots.AnthropicBot')
    def test_main_exit(self, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot_instance.load.return_value = mock_bot_instance

        with self.assertRaises(SystemExit):
            main()

    @patch('builtins.input', side_effect=['/save', '/exit'])
    @patch('src.bots.AnthropicBot')
    def test_main_save(self, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot_instance.load.return_value = mock_bot_instance
        mock_bot_instance.save.return_value = "test_save.bot"

        with self.assertRaises(SystemExit):
            main()

        mock_bot_instance.save.assert_called_once()

    @patch('builtins.input', side_effect=['/load', 'test_load.bot', '/exit'])
    @patch('src.bots.AnthropicBot')
    @patch('os.path.exists', return_value=True)
    def test_main_load(self, mock_exists, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot_instance.load.return_value = mock_bot_instance

        with self.assertRaises(SystemExit):
            main()

        mock_bot_instance.load.assert_called_with('test_load.bot')

    @patch('builtins.input', side_effect=['/auto', '3', '', '/exit'])
    @patch('src.bots.AnthropicBot')
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

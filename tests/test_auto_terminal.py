import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import patch, MagicMock, call
import ast
import subprocess
import src.bots as bots
from tests.detailed_debug import DetailedTestCase
from src.auto_terminal import main
from src.bot_tools import execute_python_code


class TestAutoTerminal(DetailedTestCase):

    @patch('subprocess.Popen')
    def test_execute_python_code_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.return_value = 'Output from complex code', ''
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
        self.assertEqual(result, 'Output from complex code')
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        self.assertEqual(call_args[0], 'python')
        self.assertTrue(call_args[1].endswith('temp_script.py'))

    @patch('subprocess.Popen')
    def test_execute_python_code_timeout(self, mock_popen):
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd
            ='test', timeout=300)
        mock_popen.return_value = mock_process
        result = execute_python_code('while True: pass')
        self.assertIn('Error: Code execution timed out', result)

    @patch('builtins.input', side_effect=['/exit'])
    @patch('src.bots.AnthropicBot')
    def test_main_exit(self, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot_instance.load.return_value = mock_bot_instance
        try:
            main()
        except SystemExit:
            pass
        else:
            self.fail('SystemExit exception not raised')

    @patch('builtins.input', side_effect=['/save', '/exit'])
    @patch('src.bots.AnthropicBot')
    def test_main_save(self, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot.load.return_value = mock_bot_instance  # Mock the class method load
        mock_bot_instance.save.return_value = 'test_save.bot'
        try:
            main()
        except SystemExit:
            pass
        mock_bot_instance.save.assert_called_once()

    @patch('builtins.input', side_effect=['/load', 'test_load.bot', '/exit'])
    @patch('src.bots.AnthropicBot')
    @patch('os.path.exists', return_value=True)
    def test_main_load(self, mock_exists, MockBot, mock_input):
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.load.return_value = mock_bot_instance
        MockBot.load.return_value = mock_bot_instance

        with patch('src.bots', MagicMock(AnthropicBot=MockBot)):
            try:
                main()
            except SystemExit:
                pass

        mock_bot_instance.load.assert_called_once_with('test_load.bot')

    @patch('builtins.input', side_effect=['/auto', '3', '', '/exit'])
    @patch('src.bots.AnthropicBot')
    def test_main_auto(self, mock_bot, mock_input):
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_bot.load.return_value = mock_bot_instance  # Mock the class method
        mock_bot_instance.respond.return_value = 'Beep Boop'
        try:
            main()
        except SystemExit:
            pass
        self.assertEqual(mock_bot_instance.respond.call_count, 3)


if __name__ == '__main__':
    test_bot_content = json.dumps({'conversation': [], 'model': 'test_model',
    'name': 'TestBot'})
    with open('test_load.bot', 'w') as f:
        f.write(test_bot_content)
    unittest.main()

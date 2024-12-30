import unittest
import ast
import os
import tempfile
from bots import AnthropicBot
from bots.tools import code_tools
from bots.flows import functional_prompts as fp
import textwrap
import bots

class TestChangeLinesWithLLM(unittest.TestCase):
    def flow(self, bot, prompt):
        """Helper method to run the test flow with a given prompt"""
        print(f"\n=== Starting test with bot {bot.name} ===")
        print(f"Prompt:\n{prompt}")
        result = fp.prompt_while(
            bot,
            prompt,
            continue_prompt="ok",
            stop_condition=fp.conditions.tool_not_used
        )
        print("\nBot conversation:")
        print(bot)
        print("\nTool handler requests:", bot.tool_handler.get_requests())
        print("\nTool handler results:", bot.tool_handler.get_results())
        print("=== Test complete ===\n")
        return result
    
    @classmethod
    def setUpClass(cls):
        # Create and configure initial bot instance
        bot = AnthropicBot(name="CodeModifier", autosave=False)
        bot.add_tools(code_tools)

        # Create a temporary directory for test files
        cls.test_dir = os.path.join('tests', 'temp')
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.test_file = os.path.join(cls.test_dir, "sample.py")
        # Note: save() will append .bot to the filename, so we don't include it here
        initial_bot_file = os.path.join(cls.test_dir, "initial_bot")
        with open(cls.test_file, "w") as f:
            f.write(textwrap.dedent('''
                def greet(name: str) -> str:
                    """Returns a greeting message.

                    Args:
                        name: The name to greet

                    Returns:
                        str: A greeting message
                    """
                    return f"Hello, {name}!"

                def add_numbers(a: int, b: int) -> int:
                    """Add two numbers together.

                    Args:
                        a: First number
                        b: Second number

                    Returns:
                        int: The sum of a and b
                    """
                    return a + b

                class Calculator:
                    """A simple calculator class."""

                    def __init__(self):
                        self.history = []

                    def add(self, a: int, b: int) -> int:
                        """Add two numbers and store in history."""
                        result = a + b
                        self.history.append(f"{a} + {b} = {result}")
                        return result

                    def clear_history(self):
                        """Clear the calculation history."""
                        self.history = []

                def process_data(data: list) -> list:
                    """Process a list of data with error handling.

                    Args:
                        data: List of values to process

                    Returns:
                        list: Processed data
                    """
                    try:
                        result = [x * 2 for x in data]
                        return result
                    except TypeError:
                        return []
                '''))
        
        # Save initial bot state - note that save() will append .bot to the filename
        cls.initial_bot_file = bot.save(initial_bot_file)  # Update to use the actual saved path

    def setUp(self):
        """Load a fresh bot instance before each test"""
        pass    

    @classmethod
    def tearDownClass(cls):
        # Comment out cleanup for debugging
        # Clean up temporary files
        # os.remove(cls.test_file)
        # os.rmdir(cls.test_dir)
        pass

    def verify_file_valid(self):
        """Helper to verify file is syntactically valid Python"""
        with open(self.test_file, 'r') as f:
            content = f.read()
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False
            
    def test_modify_function_body(self):
        """Test modifying just a function body while preserving signature"""
        prompt = textwrap.dedent(f'''
            First, examine the file by running: view("{self.test_file}")
            Then, use change_lines to modify the greet function's return statement to:
                return f"Hi there!"
            ''')
        bot = bots.load(self.initial_bot_file)
        self.flow(bot, prompt)
        bot.save("tests/temp/test_modify_function_body")

        self.assertTrue(self.verify_file_valid())
        # Verify the change
        with open(self.test_file, 'r') as f:
            new_content = f.read()
        self.assertIn("Hi there!", new_content)

    def test_modify_method_implementation(self):
        """Test modifying a class method implementation"""
        prompt = textwrap.dedent(f'''
            First, examine the file by running: view("{self.test_file}")
            Then, use change_lines to modify the Calculator.add method to add a print statement before returning. The new implementation should be:
                print(f"Result: [result]")
                self.history.append(f"[a+b] = [result]")
                return result
            ''')
        bot = bots.load(self.initial_bot_file)
        self.flow(bot, prompt)
        bot.save("tests/temp/test_modify_method_implementation")

        self.assertTrue(self.verify_file_valid())
        # Verify the change
        with open(self.test_file, 'r') as f:
            new_content = f.read()
        self.assertIn("print", new_content)

    def test_modify_error_handling(self):
        """Test modifying error handling in a function"""
        prompt = textwrap.dedent(f'''
            First, examine the file by running: view("{self.test_file}")
            Then, use change_lines to modify the error handling in the process_data function. The new implementation should be:
                try:
                    result = [x * 2 for x in data]
                    return result
                except (TypeError, ValueError):
                    return None
            ''')
        bot = bots.load(self.initial_bot_file)
        self.flow(bot, prompt)
        bot.save("tests/temp/test_modify_error_handling")

        self.assertTrue(self.verify_file_valid())
        # Verify the change
        with open(self.test_file, 'r') as f:
            new_content = f.read()
        self.assertIn("ValueError", new_content)
        self.assertIn("None", new_content)

    def test_modify_docstring(self):
        """Test modifying a function's docstring"""
        prompt = textwrap.dedent(f'''
            First, examine the file by running: view("{self.test_file}")
            Then, use change_lines to modify the docstring of the add_numbers function. The new docstring should be:
                """Add two numbers together.

                Performs type checking to ensure both inputs are integers.
                Raises TypeError if inputs are not integers.

                Args:
                    a: First number (int)
                    b: Second number (int)

                Returns:
                    int: The sum of a and b

                Example:
                    >>> add_numbers(5, 3)
                    8
                """
            ''')
        bot = bots.load(self.initial_bot_file)
        self.flow(bot, prompt)
        bot.save("tests/temp/test_modify_docstring")

        self.assertTrue(self.verify_file_valid())
        # Verify the change
        with open(self.test_file, 'r') as f:
            new_content = f.read()
        self.assertIn("example", new_content.lower())
        self.assertIn("type", new_content.lower())

    def test_modify_single_line(self):
        """Test modifying a single line in the file"""
        prompt = textwrap.dedent(f'''
            First, examine the file by running: view("{self.test_file}")
            Then, use change_lines to modify the Calculator class docstring to:
                """A simple calculator class with history tracking."""
            ''')
        bot = bots.load(self.initial_bot_file)
        self.flow(bot, prompt)
        bot.save("tests/temp/test_modify_single_line")

        self.assertTrue(self.verify_file_valid())
        # Verify the change
        with open(self.test_file, 'r') as f:
            new_content = f.read()
        self.assertIn("history tracking", new_content)


from bots.dev.decorators import debug_on_error

@debug_on_error
def main():
    test_case = TestChangeLinesWithLLM()
    test_case.setUpClass()
    
    # Get all test method names by inspecting the class
    test_methods = [attr for attr in dir(TestChangeLinesWithLLM) 
                   if attr.startswith('test_') and callable(getattr(TestChangeLinesWithLLM, attr))]
    
    for method_name in test_methods:
        print(f"Running {method_name}")
        test_case.setUp()
        method = getattr(test_case, method_name)
        method()  # Now we know it's actually a method
        test_case.tearDown()
    
    test_case.tearDownClass()


if __name__ == '__main__':
    unittest.main()
    #main()
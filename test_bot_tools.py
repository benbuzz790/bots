
import importlib
import bot_tools
importlib.reload(bot_tools)
import unittest
import os
import sys
import traceback

#TODO update to use custom assert
#TODO fix issue with f_locals and traceback

class DetailedTestCase(unittest.TestCase):
    def assertEqualWithDetails(self, first, second, msg=None):
        try:
            self.assertEqual(first, second, msg)
        except AssertionError as e:
            tb = sys.exc_info()[2]
            frame = tb.tb_next
            local_vars = frame.f_locals.copy()

            # Remove self from local_vars
            local_vars.pop('self', None)

            error_message = f"\nAssertion Error: {str(e)}\n"
            error_message += "\nLocal variables:\n"
            for key, value in local_vars.items():
                error_message += f"{key} = {repr(value)}\n"

            error_message += "\nTraceback:\n"
            error_message += ''.join(traceback.format_tb(tb))

            raise AssertionError(error_message)


class TestBotTools(DetailedTestCase):

    def setUp(self):
        self.test_file = 'test_file.txt'
        with open(self.test_file, 'w') as f:
            f.write('Original content\n')

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_rewrite(self):
        new_content = 'New content'
        bot_tools.rewrite(self.test_file, new_content)
        with open(self.test_file, 'r') as f:
            self.assertEqualWithDetails(f.read(), new_content,
                'Rewrite failed')

    def test_insert_after(self):
        bot_tools.insert_after(self.test_file, 'Original', ' inserted')
        with open(self.test_file, 'r') as f:
            self.assertEqualWithDetails(f.read(),
                'Original inserted content\n', 'Insert after failed')

    def test_replace_function(self):
        with open(self.test_file, 'w') as f:
            f.write(
                "def old_function():\n    print('Old implementation')\n\nother code"
                )
        new_function = (
            "def old_function():\n    print('New implementation')\n")
        bot_tools.replace(self.test_file, 'def old_function():',
            new_function)
        with open(self.test_file, 'r') as f:
            self.assertEqualWithDetails(f.read(), new_function +
                'other code', 'Replace function failed')

    def test_replace_complex(self):
        initial_content = (
            '\ndef complex_function(param1, param2):\n    \'\'\'This is a complex function with multiple lines.\'\'\'\n    result = 0\n    for i in range(param1):\n        result += i * param2\n    return result\n\nother_code = "This should remain unchanged"\n'
            )
        new_function = (
            "\ndef complex_function(param1, param2, param3):\n    '''This is an updated complex function with a new parameter.'''\n    result = 0\n    for i in range(param1):\n        result += i * param2 * param3\n    return result\n"
            )
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        bot_tools.replace(self.test_file,
            'def complex_function(param1, param2):', new_function)
        expected_content = (new_function +
            '\nother_code = "This should remain unchanged"\n')
        with open(self.test_file, 'r') as f:
            self.assertEqualWithDetails(f.read(), expected_content,
                'Replace complex function failed')

    def test_insert_after_complex(self):
        initial_content = (
            '\nclass ComplexClass:\n    def __init__(self, value):\n        self.value = value\n    \n    def method1(self):\n        return self.value * 2\n\nother_code = "This should remain unchanged"\n'
            )
        new_method = (
            "\n\n    def method2(self):\n        '''This is a new method added to the class.'''\n        return self.value ** 2\n"
            )
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        bot_tools.insert_after(self.test_file, 'class ComplexClass:',
            new_method)
        expected_content = (
            '\nclass ComplexClass:\n    def __init__(self, value):\n        self.value = value\n    \n    def method1(self):\n        return self.value * 2\n'
                + new_method +
            '\nother_code = "This should remain unchanged"\n')
        with open(self.test_file, 'r') as f:
            self.assertEqualWithDetails(f.read(), expected_content,
                'Insert after complex class failed')

if __name__ == '__main__':
    unittest.main(argv=[''], exit=False)
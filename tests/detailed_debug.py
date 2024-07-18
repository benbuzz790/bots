import unittest
import sys
import traceback
import difflib
import inspect

class DetailedTestCase(unittest.TestCase):
    def assertEqual(self, first, second, msg=None):

        try:
            super().assertEqual(first, second, msg)
        except AssertionError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            frame = exc_traceback.tb_frame.f_back
            
            if frame:
                local_vars = frame.f_locals.copy()
                local_vars.pop('self', None)
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "\nLocal variables:\n"
                for key, value in local_vars.items():
                    error_message += f"{key} = {repr(value)}\n"
                error_message += "\nTraceback:\n"
                error_message += ''.join(traceback.format_tb(exc_traceback))
                
                error_message += "\nDifference between expected and actual:\n"
                diff = difflib.unified_diff(
                    second.splitlines(keepends=True),
                    first.splitlines(keepends=True),
                    fromfile='Expected',
                    tofile='Actual',
                    n=3
                )
                error_message += ''.join(diff)
                
                error_message += "\nTest function source:\n"
                test_func = frame.f_code
                source_lines, start_line = inspect.getsourcelines(test_func)
                error_message += ''.join(f"{i+start_line}: {line}" for i, line in enumerate(source_lines))
                
            else:
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "Unable to retrieve local variables.\n"
                error_message += "\nTraceback:\n"
                error_message += ''.join(traceback.format_tb(exc_traceback))
            
            raise AssertionError(error_message)

    def assertFileContentEqual(self, file_path, expected_content, msg=None):
        with open(file_path, 'r') as f:
            actual_content = f.read()
        self.assertEqual(actual_content, expected_content, msg)

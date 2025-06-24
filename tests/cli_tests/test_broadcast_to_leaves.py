import unittest

import bots.flows.functional_prompts as fp
from bots.dev.cli import DynamicFunctionalPromptHandler
from bots.dev.decorators import debug_on_error


class TestBroadcastToLeaves(unittest.TestCase):
    def test_broadcast_to_leaves_function_exists(self):
        self.assertTrue(hasattr(fp, "broadcast_to_leaves"))
        self.assertTrue(callable(fp.broadcast_to_leaves))

    def test_broadcast_to_leaves_in_fp_functions(self):
        fp_handler = DynamicFunctionalPromptHandler()
        self.assertIn("broadcast_to_leaves", fp_handler.fp_functions)
        expected_func = fp.broadcast_to_leaves
        actual_func = fp_handler.fp_functions["broadcast_to_leaves"]
        self.assertEqual(actual_func, expected_func)


@debug_on_error
def main():
    fp_handler = DynamicFunctionalPromptHandler()
    if "broadcast_to_leaves" not in fp_handler.fp_functions:
        return
    expected_func = fp.broadcast_to_leaves
    actual_func = fp_handler.fp_functions["broadcast_to_leaves"]
    if actual_func != expected_func:
        return
    print("good")


if __name__ == "__main__":
    main()

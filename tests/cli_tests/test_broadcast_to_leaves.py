import unittest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bots.dev.cli import DynamicFunctionalPromptHandler, CLIContext
import bots.flows.functional_prompts as fp
class TestBroadcastToLeaves(unittest.TestCase):
    def test_broadcast_to_leaves_function_exists(self):
        self.assertTrue(hasattr(fp, "broadcast_to_leaves"))
        self.assertTrue(callable(fp.broadcast_to_leaves))
    def test_broadcast_to_leaves_in_fp_functions(self):
        fp_handler = DynamicFunctionalPromptHandler()
        self.assertIn("broadcast_to_leaves", fp_handler.fp_functions)
        self.assertEqual(
            fp_handler.fp_functions["broadcast_to_leaves"],
            fp.broadcast_to_leaves
        )
from bots.dev.decorators import debug_on_error

@debug_on_error
def main():
    fp_handler = DynamicFunctionalPromptHandler()
    if not "broadcast_to_leaves" in fp_handler.fp_functions:
        return
    if not fp_handler.fp_functions["broadcast_to_leaves"] == fp.broadcast_to_leaves:
        return
    print('good')


if __name__ == "__main__":
    main()

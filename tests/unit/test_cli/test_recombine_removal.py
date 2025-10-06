import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import bots.dev.cli as cli_module


class TestRecombineCommandRemoval(unittest.TestCase):
    def test_recombine_command_fails(self):
        # Test that /recombine command is not recognized and fails
        with patch("builtins.input", side_effect=["/recombine", "/exit"]):
            with StringIO() as buf, redirect_stdout(buf):
                with self.assertRaises(SystemExit):
                    cli_module.main("")
                output = buf.getvalue()
        self.assertIn("Unrecognized command", output)

    def test_combine_leaves_command_exists(self):
        # Test that /combine_leaves command exists and is recognized
        side_effects = ["Create a simple function", "/combine_leaves", "/exit"]
        with patch("builtins.input", side_effect=side_effects):
            with StringIO() as buf, redirect_stdout(buf):
                with self.assertRaises(SystemExit):
                    cli_module.main("")
                output = buf.getvalue()
        # Should not show "Unrecognized command" - instead should show
        # proper error about leaves
        self.assertNotIn("Unrecognized command", output)
        # Should show a proper error message about leaves
        has_leaf_error = "No leaves found" in output or "Need at least 2 leaves" in output
        self.assertTrue(has_leaf_error, "Expected proper combine_leaves error message")


if __name__ == "__main__":
    if os.path.exists("cli_config.json"):
        os.remove("cli_config.json")
    unittest.main()

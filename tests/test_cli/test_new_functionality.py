import os
import sys
import unittest
from unittest.mock import patch

import bots.dev.cli as cli_module

"""
Test suite for new CLI functionality implemented in the work order:
1. Descoped functions (prompt_for, par_dispatch)
2. Enhanced /leaf command (replacing /showleaves)
3. New /combine_leaves command
4. Proper broadcast_to_leaves integration
"""
# Add the parent directory to the path so we can import the CLI module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


class TestDescopedFunctions(unittest.TestCase):
    """Test that prompt_for and par_dispatch are properly excluded from CLI."""

    def setUp(self):
        """Set up test fixtures."""
        self.handler = cli_module.DynamicFunctionalPromptHandler()
        self.collector = cli_module.DynamicParameterCollector()

    def test_prompt_for_excluded_from_discovery(self):
        """Test that prompt_for is excluded from function discovery."""
        discovered_functions = self.handler.fp_functions
        self.assertNotIn(
            "prompt_for",
            discovered_functions,
            "prompt_for should be excluded from CLI interface",
        )

    def test_par_dispatch_excluded_from_discovery(self):
        """Test that par_dispatch is excluded from function discovery."""
        discovered_functions = self.handler.fp_functions
        self.assertNotIn(
            "par_dispatch",
            discovered_functions,
            "par_dispatch should be excluded from CLI interface",
        )

    def test_items_parameter_handler_shows_not_supported(self):
        """Test that items parameter handler shows not supported message."""
        with patch("builtins.print") as mock_print:
            result = self.collector._collect_items("items", None)
            self.assertIsNone(result)
            mock_print.assert_called_with("items is not supported in CLI interface")

    def test_dynamic_prompt_parameter_handler_shows_not_supported(self):
        """Test that dynamic_prompt parameter handler shows not supported."""
        with patch("builtins.print") as mock_print:
            result = self.collector._collect_dynamic_prompt("dynamic_prompt", None)
            self.assertIsNone(result)
            mock_print.assert_called_with("dynamic_prompt is not supported in CLI interface")

    def test_broadcast_to_leaves_still_included(self):
        """Test that broadcast_to_leaves is still included (not descoped)."""
        discovered_functions = self.handler.fp_functions
        self.assertIn(
            "broadcast_to_leaves",
            discovered_functions,
            "broadcast_to_leaves should be included in CLI interface",
        )


if __name__ == "__main__":
    unittest.main()

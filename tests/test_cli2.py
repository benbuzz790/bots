import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO
from cli2 import DynamicParameterCollector, DynamicFunctionalPromptHandler
import bots.flows.functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO
import cli2
from cli2 import DynamicParameterCollector, DynamicFunctionalPromptHandler
import bots.flows.functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from io import StringIO
import cli2
from cli2 import DynamicParameterCollector, DynamicFunctionalPromptHandler
import bots.flows.functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
"""
Test file for cli2.py dynamic parameter collection system.
"""
# Add the parent directory to the path so we can import cli2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDynamicParameterCollector:
    """Test the dynamic parameter collection system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = DynamicParameterCollector()

    def test_discover_fp_functions(self):
        """Test that we can discover functional prompt functions."""
        handler = DynamicFunctionalPromptHandler()
        functions = handler.fp_functions
        # Check that we found some expected functions
        expected_functions = ['chain', 'branch', 'single_prompt', 'prompt_while']
        for func_name in expected_functions:
            assert func_name in functions, f"Expected function '{func_name}' not found"
        print(f"Discovered functions: {list(functions.keys())}")

    def test_function_signature_inspection(self):
        """Test that we can properly inspect function signatures."""
        import inspect
        # Test chain function
        sig = inspect.signature(fp.chain)
        params = list(sig.parameters.keys())
        assert 'bot' in params
        assert 'prompt_list' in params
        assert 'callback' in params
        # Test prompt_while function
        sig = inspect.signature(fp.prompt_while)
        params = list(sig.parameters.keys())
        assert 'bot' in params
        assert 'first_prompt' in params
        assert 'continue_prompt' in params
        assert 'stop_condition' in params
if __name__ == "__main__":
    # Run a simple test
    test = TestDynamicParameterCollector()
    test.setup_method()
    print("Testing function discovery...")
    test.test_discover_fp_functions()
    print("\nTesting signature inspection...")
    test.test_function_signature_inspection()
    print("\nAll basic tests passed!")
"""
Test file for cli2.py dynamic parameter collection system.
"""
# Add the parent directory to the path so we can import cli2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Test file for cli2.py dynamic parameter collection system.
"""
# Add the current directory to the path so we can import cli2
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
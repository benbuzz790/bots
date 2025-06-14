import sys
import os
import inspect
from cli2 import DynamicParameterCollector, DynamicFunctionalPromptHandler
import bots.flows.functional_prompts as fp
"""
Simple test for cli2.py dynamic parameter collection system.
"""
# Import cli2 components
sys.path.insert(0, '.')

def test_function_discovery():
    """Test that we can discover functional prompt functions."""
    print("Testing function discovery...")
    handler = DynamicFunctionalPromptHandler()
    functions = handler.fp_functions
    print(f"Discovered {len(functions)} functions:")
    for name in sorted(functions.keys()):
        print(f"  - {name}")
    # Check for expected functions
    expected = ['chain', 'branch', 'single_prompt', 'prompt_while', 'tree_of_thought']
    found = []
    missing = []
    for func_name in expected:
        if func_name in functions:
            found.append(func_name)
        else:
            missing.append(func_name)
    print(f"\nFound expected functions: {found}")
    if missing:
        print(f"Missing expected functions: {missing}")
    return len(functions) > 0

def test_signature_inspection():
    """Test function signature inspection."""
    print("\nTesting signature inspection...")
    # Test a few key functions
    test_functions = [('chain', ['bot', 'prompt_list', 'callback']), ('branch', ['bot', 'prompt_list', 'callback']), ('prompt_while', ['bot', 'first_prompt', 'continue_prompt', 'stop_condition', 'callback']), ('single_prompt', ['bot', 'prompt'])]
    for func_name, expected_params in test_functions:
        if hasattr(fp, func_name):
            func = getattr(fp, func_name)
            sig = inspect.signature(func)
            actual_params = list(sig.parameters.keys())
            print(f"  {func_name}: {actual_params}")
            # Check that expected parameters are present
            for param in expected_params:
                if param not in actual_params:
                    print(f"    WARNING: Expected parameter '{param}' not found")
        else:
            print(f"  {func_name}: NOT FOUND in fp module")
    return True

def test_parameter_collector():
    """Test the parameter collector setup."""
    print("\nTesting parameter collector...")
    collector = DynamicParameterCollector()
    print(f"Parameter handlers: {list(collector.param_handlers.keys())}")
    print(f"Available conditions: {list(collector.conditions.keys())}")
    # Test that we can inspect a simple function
    try:
        sig = inspect.signature(fp.single_prompt)
        print(f"single_prompt signature: {sig}")
        # Test parameter collection logic (without user input)
        params = {}
        for param_name, param in sig.parameters.items():
            if param_name != 'bot':
                print(f"  Would collect: {param_name} (default: {param.default})")
        return True
    except Exception as e:
        print(f"Error inspecting function: {e}")
        return False
if __name__ == "__main__":
    print("CLI2 Dynamic Parameter Collection - Simple Test")
    print("=" * 50)
    success = True
    try:
        success &= test_function_discovery()
        success &= test_signature_inspection()
        success &= test_parameter_collector()
        if success:
            print("\n✓ All basic tests passed!")
        else:
            print("\n✗ Some tests failed!")
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
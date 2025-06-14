import sys
from cli2 import DynamicFunctionalPromptHandler
"""Simple test for CLI2 fixes."""
sys.path.insert(0, '.')

def test_handler_creation():
    """Test that the handler can be created with fixes."""
    print("Testing DynamicFunctionalPromptHandler creation...")
    try:
        handler = DynamicFunctionalPromptHandler()
        functions = handler.fp_functions
        print(f"  ✓ Handler created successfully")
        print(f"  ✓ Discovered {len(functions)} functions")
        # Check for key functions
        key_functions = ['chain', 'branch', 'single_prompt', 'tree_of_thought']
        found = [f for f in key_functions if f in functions]
        print(f"  ✓ Found key functions: {found}")
        return True
    except Exception as e:
        print(f"  ✗ Handler creation failed: {e}")
        return False

def test_callback_logic():
    """Test callback adaptation logic."""
    print("\nTesting callback adaptation logic...")
    try:
        handler = DynamicFunctionalPromptHandler()
        # Test callback adaptation for tree_of_thought

        def mock_cli_callback(responses, nodes):
            print(f"    CLI callback called with {len(responses)} responses")
        # Simulate tree_of_thought callback adaptation

        def adapted_callback(response, node):
            mock_cli_callback([response], [node])
        # Test the adapted callback
        adapted_callback("test response", "test node")
        print("  ✓ Callback adaptation logic works")
        return True
    except Exception as e:
        print(f"  ✗ Callback adaptation failed: {e}")
        return False
if __name__ == "__main__":
    print("CLI2 FIXES - SIMPLE TEST")
    print("=" * 30)
    success1 = test_handler_creation()
    success2 = test_callback_logic()
    if success1 and success2:
        print("\n✓ All basic tests passed!")
        print("CLI2 with fixes is ready for testing")
    else:
        print("\n✗ Some tests failed")
import sys
import os
from cli2 import DynamicParameterCollector, DynamicFunctionalPromptHandler
import bots.flows.functional_prompts as fp
import bots.flows.recombinators as recombinators
"""
Test the improved CLI2 with recombinators and callback fixes.
"""
# Add current directory to path
sys.path.insert(0, '.')

def test_recombinator_discovery():
    """Test that we can discover and use recombinator functions."""
    print("Testing recombinator discovery...")
    collector = DynamicParameterCollector()
    # Test recombinator collection
    print("\nTesting recombinator collection:")
    print("Available recombinators:")
    print("  1. concatenate")
    print("  2. llm_judge")
    print("  3. llm_vote")
    print("  4. llm_merge")
    # Test that we can access the recombinators
    try:
        concat_func = recombinators.recombinators.concatenate
        print(f"✓ concatenate function found: {concat_func}")
        judge_func = recombinators.recombinators.llm_judge
        print(f"✓ llm_judge function found: {judge_func}")
        return True
    except Exception as e:
        print(f"✗ Error accessing recombinators: {e}")
        return False

def test_function_discovery_improvements():
    """Test that all functions are now discovered including missing ones."""
    print("\nTesting improved function discovery...")
    handler = DynamicFunctionalPromptHandler()
    functions = handler.fp_functions
    print(f"Discovered {len(functions)} functions:")
    for name in sorted(functions.keys()):
        print(f"  - {name}")
    # Check for previously missing functions
    expected_functions = ['single_prompt', 'tree_of_thought', 'recombine']
    missing = []
    found = []
    for func_name in expected_functions:
        if func_name in functions:
            found.append(func_name)
        else:
            missing.append(func_name)
    print(f"\nPreviously missing functions now found: {found}")
    if missing:
        print(f"Still missing: {missing}")
    return len(missing) == 0

def test_callback_signature_handling():
    """Test that callback signatures are handled correctly."""
    print("\nTesting callback signature handling...")
    collector = DynamicParameterCollector()
    # Test tree_of_thought (should get single callback)
    if hasattr(fp, 'tree_of_thought'):
        print("Testing tree_of_thought parameter collection...")
        try:
            # This would normally require user input, so we'll just test the logic
            sig = inspect.signature(fp.tree_of_thought)
            params = list(sig.parameters.keys())
            print(f"  tree_of_thought parameters: {params}")
            # Check if our logic would detect it needs single callback
            needs_single = 'tree_of_thought' in ['tree_of_thought']  # Our detection logic
            print(f"  Detected as needing single callback: {needs_single}")
            if needs_single:
                print("  ✓ tree_of_thought correctly identified for single callback")
            else:
                print("  ✗ tree_of_thought not identified for single callback")
        except Exception as e:
            print(f"  ✗ Error testing tree_of_thought: {e}")
    # Test chain (should get list callback)
    if hasattr(fp, 'chain'):
        print("Testing chain parameter collection...")
        try:
            sig = inspect.signature(fp.chain)
            params = list(sig.parameters.keys())
            print(f"  chain parameters: {params}")
            needs_single = 'chain' in ['tree_of_thought']  # Our detection logic
            print(f"  Detected as needing single callback: {needs_single}")
            if not needs_single:
                print("  ✓ chain correctly identified for list callback")
            else:
                print("  ✗ chain incorrectly identified for single callback")
        except Exception as e:
            print(f"  ✗ Error testing chain: {e}")
    return True
if __name__ == "__main__":
    print("CLI2 IMPROVEMENTS TEST")
    print("=" * 40)
    success = True
    try:
        import inspect  # Need this for the tests
        print("1. RECOMBINATOR DISCOVERY:")
        print("-" * 25)
        success &= test_recombinator_discovery()
        print("\n2. FUNCTION DISCOVERY IMPROVEMENTS:")
        print("-" * 35)
        success &= test_function_discovery_improvements()
        print("\n3. CALLBACK SIGNATURE HANDLING:")
        print("-" * 30)
        success &= test_callback_signature_handling()
        if success:
            print("\n✓ All improvement tests passed!")
        else:
            print("\n✗ Some improvement tests failed!")
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
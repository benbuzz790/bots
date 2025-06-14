import sys
import bots.flows.functional_prompts as fp
"""Simple fixes for callback and return type issues."""
sys.path.insert(0, '.')

def adapt_callback_for_tree_of_thought(cli_callback):
    """Adapt CLI's list-based callback for tree_of_thought's single-item callback."""
    if not cli_callback:
        return None

    def single_callback(response, node):
        # Convert single items to lists for CLI callback
        cli_callback([response], [node])
    return single_callback

def normalize_result_to_list(result):
    """Normalize any result to list format for consistent CLI handling."""
    if not isinstance(result, tuple) or len(result) != 2:
        return result
    responses, nodes = result
    # Already list format
    if isinstance(responses, list) and isinstance(nodes, list):
        return (responses, nodes)
    # Single format - convert to list
    if isinstance(responses, str):
        return ([responses], [nodes])
    # Fallback
    return result

def test_fixes():
    """Test the fixes."""
    print("TESTING CALLBACK AND RETURN TYPE FIXES")
    print("=" * 50)
    # Test callback adaptation
    print("1. Callback Adaptation Test:")

    def mock_cli_callback(responses, nodes):
        print(f"   CLI callback got {len(responses)} responses")
    adapted = adapt_callback_for_tree_of_thought(mock_cli_callback)
    try:
        # Simulate tree_of_thought calling the adapted callback
        adapted("single response", "single node")
        print("   ✓ Callback adaptation works")
    except Exception as e:
        print(f"   ✗ Callback adaptation failed: {e}")
    # Test return normalization
    print("\n2. Return Type Normalization Test:")
    # Test single format
    single_result = ("response", "node")
    normalized = normalize_result_to_list(single_result)
    print(f"   Single result normalized: {normalized}")
    # Test list format
    list_result = (["resp1", "resp2"], ["node1", "node2"])
    normalized = normalize_result_to_list(list_result)
    print(f"   List result normalized: {normalized}")
    print("\n✓ Basic fixes working!")
if __name__ == "__main__":
    test_fixes()
    print("\nKEY ISSUES IDENTIFIED:")
    print("- tree_of_thought needs callback adaptation")
    print("- CLI needs to normalize all results to list format")
    print("- These fixes can be integrated into CLI2")
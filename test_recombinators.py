import sys
import os
from bots.flows.recombinators import recombinators
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import ConversationNode
"""
Test the new recombinator functions.
"""
# Add current directory to path
sys.path.insert(0, '.')

def test_concatenate():
    """Test the concatenate recombinator."""
    print("Testing concatenate recombinator...")
    responses = ["First analysis shows X", "Second analysis shows Y", "Third analysis shows Z"]
    nodes = [ConversationNode("test1", "assistant"), ConversationNode("test2", "assistant"), ConversationNode("test3", "assistant")]
    result_response, result_node = recombinators.concatenate(responses, nodes)
    print(f"Result: {result_response}")
    assert "Combined Analysis:" in result_response
    assert "Response 1:" in result_response
    assert "Response 2:" in result_response
    assert "Response 3:" in result_response
    print("✓ Concatenate test passed")

def test_llm_judge():
    """Test the LLM judge recombinator (without actually calling LLM)."""
    print("\nTesting LLM judge recombinator structure...")
    responses = ["Option A is good", "Option B is better", "Option C is best"]
    nodes = [ConversationNode("test1", "assistant"), ConversationNode("test2", "assistant"), ConversationNode("test3", "assistant")]
    # Test with empty responses
    empty_result = recombinators.llm_judge([], [])
    assert empty_result[0] == ""
    # Test with single response
    single_result = recombinators.llm_judge(["Only option"], [nodes[0]])
    assert single_result[0] == "Only option"
    print("✓ LLM judge structure test passed")

def test_llm_vote():
    """Test the LLM vote recombinator structure."""
    print("\nTesting LLM vote recombinator structure...")
    responses = ["Option A", "Option B", "Option C"]
    nodes = [ConversationNode("test1", "assistant"), ConversationNode("test2", "assistant"), ConversationNode("test3", "assistant")]
    # Test with empty responses
    empty_result = recombinators.llm_vote([], [])
    assert empty_result[0] == ""
    # Test with single response
    single_result = recombinators.llm_vote(["Only option"], [nodes[0]])
    assert single_result[0] == "Only option"
    print("✓ LLM vote structure test passed")

def test_llm_merge():
    """Test the LLM merge recombinator structure."""
    print("\nTesting LLM merge recombinator structure...")
    responses = ["Analysis A", "Analysis B", "Analysis C"]
    nodes = [ConversationNode("test1", "assistant"), ConversationNode("test2", "assistant"), ConversationNode("test3", "assistant")]
    # Test with empty responses
    empty_result = recombinators.llm_merge([], [])
    assert empty_result[0] == ""
    # Test with single response
    single_result = recombinators.llm_merge(["Only analysis"], [nodes[0]])
    assert single_result[0] == "Only analysis"
    print("✓ LLM merge structure test passed")

def test_import():
    """Test that we can import recombinators from functional_prompts."""
    print("\nTesting import from functional_prompts...")
    try:
        import bots.flows.functional_prompts as fp
        # Check that recombinators is available
        assert hasattr(fp, 'recombinators')
        assert hasattr(fp.recombinators, 'concatenate')
        assert hasattr(fp.recombinators, 'llm_judge')
        assert hasattr(fp.recombinators, 'llm_vote')
        assert hasattr(fp.recombinators, 'llm_merge')
        print("✓ Import test passed")
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False
    return True
if __name__ == "__main__":
    print("Testing Recombinator Functions")
    print("=" * 40)
    try:
        test_concatenate()
        test_llm_judge()
        test_llm_vote()
        test_llm_merge()
        success = test_import()
        if success:
            print("\n✓ All recombinator tests passed!")
        else:
            print("\n✗ Some tests failed!")
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

def test_concatenate():
    """Test the concatenate recombinator."""
    print("Testing concatenate recombinator...")
    responses = ["First analysis shows X", "Second analysis shows Y", "Third analysis shows Z"]
    nodes = [ConversationNode("test1", "assistant"), ConversationNode("test2", "assistant"), ConversationNode("test3", "assistant")]
    result_response, result_node = recombinators.concatenate(responses, nodes)
    print(f"Result: {result_response}")
    assert "Combined Analysis:" in result_response
    assert "Response 1:" in result_response
    assert "Response 2:" in result_response
    assert "Response 3:" in result_response
    print("✓ Concatenate test passed")

def test_llm_judge():
    """Test the LLM judge recombinator (without actually calling LLM)."""
    print("\nTesting LLM judge recombinator structure...")
    responses = ["Option A is good", "Option B is better", "Option C is best"]
    nodes = [ConversationNode("test1", "assistant"), ConversationNode("test2", "assistant"), ConversationNode("test3", "assistant")]
    # Test with empty responses
    empty_result = recombinators.llm_judge([], [])
    assert empty_result[0] == ""
    # Test with single response
    single_result = recombinators.llm_judge(["Only option"], [nodes[0]])
    assert single_result[0] == "Only option"
    print("✓ LLM judge structure test passed")

def test_llm_vote():
    """Test the LLM vote recombinator structure."""
    print("\nTesting LLM vote recombinator structure...")
    responses = ["Option A", "Option B", "Option C"]
    nodes = [ConversationNode("test1", "assistant"), ConversationNode("test2", "assistant"), ConversationNode("test3", "assistant")]
    # Test with empty responses
    empty_result = recombinators.llm_vote([], [])
    assert empty_result[0] == ""
    # Test with single response
    single_result = recombinators.llm_vote(["Only option"], [nodes[0]])
    assert single_result[0] == "Only option"
    print("✓ LLM vote structure test passed")

def test_llm_merge():
    """Test the LLM merge recombinator structure."""
    print("\nTesting LLM merge recombinator structure...")
    responses = ["Analysis A", "Analysis B", "Analysis C"]
    nodes = [ConversationNode("test1", "assistant"), ConversationNode("test2", "assistant"), ConversationNode("test3", "assistant")]
    # Test with empty responses
    empty_result = recombinators.llm_merge([], [])
    assert empty_result[0] == ""
    # Test with single response
    single_result = recombinators.llm_merge(["Only analysis"], [nodes[0]])
    assert single_result[0] == "Only analysis"
    print("✓ LLM merge structure test passed")
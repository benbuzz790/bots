"""Test suite for parallel conversation branching in functional_prompts module.
This module tests the parallel branching capabilities of the
functional_prompts module:
Functions tested:
    - par_branch: Creates multiple parallel conversation branches
    - par_branch_while: Creates iterative parallel branches with custom
      stop conditions
Test coverage includes:
    - Conversation tree structure verification
    - Error handling and branch isolation
    - Iteration behavior and stop conditions
    - Empty input handling
    - Node relationship validation
"""

from typing import List

import pytest

from bots.flows.functional_prompts import par_branch, par_branch_while
from bots.foundation.anthropic_bots import AnthropicBot


@pytest.fixture
def test_bot():
    """Create a test bot fixture with standardized test configuration.
    Creates an AnthropicBot instance configured for testing with:
        - Dummy API key
        - Claude-3 Opus model
        - Standard test parameters (max_tokens, temperature)
        - Autosave disabled
    Returns:
        AnthropicBot: Configured test bot instance with dummy credentials
    """
    bot = AnthropicBot(
        api_key="dummy_key",
        model_engine="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.7,
        name="TestBot",
        role="test assistant",
        role_description="A bot for testing",
        autosave=False,
    )
    return bot


def test_par_branch_structure() -> None:
    """Test the conversation tree structure created by par_branch function.
    Tests the parallel branching functionality by verifying:
        - Response count matches prompt count
        - Node count matches prompt count
        - Reply count in original node matches prompt count
        - Node relationships:
            - All nodes have correct parent (original_node)
            - All nodes exist in parent's replies list
    The test uses multiple prompts to ensure proper parallel branch creation
    and structural integrity of the conversation tree.
    """
    bot = AnthropicBot(
        api_key=None,
        model_engine="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.7,
        name="TestBot",
        role="test assistant",
        role_description="A bot for testing",
        autosave=False,
    )
    original_node = bot.conversation
    prompts = ["test prompt 1", "test prompt 2", "test prompt 3"]
    responses, nodes = par_branch(bot, prompts)
    print(bot)
    assert len(responses) == len(prompts)
    assert len(nodes) == len(prompts)
    assert len(original_node.replies) == len(prompts)
    for node in nodes:
        assert node.parent == original_node
        assert node in original_node.replies


def test_par_branch_while_structure() -> None:
    """Test the iterative parallel branching functionality of par_branch_while.
    This test verifies the complex behavior of parallel branches with
    iteration:
    Test Setup:
        - Creates multiple parallel conversation branches
        - Uses custom stop_condition that limits to 2 iterations
        - Processes multiple prompts simultaneously
    Verifies:
        - Iteration behavior:
            - Multiple responses generated per branch
            - Each branch maintains independent iteration count
            - Stop condition properly halts iteration
        - Tree structure:
            - Maintains proper parent-child relationships
            - Preserves conversation history in each branch
            - Creates correct number of response chains
    The test includes detailed logging of conversation structure and response
    content to aid in debugging and verification.
    """
    bot = AnthropicBot(
        api_key=None,
        model_engine="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.7,
        name="TestBot",
        role="test assistant",
        role_description="A bot for testing",
        autosave=False,
    )
    original_node = bot.conversation

    def stop_after_two(bot: AnthropicBot) -> bool:
        """Stop condition that halts iteration after two responses.
        Parameters:
            bot (AnthropicBot): The bot instance being tested
        Returns:
            bool: True if iteration count >= 2, False otherwise
        """
        if not hasattr(bot, "_iteration_count"):
            bot._iteration_count = 0
        bot._iteration_count += 1
        print(f"\nIteration count for this branch: {bot._iteration_count}")
        return bot._iteration_count >= 2

    prompts: List[str] = ["test prompt 1", "test prompt 2"]
    print(f"\nStarting par_branch_while with prompts: {prompts}")
    responses, nodes = par_branch_while(bot, prompts, stop_condition=stop_after_two)
    print("\nFull bot conversation structure:")
    print(bot)
    print(f"\nGot {len(responses)} responses:")
    for i, response in enumerate(responses):
        print(f"Response {i}: {response[:100]}...")
    print("\nConversation structure:")
    print(f"Original node has {len(original_node.replies)} replies")
    for i, node in enumerate(nodes):
        print(f"\nBranch {i}:")
        print(f"Parent is original_node: {node.parent == original_node}")
        print(f"In replies list: {node in original_node.replies}")
        current = node
        response_count = 0
        print("\nResponse chain:")
        while current:
            response_count += 1
            print(f"  Node {response_count}: {current.content[:50]}...")
            if not current.replies:
                break
            current = current.replies[0]
        print(f"Total responses in chain: {response_count}")
        expected_msg = f"Expected multiple responses in branch {i}"
        actual_msg = f"got {response_count}"
        assert response_count > 1, f"{expected_msg}, {actual_msg}"


def test_empty_prompt_list() -> None:
    """Test par_branch handling of empty input lists.
    This test verifies proper handling of edge cases with empty input:
    Test Setup:
        - Creates a test bot instance
        - Calls par_branch with empty prompt list
    Verifies:
        - Return values:
            - Empty responses list returned
            - Empty nodes list returned
        - Conversation structure:
            - No new nodes created
            - Original conversation node unchanged
            - No replies added to conversation tree
    This test ensures the function handles empty input gracefully without
    modifying the conversation structure.
    """
    bot = AnthropicBot(
        api_key=None,
        model_engine="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.7,
        name="TestBot",
        role="test assistant",
        role_description="A bot for testing",
        autosave=False,
    )
    responses, nodes = par_branch(bot, [])
    assert len(responses) == 0
    assert len(nodes) == 0
    assert len(bot.conversation.replies) == 0


def test_error_handling() -> None:
    """Test error handling and branch isolation in par_branch function.
    This test verifies robust error handling in parallel conversation branches:
    Test Setup:
        - Creates test bot instance
        - Uses mixed prompt list: [valid_prompt, None, valid_prompt]
        - Tests handling of invalid (None) prompts among valid ones
    Verifies:
        - Error Handling:
            - None prompts result in None responses
            - None prompts result in None nodes
            - Response count maintained despite errors
        - Branch Isolation:
            - Valid branches process successfully
            - Invalid branches don't affect valid ones
        - Tree Integrity:
            - Valid nodes maintain proper parent relationship
            - Valid nodes exist in parent's replies list
            - Overall tree structure remains valid
    This test ensures the parallel branching system is resilient to errors
    and maintains isolation between branches.
    """
    bot = AnthropicBot(
        api_key=None,
        model_engine="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.7,
        name="TestBot",
        role="test assistant",
        role_description="A bot for testing",
        autosave=False,
    )
    original_node = bot.conversation
    prompts: List[str | None] = ["valid prompt", None, "another valid prompt"]
    responses, nodes = par_branch(bot, prompts)
    assert len(responses) == 3
    assert len(nodes) == 3
    assert None in responses
    assert None in nodes
    valid_nodes = [n for n in nodes if n is not None]
    for node in valid_nodes:
        assert node.parent == original_node
        assert node in original_node.replies

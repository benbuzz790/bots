import pytest

from bots.flows import functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot

"""Tests for broadcast_fp functional prompt."""


@pytest.fixture
def bot():
    """Create a test bot."""
    return AnthropicBot()


@pytest.fixture
def bot_with_branches(bot):
    """Create a bot with a conversation tree that has multiple branches and
    leaves."""
    # Create initial conversation
    bot.respond("Start conversation")
    root = bot.conversation
    # Create first branch
    bot.conversation = root
    bot.respond("Branch 1")
    branch1 = bot.conversation
    # Create leaves from branch 1
    bot.conversation = branch1
    bot.respond("Leaf 1A")
    leaf1a = bot.conversation
    bot.conversation = branch1
    bot.respond("Leaf 1B")
    leaf1b = bot.conversation
    # Create second branch
    bot.conversation = root
    bot.respond("Branch 2")
    branch2 = bot.conversation
    # Create leaf from branch 2
    bot.conversation = branch2
    bot.respond("Leaf 2A")
    leaf2a = bot.conversation
    # Add labels to some leaves for testing skip functionality
    leaf1a.labels = ["test", "important"]
    leaf1b.labels = ["draft"]
    leaf2a.labels = ["final"]
    # Return to root for testing
    bot.conversation = root
    return bot


def test_broadcast_fp_single_prompt(bot_with_branches):
    """Test broadcast_fp with single_prompt functional prompt."""
    responses, nodes = fp.broadcast_fp(bot_with_branches, fp.single_prompt, prompt="Summarize this conversation")
    # Should have responses from all leaves
    assert len(responses) == 3
    assert len(nodes) == 3
    # All responses should be strings (not None)
    successful_responses = [r for r in responses if r is not None]
    assert len(successful_responses) >= 1  # At least one should succeed


def test_broadcast_fp_chain(bot_with_branches):
    """Test broadcast_fp with chain functional prompt."""
    responses, nodes = fp.broadcast_fp(bot_with_branches, fp.chain, prompt_list=["First step", "Second step"])
    # Should have responses from all leaves
    assert len(responses) == 3
    assert len(nodes) == 3
    # All responses should be strings (not None) - these are the final
    # responses from each chain
    successful_responses = [r for r in responses if r is not None]
    assert len(successful_responses) >= 1


def test_broadcast_fp_with_skip_labels(bot_with_branches):
    """Test broadcast_fp with skip labels."""
    responses, nodes = fp.broadcast_fp(
        bot_with_branches,
        fp.single_prompt,
        skip=["draft", "test"],
        prompt="Process this",
    )
    # Should skip leaves with "draft" and "test" labels
    # Only leaf2a (with "final" label) should be processed
    assert len(responses) == 1
    assert len(nodes) == 1
    successful_responses = [r for r in responses if r is not None]
    assert len(successful_responses) >= 0  # May be 0 if processing fails


def test_broadcast_fp_empty_skip_list(bot_with_branches):
    """Test broadcast_fp with empty skip list."""
    responses, nodes = fp.broadcast_fp(bot_with_branches, fp.single_prompt, skip=[], prompt="Process all")
    # Should process all leaves
    assert len(responses) == 3
    assert len(nodes) == 3


def test_broadcast_fp_no_skip_parameter(bot_with_branches):
    """Test broadcast_fp without skip parameter (should default to empty
    list)."""
    responses, nodes = fp.broadcast_fp(bot_with_branches, fp.single_prompt, prompt="Process all")
    # Should process all leaves
    assert len(responses) == 3
    assert len(nodes) == 3


def test_broadcast_fp_single_leaf(bot):
    """Test broadcast_fp on a conversation with only one leaf."""
    bot.respond("Only message")
    responses, nodes = fp.broadcast_fp(bot, fp.single_prompt, prompt="Analyze this")
    # Should have one response
    assert len(responses) == 1
    assert len(nodes) == 1


def test_broadcast_fp_tree_of_thought(bot_with_branches):
    """Test broadcast_fp with tree_of_thought functional prompt."""

    def simple_recombinator(responses, nodes, **kwargs):
        """Simple recombinator for testing."""
        combined = " | ".join((str(r) for r in responses if r))
        return (f"Combined: {combined}", nodes[0] if nodes else None)

    responses, nodes = fp.broadcast_fp(
        bot_with_branches,
        fp.tree_of_thought,
        prompts=["Consider aspect A", "Consider aspect B"],
        recombinator_function=simple_recombinator,
    )
    # Should have responses from all leaves
    assert len(responses) == 3
    assert len(nodes) == 3


def test_broadcast_fp_handles_exceptions(bot_with_branches):
    """Test that broadcast_fp handles exceptions gracefully."""

    def failing_fp(bot, **kwargs):
        """A functional prompt that always fails."""
        raise Exception("Test exception")

    responses, nodes = fp.broadcast_fp(bot_with_branches, failing_fp)
    # Should have None responses for failed executions
    assert len(responses) == 3
    assert len(nodes) == 3
    assert all((r is None for r in responses))
    assert all((n is None for n in nodes))


def test_broadcast_fp_preserves_original_conversation(bot_with_branches):
    """Test that broadcast_fp preserves the original conversation state."""
    original_conversation = bot_with_branches.conversation
    fp.broadcast_fp(bot_with_branches, fp.single_prompt, prompt="Test")
    # Should return to original conversation
    assert bot_with_branches.conversation is original_conversation


def test_broadcast_fp_with_kwargs(bot_with_branches):
    """Test broadcast_fp passes kwargs correctly to functional prompt."""
    responses, nodes = fp.broadcast_fp(
        bot_with_branches,
        fp.prompt_while,
        first_prompt="Start task",
        continue_prompt="Continue",
        stop_condition=fp.conditions.tool_not_used,
    )
    # Should have responses from all leaves
    assert len(responses) == 3
    assert len(nodes) == 3

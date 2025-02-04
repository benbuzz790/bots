import pytest
from bots.foundation.base import Bot, ConversationNode
from bots.flows.functional_prompts import par_branch, par_branch_while, conditions
from bots.foundation.anthropic_bots import AnthropicBot, AnthropicNode


@pytest.fixture
def test_bot():
    bot = AnthropicBot(api_key='dummy_key', model_engine=
        'claude-3-opus-20240229', max_tokens=1000, temperature=0.7, name=
        'TestBot', role='test assistant', role_description='A bot for testing')
    return bot


def test_par_branch_structure():
    """Test that par_branch creates correct conversation tree structure"""
    bot = AnthropicBot(api_key=None, model_engine='claude-3-opus-20240229',
        max_tokens=1000, temperature=0.7, name='TestBot', role=
        'test assistant', role_description='A bot for testing')
    original_node = bot.conversation
    prompts = ['test prompt 1', 'test prompt 2', 'test prompt 3']
    responses, nodes = par_branch(bot, prompts)
    assert len(responses) == len(prompts)
    assert len(nodes) == len(prompts)
    assert len(original_node.replies) == len(prompts)
    for node in nodes:
        assert node.parent == original_node
        assert node in original_node.replies


def test_par_branch_while_structure():
    """Test that par_branch_while creates correct conversation tree structure"""
    bot = AnthropicBot(api_key=None, model_engine='claude-3-opus-20240229',
        max_tokens=1000, temperature=0.7, name='TestBot', role=
        'test assistant', role_description='A bot for testing')
    original_node = bot.conversation

    def stop_after_two(bot):
        if not hasattr(bot, '_iteration_count'):
            bot._iteration_count = 0
        bot._iteration_count += 1
        print(f'\nIteration count for this branch: {bot._iteration_count}')
        return bot._iteration_count >= 2
    prompts = ['test prompt 1', 'test prompt 2']
    print(f'\nStarting par_branch_while with prompts: {prompts}')
    responses, nodes = par_branch_while(bot, prompts, stop_condition=
        stop_after_two)
    print('\nFull bot conversation structure:')
    print(bot)
    print(f'\nGot {len(responses)} responses:')
    for i, response in enumerate(responses):
        print(f'Response {i}: {response[:100]}...')
    print(f'\nConversation structure:')
    print(f'Original node has {len(original_node.replies)} replies')
    for i, node in enumerate(nodes):
        print(f'\nBranch {i}:')
        print(f'Parent is original_node: {node.parent == original_node}')
        print(f'In replies list: {node in original_node.replies}')
        current = node
        response_count = 0
        print('\nResponse chain:')
        while current:
            response_count += 1
            print(f'  Node {response_count}: {current.content[:50]}...')
            if not current.replies:
                break
            current = current.replies[0]
        print(f'Total responses in chain: {response_count}')
        assert response_count > 1, f'Expected multiple responses in branch {i}, got {response_count}'


def test_empty_prompt_list():
    """Test behavior with empty prompt list"""
    bot = AnthropicBot(api_key=None, model_engine='claude-3-opus-20240229',
        max_tokens=1000, temperature=0.7, name='TestBot', role=
        'test assistant', role_description='A bot for testing')
    responses, nodes = par_branch(bot, [])
    assert len(responses) == 0
    assert len(nodes) == 0
    assert len(bot.conversation.replies) == 0


def test_error_handling():
    """Test that errors in one branch don't affect others"""
    bot = AnthropicBot(api_key=None, model_engine='claude-3-opus-20240229',
        max_tokens=1000, temperature=0.7, name='TestBot', role=
        'test assistant', role_description='A bot for testing')
    original_node = bot.conversation
    prompts = ['valid prompt', None, 'another valid prompt']
    responses, nodes = par_branch(bot, prompts)
    assert len(responses) == 3
    assert len(nodes) == 3
    assert None in responses
    assert None in nodes
    valid_nodes = [n for n in nodes if n is not None]
    for node in valid_nodes:
        assert node.parent == original_node
        assert node in original_node.replies

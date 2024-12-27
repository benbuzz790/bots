import os
import tempfile
import inspect
import math
from bots.foundation.base import Bot, Engines, ModuleContext
from bots.foundation.anthropic_bots import AnthropicBot, AnthropicToolHandler
from types import ModuleType


def simple_add(x, y):
    """Simple addition function"""
    return str(int(x) + int(y))


def test_multiple_save_load_cycles():
    """Test multiple save/load cycles with tool usage"""
    temp_dir = tempfile.mkdtemp()
    try:
        bot = AnthropicBot(name='TestClaude', model_engine=Engines.
            CLAUDE35_SONNET_20240620, api_key=None, max_tokens=1000,
            temperature=0.7, role='assistant', role_description=
            'A helpful AI assistant')
        bot.tool_handler = AnthropicToolHandler()
        bot.add_tool(simple_add)
        original_tool_count = len(bot.tool_handler.tools)
        print(f'Original tool count: {original_tool_count}')
        print('\nFirst cycle...')
        result1 = bot.tool_handler.function_map['simple_add']('5', '3')
        print(f'First result: {result1}')
        save_path1 = os.path.join(temp_dir, 'cycle1_TestClaude')
        bot.save(save_path1)
        loaded1 = Bot.load(save_path1 + '.bot')
        assert len(loaded1.tool_handler.tools
            ) == original_tool_count, 'Tool count mismatch after first load'
        print('\nSecond cycle...')
        result2 = loaded1.tool_handler.function_map['simple_add']('10', '15')
        print(f'Second result: {result2}')
        save_path2 = os.path.join(temp_dir, 'cycle2_TestClaude')
        loaded1.save(save_path2)
        loaded2 = Bot.load(save_path2 + '.bot')
        assert len(loaded2.tool_handler.tools
            ) == original_tool_count, 'Tool count mismatch after second load'
        print('\nThird cycle...')
        result3 = loaded2.tool_handler.function_map['simple_add']('7', '8')
        print(f'Third result: {result3}')
        save_path3 = os.path.join(temp_dir, 'cycle3_TestClaude')
        loaded2.save(save_path3)
        loaded3 = Bot.load(save_path3 + '.bot')
        assert len(loaded3.tool_handler.tools
            ) == original_tool_count, 'Tool count mismatch after third load'
        print('\nVerifying results...')
        assert result1 == '8', f'Expected 8, got {result1}'
        assert result2 == '25', f'Expected 25, got {result2}'
        assert result3 == '15', f'Expected 15, got {result3}'
        print('\nVerifying tool handler state...')
        print(f'Original tools: {bot.tool_handler.tools}')
        print(f'Final tools: {loaded3.tool_handler.tools}')
        assert bot.tool_handler.tools == loaded3.tool_handler.tools, "Tool schemas don't match"
        assert bot.tool_handler.function_map.keys(
            ) == loaded3.tool_handler.function_map.keys(
            ), "Function maps don't match"
        final_result = loaded3.tool_handler.function_map['simple_add']('20',
            '22')
        assert final_result == '42', f'Expected 42, got {final_result}'
        print('All tests passed!')
    finally:
        for file in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, file))
            except PermissionError:
                print(f'Warning: Could not remove {file}')
        try:
            os.rmdir(temp_dir)
        except OSError as e:
            print(f'Warning: Could not remove temp dir: {e}')

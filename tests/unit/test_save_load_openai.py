import json
import os
import shutil
import tempfile

import pytest

import bots.tools.python_editing_tools as python_editing_tools
from bots.foundation.base import Bot, Engines
from bots.foundation.openai_bots import ChatGPT_Bot

"""Test module for OpenAI bot persistence functionality.

This module contains tests that verify the save/load capabilities of
OpenAI-based bots,
ensuring proper persistence of:
- Bot configuration and attributes
- Conversation history and structure
- Tool definitions and execution results
- Custom attributes and state

The tests cover various scenarios including:
- Basic save/load operations
- Conversation preservation
- Tool handling across save/load cycles
- Error handling for corrupted saves
- Working directory independence
"""


pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set - skipping OpenAI integration tests"
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not clean up {temp_dir}: {e}")


@pytest.fixture
def bot():
    """Create a test bot instance."""
    bot = ChatGPT_Bot(name="TestGPT", model_engine=Engines.GPT35TURBO)
    yield bot
    # Clean up any .bot files that might have been created in current directory
    import glob

    for bot_file in glob.glob("*.bot"):
        try:
            if os.path.exists(bot_file):
                os.unlink(bot_file)
                print(f"Cleaned up bot file: {bot_file}")
        except Exception as e:
            print(f"Warning: Could not clean up {bot_file}: {e}")
    # Clean up any specific test files that might be created
    cleanup_files = ["CICD.bot", "Claude.bot", "TestGPT.bot", "TestBotOpenAI.bot"]
    for cleanup_file in cleanup_files:
        try:
            if os.path.exists(cleanup_file):
                os.unlink(cleanup_file)
                print(f"Cleaned up: {cleanup_file}")
        except Exception as e:
            print(f"Warning: Could not clean up {cleanup_file}: {e}")


def test_basic_save_load(bot, temp_dir):
    """Test basic bot attribute preservation during save and load operations.

    Verifies that fundamental bot attributes are correctly preserved:
    - name
    - model engine
    - max tokens
    - temperature
    - role
    - role description
    """
    save_path = os.path.join(temp_dir, bot.name)
    save_path = bot.save(save_path)
    loaded_bot = Bot.load(save_path)
    assert bot.name == loaded_bot.name
    assert bot.model_engine == loaded_bot.model_engine
    assert bot.max_tokens == loaded_bot.max_tokens
    assert bot.temperature == loaded_bot.temperature
    assert bot.role == loaded_bot.role
    assert bot.role_description == loaded_bot.role_description


def test_save_load_after_conversation(bot, temp_dir):
    """Test conversation history preservation during save and load.

    Verifies that the complete conversation history, including:
    - Message content
    - Conversation structure
    - Node count
    is preserved when saving and loading a bot that has had multiple
    interactions.
    """
    bot.respond("Hello, how are you?")
    bot.respond("What's the weather like today?")
    bot.respond("Thank you for the information.")
    save_path = os.path.join(temp_dir, f"convo_{bot.name}")
    save_path = bot.save(save_path)
    loaded_bot = Bot.load(save_path)
    assert bot.conversation._node_count() == loaded_bot.conversation._node_count()
    assert bot.conversation.content == loaded_bot.conversation.content


def test_tool_execution_results(bot, temp_dir):
    """Test preservation of tool execution results in conversation nodes.

    Verifies that:
    - Tool execution results are properly stored in conversation nodes
    - Results persist through save/load operations
    - Result values remain accessible and accurate
    """
    bot.add_tools(_simple_addition)
    bot.respond("What is 2 + 3?")
    assert bot.conversation.parent.tool_results, (
        "Expected tool_results after asking '2 + 3' but got empty list. " "The API may not have called the tool."
    )
    assert any(
        ("5" in str(v) for v in bot.conversation.parent.tool_results[0].values())
    ), f"Expected '5' in tool results but got: {bot.conversation.parent.tool_results}"

    save_path = os.path.join(temp_dir, f"tool_exec_{bot.name}")
    save_path = bot.save(save_path)
    loaded_bot = Bot.load(save_path)

    assert loaded_bot.conversation.parent.tool_results, "Expected tool_results after loading but got empty list."
    assert any(
        ("5" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())
    ), f"Expected '5' in loaded bot tool results but got: {loaded_bot.conversation.parent.tool_results}"


def test_save_load_with_tool_use(bot, temp_dir):
    """Test comprehensive tool functionality preservation across save/load cycles.

    Verifies that:
    - Tools remain functional after save/load operations
    - Multiple tool executions are preserved correctly
    - Tool results are maintained in conversation nodes
    - New tool executions work correctly after loading
    """
    bot.add_tools(_simple_addition)
    interactions = ["What is 5 + 3?", "Can you add 10 and 20?", "Please add 7 and 15"]
    for query in interactions:
        _ = bot.respond(query)

    assert bot.conversation.parent.tool_results, (
        "Expected tool_results after asking '7 + 15' but got empty list. " "The API may not have called the tool."
    )
    assert any(
        ("22" in str(v) for v in bot.conversation.parent.tool_results[0].values())
    ), f"Expected '22' in tool results but got: {bot.conversation.parent.tool_results}"

    save_path = os.path.join(temp_dir, f"tool_use_{bot.name}")
    save_path = bot.save(save_path)
    loaded_bot = Bot.load(save_path)
    loaded_bot.save(save_path + "2")

    assert len(bot.tool_handler.tools) == len(loaded_bot.tool_handler.tools)
    assert loaded_bot.conversation.parent.tool_results, "Expected tool_results after loading but got empty list."
    assert any(
        ("22" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())
    ), f"Expected '22' in loaded bot tool results but got: {loaded_bot.conversation.parent.tool_results}"

    new_response = loaded_bot.respond("What is 25 + 17?")
    assert new_response is not None
    assert loaded_bot.conversation.parent.tool_results, (
        "Expected tool_results after asking '25 + 17' (after load) but got empty list. "
        "The API may not have called the tool."
    )
    assert any(
        ("42" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())
    ), f"Expected '42' in tool results but got: {loaded_bot.conversation.parent.tool_results}"


def test_module_tool_persistence(bot, temp_dir):
    """Test persistence of module-based tools through multiple save/load cycles.

    Verifies that:
    - Module tools are correctly preserved across multiple save/load operations
    - Tool count remains consistent
    - Function names are preserved
    - Functions remain callable after multiple cycles
    - Tool functionality remains intact
    """
    bot.add_tools(python_editing_tools)
    initial_tool_count = len(bot.tool_handler.tools)
    initial_function_names = set(bot.tool_handler.function_map.keys())
    save_path1 = os.path.join(temp_dir, f"module_tools_1_{bot.name}")
    bot.save(save_path1)
    loaded_bot1 = Bot.load(save_path1 + ".bot")
    assert initial_tool_count == len(loaded_bot1.tool_handler.tools)
    assert initial_function_names == set(loaded_bot1.tool_handler.function_map.keys())
    save_path2 = os.path.join(temp_dir, f"module_tools_2_{bot.name}")
    loaded_bot1.save(save_path2)
    loaded_bot2 = Bot.load(save_path2 + ".bot")
    assert initial_tool_count == len(loaded_bot2.tool_handler.tools)
    assert initial_function_names == set(loaded_bot2.tool_handler.function_map.keys())
    for func_name in initial_function_names:
        assert callable(
            loaded_bot2.tool_handler.function_map[func_name]
        ), f"Function {func_name} is not callable after two save/load cycles"


@pytest.mark.flaky(reruns=2, reruns_delay=1)
def test_save_load_empty_bot(temp_dir):
    """Test saving and loading a bot with no conversation history.

    Verifies that:
    - Empty bots can be saved and loaded correctly
    - Initial conversation state is properly initialized
    - Root node properties are correct
    - Bot remains functional after loading
    - Conversation structure develops correctly after loading

    Note: This test makes actual API calls and may be flaky due to:
    - API rate limiting
    - Network issues
    - API service availability
    """
    fresh_bot = ChatGPT_Bot(name="TestGPT", model_engine=Engines.GPT35TURBO)
    save_path = os.path.join(temp_dir, f"empty_{fresh_bot.name}")
    save_path = fresh_bot.save(save_path)
    loaded_bot = Bot.load(save_path)
    assert loaded_bot.conversation is not None

    # Check initial state - must use root for node count
    root = loaded_bot.conversation._find_root()
    assert root._node_count() == 1, "Expected only root node initially"
    assert root.role == "empty"
    assert root.content == ""
    assert len(root.replies) == 0

    response = loaded_bot.respond("Hello!")
    assert response is not None
    assert len(response) > 0

    # Check final state - must use root for node count
    root = loaded_bot.conversation._find_root()
    assert root._node_count() == 3, "Expected root node + user message + assistant response (3 nodes total)"
    assert len(root.replies) == 1, "Root should have one reply"
    user_message = root.replies[0]
    assert user_message.role == "user"
    assert user_message.content == "Hello!"
    assert len(user_message.replies) == 1, "User message should have one reply"
    assistant_response = user_message.replies[0]
    assert assistant_response.role == "assistant"
    assert len(assistant_response.content) > 0


def test_save_load_with_file_tools(bot, temp_dir):
    """Test saving and loading bots with file-based tools.

    Verifies that:
    - Tools loaded from files are correctly preserved
    - Tool attributes (name, parameters, return types) remain intact
    - Function objects maintain their type after loading
    - Tool functionality remains consistent
    """
    tool_file_path = "bots/tools/python_editing_tools.py"
    bot.add_tools(tool_file_path)
    save_path = os.path.join(temp_dir, f"file_tool_{bot.name}")
    save_path = bot.save(save_path)
    loaded_bot = Bot.load(save_path)
    assert len(bot.tool_handler.tools) == len(loaded_bot.tool_handler.tools)
    for original_tool, loaded_tool in zip(bot.tool_handler.tools, loaded_bot.tool_handler.tools):
        assert original_tool.get("name") == loaded_tool.get("name")
        assert original_tool.get("parameters") == loaded_tool.get("parameters")
        assert original_tool.get("returns", {}).get("type") == loaded_tool.get("returns", {}).get("type")
        assert original_tool.get("type") == loaded_tool.get("type")
        if "function" in original_tool and "function" in loaded_tool:
            assert type(original_tool["function"]) is type(loaded_tool["function"])


def test_save_load_with_module_tools(bot, temp_dir):
    """Test saving and loading bots with module-based tools.

    Verifies that:
    - Tools loaded from modules are correctly preserved
    - Tool count remains consistent
    - Tool attributes (name, parameters, return types) remain intact
    - Tool functionality is preserved after loading
    """
    bot.add_tools(python_editing_tools)
    save_path = os.path.join(temp_dir, f"module_tool_{bot.name}")
    save_path = bot.save(save_path)
    loaded_bot = Bot.load(save_path)
    assert len(bot.tool_handler.tools) == len(loaded_bot.tool_handler.tools)
    for original_tool, loaded_tool in zip(bot.tool_handler.tools, loaded_bot.tool_handler.tools):
        assert original_tool.get("name") == loaded_tool.get("name")
        assert original_tool.get("parameters") == loaded_tool.get("parameters")
        assert original_tool.get("returns", {}).get("type") == loaded_tool.get("returns", {}).get("type")
        assert original_tool.get("type") == loaded_tool.get("type")


def test_custom_attributes(bot, temp_dir):
    """Test preservation of custom bot attributes during save/load operations.

    Verifies that:
    - Custom attributes of various types (str, int, dict) are preserved
    - Data types remain consistent after loading
    - Non-existent attributes raise appropriate errors
    - Attribute values remain accurate
    """
    bot.custom_attr1 = "Test Value"
    bot.custom_attr2 = 42
    bot.custom_attr3 = {"key": "value"}
    save_path = os.path.join(temp_dir, f"custom_attr_{bot.name}")
    save_path = bot.save(save_path)
    loaded_bot = Bot.load(save_path)
    assert bot.custom_attr1 == loaded_bot.custom_attr1
    assert bot.custom_attr2 == loaded_bot.custom_attr2
    assert bot.custom_attr3 == loaded_bot.custom_attr3
    assert isinstance(loaded_bot.custom_attr1, str)
    assert isinstance(loaded_bot.custom_attr2, int)
    assert isinstance(loaded_bot.custom_attr3, dict)
    with pytest.raises(AttributeError):
        _ = loaded_bot.non_existent_attr


def test_file_creation(bot, temp_dir):
    """Test bot save file creation and naming conventions.

    Verifies that:
    - Save files are created in the specified location
    - File extension (.bot) is correctly appended
    - Both explicit and automatic path generation work
    - Files are actually created on disk
    """
    save_path = os.path.join(temp_dir, f"explicit_{bot.name}")
    actual_path = bot.save(save_path)
    assert os.path.exists(actual_path)
    assert actual_path == save_path + ".bot"
    auto_path = bot.save()
    assert os.path.exists(auto_path)
    assert auto_path.endswith(".bot")


def test_corrupted_save(bot, temp_dir):
    """Test handling of corrupted save files.

    Verifies that:
    - Invalid JSON content raises JSONDecodeError
    - Invalid model configurations raise ValueError
    - Error handling is consistent and appropriate
    """
    save_path = os.path.join(temp_dir, f"corrupted_{bot.name}.bot")
    bot.save(save_path[:-4])
    with open(save_path, "w") as f:
        f.write('{"invalid": "json')
    with pytest.raises(json.JSONDecodeError):
        Bot.load(save_path)
    with open(save_path, "w") as f:
        f.write('{"name": "test", "model_engine": "invalid-model"}')
    with pytest.raises(ValueError):
        Bot.load(save_path)


def test_working_directory_independence(bot, temp_dir):
    """Test bot save/load operations from different working directories.

    Verifies that:
    - Bots can be saved and loaded from different working directories
    - Tool results state is maintained correctly
    - Relative paths work properly
    - File operations are path-independent
    """
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir, exist_ok=True)
    bot.add_tools(_simple_addition)
    original_path = os.path.join(temp_dir, f"original_{bot.name}")
    bot.save(original_path)
    original_cwd = os.getcwd()
    try:
        os.chdir(subdir)
        loaded_bot = Bot.load(os.path.join("..", f"original_{bot.name}.bot"))
        loaded_bot.respond("What is 7 + 8?")
        assert loaded_bot.conversation.parent.tool_results, (
            "Expected tool_results after asking '7 + 8' but got empty list. " "The API may not have called the tool."
        )
        assert any(
            ("15" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())
        ), f"Expected '15' in tool results but got: {loaded_bot.conversation.parent.tool_results}"
        new_path = os.path.join("..", f"from_subdir_{bot.name}")
        loaded_bot.save(new_path)
    finally:
        os.chdir(original_cwd)


@pytest.mark.skip(reason="Test is flaky - LLM doesn't consistently call tools as requested")
def test_mixed_tool_sources(bot, temp_dir):
    """Test bot functionality with tools from multiple sources.

    Verifies that:
    - Bots can handle tools from different sources simultaneously
    - Individual function tools work correctly
    - Module-based tools work correctly
    - Tool results are preserved across save/load operations
    - Multiple tool types remain functional after loading

    Note: This test is skipped because it depends on the LLM actually
    deciding to call the tools, which is non-deterministic.
    """

    def floor_str(x) -> str:
        """Calculate the floor of a number and return it as a string.

        Use when you need to get the floor value of a decimal number as a
        string.

        Parameters:
            x (str): A string representation of a number (integer or float)

        Returns:
            str: The floor value of the input number as a string

        Example:
            >>> floor_str("5.7")
            "5"
        """
        import math

        return str(math.floor(float(x)))

    bot.add_tools(_simple_addition)
    bot.add_tools(floor_str)
    bot.add_tools(python_editing_tools)

    # First tool call: addition
    bot.respond("What is 3 + 4?")
    assert bot.conversation.parent.tool_results, (
        "Expected tool_results after asking '3 + 4' but got empty list. " "The API may not have called the tool."
    )
    assert any(
        ("7" in str(v) for v in bot.conversation.parent.tool_results[0].values())
    ), f"Expected '7' in tool results but got: {bot.conversation.parent.tool_results}"

    # Second tool call: floor
    bot.respond("What is the floor of 7.8?")
    assert bot.conversation.parent.tool_results, (
        "Expected tool_results after asking 'floor of 7.8' but got empty list. " "The API may not have called the tool."
    )
    assert any(
        ("7" in str(v) for v in bot.conversation.parent.tool_results[0].values())
    ), f"Expected '7' in tool results but got: {bot.conversation.parent.tool_results}"

    # Save and load
    save_path = os.path.join(temp_dir, f"mixed_tools_{bot.name}")
    bot.save(save_path)
    loaded_bot = Bot.load(save_path + ".bot")

    # Third tool call: addition after load
    loaded_bot.respond("What is 8 + 9?")
    assert loaded_bot.conversation.parent.tool_results, (
        "Expected tool_results after asking '8 + 9' (after load) but got empty list. " "The API may not have called the tool."
    )
    assert any(
        ("17" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())
    ), f"Expected '17' in tool results but got: {loaded_bot.conversation.parent.tool_results}"

    # Fourth tool call: floor after load
    loaded_bot.respond("What is the floor of 5.6?")
    assert loaded_bot.conversation.parent.tool_results, (
        "Expected tool_results after asking 'floor of 5.6' (after load) but got empty list. "
        "The API may not have called the tool."
    )
    assert any(
        ("5" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())
    ), f"Expected '5' in tool results but got: {loaded_bot.conversation.parent.tool_results}"


def _simple_addition(x: str, y: str) -> str:
    """Add two numbers and return the result as a string.

    Use when you need to perform basic addition with string conversion
    handling.

    Parameters:
        x (str): First number as a string
        y (str): Second number as a string

    Returns:
        str: The sum of x and y as a string, or error message if conversion
        fails

    Example:
        >>> _simple_addition("5", "3")
        "8"
    """
    try:
        return str(int(x) + int(y))
    except (ValueError, TypeError) as e:
        return f"Error: {str(e)}"

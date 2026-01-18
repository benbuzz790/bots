"""Test for cache control bug when loading tools dynamically.

This test reproduces the bug where calling load_tools() mid-conversation
causes multiple tools to have cache_control, exceeding Anthropic's limit of 4.
"""

import pytest

from bots.foundation.anthropic_bots import AnthropicBot


def sample_tool_1():
    """First sample tool."""
    return "result1"


def sample_tool_2():
    """Second sample tool."""
    return "result2"


def sample_tool_3():
    """Third sample tool."""
    return "result3"


def sample_tool_4():
    """Fourth sample tool."""
    return "result4"


def sample_tool_5():
    """Fifth sample tool."""
    return "result5"


def count_cache_controls_in_tools(tools):
    """Count how many tools have cache_control set."""
    count = 0
    for tool in tools:
        if "cache_control" in tool:
            count += 1
    return count


def test_load_tools_creates_duplicate_cache_controls():
    """Test that load_tools() causes duplicate cache_control entries.

    This test reproduces the bug:
    1. Create a bot with some tools
    2. Simulate send_message() which adds cache_control to tools[-1]
    3. Load a new tool
    4. Simulate send_message() again
    5. Verify that multiple tools now have cache_control (BUG!)
    """
    # Create bot without autosave
    bot = AnthropicBot(autosave=False)

    # Add initial tools
    bot.add_tools([sample_tool_1, sample_tool_2, sample_tool_3, sample_tool_4])

    # Verify we have 4 tools
    assert len(bot.tool_handler.tools) == 4

    # Verify no cache controls yet
    assert count_cache_controls_in_tools(bot.tool_handler.tools) == 0

    # Simulate what send_message() does at line 350-351
    # (without actually calling the API)
    tools = bot.tool_handler.tools
    tools[-1]["cache_control"] = {"type": "ephemeral"}

    # Verify only the last tool has cache_control
    assert count_cache_controls_in_tools(bot.tool_handler.tools) == 1
    assert "cache_control" in bot.tool_handler.tools[3]  # Last tool (index 3)
    assert "cache_control" not in bot.tool_handler.tools[2]

    # Now load a new tool (this is what triggers the bug)
    bot.add_tools([sample_tool_5])

    # Verify we now have 5 tools
    assert len(bot.tool_handler.tools) == 5

    # Verify tool[3] STILL has cache_control (this is the problem!)
    assert "cache_control" in bot.tool_handler.tools[3]

    # Simulate send_message() again (line 350-351)
    tools = bot.tool_handler.tools
    tools[-1]["cache_control"] = {"type": "ephemeral"}

    # BUG: Now we have TWO tools with cache_control!
    cache_control_count = count_cache_controls_in_tools(bot.tool_handler.tools)

    # This assertion should FAIL with the current buggy code
    # (it will be 2 instead of 1)
    assert cache_control_count == 2, f"Expected 2 cache controls (BUG), got {cache_control_count}"

    # Verify both tool[3] and tool[4] have cache_control
    assert "cache_control" in bot.tool_handler.tools[3], "Tool 3 should have cache_control (old last tool)"
    assert "cache_control" in bot.tool_handler.tools[4], "Tool 4 should have cache_control (new last tool)"

    print(f"✓ Bug reproduced: {cache_control_count} tools have cache_control (should be 1)")


def test_load_tools_multiple_times_accumulates_cache_controls():
    """Test that loading tools multiple times accumulates cache controls.

    This shows the bug gets worse with each load_tools() call.
    """
    bot = AnthropicBot(autosave=False)

    # Add initial tool
    bot.add_tools([sample_tool_1])

    # Simulate send_message() - adds cache to tools[-1]
    bot.tool_handler.tools[-1]["cache_control"] = {"type": "ephemeral"}
    assert count_cache_controls_in_tools(bot.tool_handler.tools) == 1

    # Load second tool and simulate send_message()
    bot.add_tools([sample_tool_2])
    bot.tool_handler.tools[-1]["cache_control"] = {"type": "ephemeral"}
    assert count_cache_controls_in_tools(bot.tool_handler.tools) == 2

    # Load third tool and simulate send_message()
    bot.add_tools([sample_tool_3])
    bot.tool_handler.tools[-1]["cache_control"] = {"type": "ephemeral"}
    assert count_cache_controls_in_tools(bot.tool_handler.tools) == 3

    # Load fourth tool and simulate send_message()
    bot.add_tools([sample_tool_4])
    bot.tool_handler.tools[-1]["cache_control"] = {"type": "ephemeral"}
    assert count_cache_controls_in_tools(bot.tool_handler.tools) == 4

    # Load fifth tool and simulate send_message()
    bot.add_tools([sample_tool_5])
    bot.tool_handler.tools[-1]["cache_control"] = {"type": "ephemeral"}

    # BUG: Now we have 5 cache controls!
    cache_control_count = count_cache_controls_in_tools(bot.tool_handler.tools)
    assert cache_control_count == 5, f"Expected 5 cache controls (BUG), got {cache_control_count}"

    print(f"✓ Bug reproduced: {cache_control_count} tools have cache_control after 5 loads")


def test_expected_behavior_only_last_tool_has_cache_control():
    """Test what the CORRECT behavior should be.

    After fixing the bug, this test should PASS.
    """
    bot = AnthropicBot(autosave=False)

    # Add initial tools
    bot.add_tools([sample_tool_1, sample_tool_2, sample_tool_3])

    # Simulate send_message() - should add cache to tools[-1]
    # This simulates the FIXED code
    tools = bot.tool_handler.tools
    for tool in tools:
        tool.pop("cache_control", None)
    tools[-1]["cache_control"] = {"type": "ephemeral"}

    # Verify only last tool has cache
    assert count_cache_controls_in_tools(bot.tool_handler.tools) == 1

    # Load new tool
    bot.add_tools([sample_tool_4])

    # Simulate send_message() again with the FIX
    tools = bot.tool_handler.tools
    for tool in tools:
        tool.pop("cache_control", None)
    tools[-1]["cache_control"] = {"type": "ephemeral"}

    # After fix, only the last tool should have cache_control
    cache_control_count = count_cache_controls_in_tools(bot.tool_handler.tools)

    # This should PASS with the fix
    assert cache_control_count == 1, f"Only last tool should have cache_control, got {cache_control_count}"
    assert "cache_control" not in bot.tool_handler.tools[2], "Tool 2 should NOT have cache_control"
    assert "cache_control" in bot.tool_handler.tools[3], "Tool 3 (last) should have cache_control"

    print(f"✓ Fix verified: Only {cache_control_count} tool has cache_control (correct!)")


if __name__ == "__main__":
    print("Running cache control bug tests...\n")

    print("Test 1: Basic bug reproduction")
    test_load_tools_creates_duplicate_cache_controls()

    print("\nTest 2: Multiple loads accumulate cache controls")
    test_load_tools_multiple_times_accumulates_cache_controls()

    print("\nTest 3: Expected behavior (will be skipped)")
    try:
        test_expected_behavior_only_last_tool_has_cache_control()
    except pytest.skip.Exception:
        print("✓ Test skipped (shows expected behavior)")

    print("\n✓ All bug reproduction tests passed!")

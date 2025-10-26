"""
Test to replicate the branch_self PowerShell bug.

The issue: When branch_self creates a branch and that branch tries to use
execute_powershell, it fails with "PowerShellManager not being defined".

FINDINGS:
---------
test_branch_self_tool_isolation() passes, which shows:
1. Tools ARE properly saved and loaded with Bot.save()/Bot.load()
2. PowerShellManager CAN be instantiated in the loaded bot context
3. The bug is NOT in the serialization/deserialization of tools

HYPOTHESIS:
-----------
The error "PowerShellManager not being defined" suggests that when the tool
function is actually EXECUTED (not just loaded) inside a branch, there may be
an issue with:
- Module imports within the tool function's execution context
- The way toolified functions are called in branches
- Namespace pollution or isolation in threaded/branched execution

The error message from the original issue was:
"Tool Failed: Tool execution interrupted"

This suggests it's not a simple NameError but potentially:
- An exception during tool execution that's being caught and re-raised
- A threading/execution context issue
- A problem with how the PowerShellManager singleton works across branches

NEXT STEPS:
-----------
To truly replicate the bug, we need to:
1. Actually call branch_self (not just Bot.load)
2. Have that branch execute execute_powershell
3. Observe the full error trace

This requires API calls, so should be run with pytest and credentials.
"""

import os


import pytest

from bots import AnthropicBot


def test_branch_self_powershell_bug():
    """
    Reproduce the bug where execute_powershell fails inside a branch_self branch.

    Steps:
    1. Create a bot with execute_powershell tool
    2. Call branch_self with a prompt that uses execute_powershell
    3. Observe the error about PowerShellManager

    This test uses Haiku to keep costs low.
    """
    import bots.tools.self_tools
    import bots.tools.terminal_tools

    # Create a bot with the terminal tools (includes execute_powershell)
    bot = AnthropicBot(model_engine="claude-3-5-haiku-latest", max_tokens=4000, temperature=0.0)
    bot.add_tools(bots.tools.terminal_tools, bots.tools.self_tools)

    # Give it an initial prompt
    response = bot.respond("Hello, I'm ready for testing")
    print(f"\nInitial response: {response[:200]}...")

    # Now call branch_self with a task that uses PowerShell
    # Use a simple echo command that should complete quickly
    response = bot.respond(
        'Use branch_self with allow_work=True and this prompt: ["Use execute_powershell to run: Write-Output test123"]'
    )

    print("\n=== FIRST RESPONSE TEXT ===")
    print(response)

    print("\n=== FIRST NODE INFO ===")
    print(f"Role: {bot.conversation.role}")
    print(f"Has tool_calls: {hasattr(bot.conversation, 'tool_calls') and len(bot.conversation.tool_calls) > 0}")
    print(f"Has tool_results: {hasattr(bot.conversation, 'tool_results') and len(bot.conversation.tool_results) > 0}")

    if hasattr(bot.conversation, "tool_calls"):
        print(f"Tool calls: {[tc.get('name') for tc in bot.conversation.tool_calls]}")

    # The LLM response with tool call doesn't automatically get tool results
    # We need to continue the conversation for the tool to execute and return results
    print("\n=== SENDING 'OK' TO CONTINUE ===")
    response2 = bot.respond("ok")

    print("\n=== SECOND RESPONSE TEXT ===")
    print(response2)

    print("\n=== SECOND NODE TOOL_RESULTS ===")
    if hasattr(bot.conversation, "tool_results"):
        print(f"Found {len(bot.conversation.tool_results)} tool results")
        for i, result in enumerate(bot.conversation.tool_results):
            content = result.get("content", "")
            print(f"\n--- Tool Result {i} ---")
            print(content[:1000])

    print("\n=== CHECKING FOR BUG ===")

    # Collect all text
    tool_result_text = ""
    if hasattr(bot.conversation, "tool_results"):
        for result in bot.conversation.tool_results:
            tool_result_text += str(result.get("content", ""))

    # Check parent node too (where branch_self was called)
    parent_tool_results = ""
    if bot.conversation.parent and hasattr(bot.conversation.parent, "tool_results"):
        for result in bot.conversation.parent.tool_results:
            parent_tool_results += str(result.get("content", ""))
            print("\n--- Parent Tool Result ---")
            print(result.get("content", "")[:1000])

    all_text = response + response2 + tool_result_text + parent_tool_results

    # Check for the bug patterns
    if "0/1" in all_text and ("failed" in all_text.lower() or "error" in all_text.lower()):
        print("\nâœ“ BUG REPRODUCED: branch_self reported 0/1 branches succeeded")
        pytest.fail("Bug reproduced: branch_self failed - 0/1 branches succeeded")
    elif "PowerShellManager" in all_text and "not being defined" in all_text:
        print("\nâœ“ BUG REPRODUCED: PowerShellManager not being defined error")
        pytest.fail("Bug reproduced: PowerShellManager not being defined")
    elif "Tool Failed" in all_text:
        print("\nâœ“ BUG REPRODUCED: Tool Failed error")
        print(f"Error text: {all_text[:1000]}")
        pytest.fail("Bug reproduced: Tool Failed error")
    elif "test123" in all_text:
        print("\nâœ— NO BUG: PowerShell executed successfully and returned 'test123'")
    else:
        print("\n? UNCLEAR: No clear error or success indicator")
        print(f"All text (first 1000 chars): {all_text[:1000]}")


def test_branch_self_tool_isolation():
    """
    Test whether tools loaded in the parent bot are accessible in branches.

    This is a simpler test that checks if the tooling infrastructure
    is properly set up in branches.

    RESULT: PASSES - Tools are properly serialized and PowerShellManager can be instantiated.
    """
    import bots.tools.self_tools
    import bots.tools.terminal_tools

    bot = AnthropicBot(model_engine="claude-3-5-haiku-latest", max_tokens=1000, temperature=0.0)
    bot.add_tools(bots.tools.terminal_tools)
    bot.add_tools(bots.tools.self_tools)

    # Check that bot has the tools
    tool_names = [tool.get("name") for tool in bot.tool_handler.tools]
    print(f"\nParent bot tools: {tool_names}")

    assert "execute_powershell" in tool_names, "execute_powershell not found in parent bot"
    assert "branch_self" in tool_names, "branch_self not found in parent bot"

    # Save the bot
    temp_file = "test_branch_tool_isolation.bot"
    bot.respond("Initial message")
    bot.save(temp_file)

    try:
        # Load the bot (simulating what branch_self does)
        from bots.foundation.base import Bot

        loaded_bot = Bot.load(temp_file)

        # Check if loaded bot has the tools
        loaded_tool_names = [tool.get("name") for tool in loaded_bot.tool_handler.tools]
        print(f"Loaded bot tools: {loaded_tool_names}")

        assert "execute_powershell" in loaded_tool_names, "Bug found: execute_powershell not available in loaded bot"

        # Try to access the PowerShellManager from the loaded bot's context
        # This simulates what happens when execute_powershell is called
        from bots.tools.terminal_tools import PowerShellManager

        # This should work - PowerShellManager should be importable
        manager = PowerShellManager.get_instance("test_branch")
        print(f"\nPowerShellManager instance created: {manager}")
        print(f"Manager bot_id: {manager.bot_id}")

        manager.cleanup()

        print("\nTest passed - tools are accessible in loaded bot")

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    print("Running test_branch_self_tool_isolation...")
    test_branch_self_tool_isolation()
    print("\n" + "=" * 60)
    print("\nNote: test_branch_self_powershell_bug requires API calls")
    print("and would need to be run with pytest and proper credentials")

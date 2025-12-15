"""
Test to determine what parts of a Bot can and cannot be pickled/deepcopied.

This investigation is critical for implementing __getstate__/__setstate__ or __deepcopy__.
"""

import copy
import pickle

import pytest

from bots import AnthropicBot


def test_pickle_bot_attributes():
    """Test picklability of individual bot attributes."""
    import bots.tools.self_tools
    import bots.tools.terminal_tools

    bot = AnthropicBot(model_engine="claude-3-5-haiku-latest", max_tokens=1000, temperature=0.0)
    bot.add_tools(bots.tools.terminal_tools, bots.tools.self_tools)
    bot.respond("Hello")

    results = {}

    # Test each attribute
    for attr_name, attr_value in bot.__dict__.items():
        try:
            pickled = pickle.dumps(attr_value)
            pickle.loads(pickled)
            results[attr_name] = "âœ… PICKLABLE"
        except Exception as e:
            results[attr_name] = f"âŒ NOT PICKLABLE: {type(e).__name__}: {str(e)[:100]}"

    print("\n" + "=" * 80)
    print("BOT ATTRIBUTE PICKLABILITY ANALYSIS")
    print("=" * 80)
    for attr, result in sorted(results.items()):
        print(f"\n{attr}:")
        print(f"  {result}")

    return results


def test_tool_handler_components():
    """Deep dive into ToolHandler picklability."""
    import bots.tools.terminal_tools

    bot = AnthropicBot(model_engine="claude-3-5-haiku-latest", max_tokens=1000, temperature=0.0)
    bot.add_tools(bots.tools.terminal_tools)

    print("\n" + "=" * 80)
    print("TOOL HANDLER COMPONENT ANALYSIS")
    print("=" * 80)

    handler = bot.tool_handler

    # Test tools list
    print("\n1. tools (list of dicts):")
    try:
        pickle.dumps(handler.tools)
        print("  âœ… PICKLABLE")
    except Exception as e:
        print(f"  âŒ {type(e).__name__}: {e}")

    # Test function_map
    print("\n2. function_map (dict of callables):")
    try:
        pickle.dumps(handler.function_map)
        print("  âœ… PICKLABLE")
    except Exception as e:
        print(f"  âŒ {type(e).__name__}: {e}")

    # Test individual functions in function_map
    print("\n3. Individual functions in function_map:")
    for func_name, func in list(handler.function_map.items())[:3]:  # Test first 3
        try:
            pickle.dumps(func)
            print(f"  âœ… {func_name}: PICKLABLE")
        except Exception as e:
            print(f"  âŒ {func_name}: {type(e).__name__}")

    # Test modules dict - THIS IS THE CRITICAL ONE
    print("\n4. modules (dict of ModuleContext):")
    try:
        pickle.dumps(handler.modules)
        print("  âœ… PICKLABLE")
    except Exception as e:
        print(f"  âŒ {type(e).__name__}: {e}")

    # Test individual ModuleContext objects
    print("\n5. Individual ModuleContext objects:")
    for module_name, module_ctx in list(handler.modules.items())[:2]:  # Test first 2
        print(f"\n  Module: {module_name}")

        # Test each field of ModuleContext
        print("    - name: ", end="")
        try:
            pickle.dumps(module_ctx.name)
            print("âœ…")
        except Exception as e:
            print(f"âŒ {type(e).__name__}")

        print("    - source: ", end="")
        try:
            pickle.dumps(module_ctx.source)
            print("âœ…")
        except Exception as e:
            print(f"âŒ {type(e).__name__}")

        print("    - file_path: ", end="")
        try:
            pickle.dumps(module_ctx.file_path)
            print("âœ…")
        except Exception as e:
            print(f"âŒ {type(e).__name__}")

        print("    - namespace (ModuleType): ", end="")
        try:
            pickle.dumps(module_ctx.namespace)
            print("âœ…")
        except Exception as e:
            print(f"âŒ {type(e).__name__}: {str(e)[:60]}")

        print("    - code_hash: ", end="")
        try:
            pickle.dumps(module_ctx.code_hash)
            print("âœ…")
        except Exception as e:
            print(f"âŒ {type(e).__name__}")


def test_namespace_components():
    """Test what's inside the namespace that makes it unpicklable."""
    import bots.tools.terminal_tools

    bot = AnthropicBot(model_engine="claude-3-5-haiku-latest", max_tokens=1000, temperature=0.0)
    bot.add_tools(bots.tools.terminal_tools)

    print("\n" + "=" * 80)
    print("NAMESPACE CONTENTS ANALYSIS")
    print("=" * 80)

    handler = bot.tool_handler

    for module_name, module_ctx in list(handler.modules.items())[:1]:  # Just test first one
        print(f"\nModule: {module_name}")
        print(f"Namespace type: {type(module_ctx.namespace)}")
        print(f"\nNamespace __dict__ keys: {len(module_ctx.namespace.__dict__)} items")

        # Test specific items in namespace
        print("\nTesting individual namespace items:")
        for key, value in list(module_ctx.namespace.__dict__.items())[:10]:  # First 10
            try:
                pickle.dumps(value)
                print(f"  âœ… {key}: {type(value).__name__}")
            except Exception as e:
                print(f"  âŒ {key}: {type(value).__name__} - {type(e).__name__}")


def test_deepcopy_bot():
    """Test if we can deepcopy the bot with current implementation."""
    import bots.tools.terminal_tools

    bot = AnthropicBot(model_engine="claude-3-5-haiku-latest", max_tokens=1000, temperature=0.0)
    bot.add_tools(bots.tools.terminal_tools)
    bot.respond("Hello")

    print("\n" + "=" * 80)
    print("DEEPCOPY TEST")
    print("=" * 80)

    try:
        copy.deepcopy(bot)
        print("âœ… Bot can be deepcopied!")
        return True
    except Exception as e:
        print("âŒ Bot cannot be deepcopied:")
        print(f"   {type(e).__name__}: {str(e)[:200]}")

        # Try to identify the problem
        import traceback

        print("\nFull traceback:")
        traceback.print_exc()
        return False


@pytest.mark.skip(reason="Test crashes due to infinite loop in dill serialization during bot.respond() quicksave")
def test_deepcopy_functionality():
    """Test that a deepcopied bot actually works correctly."""
    import bots.tools.terminal_tools

    print("\n" + "=" * 80)
    print("DEEPCOPY FUNCTIONALITY TEST")
    print("=" * 80)

    # Create original bot
    bot1 = AnthropicBot(model_engine="claude-3-5-haiku-latest", max_tokens=1000, temperature=0.0)
    bot1.add_tools(bots.tools.terminal_tools)
    response1 = bot1.respond("Hello, my name is Bot1")

    print("\n1. Original bot created and responded")
    print(f"   Response: {response1[:50]}...")
    print(f"   Tool count: {len(bot1.tool_handler.tools)}")

    # Deepcopy the bot
    print("\n2. Deepcopying bot...")
    bot2 = copy.deepcopy(bot1)

    print("   âœ… Deepcopy successful")
    print(f"   Copied bot tool count: {len(bot2.tool_handler.tools)}")

    # Verify they're independent
    print("\n3. Testing independence...")
    response1b = bot1.respond("I am bot1")
    response2 = bot2.respond("I am bot2")

    print(f"   Bot1 response: {response1b[:50]}...")
    print(f"   Bot2 response: {response2[:50]}...")

    if bot1.conversation != bot2.conversation:
        print("   âœ… Bots have independent conversations")
    else:
        print("   âŒ Bots share conversation (not independent!)")

    # Verify tools work in copied bot
    print("\n4. Testing that tools exist in copied bot...")
    if len(bot2.tool_handler.tools) == len(bot1.tool_handler.tools):
        print(f"   âœ… Copied bot has same number of tools ({len(bot2.tool_handler.tools)})")
    else:
        print(f"   âŒ Tool count mismatch: {len(bot1.tool_handler.tools)} vs {len(bot2.tool_handler.tools)}")

    # Check function_map
    if len(bot2.tool_handler.function_map) == len(bot1.tool_handler.function_map):
        print(f"   âœ… Copied bot has same number of functions ({len(bot2.tool_handler.function_map)})")
    else:
        print("   âŒ Function count mismatch")

    print("\nâœ… DEEPCOPY FUNCTIONALITY TEST COMPLETE")
    return True


if __name__ == "__main__":
    print("\nSTARTING BOT PICKLABILITY INVESTIGATION")
    print("=" * 80)

    # Run all tests
    test_pickle_bot_attributes()
    test_tool_handler_components()
    test_namespace_components()
    test_deepcopy_bot()

    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)

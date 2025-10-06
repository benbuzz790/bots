import pytest

pytestmark = pytest.mark.unit


"""
Test file to verify MockBot implementation works correctly.
Run this to ensure all components are functioning as expected.
"""

import sys


def test_mock_bot_basic():
    """Test basic MockBot functionality."""
    print("Testing basic MockBot functionality...")

    try:
        from bots.testing import MockBot

        # Create a mock bot
        bot = MockBot(name="TestBot")
        bot.set_response_pattern("Hello, {user_input}!")

        # Test basic response
        response = bot.respond("world")
        expected = "Hello, world!"

        assert response == expected, f"Expected '{expected}', got '{response}'"
        assert bot.get_response_count() == 1, f"Expected 1 response, got {bot.get_response_count()}"

        print("✓ Basic MockBot functionality works!")
        return True

    except Exception as e:
        print(f"✗ Basic MockBot test failed: {e}")
        return False


def test_mock_tool_handler():
    """Test MockToolHandler functionality."""
    print("Testing MockToolHandler functionality...")

    try:
        from bots.testing import MockBot

        # Create bot with tools
        bot = MockBot()
        bot.add_mock_tool("test_tool")
        bot.set_tool_response("test_tool", "Mock tool result")

        # Simulate tool usage
        bot.tool_handler.add_request({"name": "test_tool", "parameters": {"arg": "value"}})
        results = bot.tool_handler.exec_requests()

        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        assert results[0]["status"] == "success", f"Expected success status, got {results[0]['status']}"

        # Check call history
        history = bot.get_tool_call_history()
        assert len(history) == 1, f"Expected 1 call in history, got {len(history)}"
        assert history[0]["tool_name"] == "test_tool", f"Expected 'test_tool', got {history[0]['tool_name']}"

        print("✓ MockToolHandler functionality works!")
        return True

    except Exception as e:
        print(f"✗ MockToolHandler test failed: {e}")
        return False


def test_mock_mailbox():
    """Test MockMailbox functionality."""
    print("Testing MockMailbox functionality...")

    try:
        from bots.testing import MockBot

        bot = MockBot()
        bot.set_response_pattern("You said: '{user_input}' (call #{call_count})")

        # Test multiple responses
        response1 = bot.respond("first")
        response2 = bot.respond("second")

        assert "first" in response1, f"Expected 'first' in response1: {response1}"
        assert "second" in response2, f"Expected 'second' in response2: {response2}"
        assert "call #0" in response1, f"Expected 'call #0' in response1: {response1}"
        assert "call #1" in response2, f"Expected 'call #1' in response2: {response2}"

        print("✓ MockMailbox functionality works!")
        return True

    except Exception as e:
        print(f"✗ MockMailbox test failed: {e}")
        return False


def test_conversation_node():
    """Test MockConversationNode functionality."""
    print("Testing MockConversationNode functionality...")

    try:
        from bots.testing import MockConversationNode

        # Create conversation
        root = MockConversationNode._create_empty()
        user_msg = root._add_reply(content="Hello", role="user")
        user_msg._add_reply(content="Hi there!", role="assistant")

        # Test counting
        user_count = root.count_nodes_with_role("user")
        assistant_count = root.count_nodes_with_role("assistant")

        assert user_count == 1, f"Expected 1 user message, got {user_count}"
        assert assistant_count == 1, f"Expected 1 assistant message, got {assistant_count}"

        # Test content search
        matches = root.find_nodes_with_content("Hello")
        assert len(matches) == 1, f"Expected 1 match for 'Hello', got {len(matches)}"

        # Test metadata
        user_msg.set_test_metadata("test_key", "test_value")
        assert user_msg.get_test_metadata("test_key") == "test_value"

        print("✓ MockConversationNode functionality works!")
        return True

    except Exception as e:
        print(f"✗ MockConversationNode test failed: {e}")
        return False


def test_utility_functions():
    """Test utility functions."""
    print("Testing utility functions...")

    try:
        from bots.testing import (
            MockBot,
            assert_conversation_flow,
            create_mock_bot_with_tools,
            create_test_conversation,
        )

        # Test conversation creation
        conversation = create_test_conversation([("user", "Hello"), ("assistant", "Hi there!")])

        messages = conversation._build_messages()
        assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"

        # Test bot with tools creation
        bot = create_mock_bot_with_tools(
            [{"name": "tool1", "response": "result1"}, {"name": "tool2", "should_fail": True, "error_message": "Tool failed"}]
        )

        assert len(bot.tool_handler.tools) == 2, f"Expected 2 tools, got {len(bot.tool_handler.tools)}"

        # Test conversation flow assertion
        test_bot = MockBot()
        test_bot.respond("Hello")

        try:
            assert_conversation_flow(test_bot, [{"role": "user", "content": "Hello"}, {"role": "assistant"}])
            print("✓ Conversation flow assertion works!")
        except AssertionError:
            print("✗ Conversation flow assertion failed")
            return False

        print("✓ Utility functions work!")
        return True

    except Exception as e:
        print(f"✗ Utility functions test failed: {e}")
        return False


def test_failure_modes():
    """Test failure simulation."""
    print("Testing failure modes...")

    try:
        from bots.testing import MockBot

        bot = MockBot()
        bot.set_failure_mode(True, "Simulated failure")

        try:
            bot.respond("Hello")
            print("✗ Expected failure but got response")
            return False
        except Exception as e:
            if "Simulated failure" in str(e):
                print("✓ Failure mode works!")
                return True
            else:
                print(f"✗ Wrong error message: {e}")
                return False

    except Exception as e:
        print(f"✗ Failure mode test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 50)
    print("Running MockBot Implementation Tests")
    print("=" * 50)

    tests = [
        test_mock_bot_basic,
        test_mock_tool_handler,
        test_mock_mailbox,
        test_conversation_node,
        test_utility_functions,
        test_failure_modes,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        print()

    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)

    if failed == 0:
        print("🎉 All tests passed! MockBot implementation is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

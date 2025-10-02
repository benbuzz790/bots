"""
Test to verify the CLI tool crash bug fix works correctly.
"""

from unittest.mock import Mock

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines


def crashing_tool(message: str) -> str:
    """A tool that always crashes to simulate the bug scenario."""
    raise Exception("Simulated tool crash!")


def working_tool(message: str) -> str:
    """A tool that works normally."""
    return f"Echo: {message}"


class TestCLIToolCrashBugFix:
    """Test class to verify the CLI tool crash bug fix."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bot = AnthropicBot(
            api_key="test-key",
            model_engine=Engines.CLAUDE3_HAIKU,
            max_tokens=1000,
            temperature=0.0,
            name="TestBot",
            role="assistant",
            role_description="Test bot",
        )

        # Add both working and crashing tools
        self.bot.add_tools(working_tool, crashing_tool)

    def test_tool_handler_clear_prevents_corruption(self):
        """Test that clearing tool handler prevents corruption after crashes."""

        # Initial state should be clean
        assert len(self.bot.tool_handler.requests) == 0
        assert len(self.bot.tool_handler.results) == 0

        # Simulate a tool request that will crash
        mock_response = Mock()
        mock_response.content = [Mock(type="tool_use", id="tool_123", name="crashing_tool", input={"message": "test"})]

        # Extract requests and execute (will create error results)
        _ = self.bot.tool_handler.extract_requests(mock_response)
        _ = self.bot.tool_handler.exec_requests()

        print("After first tool execution:")
        print(f"  Requests: {len(self.bot.tool_handler.requests)}")
        print(f"  Results: {len(self.bot.tool_handler.results)}")

        # Simulate what the fixed CLI does - clear the tool handler
        self.bot.tool_handler.clear()

        print("After tool handler clear:")
        print(f"  Requests: {len(self.bot.tool_handler.requests)}")
        print(f"  Results: {len(self.bot.tool_handler.results)}")

        # Verify clean state
        assert len(self.bot.tool_handler.requests) == 0
        assert len(self.bot.tool_handler.results) == 0

        # Try another tool request - should work cleanly
        mock_response2 = Mock()
        mock_response2.content = [Mock(type="tool_use", id="tool_456", name="working_tool", input={"message": "hello"})]

        _ = self.bot.tool_handler.extract_requests(mock_response2)
        _ = self.bot.tool_handler.exec_requests()

        print("After second tool execution:")
        print(f"  Requests: {len(self.bot.tool_handler.requests)}")
        print(f"  Results: {len(self.bot.tool_handler.results)}")

        # Should have exactly 1 request and 1 result (no accumulation)
        assert len(self.bot.tool_handler.requests) == 1
        assert len(self.bot.tool_handler.results) == 1

        # Verify the tool_use_ids match
        assert self.bot.tool_handler.requests[0]["id"] == "tool_456"
        assert self.bot.tool_handler.results[0]["tool_use_id"] == "tool_456"

        print("✅ Fix verified: No corruption after tool handler clear!")

    def test_without_clear_shows_corruption(self):
        """Test that without clearing, corruption occurs (demonstrates the original bug)."""

        # Simulate the original buggy behavior (no clear)
        mock_response = Mock()
        mock_response.content = [Mock(type="tool_use", id="tool_123", name="crashing_tool", input={"message": "test"})]

        # First tool execution
        _ = self.bot.tool_handler.extract_requests(mock_response)
        _ = self.bot.tool_handler.exec_requests()

        # DON'T clear (simulating the bug)
        # self.bot.tool_handler.clear()  # This line is commented out to show the bug

        # Second tool request
        mock_response2 = Mock()
        mock_response2.content = [Mock(type="tool_use", id="tool_456", name="working_tool", input={"message": "hello"})]

        _ = self.bot.tool_handler.extract_requests(mock_response2)
        _ = self.bot.tool_handler.exec_requests()

        print("Without clear - final state:")
        print(f"  Requests: {len(self.bot.tool_handler.requests)}")
        print(f"  Results: {len(self.bot.tool_handler.results)}")

        # This demonstrates the bug: results accumulate but requests don't
        assert len(self.bot.tool_handler.requests) == 1  # extract_requests clears old requests
        assert len(self.bot.tool_handler.results) == 2  # results accumulate (THE BUG!)

        # Show the tool_use_id mismatch
        print(f"  Request tool_use_id: {self.bot.tool_handler.requests[0]['id']}")
        print(f"  Result tool_use_ids: {[r['tool_use_id'] for r in self.bot.tool_handler.results]}")

        print("🐛 Bug demonstrated: Results accumulate causing tool_use_id mismatches!")


if __name__ == "__main__":
    test = TestCLIToolCrashBugFix()
    test.setup_method()

    print("=== Testing the fix prevents corruption ===")
    test.test_tool_handler_clear_prevents_corruption()

    print("\n=== Demonstrating the original bug ===")
    test.setup_method()  # Reset for second test
    test.test_without_clear_shows_corruption()

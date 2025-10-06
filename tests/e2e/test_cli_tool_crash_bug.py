"""
Test to reproduce the CLI tool crash bug where tool request/result structure
becomes corrupt when a tool crashes and the CLI backs up.
"""

import pytest
from unittest.mock import Mock

from bots.foundation.anthropic_bots import AnthropicBot, AnthropicNode
from bots.foundation.base import Engines




pytestmark = pytest.mark.e2e

def crashing_tool(message: str) -> str:
    """A tool that always crashes to simulate the bug scenario.

    Args:
        message: Input message

    Returns:
        str: Never returns, always crashes
    """
    raise Exception("Simulated tool crash!")


def working_tool(message: str) -> str:
    """A tool that works normally.

    Args:
        message: Input message

    Returns:
        str: Echo of the input message
    """
    return f"Echo: {message}"


class TestCLIToolCrashBug:
    """Test class to reproduce and verify the CLI tool crash bug."""

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

    def test_tool_crash_corruption_scenario(self):
        """Test the scenario where a tool crash corrupts the tool request/result structure."""

        # Simulate the CLI conversation backup mechanism
        conversation_backup = self.bot.conversation

        # Create a mock response that would trigger tool usage
        mock_response = Mock()
        mock_response.content = [
            Mock(type="text", text="I'll use the crashing tool"),
            Mock(type="tool_use", id="tool_123", name="crashing_tool", input={"message": "test"}),
        ]
        mock_response.role = "assistant"

        try:
            # Simulate what happens in CLI when a tool is used
            # 1. Extract tool requests
            requests = self.bot.tool_handler.extract_requests(mock_response)
            print(f"Extracted requests: {requests}")

            # 2. Execute tool requests (this will crash)
            results = self.bot.tool_handler.exec_requests()
            print(f"Tool results: {results}")

            # 3. Check the state of tool_handler after crash
            print(f"Tool handler requests after crash: {self.bot.tool_handler.requests}")
            print(f"Tool handler results after crash: {self.bot.tool_handler.results}")

            # 4. Simulate CLI backing up to previous conversation state
            self.bot.conversation = conversation_backup

            # 5. Try to send another message - this should work but might be corrupted
            # Create another mock response for a working tool
            mock_response2 = Mock()
            mock_response2.content = [
                Mock(type="text", text="I'll use the working tool"),
                Mock(type="tool_use", id="tool_456", name="working_tool", input={"message": "hello"}),
            ]
            mock_response2.role = "assistant"

            # Extract and execute the working tool
            requests2 = self.bot.tool_handler.extract_requests(mock_response2)
            results2 = self.bot.tool_handler.exec_requests()

            print(f"Second requests: {requests2}")
            print(f"Second results: {results2}")

            # Check if the tool handler state is corrupted
            print(f"Final tool handler requests: {self.bot.tool_handler.requests}")
            print(f"Final tool handler results: {self.bot.tool_handler.results}")

            # The bug might manifest as:
            # 1. Old failed requests still in the handler
            # 2. Mismatched tool_use_ids between requests and results
            # 3. Corrupted conversation node tool_calls/tool_results

        except Exception as e:
            print(f"Exception during tool execution: {e}")

            # Check the state after exception
            print(f"Tool handler requests after exception: {self.bot.tool_handler.requests}")
            print(f"Tool handler results after exception: {self.bot.tool_handler.results}")

    def test_conversation_node_tool_state_after_crash(self):
        """Test the conversation node's tool state after a tool crash and backup."""

        # Create a conversation node with tool calls
        node = AnthropicNode(
            content="Test message",
            role="assistant",
            tool_calls=[{"id": "tool_123", "name": "crashing_tool", "input": {"message": "test"}}],
        )

        # Add tool results (this might be where corruption occurs)
        try:
            node._add_tool_results([{"tool_use_id": "tool_123", "content": "This should fail", "type": "tool_result"}])
        except Exception as e:
            print(f"Error adding tool results: {e}")

        print(f"Node tool_calls: {node.tool_calls}")
        print(f"Node tool_results: {node.tool_results}")
        print(f"Node pending_results: {node.pending_results}")

    def test_tool_handler_state_persistence(self):
        """Test if tool handler state persists incorrectly after crashes."""

        # Initial state should be clean
        assert len(self.bot.tool_handler.requests) == 0
        assert len(self.bot.tool_handler.results) == 0

        # Simulate a tool request that will crash
        mock_response = Mock()
        mock_response.content = [Mock(type="tool_use", id="tool_123", name="crashing_tool", input={"message": "test"})]

        # Extract requests
        self.bot.tool_handler.extract_requests(mock_response)
        assert len(self.bot.tool_handler.requests) == 1

        # Execute requests (will create error results)
        self.bot.tool_handler.exec_requests()
        assert len(self.bot.tool_handler.results) == 1

        # The bug might be that these don't get cleared properly
        # when the CLI backs up the conversation
        print(f"Requests after crash: {self.bot.tool_handler.requests}")
        print(f"Results after crash: {self.bot.tool_handler.results}")

        # Simulate what CLI should do - clear the tool handler state
        # self.bot.tool_handler.clear()  # This might not be called in the bug scenario

        # Try another tool request
        mock_response2 = Mock()
        mock_response2.content = [Mock(type="tool_use", id="tool_456", name="working_tool", input={"message": "hello"})]

        self.bot.tool_handler.extract_requests(mock_response2)
        self.bot.tool_handler.exec_requests()

        # Check if we have accumulated state (the bug)
        print(f"Total requests after second call: {len(self.bot.tool_handler.requests)}")
        print(f"Total results after second call: {len(self.bot.tool_handler.results)}")

        # The bug would manifest as having more than 1 request/result
        # because the old ones weren't cleared


if __name__ == "__main__":
    test = TestCLIToolCrashBug()
    test.setup_method()

    print("=== Testing tool crash corruption scenario ===")
    test.test_tool_crash_corruption_scenario()

    print("\n=== Testing conversation node tool state ===")
    test.test_conversation_node_tool_state_after_crash()

    print("\n=== Testing tool handler state persistence ===")
    test.test_tool_handler_state_persistence()

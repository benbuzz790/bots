#!/usr/bin/env python3
"""
Quick test to verify the tree serialization fix is working.
"""

import sys
import os
import asyncio
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from bot_manager import BotManager
from models import BotState, ConversationNode, Message, MessageRole


async def test_tree_serialization_fix():
    """Test that tree serialization now shows all nodes."""

    print("🔧 Testing Tree Serialization Fix")
    print("=" * 50)

    mock_responses = [
        "Hello! I'm here to help.",
        "Python has basic data types.",
        "Here are some examples.",
        "Lists are mutable, tuples are not."
    ]

    with patch('bots.foundation.anthropic_bots.AnthropicBot') as MockBot, \
         patch('bots.tools.code_tools') as mock_tools:

        mock_bot_instance = MagicMock()
        mock_bot_instance.respond = MagicMock(side_effect=mock_responses)
        mock_bot_instance.name = "Test Bot"
        MockBot.return_value = mock_bot_instance

        bot_manager = BotManager()
        bot_id = await bot_manager.create_bot("Tree Test Bot")

        print(f"✅ Created bot: {bot_id}")

        # Send 4 messages to create 8 nodes
        conversation_turns = [
            "Hello, can you help me?",
            "What are Python data types?",
            "Show me examples please.",
            "What about lists vs tuples?"
        ]

        for i, content in enumerate(conversation_turns):
            print(f"📝 Turn {i+1}: Sending message...")
            state = await bot_manager.send_message(bot_id, content)
            print(f"   📊 Conversation tree: {len(state.conversation_tree)} nodes")

            # Check tree serialization
            if state.react_flow_data:
                tree_nodes = state.react_flow_data.get('nodes', [])
                tree_edges = state.react_flow_data.get('edges', [])
                print(f"   🌳 Tree view: {len(tree_nodes)} nodes, {len(tree_edges)} edges")

                # Verify current node is marked
                current_found = False
                for node in tree_nodes:
                    if node.get('data', {}).get('isCurrent'):
                        current_found = True
                        print(f"   👉 Current node: {node['id'][:8]}...")
                        break

                if not current_found:
                    print("   ❌ No current node marked in tree!")
            else:
                print("   ❌ No react_flow_data generated!")

        # Final verification
        final_state = await bot_manager.get_bot_state(bot_id)
        print(f"\n🔍 Final Verification:")
        print(f"   📊 Conversation tree: {len(final_state.conversation_tree)} nodes")

        if final_state.react_flow_data:
            tree_nodes = final_state.react_flow_data.get('nodes', [])
            tree_edges = final_state.react_flow_data.get('edges', [])
            print(f"   🌳 Tree view: {len(tree_nodes)} nodes, {len(tree_edges)} edges")

            if len(tree_nodes) == len(final_state.conversation_tree):
                print("   ✅ Tree serialization FIXED! All nodes are now visible.")
            else:
                print(f"   ❌ Tree serialization still broken: {len(tree_nodes)} tree nodes vs {len(final_state.conversation_tree)} conversation nodes")
        else:
            print("   ❌ No react_flow_data in final state!")

        return True


if __name__ == "__main__":
    success = asyncio.run(test_tree_serialization_fix())
    print("\n✅ Tree serialization test completed!")
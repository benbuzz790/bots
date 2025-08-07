#!/usr/bin/env python3
"""
Test frontend compatibility - verify all required fields are present.
"""

import sys
import os
import asyncio
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from bot_manager import BotManager
from models import BotState, ConversationNode, Message, MessageRole


async def test_frontend_compatibility():
    """Test that all required frontend fields are present in tree data."""

    print("🔍 Testing Frontend Compatibility")
    print("=" * 50)

    # Required fields that frontend expects
    required_node_fields = [
        'role', 'content', 'preview', 'timestamp',
        'is_current', 'isCurrent',  # Both naming conventions
        'has_tool_calls', 'hasToolCalls',  # Both naming conventions
        'tool_count', 'toolCount'  # Both naming conventions
    ]

    mock_responses = ["Hello! I can help you.", "Python has data types."]

    with patch('bots.foundation.anthropic_bots.AnthropicBot') as MockBot, \
         patch('bots.tools.code_tools') as mock_tools:

        mock_bot_instance = MagicMock()
        mock_bot_instance.respond = MagicMock(side_effect=mock_responses)
        mock_bot_instance.name = "Test Bot"
        MockBot.return_value = mock_bot_instance

        bot_manager = BotManager()
        bot_id = await bot_manager.create_bot("Compatibility Test Bot")

        print(f"✅ Created bot: {bot_id}")

        # Send a couple messages
        await bot_manager.send_message(bot_id, "Hello, can you help me?")
        final_state = await bot_manager.send_message(bot_id, "What are Python data types?")

        print(f"📊 Conversation tree: {len(final_state.conversation_tree)} nodes")

        # Check tree serialization
        if not final_state.react_flow_data:
            print("❌ No react_flow_data generated!")
            return False

        tree_nodes = final_state.react_flow_data.get('nodes', [])
        tree_edges = final_state.react_flow_data.get('edges', [])

        print(f"🌳 Tree view: {len(tree_nodes)} nodes, {len(tree_edges)} edges")

        # Validate each node has all required fields
        all_fields_present = True

        for i, node in enumerate(tree_nodes):
            print(f"\n🔍 Node {i+1} ({node.get('id', 'unknown')[:8]}...):")

            node_data = node.get('data', {})
            missing_fields = []

            for field in required_node_fields:
                if field not in node_data:
                    missing_fields.append(field)
                else:
                    print(f"   ✅ {field}: {node_data[field]}")

            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                all_fields_present = False
            else:
                print(f"   ✅ All required fields present")

        # Check edge structure
        print(f"\n🔗 Edge validation:")
        required_edge_fields = ['id', 'source', 'target', 'type']

        for i, edge in enumerate(tree_edges):
            missing_edge_fields = []
            for field in required_edge_fields:
                if field not in edge:
                    missing_edge_fields.append(field)

            if missing_edge_fields:
                print(f"   ❌ Edge {i+1} missing: {missing_edge_fields}")
                all_fields_present = False
            else:
                print(f"   ✅ Edge {i+1}: {edge['source'][:8]}... → {edge['target'][:8]}...")

        # Final result
        if all_fields_present:
            print(f"\n🎉 FRONTEND COMPATIBILITY TEST PASSED!")
            print(f"   ✅ All required fields present in tree data")
            print(f"   ✅ Frontend should load without errors")
            return True
        else:
            print(f"\n❌ FRONTEND COMPATIBILITY TEST FAILED!")
            print(f"   ❌ Missing required fields - frontend will show errors")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_frontend_compatibility())
    if not success:
        print("\n❌ Frontend compatibility test failed!")
        sys.exit(1)
    print("\n✅ Frontend compatibility test passed!")
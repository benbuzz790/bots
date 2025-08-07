#!/usr/bin/env python3
"""
Test camelCase/snake_case conversion in WebSocket responses
"""

import sys
import os

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def test_field_conversion():
    """Test the field conversion function."""
    print("Testing camelCase/snake_case conversion...")

    try:
        from websocket_handler import WebSocketHandler
        from bot_manager import BotManager

        # Create handler
        manager = BotManager()
        handler = WebSocketHandler(manager)

        # Test data with snake_case fields
        test_data = {
            'id': 'test-bot-123',
            'name': 'Test Bot',
            'conversation_tree': {'node1': {'id': 'node1'}},
            'current_node_id': 'node1',
            'is_connected': True,
            'is_thinking': False,
            'react_flow_data': {'nodes': [], 'edges': []}
        }

        # Convert to camelCase
        converted = handler._convert_bot_state_for_frontend(test_data)

        print("Original keys:", list(test_data.keys()))
        print("Converted keys:", list(converted.keys()))

        # Check specific conversions
        expected_conversions = {
            'conversation_tree': 'conversationTree',
            'current_node_id': 'currentNodeId',
            'is_connected': 'isConnected',
            'is_thinking': 'isThinking',
            'react_flow_data': 'reactFlowData'
        }

        for snake_case, camel_case in expected_conversions.items():
            if snake_case in test_data:
                if camel_case in converted:
                    print(f"✅ {snake_case} -> {camel_case}")
                else:
                    print(f"❌ {snake_case} -> {camel_case} (missing)")
                    return False

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_field_conversion()
    if success:
        print("\n🎉 Field conversion test passed!")
    else:
        print("\n❌ Field conversion test failed!")
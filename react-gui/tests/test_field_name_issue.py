#!/usr/bin/env python3
"""
Test to verify the camelCase/snake_case field name issue
"""

import json

def test_field_name_conversion():
    """Test if the issue is field name casing."""
    print("🔍 Testing camelCase/snake_case field name issue")
    print("=" * 50)

    # Simulate what the backend might be sending (snake_case)
    backend_response = {
        "type": "bot_response",
        "data": {
            "botId": "test-bot-123",
            "botState": {
                "id": "test-bot-123",
                "name": "Test Bot",
                "conversation_tree": {  # snake_case - this is the problem!
                    "node1": {
                        "id": "node1",
                        "message": {"content": "Hello"},
                        "parent": None,
                        "children": [],
                        "is_current": True
                    }
                },
                "current_node_id": "node1",  # snake_case
                "is_connected": True,        # snake_case
                "is_thinking": False         # snake_case
            }
        }
    }

    # Simulate what the frontend expects (camelCase)
    frontend_expected = {
        "type": "bot_response",
        "data": {
            "botId": "test-bot-123",
            "botState": {
                "id": "test-bot-123",
                "name": "Test Bot",
                "conversationTree": {  # camelCase - what frontend expects
                    "node1": {
                        "id": "node1",
                        "message": {"content": "Hello"},
                        "parent": None,
                        "children": [],
                        "is_current": True
                    }
                },
                "currentNodeId": "node1",  # camelCase
                "isConnected": True,       # camelCase
                "isThinking": False        # camelCase
            }
        }
    }

    print("Backend sends (snake_case):")
    backend_bot_state = backend_response["data"]["botState"]
    print(f"  - conversation_tree: {type(backend_bot_state.get('conversation_tree'))}")
    print(f"  - current_node_id: {backend_bot_state.get('current_node_id')}")
    print(f"  - is_connected: {backend_bot_state.get('is_connected')}")
    print(f"  - is_thinking: {backend_bot_state.get('is_thinking')}")

    print("\nFrontend expects (camelCase):")
    frontend_bot_state = frontend_expected["data"]["botState"]
    print(f"  - conversationTree: {type(frontend_bot_state.get('conversationTree'))}")
    print(f"  - currentNodeId: {frontend_bot_state.get('currentNodeId')}")
    print(f"  - isConnected: {frontend_bot_state.get('isConnected')}")
    print(f"  - isThinking: {frontend_bot_state.get('isThinking')}")

    # Test the conversion function
    def convert_snake_to_camel(data):
        """Convert snake_case keys to camelCase."""
        field_mapping = {
            'conversation_tree': 'conversationTree',
            'current_node_id': 'currentNodeId',
            'is_connected': 'isConnected',
            'is_thinking': 'isThinking',
            'react_flow_data': 'reactFlowData'
        }
        converted = {}
        for key, value in data.items():
            converted[field_mapping.get(key, key)] = value
        return converted

    print("\nApplying conversion:")
    converted_bot_state = convert_snake_to_camel(backend_bot_state)
    print(f"  - conversationTree: {type(converted_bot_state.get('conversationTree'))}")
    print(f"  - currentNodeId: {converted_bot_state.get('currentNodeId')}")
    print(f"  - isConnected: {converted_bot_state.get('isConnected')}")
    print(f"  - isThinking: {converted_bot_state.get('isThinking')}")

    # Verify the conversion worked
    success = True
    if not isinstance(converted_bot_state.get('conversationTree'), dict):
        print("❌ conversationTree is not a dict after conversion!")
        success = False
    else:
        print("✅ conversationTree is a dict after conversion")

    if converted_bot_state.get('currentNodeId') != "node1":
        print("❌ currentNodeId not converted correctly!")
        success = False
    else:
        print("✅ currentNodeId converted correctly")

    return success

if __name__ == "__main__":
    success = test_field_name_conversion()
    if success:
        print("\n🎉 Field name conversion test passed!")
        print("The issue is likely camelCase/snake_case field name mismatch.")
        print("Solution: Ensure WebSocket responses apply field name conversion.")
    else:
        print("\n❌ Field name conversion test failed!")
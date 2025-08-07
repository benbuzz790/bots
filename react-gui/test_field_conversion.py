#!/usr/bin/env python3
"""
Test script to verify field name conversion between snake_case and camelCase.
This tests the core issue without requiring a running backend server.
"""

import sys
import os
import json
from typing import Dict, Any

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

def convert_bot_state_for_frontend(bot_state_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert bot state field names from snake_case to camelCase for frontend."""
    field_mapping = {
        'conversation_tree': 'conversationTree',
        'current_node_id': 'currentNodeId',
        'is_connected': 'isConnected',
        'is_thinking': 'isThinking',
        'react_flow_data': 'reactFlowData'
    }

    converted = {}
    for key, value in bot_state_dict.items():
        new_key = field_mapping.get(key, key)

        # Special handling for conversation_tree - convert nested ConversationNode objects
        if key == 'conversation_tree' and isinstance(value, dict):
            converted_tree = {}
            for node_id, node in value.items():
                if hasattr(node, 'dict'):
                    # Pydantic model - convert to dict
                    node_dict = node.dict()
                elif isinstance(node, dict):
                    # Already a dict
                    node_dict = node
                else:
                    # Fallback
                    node_dict = node

                # Convert node field names from snake_case to camelCase
                converted_node = {}
                node_field_mapping = {
                    'is_current': 'isCurrent',
                    'tool_calls': 'toolCalls'
                }

                for node_key, node_value in node_dict.items():
                    converted_node[node_field_mapping.get(node_key, node_key)] = node_value

                converted_tree[node_id] = converted_node
            converted[new_key] = converted_tree
        else:
            converted[new_key] = value

    return converted

def test_field_conversion():
    """Test the field conversion logic."""
    print("🧪 Testing Field Conversion Logic")
    print("=" * 50)

    # Create a mock bot state with snake_case fields
    mock_bot_state = {
        'id': 'test-bot-123',
        'name': 'Test Bot',
        'conversation_tree': {
            'node-1': {
                'id': 'node-1',
                'message': {
                    'id': 'msg-1',
                    'role': 'user',
                    'content': 'Hello',
                    'timestamp': '2024-01-01T00:00:00Z',
                    'tool_calls': []
                },
                'parent': None,
                'children': ['node-2'],
                'is_current': False
            },
            'node-2': {
                'id': 'node-2',
                'message': {
                    'id': 'msg-2',
                    'role': 'assistant',
                    'content': 'Hi there!',
                    'timestamp': '2024-01-01T00:00:01Z',
                    'tool_calls': []
                },
                'parent': 'node-1',
                'children': [],
                'is_current': True
            }
        },
        'current_node_id': 'node-2',
        'is_connected': True,
        'is_thinking': False,
        'react_flow_data': {'nodes': [], 'edges': []}
    }

    print("1. Original bot state (snake_case):")
    print(f"   - conversation_tree: {type(mock_bot_state['conversation_tree'])}")
    print(f"   - current_node_id: {mock_bot_state['current_node_id']}")
    print(f"   - is_connected: {mock_bot_state['is_connected']}")
    print(f"   - is_thinking: {mock_bot_state['is_thinking']}")

    # Test conversion
    converted = convert_bot_state_for_frontend(mock_bot_state)

    print("\n2. Converted bot state (camelCase):")
    print(f"   - conversationTree: {type(converted.get('conversationTree', 'MISSING'))}")
    print(f"   - currentNodeId: {converted.get('currentNodeId', 'MISSING')}")
    print(f"   - isConnected: {converted.get('isConnected', 'MISSING')}")
    print(f"   - isThinking: {converted.get('isThinking', 'MISSING')}")

    # Validate conversationTree structure
    conversation_tree = converted.get('conversationTree')
    if isinstance(conversation_tree, dict):
        print(f"\n3. ConversationTree validation:")
        print(f"   ✅ conversationTree is an object with {len(conversation_tree)} nodes")

        for node_id, node in conversation_tree.items():
            if not isinstance(node, dict):
                print(f"   ❌ Node {node_id} is not an object: {type(node)}")
                return False

            # Check for camelCase fields in nodes
            if 'is_current' in node:
                print(f"   ❌ Node {node_id} still has snake_case field 'is_current'")
                return False

            if 'isCurrent' not in node:
                print(f"   ❌ Node {node_id} missing camelCase field 'isCurrent'")
                return False

            print(f"   ✅ Node {node_id} has proper camelCase fields")
    else:
        print(f"   ❌ conversationTree is not an object: {type(conversation_tree)}")
        return False

    # Test WebSocket response format
    print("\n4. Testing WebSocket response format:")
    websocket_response = {
        'type': 'bot_response',
        'data': {
            'botId': 'test-bot-123',
            **converted  # This is what we're doing in the fixed WebSocket handler
        }
    }

    response_data = websocket_response['data']
    if 'conversationTree' in response_data and isinstance(response_data['conversationTree'], dict):
        print("   ✅ WebSocket response has conversationTree as object")
    else:
        print(f"   ❌ WebSocket response conversationTree issue: {type(response_data.get('conversationTree'))}")
        return False

    print("\n🎉 All field conversion tests passed!")
    print("The 'conversationTree must be an object' error should be fixed.")
    return True

if __name__ == "__main__":
    success = test_field_conversion()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test BotState creation with field aliases.
"""

import sys
import os
from datetime import datetime
import uuid

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

from models import BotState, ConversationNode, Message, MessageRole

def test_botstate_creation():
    """Test BotState creation with different approaches."""
    print("🧪 Testing BotState Creation")
    print("=" * 50)

    # Create sample conversation nodes
    user_msg_id = str(uuid.uuid4())
    bot_msg_id = str(uuid.uuid4())

    user_message = Message(
        id=user_msg_id,
        role=MessageRole.USER,
        content="Hello",
        timestamp=datetime.now().isoformat(),
        tool_calls=[]
    )

    bot_message = Message(
        id=bot_msg_id,
        role=MessageRole.ASSISTANT,
        content="Hi there!",
        timestamp=datetime.now().isoformat(),
        tool_calls=[]
    )

    user_node = ConversationNode(
        id=user_msg_id,
        message=user_message,
        parent=None,
        children=[bot_msg_id],
        is_current=False
    )

    bot_node = ConversationNode(
        id=bot_msg_id,
        message=bot_message,
        parent=user_msg_id,
        children=[],
        is_current=True
    )

    conversation_tree = {
        user_msg_id: user_node,
        bot_msg_id: bot_node
    }

    print(f"1. Created conversation tree with {len(conversation_tree)} nodes")

    # Test 1: Create BotState using field names (snake_case)
    print("2. Testing BotState creation with snake_case field names...")
    try:
        bot_state_1 = BotState(
            id="test-bot-1",
            name="Test Bot 1",
            conversation_tree=conversation_tree,
            current_node_id=bot_msg_id,
            is_connected=True,
            is_thinking=False
        )
        print(f"   ✅ Created BotState with snake_case")
        print(f"   conversation_tree size: {len(bot_state_1.conversation_tree)}")
    except Exception as e:
        print(f"   ❌ Failed with snake_case: {e}")

    # Test 2: Create BotState using aliases (camelCase)
    print("3. Testing BotState creation with camelCase aliases...")
    try:
        bot_state_2 = BotState(
            id="test-bot-2",
            name="Test Bot 2",
            conversationTree=conversation_tree,  # Using alias
            currentNodeId=bot_msg_id,           # Using alias
            isConnected=True,                   # Using alias
            isThinking=False                    # Using alias
        )
        print(f"   ✅ Created BotState with camelCase")
        print(f"   conversation_tree size: {len(bot_state_2.conversation_tree)}")
    except Exception as e:
        print(f"   ❌ Failed with camelCase: {e}")

    # Test 3: Check dict() output
    if 'bot_state_1' in locals():
        print("4. Testing dict() output...")
        state_dict = bot_state_1.dict()
        print(f"   dict() keys: {list(state_dict.keys())}")
        print(f"   conversation_tree in dict: {'conversation_tree' in state_dict}")
        print(f"   conversationTree in dict: {'conversationTree' in state_dict}")
        if 'conversation_tree' in state_dict:
            print(f"   conversation_tree size in dict: {len(state_dict['conversation_tree'])}")

    # Test 4: Check model_dump() output (Pydantic v2)
    if 'bot_state_1' in locals():
        print("5. Testing model_dump() output...")
        try:
            state_dump = bot_state_1.model_dump()
            print(f"   model_dump() keys: {list(state_dump.keys())}")
            print(f"   conversation_tree in dump: {'conversation_tree' in state_dump}")
            print(f"   conversationTree in dump: {'conversationTree' in state_dump}")
            if 'conversation_tree' in state_dump:
                print(f"   conversation_tree size in dump: {len(state_dump['conversation_tree'])}")
        except AttributeError:
            print("   model_dump() not available (Pydantic v1)")

    # Test 5: Check by_alias output
    if 'bot_state_1' in locals():
        print("6. Testing dict(by_alias=True) output...")
        try:
            state_alias_dict = bot_state_1.dict(by_alias=True)
            print(f"   dict(by_alias=True) keys: {list(state_alias_dict.keys())}")
            print(f"   conversation_tree in alias dict: {'conversation_tree' in state_alias_dict}")
            print(f"   conversationTree in alias dict: {'conversationTree' in state_alias_dict}")
            if 'conversationTree' in state_alias_dict:
                print(f"   conversationTree size in alias dict: {len(state_alias_dict['conversationTree'])}")
        except Exception as e:
            print(f"   ❌ dict(by_alias=True) failed: {e}")

    print("\n🎉 BotState creation tests completed!")
    return True

if __name__ == "__main__":
    test_botstate_creation()
#!/usr/bin/env python3
"""
Test to confirm the field name mismatch issue.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import BotState
from bot_manager import BotManager

def test_field_name_serialization():
    """Test how BotState serializes field names."""
    print("🔍 Testing Field Name Serialization")
    print("=" * 40)

    # Create a bot manager and bot
    bot_manager = BotManager()
    bot_id = bot_manager.create_bot("Test Bot")

    # Get bot state
    bot_state = bot_manager.get_bot_state(bot_id)

    # Serialize to dict (this is what WebSocket sends)
    serialized = bot_state.dict()

    print("Serialized bot state keys:")
    for key in serialized.keys():
        print(f"  - {key}")

    print(f"\nconversation_tree field:")
    print(f"  Type: {type(serialized.get('conversation_tree'))}")
    print(f"  Value: {serialized.get('conversation_tree')}")

    # Check if frontend-expected field exists
    if 'conversationTree' in serialized:
        print("✅ Frontend field 'conversationTree' found")
    else:
        print("❌ Frontend field 'conversationTree' NOT found")
        print("   This would cause 'conversationTree must be an object' error!")

    if 'conversation_tree' in serialized:
        print("✅ Backend field 'conversation_tree' found")
    else:
        print("❌ Backend field 'conversation_tree' NOT found")

    return 'conversationTree' in serialized

if __name__ == "__main__":
    success = test_field_name_serialization()
    if not success:
        print("\n🎯 FOUND THE ISSUE!")
        print("Backend uses 'conversation_tree' but frontend expects 'conversationTree'")
    exit(0 if success else 1)
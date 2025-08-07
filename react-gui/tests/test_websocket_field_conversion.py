#!/usr/bin/env python3
"""
Test WebSocket field name conversion fix.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from websocket_handler import WebSocketHandler
from bot_manager import BotManager

def test_websocket_field_conversion():
    """Test the WebSocket field name conversion."""
    print("🔧 Testing WebSocket Field Name Conversion")
    print("=" * 50)

    # Create bot manager and handler
    bot_manager = BotManager()
    ws_handler = WebSocketHandler(bot_manager)

    # Create a bot and get its state
    bot_id = bot_manager.create_bot("Test Bot")
    bot_state = bot_manager.get_bot_state(bot_id)

    # Test the original serialization
    original_dict = bot_state.dict()
    print("Original bot state fields:")
    for key in original_dict.keys():
        print(f"  - {key}")

    # Test the converted serialization
    converted_dict = ws_handler._convert_bot_state_for_frontend(original_dict)
    print("\nConverted bot state fields:")
    for key in converted_dict.keys():
        print(f"  - {key}")

    # Check for the specific field that was causing issues
    if 'conversationTree' in converted_dict:
        print("\n✅ SUCCESS: 'conversationTree' field found!")
        print(f"   Type: {type(converted_dict['conversationTree'])}")
        print(f"   Value: {converted_dict['conversationTree']}")
        return True
    else:
        print("\n❌ FAILED: 'conversationTree' field still missing!")
        return False

if __name__ == "__main__":
    success = test_websocket_field_conversion()
    if success:
        print("\n🎉 Field name conversion is working!")
        print("The 'conversationTree must be an object' error should be fixed.")
    else:
        print("\n❌ Field name conversion failed!")
    exit(0 if success else 1)
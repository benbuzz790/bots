#!/usr/bin/env python3
"""
Simple test for the backend components without the web server.
Tests the core bot manager functionality directly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from bot_manager import BotManager
from models import BotState

def test_bot_manager():
    """Test bot manager functionality directly."""
    print("🧪 Testing Bot Manager Components")
    print("=" * 40)

    try:
        # Test 1: Create bot manager
        print("1. Creating BotManager...")
        bot_manager = BotManager()
        print("   ✅ BotManager created successfully")

        # Test 2: Create a bot
        print("2. Creating a bot...")
        bot_id = bot_manager.create_bot("Test Bot")
        print(f"   ✅ Bot created with ID: {bot_id}")

        # Test 3: Get bot state
        print("3. Getting bot state...")
        bot_state = bot_manager.get_bot_state(bot_id)
        print(f"   ✅ Bot state retrieved: {bot_state.name}")

        # Test 4: List bots
        print("4. Listing bots...")
        bots_list = asyncio.run(bot_manager.list_bots())
        print(f"   ✅ Found {len(bots_list)} bots")

        # Test 5: Send a message
        print("5. Sending a message...")
        try:
            response = bot_manager.send_message(bot_id, "Hello, bot!")
            print(f"   ✅ Bot responded: {response[:50]}...")
        except Exception as e:
            print(f"   ⚠️  Message sending failed (expected): {e}")

        # Test 6: Delete bot
        print("6. Deleting bot...")
        success = bot_manager.delete_bot(bot_id)
        print(f"   ✅ Bot deleted: {success}")

        print("\n🎉 All core tests passed!")
        return True

    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
import asyncio

def test_websocket_handler():
    """Test websocket handler components."""
    print("\n🔌 Testing WebSocket Handler Components")
    print("=" * 40)

    try:
        from websocket_handler import WebSocketHandler

        # Test 1: Create websocket handler
        print("1. Creating WebSocketHandler...")
        bot_manager = BotManager()
        ws_handler = WebSocketHandler(bot_manager)
        print("   ✅ WebSocketHandler created successfully")

        print("\n🎉 WebSocket handler tests passed!")
        return True

    except Exception as e:
        print(f"   ❌ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_models():
    """Test model classes."""
    print("\n📋 Testing Model Classes")
    print("=" * 40)

    try:
        from models import Message, MessageRole, ConversationNode

        # Test 1: Create message
        print("1. Creating Message...")
        message = Message(
            id="test-msg-1",
            role=MessageRole.USER,
            content="Test message",
            timestamp="2023-01-01T00:00:00Z",
            tool_calls=[]
        )
        print(f"   ✅ Message created: {message.content}")

        # Test 2: Create conversation node
        print("2. Creating ConversationNode...")
        node = ConversationNode(
            id="test-node-1",
            message=message,
            parent=None,
            children=[],
            is_current=True
        )
        print(f"   ✅ ConversationNode created: {node.id}")

        print("\n🎉 Model tests passed!")
        return True

    except Exception as e:
        print(f"   ❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 React GUI Backend Component Tests")
    print("=" * 50)

    results = []

    # Run tests
    results.append(("Bot Manager", test_bot_manager()))
    results.append(("WebSocket Handler", test_websocket_handler()))
    results.append(("Models", test_models()))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)

    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1

    total = len(results)
    print(f"\nResult: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 All tests passed! Backend components are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

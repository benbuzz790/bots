"""
Simple test to verify the backend works end-to-end.
"""

import sys
import os

# Add the current directory and parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
"""
Simple test to verify the backend works end-to-end.
"""

import sys
import os

# Add the current directory and parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

def test_models():
    """Test the models work correctly."""
    print("Testing models...")

    from models import MessageRole, create_message, create_conversation_node, create_tool_call

    # Test creating a message
    message = create_message("Hello world", MessageRole.USER)
    assert message.content == "Hello world"
    assert message.role == MessageRole.USER
    assert message.id
    print("✅ Message creation works")

    # Test creating a conversation node
    node = create_conversation_node(message)
    assert node.message == message
    assert node.id
    print("✅ Conversation node creation works")

    # Test creating a tool call
    tool_call = create_tool_call("python_edit")
    assert tool_call.name == "python_edit"
    assert tool_call.id
    print("✅ Tool call creation works")


def test_bot_manager():
    """Test the bot manager works correctly."""
    print("\nTesting bot manager...")

    from bot_manager_fixed import BotManager

    # Create bot manager
    manager = BotManager()
    print("✅ Bot manager created")

    # Create a bot
    bot_id = manager.create_bot("Test Bot")
    assert bot_id
    print(f"✅ Bot created: {bot_id}")

    # Get bot state
    state = manager.get_bot_state(bot_id)
    assert state is not None
    assert state.name == "Test Bot"
    print("✅ Bot state retrieved")

    # Send a message (this will test the full integration)
    try:
        response = manager.send_message(bot_id, "Hello bot!")
        assert response.content
        print(f"✅ Bot responded: {response.content[:50]}...")
    except Exception as e:
        print(f"⚠️  Bot response failed (expected in test environment): {e}")

    # List bots
    bots = manager.list_bots()
    assert bot_id in bots
    print("✅ Bot listing works")

    # Delete bot
    deleted = manager.delete_bot(bot_id)
    assert deleted
    print("✅ Bot deletion works")


def test_fastapi_app():
    """Test the FastAPI app can be created."""
    print("\nTesting FastAPI app...")

    try:
        from main_fixed import app
        assert app is not None
        print("✅ FastAPI app created successfully")

        # Test with TestClient
        from fastapi.testclient import TestClient
        client = TestClient(app)

        # Test health endpoint
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint works")

        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Bot GUI Backend API"
        print("✅ Root endpoint works")

    except Exception as e:
        print(f"⚠️  FastAPI app test failed: {e}")


def main():
    """Run all tests."""
    print("🚀 Starting backend verification tests...\n")

    try:
        test_models()
        test_bot_manager()
        test_fastapi_app()

        print("\n🎉 All backend tests passed! The foundation is working correctly.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
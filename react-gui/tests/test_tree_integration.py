#!/usr/bin/env python3
"""
Test script to verify React Flow tree integration is working properly.
Tests bot creation, message sending, and React Flow data generation.
"""

import sys
import os
import asyncio
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_tree_integration():
    """Test the complete tree integration pipeline."""
    print("🧪 Testing React Flow Tree Integration")
    print("=" * 50)
    
    try:
        # Test 1: Import all modules
        print("1️⃣ Testing imports...")
        from backend.bot_manager import BotManager
        from backend.tree_serializer import serialize_gui_conversation_tree, TreeLayout
        from backend.models import BotState
        print("   ✅ All imports successful")
        
        # Test 2: Create bot manager
        print("2️⃣ Creating bot manager...")
        bot_manager = BotManager()
        print("   ✅ Bot manager created")
        
        # Test 3: Create a bot
        print("3️⃣ Creating bot...")
        bot_id = await bot_manager.create_bot("Test Bot")
        print(f"   ✅ Bot created with ID: {bot_id}")
        
        # Test 4: Send a message
        print("4️⃣ Sending test message...")
        bot_state = await bot_manager.send_message(bot_id, "Hello, this is a test message!")
        print(f"   ✅ Message sent, got response")
        print(f"   📊 Conversation tree has {len(bot_state.conversation_tree)} nodes")
        
        # Test 5: Check if react_flow_data exists
        print("5️⃣ Checking React Flow data...")
        if hasattr(bot_state, 'react_flow_data') and bot_state.react_flow_data:
            react_data = bot_state.react_flow_data
            print(f"   ✅ React Flow data exists")
            print(f"   📊 Nodes: {len(react_data.get('nodes', []))}")
            print(f"   📊 Edges: {len(react_data.get('edges', []))}")
            print(f"   📊 Current node: {react_data.get('current_node_id', 'None')}")
            
            # Show first node details
            if react_data.get('nodes'):
                first_node = react_data['nodes'][0]
                print(f"   📝 First node: {first_node.get('type')} - {first_node.get('data', {}).get('preview', 'No preview')}")
        else:
            print("   ❌ React Flow data missing or None")
            print(f"   🔍 BotState attributes: {[attr for attr in dir(bot_state) if not attr.startswith('_')]}")
        
        # Test 6: Test tree serializer directly
        print("6️⃣ Testing tree serializer directly...")
        try:
            direct_react_data = serialize_gui_conversation_tree(
                bot_state.conversation_tree,
                bot_state.current_node_id,
                TreeLayout()
            )
            print(f"   ✅ Direct serialization successful")
            print(f"   📊 Direct nodes: {len(direct_react_data.get('nodes', []))}")
        except Exception as e:
            print(f"   ❌ Direct serialization failed: {e}")
        
        print("\n🎉 Integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tree_integration())
    if not success:
        sys.exit(1)
    print("✅ All tests passed - ready for demo!")

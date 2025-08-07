"""
Corrected Bot manager service - fixes conversation tree accumulation issues.
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("Attempting to import bots framework...")

try:
    from .models import BotState, ConversationNode, Message, MessageRole, ToolCall, ToolCallStatus
    from .tree_serializer import serialize_gui_conversation_tree_fixed as serialize_gui_conversation_tree, TreeLayout
except ImportError:
    from models import BotState, ConversationNode, Message, MessageRole, ToolCall, ToolCallStatus
    from tree_serializer import serialize_gui_conversation_tree_fixed as serialize_gui_conversation_tree, TreeLayout

class BotInstance:
    """Individual bot instance with conversation state."""

    def __init__(self, bot_id: str, name: str, bot=None):
        assert isinstance(bot_id, str) and bot_id.strip(), "Bot ID must be non-empty string"
        assert isinstance(name, str) and name.strip(), "Name must be non-empty string"

        self.id = bot_id
        self.name = name
        self.bot = bot
        self.conversation_tree = {}
        self.current_node_id = None
        self.is_thinking = False

    async def send_message(self, content: str) -> str:
        """Send message to the bot."""
        assert isinstance(content, str) and content.strip(), "Content must be non-empty string"
        assert self.bot is not None, "Bot instance not initialized"

        response = self.bot.respond(content.strip())
        return response

    def get_state(self) -> Dict[str, Any]:
        """Get current bot state."""
        return {
            "id": self.id,
            "name": self.name,
            "conversation_tree": self.conversation_tree,
            "current_node_id": self.current_node_id,
            "is_connected": True,
            "is_thinking": self.is_thinking
        }
_bot_manager_instance: Optional['BotManager'] = None

def get_bot_manager() -> 'BotManager':
    """Get the global bot manager instance."""
    global _bot_manager_instance
    if _bot_manager_instance is None:
        raise RuntimeError("Bot manager not initialized. Call set_bot_manager() first.")
    return _bot_manager_instance

def set_bot_manager(manager: 'BotManager') -> None:
    """Set the global bot manager instance."""
    global _bot_manager_instance
    assert isinstance(manager, BotManager), f"Expected BotManager, got {type(manager)}"
    _bot_manager_instance = manager

class BotManager:
    """Manages bot instances with proper conversation tree accumulation."""

    def __init__(self):
        self._bots: Dict[str, Any] = {}
        self._conversation_trees: Dict[str, Dict[str, ConversationNode]] = {}
        self._current_node_ids: Dict[str, str] = {}  # Track current node for each bot
        self._bot_metadata: Dict[str, Dict[str, Any]] = {}

    def create_bot(self, name: str) -> str:
        """Create new bot instance."""
        assert isinstance(name, str), f"name must be str, got {type(name)}"
        assert name.strip(), "name cannot be empty"

        bot_id = str(uuid.uuid4())

        try:
            from bots.foundation.anthropic_bots import AnthropicBot
            import bots.tools.code_tools as code_tools

            bot = AnthropicBot()
            bot.add_tools(code_tools)
            bot.name = name.strip()
        except ImportError as e:
            logger.error(f"Failed to import bots framework: {e}")
            raise RuntimeError(f"Bots framework not available: {e}")

        self._bots[bot_id] = bot
        self._conversation_trees[bot_id] = {}
        self._current_node_ids[bot_id] = None
        self._bot_metadata[bot_id] = {
            'name': name.strip(),
            'created_at': datetime.utcnow(),
        }

        logger.info(f"Created real bot: {bot_id} ({name})")
        return bot_id

    async def send_message(self, bot_id: str, content: str) -> BotState:
        """Send message to bot and return updated state with accumulated conversation tree."""

        # Defensive validation
        assert isinstance(bot_id, str) and bot_id.strip(), "Bot ID must be non-empty string"
        assert isinstance(content, str) and content.strip(), "Content must be non-empty string"
        assert bot_id in self._bots, f"Bot {bot_id} not found"

        bot = self._bots[bot_id]
        response = bot.respond(content.strip())

        # Get existing conversation tree
        conversation_tree = self._conversation_trees[bot_id].copy()  # Copy existing tree
        current_node_id = self._current_node_ids[bot_id]

        # Generate new node IDs
        user_msg_id = str(uuid.uuid4())
        bot_msg_id = str(uuid.uuid4())

        # Create user message node
        user_message = Message(
            id=user_msg_id,
            role=MessageRole.USER,
            content=content.strip(),
            timestamp=datetime.utcnow().isoformat(),
            tool_calls=[]
        )

        # Determine parent for user message
        user_parent = current_node_id  # User message continues from current node

        user_node = ConversationNode(
            id=user_msg_id,
            message=user_message,
            parent=user_parent,
            children=[bot_msg_id],  # User message leads to bot response
            is_current=False
        )

        # Create bot response node
        bot_message = Message(
            id=bot_msg_id,
            role=MessageRole.ASSISTANT,
            content=response,
            timestamp=datetime.utcnow().isoformat(),
            tool_calls=[]
        )

        bot_node = ConversationNode(
            id=bot_msg_id,
            message=bot_message,
            parent=user_msg_id,  # Bot response follows user message
            children=[],  # No children yet
            is_current=True  # Bot response is now current
        )

        # Update parent node to include user message as child
        if current_node_id and current_node_id in conversation_tree:
            parent_node = conversation_tree[current_node_id]
            if user_msg_id not in parent_node.children:
                parent_node.children.append(user_msg_id)
            parent_node.is_current = False  # No longer current

        # Mark all other nodes as not current
        for node in conversation_tree.values():
            node.is_current = False

        # Add new nodes to conversation tree (ACCUMULATE, don't replace!)
        conversation_tree[user_msg_id] = user_node
        conversation_tree[bot_msg_id] = bot_node

        # Update stored state
        self._conversation_trees[bot_id] = conversation_tree
        self._current_node_ids[bot_id] = bot_msg_id  # Bot response is now current

        # Generate React Flow data for tree view
        react_flow_data = serialize_gui_conversation_tree(
            conversation_tree,
            bot_msg_id,
            TreeLayout()
        )

        # Create BotState using camelCase aliases (this is the fix!)
        return BotState(
            id=bot_id,
            name=self._bot_metadata[bot_id]['name'],
            conversationTree=conversation_tree,  # Use camelCase alias
            currentNodeId=bot_msg_id,           # Use camelCase alias
            isConnected=True,                   # Use camelCase alias
            isThinking=False,                   # Use camelCase alias
            reactFlowData=react_flow_data       # Use camelCase alias
        )

    async def get_bot_state(self, bot_id: str) -> BotState:
        """Get current bot state with proper current node ID."""
        assert isinstance(bot_id, str) and bot_id.strip(), "Bot ID must be non-empty string"

        if bot_id not in self._bots:
            return None

        conversation_tree = self._conversation_trees.get(bot_id, {})
        current_node_id = self._current_node_ids.get(bot_id)

        # Create BotState using camelCase aliases
        return BotState(
            id=bot_id,
            name=self._bot_metadata[bot_id]['name'],
            conversationTree=conversation_tree,  # Use camelCase alias
            currentNodeId=current_node_id or "",  # Use camelCase alias
            isConnected=True,                     # Use camelCase alias
            isThinking=False                      # Use camelCase alias
        )

    def delete_bot(self, bot_id: str) -> bool:
        """Delete a bot instance."""
        assert isinstance(bot_id, str) and bot_id.strip(), "Bot ID must be non-empty string"

        if bot_id not in self._bots:
            return False

        del self._bots[bot_id]
        if bot_id in self._conversation_trees:
            del self._conversation_trees[bot_id]
        if bot_id in self._current_node_ids:
            del self._current_node_ids[bot_id]
        if bot_id in self._bot_metadata:
            del self._bot_metadata[bot_id]

        logger.info(f"Deleted bot: {bot_id}")
        return True

    @property
    def bots(self) -> Dict[str, Any]:
        """Public access to bots dictionary for testing."""
        return self._bots
async def list_bots_async(self) -> List[Dict[str, Any]]:
    """Async version for web API."""
    return [{'id': bot_id, 'name': meta['name']} 
            for bot_id, meta in self._bot_metadata.items()]
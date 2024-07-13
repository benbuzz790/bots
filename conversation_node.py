import json
from typing import Optional, Dict, Any, Union


class ConversationNode:
    def copy(self):
        """Create a deep copy of the ConversationNode."""
        new_node = ConversationNode(self.role, self.content)
        new_node.replies = [reply.copy() for reply in self.replies]
        return new_node

    """
    Represents a node in a conversation tree.
    """

    def __init__(
        self, role: str, content: str, parent: Optional["ConversationNode"] = None
    ):
        self.role = role
        self.content = content
        self.replies: list["ConversationNode"] = []
        self.parent = parent
        self._history: Optional[list[Dict[str, str]]] = None

    def add_reply(self, content: str, role: str = "user") -> "ConversationNode":
        """
        Adds a reply to the conversation node.
        """
        reply = self.__class__(role, content, parent=self)
        self.replies.append(reply)
        return reply

    def append(self, conversation: "ConversationNode") -> "ConversationNode":
        """
        Appends a conversation node to the current node.
        """
        self.replies.append(conversation)
        return conversation

    def root(self) -> "ConversationNode":
        """
        Returns the root node of the conversation tree.
        """
        return self._root()[0]

    def depth(self) -> int:
        """
        Returns the depth of the current node in the conversation tree.
        """
        return self._root()[1]

    def _root(self) -> tuple["ConversationNode", int]:
        """
        Returns the root node and depth of the current node.
        """
        node = self
        depth = 0
        while node.parent is not None:
            node = node.parent
            depth = depth + 1
        return node, depth

    def to_dict(self) -> list[Dict[str, str]]:
        """
        Converts the conversation node and its replies to a dictionary.
        """
        node = self
        conversation_dict = [{"role": node.role, "content": node.content}]
        if node.parent is not None:
            parent_dict = node.parent.to_dict()
            conversation_dict = parent_dict + conversation_dict
        return conversation_dict

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], list[Dict[str, str]]]) -> "ConversationNode":
        """
        Creates a ConversationNode instance from a dictionary.
        """
        if isinstance(data, list):
            if len(data) == 0:
                raise ValueError("Empty conversation data")
            root_node = None
            current_node = None
            for message_data in data:
                role = message_data["role"]
                content = message_data["content"]
                if root_node is None:
                    root_node = cls(role, content)
                    current_node = root_node
                else:
                    reply_node = cls(role, content)
                    reply_node.parent = current_node
                    current_node.replies.append(reply_node)
                    current_node = reply_node
            return root_node
        elif data is None:
            return EmptyConversationNode()
        else:
            role = data["role"]
            content = data["content"]
            node = cls(role, content)
            for reply_data in data.get("replies", []):
                reply_node = cls.from_dict(reply_data)
                reply_node.parent = node
                node.replies.append(reply_node)

            return node

    def to_json(self) -> str:
        """
        Converts the conversation node and its replies to a JSON string.
        """
        conversation_dict = self.to_dict()
        json_data = json.dumps(conversation_dict)
        return json_data

    @classmethod
    def from_json(cls, json_data: str) -> "ConversationNode":
        """
        Creates a ConversationNode instance from a JSON string.
        """
        conversation_dict = json.loads(json_data)
        node = cls.from_dict(conversation_dict)
        return node

    def to_string(self) -> str:
        """
        Returns a string representation of the conversation tree starting from the current node.
        """
        return self.__to_string__(0)

    def __to_string__(self, level: int = 0) -> str:
        """
        Recursively generates a string representation of the conversation tree.
        """
        indent = " " * level
        result = f"{indent}{self.role}: {self.content}\n"
        for reply in self.replies:
            result += reply.__to_string__(level + 1)
        return result

class EmptyConversationNode(ConversationNode):
    """
    Represents an empty conversation node, implementing the Null Object pattern.
    """

    def __init__(self):
        super().__init__("empty", "")

    def add_reply(self, content: str, role: str = "user") -> "ConversationNode":
        return ConversationNode(content=content, role=role)

    def append(self, conversation: "ConversationNode") -> "ConversationNode":
        return conversation

    def root(self) -> "ConversationNode":
        return self

    def depth(self) -> int:
        return 0

    def _root(self) -> tuple["ConversationNode", int]:
        return self, 0

    def to_dict(self) -> list[Dict[str, str]]:
        return []

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], list[Dict[str, str]]]) -> "EmptyConversationNode":
        return cls()

    def to_json(self) -> str:
        return "[]"

    @classmethod
    def from_json(cls, json_data: str) -> "EmptyConversationNode":
        return cls()

    def to_string(self) -> str:
        return ""

    def __to_string__(self, level: int = 0) -> str:
        return ""
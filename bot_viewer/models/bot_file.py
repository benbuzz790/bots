import json
from typing import Dict, Any, List

class ConversationNode:
    def __init__(self, role: str, content: str, **kwargs):
        self.role = role
        self.content = content
        self.attributes = kwargs
        self.replies: List[ConversationNode] = []

    def add_reply(self, reply: 'ConversationNode'):
        self.replies.append(reply)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "attributes": self.attributes,
            "replies": [reply.to_dict() for reply in self.replies]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationNode':
        node = cls(data["role"], data["content"], **data.get("attributes", {}))
        for reply_data in data.get("replies", []):
            node.add_reply(cls.from_dict(reply_data))
        return node

class BotFile:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: Dict[str, Any] = {}
        self.conversation: ConversationNode = None
        self.load()

    def load(self):
        with open(self.file_path, 'r') as file:
            self.data = json.load(file)
        self.conversation = ConversationNode.from_dict(self.data.get("conversation", {}))

    def save(self):
        self.data["conversation"] = self.conversation.to_dict()
        with open(self.file_path, 'w') as file:
            json.dump(self.data, file, indent=2)

    def get_bot_info(self) -> Dict[str, Any]:
        return {k: v for k, v in self.data.items() if k != "conversation"}

    def get_conversation(self) -> ConversationNode:
        return self.conversation
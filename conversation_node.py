import json

# TODO - Combine this file with bots.py

class ConversationNode:
    """
    Represents a node in a conversation tree.

    Methods:
    - **init**(role, content, parent=None): Initializes a ConversationNode instance.
    - add_reply(content, role='user'): Adds a reply to the conversation node.
    - append(conversation): Appends a conversation node to the current node.
    - root(): Returns the root node of the conversation tree.
    - first_reply(): Returns the first reply of the current node.
    - last_reply(): Returns the last reply of the current node.
    - to_dict(): Converts the conversation node and its replies to a dictionary.
    - from_dict(data): Creates a ConversationNode instance from a dictionary.
    - to_string(): Returns a string representation of the conversation tree starting from the current node.
    - to_json(): Converts the conversation node and its replies to a JSON string.
    - from_json(json_data): Creates a ConversationNode instance from a JSON string.
    """

    def __init__(self, role: str, content: str, parent:'ConversationNode'=None):
        self.role = role
        self.content = content
        self.replies = []
        self.parent = parent
        self._history = None
    
    def add_reply(self, content: str, role: str = 'user'):
        reply = self.__class__(role, content, parent=self)
        self.replies.append(reply)
        return reply

    def append(self, conversation: "ConversationNode"):
        self.replies.append(conversation)
        return conversation

    def root(self):
        return self._root()[0]
    
    def depth(self):
        return self._root()[1]

    def _root(self):
        node = self
        depth = 0
        while node.parent is not None:
            node = node.parent
            depth = depth + 1
        return node, depth

    def to_dict(self):
        node = self
        conversation_dict = [{"role": node.role, "content": node.content}]
        if node.parent is not None:
            parent_dict = node.parent.to_dict()
            conversation_dict = parent_dict + conversation_dict
        return conversation_dict

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, list):
            raise ValueError("Conversation data must be a list")

        if len(data) == 0:
            raise ValueError("Empty conversation data")

        root_node = None
        current_node = None

        for message_data in data:
            role = message_data['role']
            content = message_data['content']

            if root_node is None:
                root_node = cls(role, content)
                current_node = root_node
            else:
                reply_node = cls(role, content)
                reply_node.parent = current_node
                current_node.replies.append(reply_node)
                current_node = reply_node

        return root_node

    def to_json(self):
        conversation_dict = self.to_dict()
        json_data = json.dumps(conversation_dict)
        return json_data

    @classmethod
    def from_json(cls, json_data):
        conversation_dict = json.loads(json_data)
        node = cls.from_dict(conversation_dict)
        return node

    def to_string(self):
        # Returns the FORWARD conversation tree from this node
        # To print the entire conversation tree, use cn.root().to_string()
        return self.__to_string__(0)

    def __to_string__(self, level=0):
        indent = ' ' * level
        result = f'{indent}{self.role}: {self.content}\n'
        for reply in self.replies:
            result += reply.__to_string__(level + 1)
        return result
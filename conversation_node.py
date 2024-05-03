import json

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
        reply = ConversationNode(role, content, parent=self)
        self.replies.append(reply)
        return reply

    def append(self, conversation: "ConversationNode"):
        self.replies.append(conversation)
        return conversation

    def root(self):
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    def first_reply(self):
        return self.replies[0]

    def last_reply(self):
        return self.replies[-1]

    def to_dict(self):
        node = self
        conversation_dict = [{"role": node.role, "content": node.content}]
        if node.parent is not None:
            parent_dict = node.parent.to_dict()
            conversation_dict = parent_dict + conversation_dict
        return conversation_dict

    @classmethod
    def from_dict(cls, data):
        if isinstance(data, list):
            if len(data) > 0:
                data = data[0]
            else:
                raise ValueError("Empty conversation data")
        role = data['role']
        content = data['content']
        node = cls(role, content)
        for reply_data in data.get('replies', []):
            reply_node = cls.from_dict(reply_data)
            reply_node.parent = node
            node.replies.append(reply_node)
        return node

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
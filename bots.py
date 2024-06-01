from abc import ABC, abstractmethod
from enum import Enum
import conversation_node as CN
import bot_mailbox as MB
import datetime as DT
import re
import json
import os


class Engine(Enum):
    """
    Enum class representing different AI model engines.

    Attributes:
        - GPT4: String value for GPT-4 model.
        - GPT432k: String value for GPT-4-32k model.
        - GPT35: String value for GPT-3.5-turbo model.
        - CLAUDE3OPUS: String value for Claude-3-Opus model.
        - CLAUDE3SONNET: String value for Claude-3-Sonnet model.
    """
    
    GPT4 = "gpt-4"
    GPT432k = "gpt-4-32k"
    GPT35 = "gpt-3.5-turbo"
    CLAUDE3OPUS = "claude-3-opus-20240229"
    CLAUDE3SONNET = "claude-3-sonnet-20240229"

class BaseBot(ABC):
    """
    Abstract base class for bot implementations.

    Methods:
        - respond(content, role='user') -> str: Generates a response based on the given content and role.
        - cvsn_respond(text=None, cvsn=None, role='user'): Generates a response based on the conversation node and text.
        - save_conversation_tree(conversation_root): Saves the conversation tree to a file.
        - save_linear_conversation(linear_conversation): Saves the linear conversation to a file.
        - load(filepath) -> 'BaseBot': Loads a bot instance or conversation from a file.
        - save(filename=None): Saves the bot instance to a file.
        - converse(): Starts an interactive conversation with the bot in the console.
        - sys_say(string): Prints a message from the system. 
        - say(string): Prints a message from the bot.

    Abstract Methods:
        - _send_message(cvsn): Sends a message to the bot's mailbox (to be implemented by subclasses).
    """
        
    def __init__(self, api_key, model_engine, max_tokens, temperature, name, role, role_description):
        self.api_key = api_key
        self.name = name
        self.model_engine = model_engine
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.role = role
        self.role_description = role_description
        self.conversation: CN.ConversationNode = None

    def respond(self, content, role='user') -> str:
        reply, self.conversation = self.cvsn_respond(text=content, cvsn=self.conversation, role=role)
        return reply

    def cvsn_respond(self, text=None, cvsn: CN.ConversationNode=None, role='user'):
        # Default: if text to the conversation as a new node then, ...
            # Add the bot's response to the conversation as a new node
        # If only cvsn is provided,
            # Add the bot's response to the conversation as a new node
        # If only text is provided, 
            # Create a new conversation node and then go to default case.
        # If neither text nor cvsn is provided, raise an exception.
        # Always return the response text and the last created conversation node.

        if cvsn is not None and text is not None:
            try:
                cvsn = cvsn.add_reply(text, role)
                response_text, response_role, _ = self._send_message(cvsn)
                cvsn = cvsn.add_reply(response_text, response_role)
                return response_text, cvsn
            except Exception as e:
                raise e
        elif cvsn is not None:
            try:
                response_text, response_role, _ = self._send_message(cvsn)
                cvsn = cvsn.add_reply(response_text, response_role)
                return response_text, cvsn
            except Exception as e:
                raise e
        elif text is not None:
            c = CN.ConversationNode(role=role, content=text)
            return self.cvsn_respond(cvsn=c)
        elif text is None and cvsn is not None:
            try:
                response_text, response_role, _ = self._send_message(cvsn)
                cvsn = cvsn.add_reply(response_text, response_role)
                return response_text, cvsn
            except Exception as e:
                raise e
        else:
            raise Exception

    @abstractmethod
    def _send_message(self, cvsn):
        pass

    def formatted_datetime(self):
        now = DT.datetime.now()
        return now.strftime("%Y.%m.%d-%H.%M.%S")

    def save_conversation_tree(self, conversation_root):
        filename = f"{self.name}@{self.formatted_datetime()}.cvsn"
        data = conversation_root.to_dict()
        with open(filename, 'w') as file:
            json.dump(data, file)

    @classmethod
    def load(cls, filepath):
        _, extension = os.path.splitext(filepath)

        if extension == '.bot':
            with open(filepath, 'r') as file:
                data = json.load(file)
            
            bot_class = globals()[data['bot_class']]
            bot = bot_class(api_key=None, model_engine=Engine(data['model_engine']), max_tokens=data['max_tokens'],
                            temperature=data['temperature'], name=data['name'], role=data['role'],
                            role_description=data['role_description'])
            
            if data['conversation']:
                bot.conversation = CN.ConversationNode.from_dict(data['conversation'])
            
            return bot

        elif extension == '.cvsn':
            with open(filepath, 'r') as file:
                conversation_data = json.load(file)
            
            conversation_node = CN.ConversationNode.from_dict(conversation_data)
            return conversation_node

        else:
            raise ValueError(f"Unsupported file extension: {extension}")

    def save(self, filename=None):
        now = DT.datetime.now()
        formatted_datetime = now.strftime("%Y.%m.%d-%H.%M.%S")
        if filename is None:
            filename = f"{self.name}@{formatted_datetime}.bot"
        data = {
            'bot_class': self.__class__.__name__,
            'name': self.name,
            'model_engine': self.model_engine,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'role': self.role,
            'role_description': self.role_description,
            'conversation': self.conversation.to_dict() if self.conversation else None
        }
        with open(filename, 'w') as file:
            json.dump(data, file)
    
    def converse(self):
        self.sys_say("Begin Conversation")

        while True:
            user_input = input("You: ")
            match user_input:
                case "/debug":
                    print("---")
                    self.sys_say("Debug:")
                    print("\n")
                    self.sys_say(f'Name:{self.name}, Role:{self.role}, Description:{self.role_description}')
                    print("\n")
                    print("\n")
                    print(self.conversation.root().to_string())
                    print("\n")
                    print("---")
                case "/break":
                    self.sys_say("conversation ended")
                    break
                case "/save":
                    self.save()
                case "/load":
                    self.sys_say("Enter path")
                    self = self.load(input("You: "))
                case _:
                    if self.conversation is not None:
                        self.conversation = self.conversation.add_reply(user_input, 'user')
                    else:
                        self.conversation = CN.ConversationNode(role='user', content=user_input)
                    response, self.conversation = self.cvsn_respond(cvsn=self.conversation)
                    self.say(response)

    def sys_say(self, string):
        print(f'System: {string}')

    def say(self, string):
        print(f'{self.name}: {string}')

class GPTBot(BaseBot):
    """
    ChatGPT-based bot implementation.

    Methods:
        - __init__(api_key=None, model_engine=Engine.GPT4, max_tokens=4096, temperature=0.9, name="bot", role="assistant", role_description="a friendly AI assistant"): Initializes a GPTBot instance.
        - load(filepath) -> 'GPTBot': Loads a GPTBot instance from a file.
        - _send_message(cvsn): Sends a message to the bot's mailbox using the OpenAI API.
    """

    def __init__(self, api_key=None, model_engine=Engine.GPT4, max_tokens=4096, temperature=0.9, name="bot", role="assistant", role_description="a friendly AI assistant"):
        super().__init__(api_key, model_engine.value, max_tokens, temperature, name, role, role_description)
        match model_engine:
            case Engine.GPT4 | Engine.GPT35 | Engine.GPT432k:
                self.mailbox = MB.OpenAIMailbox(verbose=True)
            case _:
                raise Exception(f'model_engine: {model_engine} not found')
    
    @classmethod
    def load(cls, filepath):
        return super().load(filepath)
    
    def _send_message(self, cvsn):
        return self.mailbox.send_message(cvsn, self.model_engine, self.max_tokens, self.temperature, self.api_key)

class AnthropicBot(BaseBot):
    """
    Anthropic-based bot implementation.

    Methods:
        - __init__(api_key=None, model_engine=Engine.CLAUDE3OPUS, max_tokens=4096, temperature=0.9, name="bot", role="assistant", role_description="a friendly AI assistant"): Initializes an AnthropicBot instance.
        - load(filepath) -> 'AnthropicBot': Loads an AnthropicBot instance from a file.
        - _send_message(cvsn): Sends a message to the bot's mailbox using the Anthropic API.
    """
    def __init__(self, api_key=None, model_engine=Engine.CLAUDE3OPUS, max_tokens=4096, temperature=0.9, name="bot", role="assistant", role_description="a friendly AI assistant"):
        super().__init__(api_key, model_engine.value, max_tokens, temperature, name, role, role_description)
        match model_engine:
            case Engine.CLAUDE3OPUS | Engine.CLAUDE3SONNET:
                self.mailbox = MB.AnthropicMailbox(verbose=True)
            case _:
                raise Exception(f'model_engine: {model_engine} not found')
    
    @classmethod
    def load(cls, filepath):
        return super().load(filepath)
    
    def _send_message(self, cvsn):
        return self.mailbox.send_message(cvsn, self.model_engine, self.max_tokens, self.temperature, self.api_key)


# Utility functions
def remove_code_blocks(text):
    """
        Extracts the content inside a code block from the given text, 
        considering an optional language identifier.

        Args:
        - text (str): Input text containing the code block.

        Returns:
        - str: Extracted code or an empty string if no code block is found.
    """
    pattern = r'```(?:[a-zA-Z0-9_+-]+)?\s*([\s\S]*?)```'
    code_blocks = []
    
    while True:
        match = re.search(pattern, text)
        if match:
            code_block = match.group(1).strip()
            code_blocks.append(code_block)
            text = text[:match.start()] + text[match.end():]
        else:
            break
    
    return code_blocks

if __name__ == "__main__":
    import os
    GPTBot(os.getenv('OPENAI_API_KEY')).converse()


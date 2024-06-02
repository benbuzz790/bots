from openai import OpenAI
import json
from datetime import datetime
import anthropic
import os
from abc import ABC, abstractmethod
import conversation_node as CN

# TODO - Add docstrings to all methods and classes
# TODO - Add type hints to all methods and classes
# TODO - Combine this file with bots.py

class BaseMailbox(ABC):
    """
    Abstract base class for mailbox implementations.

    Methods:
        - __init__(verbose=False): Initializes a BaseMailbox instance.
        - log_message(message): Logs a message to a file.
        - send_message(conversation, model, max_tokens, temperature, api_key): Sends a message to the mailbox.

    Abstract Methods:
        - _send_message_implementation(conversation, model, max_tokens, temperature, api_key): Implementation of sending a message (to be implemented by subclasses).
        - _process_response(response): Processes the response received from the mailbox (to be implemented by subclasses).
    """
        
    def __init__(self, verbose: bool = False):
        self.verbose = verbose #currently unused. useful for debugging.

    def log_message(self, message: str):
        #with open('mailbox_log.txt', 'a') as log_file:
        pass #   log_file.write(message + '\n\n\n')

    def __formatted_datetime__(self):
        now = datetime.now()
        formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_datetime

    def send_message(self, conversation: CN.ConversationNode, model, max_tokens, temperature, api_key):
        message = {
            'date': self.__formatted_datetime__(),
            'messages': conversation.to_dict(),
            'max_tokens': max_tokens,
            'temperature': temperature,
            'model': model
        }

        self.log_message(json.dumps(message))

        try:
            response = self._send_message_implementation(conversation, model, max_tokens, temperature, api_key)
        except Exception as e:
            raise e

        response_text, response_role = self._process_response(response)

        message = {
            'date': self.__formatted_datetime__(),
            'role': response_role,
            'content': response_text
        }

        self.log_message(json.dumps(message))
        return response_text, response_role, response

    @abstractmethod
    def _send_message_implementation(self, conversation, model, max_tokens, temperature, api_key):
        pass

    @abstractmethod
    def _process_response(self, response):
        pass

class OpenAIMailbox(BaseMailbox):
    """
    OpenAI-based mailbox implementation.

    Methods:
        - __init__(api_key=None, verbose=False): Initializes an OpenAIMailbox instance.
        - _send_message_implementation(conversation, model, max_tokens, temperature, api_key): Sends a message using the OpenAI API.
        - _process_response(response): Processes the response received from the OpenAI API.
    """
        
    def __init__(self, api_key=None, verbose: bool = False):
        super().__init__(verbose)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided.")
        
    def _send_message_implementation(self, conversation, model, max_tokens, temperature, api_key):
        client = OpenAI(api_key=api_key)
        return client.chat.completions.create(
            messages=conversation.to_dict(),
            max_tokens=max_tokens,
            temperature=temperature,
            model=model
        )

    def _process_response(self, response):
        response_text = response.choices[0].message.content
        response_role = response.choices[0].message.role
        return response_text, response_role

class AnthropicMailbox(BaseMailbox):
    """
    Anthropic-based mailbox implementation.

    Methods:
        - __init__(api_key=None, verbose=False): Initializes an AnthropicMailbox instance.
        - _send_message_implementation(conversation, model, max_tokens, temperature, api_key): Sends a message using the Anthropic API.
        - _process_response(response): Processes the response received from the Anthropic API.
    """
        
    def __init__(self, api_key=None, verbose: bool = False):
        super().__init__(verbose)
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key not provided.")
    
    def _send_message_implementation(self, conversation, model, max_tokens, temperature, api_key):
        client = anthropic.Anthropic(api_key=api_key)

        # Anthropic API requires the first message to be from the user
        # Maybe not the best way to do this, but it works
        def fix_messages(csvn):
            msg_dict = csvn.to_dict()
            if msg_dict[0]['role'] == 'assistant':
                if self.verbose:
                    Warning("Anthropic requires first message  be from the user. Ignoring first message.")
                msg_dict = msg_dict[1:]
            return msg_dict

        return client.messages.create(
            messages=fix_messages(conversation),
            max_tokens=max_tokens,
            temperature=temperature,
            model=model
        )

    def _process_response(self, response):
        response_text = response.content[0].text
        response_role = response.role
        return response_text, response_role
    
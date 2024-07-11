
from openai import OpenAI
import json
from datetime import datetime
import anthropic
import os
from abc import ABC, abstractmethod
import conversation_node as CN
from typing import Optional, Dict, Any

#TODO fix logging

class BaseMailbox(ABC):
    """
    Abstract base class for mailbox implementations.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose  # currently unused. useful for debugging.

    def log_message(self, message: str) -> None:
        """
        Logs a message to a file.
        """
        pass

    def __formatted_datetime__(self) -> str:
        """
        Returns the current date and time in a formatted string.
        """
        now = datetime.now()
        formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_datetime

    def send_message(
        self,
        conversation: CN.ConversationNode,
        model: str,
        max_tokens: int,
        temperature: float,
        api_key: str,
        system_message: Optional[str] = None
    ) -> tuple[str, str, Dict[str, Any]]:
        """
        Sends a message to the mailbox.
        """
        message = {
            "date": self.__formatted_datetime__(),
            "messages": conversation.to_dict(),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": model,
        }

        self.log_message(json.dumps(message))

        try:
            response = self._send_message_implementation(
                conversation, model, max_tokens, temperature, api_key, system_message
            )
        except Exception as e:
            raise e

        response_text, response_role = self._process_response(response)

        message = {
            "date": self.__formatted_datetime__(),
            "role": response_role,
            "content": response_text,
        }

        self.log_message(json.dumps(message))
        return response_text, response_role, response

    @abstractmethod
    def _send_message_implementation(
        self,
        conversation: CN.ConversationNode,
        model: str,
        max_tokens: int,
        temperature: float,
        api_key: str,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Implementation of sending a message (to be implemented by subclasses).
        """
        pass

    @abstractmethod
    def _process_response(self, response: Dict[str, Any]) -> tuple[str, str]:
        """
        Processes the response received from the mailbox (to be implemented by subclasses).
        """
        pass


class OpenAIMailbox(BaseMailbox):
    """
    OpenAI-based mailbox implementation.
    """

    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        super().__init__(verbose)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided.")

    def _send_message_implementation(
        self,
        conversation: CN.ConversationNode,
        model: str,
        max_tokens: int,
        temperature: float,
        api_key: str,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends a message using the OpenAI API.
        """
        client = OpenAI(api_key=api_key)
        messages = conversation.to_dict()
        if system_message:
            messages.insert(0, {"role": "system", "content": system_message})
        return client.chat.completions.create(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

    def _process_response(self, response: Dict[str, Any]) -> tuple:
        """
        Processes the response received from the OpenAI API.
        """
        response_text = response.choices[0].message.content
        response_role = response.choices[0].message.role
        return response_text, response_role



class AnthropicMailbox(BaseMailbox):
    """
    Anthropic-based mailbox implementation.
    """
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        super().__init__(verbose)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided.")

    def _send_message_implementation(
        self,
        conversation: CN.ConversationNode,
        model: str,
        max_tokens: int,
        temperature: float,
        api_key: str,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends a message using the Anthropic API.
        """
        client = anthropic.Anthropic(api_key=api_key)

        messages = self._fix_messages(conversation)

        try:

            if system_message:
                response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=messages
                )
            else:
                response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
                )
        except Exception as e:
            print('\n\n\n ---debug---\n')
            print(f"System message: {system_message}")
            print(f"Messages: {messages}")
            print('\n---debug---\n\n\n')
            raise e

        return response

    def _fix_messages(self, csvn: CN.ConversationNode) -> list[dict[str, str]]:
        messages = csvn.to_dict()
        # Remove any 'system' role messages as Anthropic handles them separately
        return [msg for msg in messages if msg['role'] != 'system']

    def _process_response(self, response: Dict[str, Any]) -> tuple[str, str]:
        """
        Processes the response received from the Anthropic API.
        """
        response_text = response.content[0].text
        response_role = response.role
        return response_text, response_role

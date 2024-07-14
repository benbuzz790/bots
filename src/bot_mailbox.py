import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
import json
from datetime import datetime
import anthropic
import os
from abc import ABC, abstractmethod
import src.conversation_node as CN
from typing import Optional, Dict, Any
import threading

class BaseMailbox(ABC):
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.log_file = r"data\mailbox_log.txt"

    def log_message(self, message: str, direction: str) -> None:
        timestamp = self.__formatted_datetime__()
        log_entry = f"[{timestamp}] {direction.upper()}:\n{message}\n\n"
        with open(self.log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)

    def __formatted_datetime__(self) -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")

    def send_message(self, conversation: CN.ConversationNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> tuple[str, str, Dict[str, Any]]:
        message = {
            "date": self.__formatted_datetime__(),
            "messages": conversation.to_dict(),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": model,
        }
        self.log_message(json.dumps(message, indent=2), "OUTGOING")
        try:
            response = self._send_message_implementation(conversation, model, max_tokens, temperature, api_key, system_message)
        except Exception as e:
            raise e
        response_text, response_role = self._process_response(response)
        message = {
            "date": self.__formatted_datetime__(),
            "role": response_role,
            "content": response_text,
        }
        self.log_message(json.dumps(message, indent=2), "INCOMING")
        return response_text, response_role, response

    @abstractmethod
    def _send_message_implementation(self, conversation: CN.ConversationNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _process_response(self, response: Dict[str, Any]) -> tuple[str, str]:
        pass

    def batch_send(self, conversations, model, max_tokens, temperature, api_key, system_message=None):
        threads = []
        results = [None] * len(conversations)
        
        def send_thread(index, conv):
            result = self.send_message(conv, model, max_tokens, temperature, api_key, system_message)
            results[index] = result
        
        for i, conversation in enumerate(conversations):
            thread = threading.Thread(target=send_thread, args=(i, conversation))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        return results

class OpenAIMailbox(BaseMailbox):
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        super().__init__(verbose)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided.")

    def _send_message_implementation(self, conversation: CN.ConversationNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> Dict[str, Any]:
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
        response_text = response.choices[0].message.content
        response_role = response.choices[0].message.role
        return response_text, response_role

class AnthropicMailbox(BaseMailbox):
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        super().__init__(verbose)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided.")

    def _send_message_implementation(self, conversation: CN.ConversationNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> Dict[str, Any]:
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
        return [msg for msg in messages if msg['role'] != 'system']

    def _process_response(self, response: Dict[str, Any]) -> tuple[str, str]:
        response_text = response.content[0].text
        response_role = response.role
        return response_text, response_role

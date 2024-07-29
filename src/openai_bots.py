from src.base import Bot, Mailbox, ConversationNode, Engines, ToolHandler
from typing import Optional, Dict, Any, List, Tuple, Callable
from openai import OpenAI
import os

class OpenAIMailbox(Mailbox):
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        super().__init__(verbose)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided.")

    def _send_message_implementation(self, 
            conversation: ConversationNode, 
            model: str, 
            max_tokens: int, 
            temperature: float, 
            api_key: str, 
            system_message: Optional[str] = None
            ) -> Dict[str, Any]:
        client = OpenAI(api_key=api_key)
        messages = conversation.get_message_list()
        if system_message:
            messages.insert(0, {"role": "system", "content": system_message})
        return client.chat.completions.create(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

    def _process_response(self, response: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        response_text = response.choices[0].message.content
        response_role = response.choices[0].message.role
        metadata = {
            "finish_reason": response.choices[0].finish_reason,
            "model": response.model,
            "usage": response.usage.to_dict() if response.usage else None,
        }
        return response_text, response_role, metadata

class OpenAIToolHandler(ToolHandler):
    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        # Implement OpenAI-specific tool schema generation
        pass

    def handle_tool_use(self, response: Any) -> List[Dict[str, Any]]:
        # Implement OpenAI-specific tool use handling
        pass

class GPTBot(Bot):
    ToolHandlerClass = OpenAIToolHandler

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_engine: Engines = Engines.GPT4,
        max_tokens: int = 4096,
        temperature: float = 0.9,
        name: str = "bot",
        role: str = "assistant",
        role_description: str = "a friendly AI assistant",
        tool_handler: Optional[OpenAIToolHandler] = None,
    ):
        super().__init__(api_key, model_engine, max_tokens, temperature,
                         name, role, role_description)
        self.mailbox = OpenAIMailbox(api_key=api_key, verbose=True)
        self.tool_handler = tool_handler or OpenAIToolHandler()

    def _send_message(self, cvsn: ConversationNode) -> Tuple[str, str]:
        response_text, response_role, metadata = self.mailbox.send_message(
            cvsn, self.model_engine.value, self.max_tokens, self.temperature, self.api_key, self.system_message
        )
        # Handle tool use if necessary
        tool_results = self.tool_handler.handle_tool_use(metadata)
        if tool_results:
            for result in tool_results:
                self.tool_handler.add_result(result)
        return response_text, response_role#, tool_results

    @classmethod
    def load(cls, filepath: str) -> "GPTBot":
        return super().load(filepath)
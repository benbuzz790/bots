import json
import re

def format_content(content, indent=0):
    if isinstance(content, list):
        formatted = []
        for item in content:
            formatted.append(format_content(item, indent + 2))
        return '[\n' + ',\n'.join(formatted) + '\n' + ' ' * indent + ']'
    elif isinstance(content, dict):
        formatted = []
        for key, value in content.items():
            formatted.append(f"{' ' * (indent + 2)}{json.dumps(key)}: {format_content(value, indent + 2)}")
        return '{\n' + ',\n'.join(formatted) + '\n' + ' ' * indent + '}'
    elif isinstance(content, str):
        # Handle escaped newlines
        lines = re.split(r'(?<!\\)\\n', content)  # Split on non-escaped \n
        if len(lines) > 1:
            formatted = [(' ' * (indent + 2) + line.strip()) for line in lines]
            return '\n'.join(formatted)
        else:
            # If there are no newlines, just return the JSON-encoded string
            return json.dumps(content)
    else:
        return json.dumps(content)

def get_brief_content(content):
    if isinstance(content, list):
        return ', '.join(get_brief_content(item) for item in content)
    elif isinstance(content, dict):
        return ', '.join(f"{k}: {get_brief_content(v)}" for k, v in content.items())
    else:
        return str(content)

# Test function
def test_format_content():
    test_cases = [
        "Simple string",
        "String with\\nnewline",
        ["List", "with\\nnewline"],
        {"key": "value\\nwith\\nnewline"},
        {
            "content": "# anthropic_bot.py\\n\\nfrom src.base import Bot, Mailbox, ConversationNode, Engines, ToolHandler\\nimport src.base as base\\nfrom typing import Optional, Dict, Any, List, Callable, Tuple\\nimport anthropic\\nimport os\\nimport inspect\\n\\n\\nclass AnthropicNode(ConversationNode):\\n    def __init__(self, **kwargs: Any) -> None:\\n        super().__init__(role=kwargs.pop('role'), content=kwargs.pop('content'))\\n        for key, value in kwargs.items():\\n            self.content += f\"{key}: {value}\"\\n\\n\\nclass AnthropicToolHandler(ToolHandler):\\n    def __init__(self) -> None:\\n        super().__init__()\\n\\n    def generate_tool_schema(self, func: Callable) -> None:\\n        sig: inspect.Signature = inspect.signature(func)\\n        doc: str = inspect.getdoc(func) or \"No description provided.\"\\n\\n        tool: Dict[str, Any] = {"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"Test case {i}:")
        print(format_content(case))
        print()

if __name__ == "__main__":
    test_format_content()
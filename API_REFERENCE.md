# API Reference

## Core Classes

### Bot
The main Bot class for creating conversational AI agents.

```python
from bots import Bot

bot = Bot(
    model="claude-3-sonnet-20240229",
    system_prompt="You are a helpful assistant.",
    tools=["python", "web_search"]
)

response = bot.chat("Hello, how can you help me?")
```

#### Methods

- `chat(message: str) -> str`: Send a message and get a response
- `add_tool(tool_name: str)`: Add a tool to the bot's capabilities
- `save_conversation(filepath: str)`: Save conversation history
- `load_conversation(filepath: str)`: Load conversation history

### ToolHandler
Manages tool execution and registration.

```python
from bots.tools import ToolHandler

handler = ToolHandler()
handler.register_tool("custom_tool", custom_function)
```

## Available Tools

### Python Tool
Execute Python code in a sandboxed environment.

```python
bot.add_tool("python")
response = bot.chat("Calculate the factorial of 10")
```

### Web Search Tool
Search the web for information.

```python
bot.add_tool("web_search")
response = bot.chat("What's the latest news about AI?")
```

### File Operations
Read, write, and manipulate files.

```python
bot.add_tool("file_ops")
response = bot.chat("Read the contents of data.txt")
```

## Configuration

### Environment Variables
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI models)
- `BOT_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Config File
Create a `config.json` file:

```json
{
    "default_model": "claude-3-sonnet-20240229",
    "max_tokens": 4096,
    "temperature": 0.7,
    "tools": ["python", "web_search"]
}
```

## Error Handling

The library provides comprehensive error handling:

```python
from bots.exceptions import BotError, ToolError

try:
    response = bot.chat("Invalid request")
except BotError as e:
    print(f"Bot error: {e}")
except ToolError as e:
    print(f"Tool error: {e}")
```

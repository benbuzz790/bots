# LLM Utilities

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Requirements](#requirements)
5. [Quick Start](#quick-start)
6. [Usage Examples](#usage-examples)
7. [Core Components](#core-components)
8. [API Reference](#api-reference)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)
12. [License](#license)
13. [Additional Resources](#additional-resources)

## Overview
LLM Utilities is a Python library designed to simplify interactions with various Large Language Models (LLMs) such as OpenAI's GPT and Anthropic's Claude. It provides a unified interface for creating conversational AI bots, handling custom tools, and managing complex conversations. This library is ideal for developers and researchers working on AI-powered applications, chatbots, or any project requiring advanced language model interactions.

## Features
- **Multi-Provider Support**: Seamlessly work with different LLM providers, including OpenAI and Anthropic, using a consistent interface.
- **Extensible Bot Classes**: Easily create and customize bots for different LLM engines with the flexible `Bot` base class.
- **Advanced Conversation Management**: Utilize the `ConversationNode` class to create and navigate tree-like conversation structures.
- **Tool Integration**: Add custom functions as tools to your bots using the `ToolHandler` class, allowing for dynamic function calling within conversations. Simply define a python function, and run bot.add_tool(function:Callable). You can add an entire file of top level functions with add_tools(filename:str)
- **Flexible Mailbox System**: Manage message sending and receiving with the `Mailbox` class, which includes logging capabilities for debugging and analysis.
- **Engine Abstraction**: Use the `Engines` enum to easily switch between different LLM models and providers.
- **Serialization and Deserialization**: Save and load bot states, including conversation history and tool configurations.
- **Asynchronous Batch Processing (TBD)**: Send multiple messages concurrently using the batch sending feature.
- **Automatic Terminal**: Utilize `auto_terminal.py` to run an LLM session in your terminal, where the llm has tools to read and modify python code
- **Lazy Decorator**: Utilize the "@lazy()" decorator from `lazy.py` to tag functions as LLM responsibilities, and have them lazily generated and run the first time they are called.
- **Project Trees**: use `project_tree.py` to automatically generate project skeletons, including requirements, goals, and interfaces for each level of the project; then, automatically generate the files which are required. This is in active development and usually the final code requires a lot of debugging, although the requirements and goals seem reasonable.
- **Automated README Updates**: Utilize the `prep_repo.py` script to automatically update the README.md file based on recent changes in Python files.
- **Automated Code Formatting**: Use the `prep_repo.py` script to ensure consistent formatting, type hints, and PEP8 compliance across Python files in the project.

## Installation

To install LLM Utilities, you ~~can~~ can't use pip (TBD):

```bash
pip install llm-utilities
```

Alternatively, you can clone the repository and install it manually:

```bash
git clone https://github.com/benbuzz790/llm-utilities.git
~~cd llm-utilities~~
~~pip install -e .~~ (TBD)
```

## ~~Requirements~~ (Out of date)

LLM Utilities requires Python 3.7 or later. The following dependencies are required:

- `openai`: For interacting with OpenAI's GPT models
- `anthropic`: For interacting with Anthropic's Claude models
- `requests`: For making HTTP requests

You can't install all required dependencies using (TBD):

```bash
pip install -r requirements.txt
```

as requrements.txt does not exist yet.

## Quick Start

Here's a simple example to get you started with LLM Utilities:

```python
# Initialize a GPT-4 bot
bot = GPTBot(
    api_key="your_openai_api_key_here",
    model_engine=Engines.GPT4,
    max_tokens=150,
    temperature=0.7,
    name="MyAssistant"
)

# Set a system message
bot.set_system_message("You are a helpful assistant that specializes in Python programming.")

# Start a conversation
response = bot.respond("What's the best way to handle exceptions in Python?")
print(response)

# Continue the conversation
response = bot.respond("Can you show me an example?")
print(response)
```

## Usage Examples

### 0. Chatting with a Bot inside your Terminal
```python
# The simplest way to use a bot
AnthropicBot().chat()
```

### 1. Creating a Claude Bot with Custom Tools

```python
def calculate_square(number: int) -> int:
    """Calculate the square of a given number."""
    return number ** 2

# Initialize the bot
claude_bot = AnthropicBot(
    api_key="your_anthropic_api_key_here",
    model_engine=Engines.CLAUDE35,
    max_tokens=1000,
    temperature=0.5,
    name="ClaudeAssistant"
)

# Add the tool
bot.add_tool(calculate_square)

# Use the bot with the custom tool
response = claude_bot.respond("What's the square of 7?")
print(response)
```

### 2. Managing Complex Conversations

```python
bot = GPTBot(api_key="your_openai_api_key_here", model_engine=Engines.GPT35)

# Start a conversation
root = ConversationNode(role="user", content="Tell me a short story.")
response, root = bot._cvsn_respond(cvsn=root)
print("Bot:", response)

# Add a branch to the conversation
branch1 = root.add_reply(role="user", content="Make it a mystery story instead.")
response, branch1 = bot._cvsn_respond(cvsn=branch1)
print("Bot (Mystery):", response)

# Add another branch from the root
branch2 = root.add_reply(role="user", content="Please make it a comedy story.")
response, branch2 = bot._cvsn_respond(cvsn=branch2)
print("Bot (Comedy):", response)
```

### 3. Saving and Loading Bot States

```python
# Create and use a bot
bot = GPTBot(api_key="your_openai_api_key_here", model_engine=Engines.GPT4)
bot.respond("Hello, how are you?")
bot.respond("Tell me a joke.")

# Save the bot state (api keys are not saved)
save_path = bot.save("my_bot")
print(f"Bot state saved to {save_path}") # my_bot.bot 

# Load the bot state later
# If api_key is blank, environment variables are attempted.
loaded_bot = base.load("my_bot_state", api_key="your_openai_api_key_here")

# Continue the conversation
response = loaded_bot.respond("Explain the joke you just told.")
print(response)
```

## Core Components

### 1. Bot
The `Bot` class is the central component of the library. It represents an AI assistant and manages interactions with the LLM. Key features include:
- Initialization with model parameters (API key, engine, max tokens, temperature, etc.)
- Conversation management
- Integration with ToolHandler for custom function support
- System message setting for guiding bot behavior
- Save and load functionality for persistent bot states

### 2. ConversationNode
`ConversationNode` implements a tree-like structure for managing complex conversations. It allows for:
- Creating branching dialogues
- Traversing conversation history
- Converting conversations to and from dictionary representations
- Building message lists for API requests

### 3. ToolHandler
The `ToolHandler` class manages custom functions that can be called by the LLM. Features include:
- Adding tools from Python functions
- Generating tool schemas for LLM consumption
- Handling tool requests and responses
- Serialization and deserialization of tool configurations

### 4. Mailbox
`Mailbox` is an abstract base class for handling message sending and receiving. It provides:
- A unified interface for different LLM providers
- Logging of incoming and outgoing messages
- Batch sending capabilities for concurrent processing

### 5. Auto Terminal
`auto_terminal.py` is a file which starts a chat session with an LLM in which: 
- A bot has access to their computer. 
- It can read and write files, modify python code, and even execute powershell. 
- Use wisely! There are no safety checks in place except those applied to the external LLM (Claude 3.5 Sonnet)

### 6. Lazy Decorator
`lazy.py` is a file which defines a python function decorator. When applied to a function
- The function is filled in by an LLM (Claude 3.5 Sonnet),
- The source code is overwritten,
- The function is run as though it were part of the source code for the remainder of the session.
- Additionally, the code is generated lazily -- functions that are not called during runtime are not created.

### 7. Project Tree
The `project tree` directory is currently under development. The goal is to produce scalable, reliable python products autonomously. Initial project goals and requirements are broken down into modules, and further broken down to the file level. Code in python leaf nodes are generated based on the chain of context from the project root to the python file leaf.

## API Reference

### Bot

The `Bot` class is the base class for all LLM bots.

#### Methods:

- `__init__(api_key, model_engine, max_tokens, temperature, name, role, role_description, conversation, tool_handler, mailbox)`
  - Initializes a new Bot instance.

- `respond(content: str, role: str = "user") -> str`
  - Sends a message to the bot and returns its response.

- `set_system_message(message: str) -> None`
  - Sets the system message for the bot.

- `add_tool(func: Callable) -> None`
  - Adds the function to the bot as a tool.
  - AnthropicBot only at the moment

- `add_tools(filepath: str) -> None`
  - Adds top level functions from a specified file to the bot as tools.
  - AnthropicBot only at the moment

- `save(filename: Optional[str] = None) -> str`
  - Saves the bot's state to a file and returns the filename.

- `chat() -> None`
  - Starts an interactive chat session with the bot.

#### Class Methods:

- `load(filepath: str, api_key=None) -> Bot`
  - Loads a bot from a saved state file.

### ConversationNode

The `ConversationNode` class represents a node in the conversation tree.

#### Methods:

- `__init__(content, role, **kwargs)`
  - Initializes a new ConversationNode.

- `add_reply(**kwargs) -> ConversationNode`
  - Adds a reply to the current node and returns the new node.

- `find_root() -> ConversationNode`
  - Returns the root node of the conversation tree.

- `to_dict() -> Dict[str, Any]`
  - Converts the conversation tree to a dictionary.

- `build_messages() -> List[Dict[str, str]]`
  - Builds a list of messages for API requests.

#### Class Methods:

- `from_dict(data: Dict[str, Any]) -> ConversationNode`
  - Creates a ConversationNode from a dictionary representation.

### ToolHandler

The `ToolHandler` class manages custom tools for the bot.

#### Methods:

- `add_tool(func: Callable) -> None`
  - Adds a new tool (function) to the handler.

- `add_tools_from_file(filepath: str) -> None`
  - Adds tools from a specified Python file.

- `handle_response(response) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]`
  - Processes a response containing tool calls and returns requests and results.

- `get_tools_json() -> str`
  - Returns a JSON string representation of all tools.

### Mailbox

The `Mailbox` class is an abstract base class for handling message sending and receiving.

#### Methods:

- `send_message(conversation, model, max_tokens, temperature, api_key, system_message) -> Tuple[str, str, Dict[str, Any]]`
  - Sends a message to the LLM and returns the processed response.

- `batch_send(conversations, model, max_tokens, temperature, api_key, system_message) -> List[Tuple[str, str, Dict[str, Any]]]`
  - Sends multiple messages concurrently and returns their responses. (Not implemented!)

### Engines

The `Engines` enum represents different LLM models and providers.

#### Enum Values:

- `GPT4`
- `GPT432k`
- `GPT35`
- `CLAUDE3OPUS`
- `CLAUDE3SONNET`
- `CLAUDE35`
- More can be added upon request

#### Methods:

- `get(name: str) -> Engines`
  - Retrieves an Engines enum member by its value.

- `get_bot_class(model_engine: Engines) -> Type[Bot]`
  - Returns the appropriate bot class for the given engine.

## Configuration

LLM Utilities can be configured through environment variables or directly in your code. Here are some important configuration options:

1. API Keys:
   - Set `OPENAI_API_KEY` environment variable for OpenAI models
   - Set `ANTHROPIC_API_KEY` environment variable for Anthropic models

2. Model Selection:
   - Use the `Engines` enum to select the desired model in your code

## Troubleshooting

Here are some common issues and their solutions:

1. **API Key Issues**:
   - Ensure you've set the correct API key for the model you're using.
   - Check that the API key is valid and has the necessary permissions.

2. **Rate Limiting**:
   - Rate limiting options are not yet implemented. Please integrate externally.

3. **Model Availability**:
   - Ensure you're using a model that's available in your account. Some models may require special access.

4. **Memory Issues**:
   - For long conversations, you might encounter memory issues. Consider implementing conversation summarization or pruning old messages.

5. **Tool Execution Errors**:
   - When using custom tools, ensure that all necessary dependencies are installed and that the tool functions are properly defined.

If you encounter any other issues, please check the [GitHub Issues](https://github.com/benbuzz790/llm-utilities/issues) page or open a new issue if your problem isn't already reported.

## Contributing

We welcome contributions to LLM Utilities! Here are some ways you can contribute:

1. Report bugs or suggest features by opening an issue.
2. Improve documentation by submitting pull requests.
3. Add new features or fix bugs by forking the repository and submitting pull requests.

To contribute code:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Write your code and add tests if applicable.
4. Ensure all tests pass.
5. Submit a pull request with a clear description of your changes.

Please adhere to the existing code style and include appropriate tests for new features.

I am still learning git and github, so I may not respond immediately or even in a reasonable amount of time, but I'll try.

## License

LLM Utilities is released under the MIT License. See the [LICENSE](LICENSE) file for details (TBD).

## Additional Resources

~~- [Official Documentation](https://llm-utilities.readthedocs.io/)~~
- [GitHub Repository](https://github.com/benbuzz790/llm-utilities)
~~- [PyPI Package](https://pypi.org/project/llm-utilities/)~~
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Anthropic API Documentation](https://docs.anthropic.com/)

# Bots Framework API Reference
## Overview
The Bots framework provides a unified interface for working with different LLM services (OpenAI and Anthropic), featuring sophisticated conversation management, tool integration, and state persistence. This reference covers all public classes, methods, and their parameters.
## Core Classes
### Bot (Abstract Base Class)
The foundational class for all LLM-powered conversational agents.
#### Constructor Parameters
- pi_key (Optional[str]): API key for the LLM service
- model_engine (Engines): The specific LLM model to use
- max_tokens (int): Maximum tokens in model responses
- 	emperature (float): Randomness in model responses (0.0-1.0)
- 
ame (str): Name identifier for the bot
- ole (str): Bot's role identifier
- ole_description (str): Detailed description of bot's role
- conversation (Optional[ConversationNode]): Initial conversation state
- 	ool_handler (Optional[ToolHandler]): Manager for bot's tools
- mailbox (Optional[Mailbox]): Handler for LLM communication
- utosave (bool): Whether to automatically save state after responses
#### Primary Methods
##### espond(prompt: str, role: str = "user") -> str
Send a prompt to the bot and get its response.
**Parameters:**
- prompt (str): The message to send to the bot
- ole (str): Role of the message sender (defaults to 'user')
**Returns:** str - The bot's response text
**Example:**
`python
bot = AnthropicBot()
response = bot.respond("Hello, how are you?")
print(response)
`
##### dd_tools(*args) -> None
Add Python functions as tools available to the bot.
**Parameters:**
- *args: Variable arguments that can be:
  - str: Path to Python file with tools
  - ModuleType: Module containing tools
  - Callable: Single function to add
  - List/Tuple: Collection of any above types
**Example:**
`python
# Single function
bot.add_tools(calculate_area)
# Multiple files and modules
bot.add_tools(
    "tools/file_ops.py",
    math_tools,
    "tools/network.py",
    [process_data, custom_sort]
)
`
##### save(filename: Optional[str] = None) -> str
Save the bot's complete state to a file.
**Parameters:**
- ilename (Optional[str]): Name for the save file. If None, generates name using bot name and timestamp
**Returns:** str - Path to the saved file
**Example:**
`python
# Save with generated name
path = bot.save()  # e.g., "MyBot@2024-01-20_15-30-45.bot"
# Save with specific name
path = bot.save("code_review_bot")  # saves as "code_review_bot.bot"
`
##### chat() -> None
Start an interactive chat session with the bot in the terminal.
**Example:**
`python
bot.add_tools(my_tools)
bot.chat()
# Interactive session begins
`
##### set_system_message(message: str) -> None
Set the system-level instructions for the bot.
**Parameters:**
- message (str): System instructions for the bot
**Example:**
`python
bot.set_system_message(
    "You are a code review expert. Focus on security and performance."
)
`
#### Class Methods
##### load(filepath: str, api_key: Optional[str] = None) -> "Bot"
Load a saved bot from a file.
**Parameters:**
- ilepath (str): Path to the .bot file to load
- pi_key (Optional[str]): New API key to use, if different from saved
**Returns:** Bot - Reconstructed bot instance with restored state
**Example:**
`python
# Save bot state
bot.save("code_review_bot.bot")
# Later, restore the bot
bot = Bot.load("code_review_bot.bot", api_key="new_key")
`
### AnthropicBot
Anthropic-specific bot implementation for Claude models.
#### Constructor
`python
AnthropicBot(
    api_key: Optional[str] = None,
    model_engine: Engines = Engines.CLAUDE4_SONNET,
    max_tokens: int = 8192,
    temperature: float = 0.3,
    name: str = "Claude",
    role: str = "assistant",
    role_description: str = "a friendly AI assistant",
    autosave: bool = True
)
`
**Parameters:**
- pi_key (Optional[str]): Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
- model_engine (Engines): The Anthropic model to use (default: CLAUDE4_SONNET)
- max_tokens (int): Maximum tokens per response (default: 8192)
- 	emperature (float): Response randomness, 0-1 (default: 0.3)
- 
ame (str): Bot's name (default: 'Claude')
- ole (str): Bot's role (default: 'assistant')
- ole_description (str): Description of bot's role (default: 'a friendly AI assistant')
- utosave (bool): Whether to autosave state after responses (default: True)
**Example:**
`python
from bots import AnthropicBot, Engines
import bots.tools.code_tools as code_tools
# Create a documentation expert bot
bot = AnthropicBot(
    model_engine=Engines.CLAUDE35_SONNET_20241022,
    temperature=0.3,
    role_description="a Python documentation expert"
)
# Add tools and use the bot
bot.add_tools(code_tools)
response = bot.respond("Please analyze this codebase structure.")
`
### ChatGPT_Bot
OpenAI-specific bot implementation for GPT models.
#### Constructor
`python
ChatGPT_Bot(
    api_key: Optional[str] = None,
    model_engine: Engines = Engines.GPT4,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    name: str = "bot",
    role: str = "assistant",
    role_description: str = "a friendly AI assistant",
    autosave: bool = True
)
`
**Parameters:**
- pi_key (Optional[str]): OpenAI API key (uses OPENAI_API_KEY env var if not provided)
- model_engine (Engines): The OpenAI model to use (default: GPT4)
- max_tokens (int): Maximum tokens per response (default: 4096)
- 	emperature (float): Response randomness, 0-1 (default: 0.3)
- 
ame (str): Bot's name (default: 'bot')
- ole (str): Bot's role (default: 'assistant')
- ole_description (str): Description of bot's role (default: 'a friendly AI assistant')
- utosave (bool): Whether to autosave state after responses (default: True)
**Example:**
`python
from bots import ChatGPT_Bot, Engines
import bots.tools.terminal_tools as terminal_tools
# Create a system administration bot
bot = ChatGPT_Bot(
    model_engine=Engines.GPT4TURBO,
    temperature=0.1,
    role_description="a system administration expert"
)
# Add tools and use the bot
bot.add_tools(terminal_tools)
response = bot.respond("Check the system status and disk usage.")
`
## Utility Functions
### load(filepath: str) -> Bot
Convenience function to load a saved bot from a file.
**Parameters:**
- ilepath (str): Path to the .bot file containing the saved bot state
**Returns:** Bot - A reconstructed Bot instance with the saved state
**Example:**
`python
import bots
bot = bots.load("my_saved_bot.bot")
bot.respond("Continue our previous conversation")
`
## Engines Enum
Enumeration of supported LLM models.
### OpenAI Models
- GPT4 = "gpt-4"
- GPT4_0613 = "gpt-4-0613"
- GPT4_32K = "gpt-4-32k"
- GPT4_32K_0613 = "gpt-4-32k-0613"
- GPT4TURBO = "gpt-4-turbo-preview"
- GPT4TURBO_0125 = "gpt-4-0125-preview"
- GPT4TURBO_VISION = "gpt-4-vision-preview"
- GPT35TURBO = "gpt-3.5-turbo"
- GPT35TURBO_16K = "gpt-3.5-turbo-16k"
- GPT35TURBO_0125 = "gpt-3.5-turbo-0125"
- GPT35TURBO_INSTRUCT = "gpt-3.5-turbo-instruct"
### Anthropic Models
- CLAUDE3_HAIKU = "claude-3-haiku-20240307"
- CLAUDE3_SONNET = "claude-3-sonnet-20240229"
- CLAUDE3_OPUS = "claude-3-opus-20240229"
- CLAUDE35_SONNET_20240620 = "claude-3-5-sonnet-20240620"
- CLAUDE35_SONNET_20241022 = "claude-3-5-sonnet-20241022"
- CLAUDE37_SONNET_20250219 = "claude-3-7-sonnet-20250219"
- CLAUDE4_OPUS = "claude-opus-4-20250514"
- CLAUDE4_SONNET = "claude-sonnet-4-20250514"
### Engines Methods
#### get(name: str) -> Optional[Engines]
Retrieve an Engines enum member by its string value.
**Parameters:**
- 
ame (str): The string value of the engine
**Returns:** Optional[Engines] - The corresponding Engines enum member, or None if not found
**Example:**
`python
engine = Engines.get('gpt-4')
if engine:
    bot = ChatGPT_Bot(model_engine=engine)
`
## ConversationNode
Tree-based storage for conversation history and tool interactions.
### Attributes
- ole (str): The role of the message sender ('user', 'assistant', etc.)
- content (str): The message content
- parent (ConversationNode): Reference to the parent node
- eplies (List[ConversationNode]): List of reply nodes
- 	ool_calls (List[Dict]): Tool invocations made in this message
- 	ool_results (List[Dict]): Results from tool executions
- pending_results (List[Dict]): Tool results waiting to be processed
### Key Methods
#### _add_reply(**kwargs) -> ConversationNode
Add a new reply node to this conversation node.
**Parameters:**
- **kwargs: Attributes to set on the new node (content, role, etc.)
**Returns:** ConversationNode - The newly created reply node
#### _build_messages() -> List[Dict[str, Any]]
Build a chronological list of messages from root to this node.
**Returns:** List[Dict[str, Any]] - List of message dictionaries for LLM API
#### _node_count() -> int
Count the total number of nodes in the conversation tree.
**Returns:** int - Total number of nodes in the conversation tree
## Tool Development
### Tool Function Requirements
Tools must follow these requirements:
1. **Function Requirements**
   - Must be top-level functions (not nested in classes)
   - Should prefer string inputs
   - Must return a string
   - Must catch all errors and return error messages as strings
2. **Documentation Requirements**
   - Clear docstring describing what the tool does
   - Explicit "Use when..." section explaining when to use the tool
   - All parameters documented with types and descriptions
   - Return format clearly specified
### Example Tool Function
`python
def lint_code(file_path: str) -> str:
    """Clean code with built in linter.
    Use when you need to clean up your files
    Parameters:
    - file_path (str): Path to the Python file to analyze
    Returns:
    str: Analysis results or error message
    """
    try:
        # Perform analysis
        result = _lint(file_path)
        return result
    except Exception as e:
        return f'Error analyzing {file_path}: {str(e)}'
`
## Complete Usage Examples
### Basic Bot Creation and Usage
`python
from bots import AnthropicBot
import bots.tools.code_tools as code_tools
# Initialize and equip bot
bot = AnthropicBot()
bot.add_tools(code_tools)
# Single response
response = bot.respond("Please write a basic Flask app in app.py")
# Interactive mode
bot.chat()
`
### Save/Load Bot States
`python
import bots
from bots.flows import functional_prompts as fp
# Create a bot with repository context
bot = AnthropicBot()
bot.add_tools(code_tools)
fp.prompt_while(bot, "Read and understand our repo structure")
bot.save("repo.bot")
# Later use
review_bot = bots.load("repo.bot")
review_bot.respond("Review PR #123")
`
### Advanced Configuration
`python
from bots import ChatGPT_Bot, Engines
# Create a specialized bot
bot = ChatGPT_Bot(
    model_engine=Engines.GPT4TURBO,
    max_tokens=8000,
    temperature=0.1,
    name="CodeReviewer",
    role_description="an expert code reviewer focusing on security and performance"
)
# Set system instructions
bot.set_system_message(
    "You are an expert code reviewer. Always check for security vulnerabilities, "
    "performance issues, and adherence to best practices. Provide specific, "
    "actionable feedback."
)
# Add multiple tool sources
bot.add_tools(
    "tools/security_tools.py",
    performance_analysis_module,
    [custom_linter, complexity_analyzer]
)
# Use the bot
response = bot.respond("Please review the authentication system in auth.py")
# Save for later use
bot.save("code_reviewer_v1.bot")
`
## Error Handling
The framework includes comprehensive error handling:
- **ToolNotFoundError**: Raised when a requested tool is not available
- **ModuleLoadError**: Raised when a module cannot be loaded for tool extraction
- **ToolHandlerError**: Base exception class for tool-related errors
`python
from bots.foundation.base import ToolNotFoundError, ModuleLoadError
try:
    bot.add_tools("nonexistent_file.py")
except ModuleLoadError as e:
    print(f"Failed to load tools: {e}")
try:
    # This would raise ToolNotFoundError if tool doesn't exist
    response = bot.respond("Use the nonexistent_tool")
except ToolNotFoundError as e:
    print(f"Tool error: {e}")
`
## Best Practices
1. **Tool Design**: Keep tools focused and single-purpose
2. **Error Handling**: Always catch exceptions in tools and return descriptive error messages
3. **Documentation**: Provide clear docstrings with "Use when..." sections
4. **State Management**: Use autosave for important conversations, disable for temporary interactions
5. **Model Selection**: Choose appropriate models based on task complexity and cost requirements
6. **Temperature Settings**: Use lower temperatures (0.1-0.3) for factual tasks, higher (0.7-0.9) for creative tasks

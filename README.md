# bots

**bots built bots**

## Overview

**bots** is yet another agent framework. What sets bots apart is that it represents conversations as graphs. Messages are nodes, and the conversation is a tree.

This structure facilitates the development of tools which allow bots to manage their own context in various ways, including agentic context removal and agentic branching.

A cli is built on top of this architecture, allowing the user to command a bot which can self-branch and self-prune.

The conversation trees are packaged with python functions and llm model metadata as a "bot". The specified llm will be allowed and able to call those python functions on your system. Agentic branching and pruning are implemented as tools this way. 

**bots** also supports saving and loading. Tools, conversation, and metadata are preserved in a single .bot (json) file.

The bots library also provides a structured interface for programming with such agents, aiming to make agents with dynamic context accessible and sharable for researchers and other sentients. 

## Foundation (bots.foundation)

The core of the Bots library is built on a robust foundation:

- Tool handling capabilities - any well-structured Python function can be used by a bot
- Simple primary interface: `bot.respond()`, with supporting operations `add_tool(s)`, `save()`, `load()`, and `chat()`
- Tree-based conversation management:
  - Implements a linked tree structure for conversation histories
  - Allows branching conversations and exploring multiple dialogue paths
  - Efficiently manages context by only sending path to root
  - Enables saving and loading specific conversation states
- Abstract base classes for wrapping LLM API interfaces into a unified 'bot' interface
- Pre-built implementations for ChatGPT and Anthropic bots
- Complete bot portability - save and share bots with their full context and tools

## Key Features

1. **Auto Terminal (bots.dev.auto_terminal)**
   ```bash
   python -m bots.dev.auto_terminal
   ```
   - Advanced terminal interface for autonomous coding
   - Full conversation tree navigation (/up, /down, /left, /right)
   - Autonomous mode (/auto) - bot works until task completion
   - Tool usage visibility controls (/verbose, /quiet)
   - Save/load bot states for different tasks
   - Integrated Python and PowerShell execution

2. **Tool System (bots.tools)**
   - Standardized tool requirements:
     - Clear docstrings with usage instructions
     - Consistent error handling
     - Predictable return formats
     - Self-contained with explicit dependencies
   - Built-in tools for:
     - File operations (read, write, modify)
     - Code manipulation
     - GitHub integration
     - Terminal operations
   - Tool portability and preservation

3. **Functional Prompts (bots.flows.functional_prompts)**
   - Core operations: chain(), branch(), tree_of_thought()
   - Composable patterns for complex tasks
   - Iteration control (prompt_while, chain_while)
   - Support for parallel exploration
   - Parallel execution functions:
     - par_branch() - Like branch() but processes in parallel
     - par_branch_while() - Like branch_while() but processes in parallel
     - par_dispatch() - Run any functional prompt across multiple bots in parallel
   ```python
   # Example: Parallel analysis using branch()
   responses, nodes = fp.branch(bot, [
       "Technical perspective",
       "User perspective",
       "Business perspective"
   ])

   # Example: Parallel processing with par_branch()
   responses, nodes = fp.par_branch(bot, [
       "Analyze code structure",
       "Review documentation",
       "Check test coverage",
       "Audit dependencies"
   ])

   # Example: Parallel dispatch across multiple bots
   results = fp.par_dispatch(
       bot_list=[bot1, bot2, bot3],
       functional_prompt=fp.chain,
       prompts=["Analyze this component", "Suggest improvements"]
   )
   ```

4. **Lazy Decorator (bots.lazy)**
   - Runtime code generation via LLM
   - Context-aware implementations
   ```python
   @lazy("Sort using a funny algorithm. Name variables as though you're a clown.")
   def sort(arr: list[int]) -> list[int]:
       pass
   ```

## Installation

```bash
pip install git+https://github.com/benbuzz790/bots.git
```

## Quick Start

1. Set up your API key as an environment variable:
   - [OpenAI](https://platform.openai.com/docs/quickstart) or
   - [Anthropic](https://docs.anthropic.com/en/docs/initial-setup#set-your-api-key)

2. Basic Usage:
```python
from bots import AnthropicBot
import bots.tools.code_tools as code_tools

# Initialize and equip bot
bot = AnthropicBot()
bot.add_tools(code_tools)

# Single response
response = bot.respond("Please write a basic Flask app in app.py")

# Interactive mode
bot.chat()
```

3. Save/Load Bot States:
```python
# Create a bot with repository context
bot = AnthropicBot()
bot.add_tools(code_tools)
bot.chat()
  ...
  "Read and understand our repository structure"
  ...
  Tools used...
  ...
  /save

# Later use
import bots
review_bot = bots.load("repo_context.bot", autosave=False)
review_bot.respond("Review PR #123")
```

4. Functional Patterns:
```python
import bots.flows.functional_prompts as fp

# Chain of thought
responses, nodes = fp.chain(bot, [
    "Look at the directory",
    "Read x, y, z",
    "Refactor these three files to better separate concerns"
])

# Parallel exploration
analyses, nodes = fp.branch(bot, [
    "Security analysis",
    "Performance analysis",
    "Usability analysis"
])

# Iterative refinement
fp.prompt_while(
    bot,
    "Run tests and create issues",
    continue_prompt="ok",
    stop_condition=fp.conditions.tool_not_used
)
```

## Advanced Usage

### Tool Development

Tools must follow these patterns for reliability:

```python
def my_tool(param: type) -> str:
    """Clear description of what the tool does.
    
    Use when you need to [specific use case].
    
    Parameters:
    - param (type): Parameter description
    
    Returns:
    str: Description of return format
    """
    try:
        result = do_operation()
        return json.dumps(result)  # For complex returns
    except Exception as e:
        return f'Error: {str(e)}'
```

## Contributing

We welcome contributions!

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Disclaimer

This library is under active development. While it's being used successfully in various projects, please test thoroughly before using in production environments.

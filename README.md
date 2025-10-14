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

1. **Auto Terminal (bots.dev.cli)**
   ```bash
   python -m bots.dev.cli [filename.bot]
   ```
This cli is similar to claude code. Use /help to see all commands.

2. **Tool System (bots.tools)**
   - Supports parallel tool calls
   - Built-in tools for:
     - Reliable python editing
     - Powershell operations
     - Agentic context manipulation
     - General textfile editing

3. **Functional Prompts (bots.flows.functional_prompts)**
   - Core operations: 
      - prompt_while(bot, task_prompt, continue_prompt, condition): bot works in an agentic loop
   - Parallel execution functions:
     - par_branch_while() - processes multiple branches from the current conversation node in parallel

   ```python
   from bots.flows import functional_prompts as fp

   # Example: after discussing a task, execute on multiple files:
   responses, nodes = fp.par_branch_while(bot, [
       "Execute on file one",
       "Execute on file two",
       "Execute on file three"
   ])

   # Example: Parallel dispatch across multiple bots
   results = fp.par_dispatch(
       bot_list=[bot1, bot2, bot3],
       functional_prompt=fp.chain_while,
       prompts=["Commit your changes", "Push to a new PR"]
   )
   ```

4. **Lazy Decorator (bots.lazy)**
   - An experiment
   - Runtime code generation via LLM
   ```python
   @lazy("Sort using a funny algorithm. Name variables as though you're a clown.")
   def sort(arr: list[int]) -> list[int]:
       pass
   # Source code is filled out (and executes) the first time the function is called.
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

## Contributing

We welcome contributions! Read [CONTRIBUTING.md](CONTRIBUTING.md)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Disclaimer

This library is under active development. While it's being used successfully in various projects, please test thoroughly before using in production environments.

# bots: convenient agentic programming

## Overview

**bots** (bɒts), ***n.pl.*** : Tool-using agents, encapsulated with model parameters, conversation history, and tool source code in a single sharable file.

The bots library provides a structured interface for working with such agents, aiming to make agents more convenient, accessible, and sharable for developers and researchers.

## Core Elements

1. **The 'bot' Abstraction**
   The bot abstraction provides a unified interface for working with different LLM services (like OpenAI and Anthropic), 
   handling all the complexity of tool management, conversation history, and state preservation. When you save a bot, 
   it preserves not just the conversation history and model parameters, but also all added tools and their context, 
   allowing complete portability and sharing between developers.
   
   Core functions:
   - `respond(prompt)`: Send a message to the bot and get its response.
   - `add_tools(tools)`: Add Python functions, modules, or files as tools the bot can use.
   - `save(filename)`: Save the complete bot state including conversation history and tools
   - `load(filename)`: Restore a previously saved bot with all its context
   - `chat()`: Start an interactive chat in a terminal with the bot

2. **Automatic Function to Tool Conversion**
   - Define a python function which returns a string. Call bot.add_tools(my_function). The bot can now use the function as a tool.
   - Tools are saved with the bot and run locally.

3. **Tree-based Conversations**
   - Implements a linked tree structure for conversation histories
   - Allows branching conversations and exploring multiple prompt paths
   - Allows sophisticated workflows.

   Example of manual conversation branching:
   ```python
   # Start a conversation
   response = bot.respond("View the current working directory")
   
   # Save current conversation point
   context_complete = bot.conversation
   
   # Branch 1: Update a file
   bot.conversation = context_complete
   branch1_response = bot.respond("Refactor cli.py")
   
   # Branch 2: Update a different file
   bot.conversation = context_complete
   branch2_response = bot.respond("Refactor test_cli.py")
   ```

4. **Functional Prompting**
   - Core operations: chain(), branch(), prompt_while()
   - Composable patterns for complex tasks
   - Iteration control (prompt_while, chain_while)
   - Support for parallel exploration with par_branch() and par_dispatch()

   Example of using prompt_while:
   ```python
   # Continue analyzing until no more tools are used
   responses, nodes = prompt_while(
       bot,
       "Analyze this codebase and fix any issues you find",
       continue_prompt="ok",
       stop_condition=conditions.tool_not_used
   )
   ```

## Key Features

1. **Pre-built Tools**
   - Built-in tools for:
     - Powershell execution
     - Python execution
   - Tool state preservation: When tools are added to a bot and the bot is saved, all tool context 
     (including source code and dependencies) is preserved, allowing the bot to be shared with others 
     who can use the same tools without additional setup (beyond installing this and any other required
     libraries for the tools).

2. **Functional Prompts**
   - A functional prompt is function which sends a bot a prompt or sequence of prompts in a particular way.
   - A 'chain' prompt, for example, sends an array of prompts one after the other:
     ```python
     import functional_prompts as fp
     import bots
     bot = bots.load('my_file.bot')
     fp.chain(bot, ["View the directory", "Read cli.py", "Make me a mermaid diagram of the program flow"])
     ```
   - A 'branch' prompt is similar to a chain, but creates a new conversation branch for each prompt in the list.
   - Parallel branching is easy with the par_branch fp. General parallelization is possible with the par_dispatch fp.
   - Why "functional prompt" and not "workflow?" To emphasize that these are *composable*. 
   - See functional_prompts.py for all available functional prompts and functional_prompt_primer.md for more information.

3. **CLI Interface**
   The CLI interface provides an advanced interface for working with bots interactively. It allows you to
   navigate through conversation history like a tree, moving up to previous points in the conversation and
   exploring different branches. The CLI also features an autonomous mode where the bot will continue
   working on a task until it completes (indicated by no further tool usage).

   ```bash
   python -m bots.dev.cli

   or

   python -m bots.dev.cli [filepath] #Loads bot at filepath
   ```

   Key capabilities:
   - Navigate conversation history with /up, /down, /left, /right, /label, and /goto commands
   - Enable autonomous operation with /auto command (sends 'ok' after each bot response until the bot doesn't use a tool)
   - Control tool output visibility with /verbose and /quiet
   - Save and load bots with /save and /load
   - Run a functional prompt with /fp
        - This starts a wizard to choose and set up a functional prompt
        - Try parallel branching with 'par_branch_while' to make multiple files at the same time
        - Try 'broadcast_to_leaves' afterward to debug each file at the same time

4. **Lazy Decorator**
   The Lazy Decorator enables *runtime code generation* using LLMs. When applied to a function or class,
   it defers implementation until the first time that code is actually called. At runtime, the decorator
   sends relevant context to the LLM and uses its response to create the implementation. The context
   levels control how much information about your codebase is sent to help generate better implementations.

   ```python
   from bots import lazy
   # Using the smart decorator for functions
   @lazy("Sort using a divide-and-conquer approach with O(n log n) complexity")
   def mergesort(arr: list[int]) -> list[int]:
       pass  # Will be implemented by LLM on first call
   
   # Using the smart decorator for classes
   @lazy("Implement a key-value store with LRU eviction policy")
   class Cache:
       pass  # Will be implemented by LLM on first instantiation
   ```
   - Customizable context levels for better implementations:
     - None: No additional context
     - low: Minimal context (class or module)
     - medium: Entire current file
     - high: Current file plus interfaces of other files
     - very high: All Python files in directory
   - Saved bots can be used

   ```python
   # Using the decorator with all options
   @lazy("Implement a key-value store with LRU eviction policy", bot=bots.load('mybot.bot'), context='medium')
   class Cache:
       pass  # Will be implemented by LLM on first instantiation
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
import bots
from bots.flows import functional_prompts as fp
# Create a bot with repository context
bot = AnthropicBot()
bot.add_tools(code_tools)
fp.prompt_while(bot, "Read and understand our repo structure")
bot.save("repo.bot")

# Later use
import bots
review_bot = bots.load("repo.bot", autosave=False)
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

## Tool Development

Tools must follow these specific requirements for reliability and compatibility:

1. **Function Requirements**
   - If using a module or file:
      - Tools must be top-level functions (not nested in classes or other functions)
      - Tools must not start with an underscore (all "_functions()" are stored with the bot, but not made available as tools)
   - Should prefer string inputs
   - Must return a string
   - Must catch all errors and return error messages as strings

2. **Documentation Requirements**
   - Clear docstring describing what the tool does
   - Explicit "Use when..." section explaining when to use the tool
   - All parameters documented with types and descriptions
   - Return format clearly specified

Example of a well-structured tool:

```python
def lint_code(file_path: str) -> str:
    """Clean code with built in linter.

    Use when you need to clean up your files

    Parameters:
    - file_path (str): Path to the Python file to analyze

    Returns:
    str: Analysis results or error message

    cost: medium
    """
    try:
        # Perform analysis
        result = _lint(file_path)
        return result
    except Exception as e:
        return f'Error analyzing {file_path}: {str(e)}'
```

3. **Best Practices**
   - Keep tools focused and single-purpose
   - Handle all edge cases gracefully
   - Return helpful error messages

## Contributing

We welcome contributions!

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Disclaimer

This library is under active development. While it's being used successfully in various projects, please test thoroughly before using in production environments.

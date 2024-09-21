# bots: Making LLM Tools Convenient

## Overview

**bots** (bɒts), ***n.pl.*** : Language Models which are instruct-tuned, have the ability to use tools, and are encapsulated with model parameters, metadata, and conversation history.

The bots library provides a structured interface for working with such agents, aiming to make LLM tools more convenient and accessible for developers and researchers.

## Foundation (bots.foundation)

The core of the Bots library is built on a robust foundation:

- Tool handling capabilities - any python function, file, or module can be given to a bot as a tool
- Key interfaces: `bot.chat()`, `bot.add_tools()`, `bot.respond()`, `bot.save()`, and `bot.load()`
- Tree-based conversation history management:
  - Implements a linked m-tree structure for conversation histories
  - Allows for branching conversations and exploring multiple dialogue paths
- Abstract base classes for wrapping LLM API interfaces into a unified 'bot' interface
- Pre-built implementations for ChatGPT and Anthropic bots

## Features built with bots

1. **Auto Terminal (bots.auto_terminal.auto_terminal)**
   - Command-line interface for autonomous coding (similar to Cursor or Claude-Dev, but in a terminal)
   - Enables bots to work on complex programming tasks with little to no intervention
   - Supports loading and saving bot states for long-running projects
   - Offers verbose and quiet modes for monitoring bot activities

2. **Python Tools (bots.tools.python_tools)**
   - Comprehensive toolkit enabling bots to perform file and code operations autonomously
   - Functions for reading, writing, and modifying Python files
   - Code execution capabilities for both Python and PowerShell
   - Specialized functions for adding, replacing, or modifying classes and functions in existing Python files
   - Empowers bots to engage in complex coding tasks and project modifications

3. **Lazy Decorator (bots.lazy.lazy)**
   - Decorator for runtime code generation via LLM calls
   - Automatically replaces placeholder functions with LLM-generated implementations
   - Supports various levels of context awareness for accurate code generation
   - Integrates with existing codebases for dynamic functionality expansion

4. **Functional Prompts (bots.functional_prompts)**
   - Advanced prompting techniques for complex, multi-step tasks
   - Supports sequential processing and branching with multiple bots
   - Enables the creation of sophisticated workflows for content generation and problem-solving
## Installation

```bash
pip install git+https://github.com/benbuzz790/bots.git
```

## Quick Start
Set up your api key environment variables
[OpenAI](https://platform.openai.com/docs/quickstart)
[Anthropic](https://docs.anthropic.com/en/docs/initial-setup#set-your-api-key)

You'll need one of these two to use bots, and for now you'll need an Anthropic key for auto_terminal.

```python
from bots import AnthropicBot
from bots.tools import python_tools

# Initialize a bot
bot = AnthropicBot(name='Claude')

# Add Python tools to the bot
bot.add_tools(python_tools)

# Request action
bot.respond("Please write Conway's game of life in a new file conway.py")
```

```cmd
:: Start an autonomous coding session
>>> python -m bots.auto_terminal.auto_terminal
System: Bot initialized

---  
     
You: /help

---

System:
    This program is an interactive terminal that uses Anthropic's Claude Sonnet 3.5.
    It allows you to chat with the LLM, save and load bot states, and execute various commands.
    The bot has the ability to read and write files and can execute powershell and python code 
    directly.
    The bot also has tools to help edit python files in an accurate and token-efficient way.
    Available commands:
    /help: Show this help message
    /verbose: Show tool requests and results (default on)
    /quiet: Hide tool requests and results
    /save: Save the current bot
    /load: Load a previously saved bot
    /auto: Prompt the bot to work autonomously for a preset number of prompts
    /exit: Exit the program
    Type your messages normally to chat with the AI assistant.

---


You: please write conway's game of life into a GUI and execute it. no need to save

---

Claude: Let's create a GUI version of Conway's Game of Life using
    Python's tkinter library. Here's the code:

---

System: Tool Requests
    [
     {
      "type": "tool_use",
      "id": "toolu_0139UTzShnVnXTen2pT1y8Su",
      "name": "execute_python_code",
      "input": {
       "code": <removed for brevity>
      }
     }
    ]

---

System: Tool Results
    [
     {
      "type": "tool_result",
      "tool_use_id": "toolu_0139UTzShnVnXTen2pT1y8Su",
      "content": ""
     }
    ]

---

```

## Advanced Usage

### Using the Lazy Decorator

```python
from bots.lazy import lazy

@lazy(prompt="Implement a function that calculates the fibonacci sequence up to n terms.")
def fibonacci(n: int) -> list:
    pass

# The first call to fibonacci will generate the implementation
result = fibonacci(10)
print(result)
```

### Working with Functional Prompts

```python
import bots
import bots.functional_prompts as fp

def main():
    bot = bots.AnthropicBot(name="letter_writer")

    # First prompt
    p1 = "Please help me write an invitaion to a birthday party"

    # Define different styles for the letter
    styles = ["formal", "casual", "humorous"]

    # Define branching prompt list
    plist = [f"Use a {style} style" for style in styles]

    # Use the branch function to generate letters in different styles
    first_response = bot.respond(p1)
    letters, _ = fp.branch(bot, plist)

    # Print the results
    for style, letter in zip(styles, letters):
        print(f"\n--- {style.capitalize()} Letter ---")
        print(letter)
        print("-------------------------\n")

if __name__ == "__main__":
    main()
```

This example demonstrates how to use functional prompts with the `branch` function to generate multiple versions of a letter in different styles, based on a single purpose.

## Contributing

We welcome contributions to the Bots project! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Disclaimer

This library is still under active development and may not be suitable for large-scale industry adoption. Use with caution in production environments.

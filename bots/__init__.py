"""Bots package initialization and primary interface.

This module serves as the main entry point for the bots package, providing access to:
- Core bot implementations:
    - AnthropicBot: Claude-based bot implementation
    - ChatGPT_Bot: GPT-based bot implementation
- Development tools:
    - auto_terminal: Advanced terminal interface for autonomous coding
    - lazy: Runtime code generation decorator
    - project_tree: Project structure analysis and management
- Tool collections:
    - python_editing_tools: Python code modification utilities
    - meta_tools: Bot self-modification capabilities
    - terminal_tools: Command-line interaction tools
    - code_tools: General code manipulation utilities
    - self_tools: Bot introspection utilities

The package follows a layered architecture with foundation, flows, and tools layers.
All commonly used components are imported here for convenient access.

Example Usage:
    >>> from bots import AnthropicBot
    >>> import bots.tools.code_tools as code_tools
    >>> 
    >>> # Initialize and equip bot
    >>> bot = AnthropicBot()
    >>> bot.add_tools(code_tools)
    >>> 
    >>> # Single response
    >>> response = bot.respond("Please write a basic Flask app")
    >>> 
    >>> # Interactive mode
    >>> bot.chat()
"""

# Core bot implementations and base classes
from .foundation.anthropic_bots import AnthropicBot
from .foundation.openai_bots import ChatGPT_Bot
from .foundation.base import Engines
from .foundation.base import load

# Development and project management tools
from .dev import auto_terminal
from .dev.decorators import lazy
from .flows.project_tree import project_tree

# Tool collections for bot capabilities
from .tools import *

__all__ = [
    # Core bot implementations
    'AnthropicBot',
    'ChatGPT_Bot',
    'Engines',
    'load',
    
    # Development tools
    'auto_terminal',
    'lazy',
    'project_tree',
    
    # Tool collections
    'python_editing_tools',
    'python_execution_tool',
    'meta_tools',
    'terminal_tools',
    'self_tools',
    'code_tools',
]

"""Foundation module for the bots library.

This module provides the core abstractions and implementations for working with Language Models
that are instruct-tuned and have tool-using capabilities. It includes base classes and specific
implementations for different LLM providers.

Performance Considerations:
    - Conversation trees optimize context window usage
    - Tool execution is handled efficiently with proper error management

Key Components:
    - Bot: Abstract base class defining the core bot interface
    - ToolHandler: Manages tool registration and execution
    - ConversationNode: Tree-based conversation history management
    - Specific implementations (e.g., AnthropicBot, OpenAIBot)

The foundation module emphasizes:
    - Simple primary interface with bot.respond()
    - Comprehensive tool use capabilities - any Callables, modules, or python files can be tools.
    - Tree-based conversation management
    - Complete bot portability
    - Unified interface across different LLM providers

Example:
    >>> from bots import AnthropicBot
    >>> from typing import Callable
    >>> def my_function(x: int) -> str:
    ...     '''Example tool function'''
    ...     return str(x * 2)
    >>> 
    >>> bot = AnthropicBot()
    >>> bot.add_tool(my_function)  # type: Callable
    >>> response: str = bot.respond("Use the tool to multiply 5 by 2")
    >>> bot.save("my_bot.bot")  # Save complete bot state
    
See Also:
    - bots.flows: Higher-level interaction patterns
    - bots.tools: Built-in tool implementations
"""
# Version and compatibility information
__version__ = "0.1.0"  # type: str
"""Package version number, following semantic versioning."""

__python_requires__ = ">=3.9"
"""Minimum Python version required for this package."""
__version__ = "0.1.0"

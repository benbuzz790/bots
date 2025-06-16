bots: Making LLM Tool Use Convenient and Powerful
===============================================
Overview
--------
**bots** (*bɒts*), *n.pl.* : Language Models which are instruct-tuned, have the ability to use tools, and are encapsulated with model parameters, metadata, and conversation history.
The bots library provides a structured interface for working with such agents, aiming to make LLM tools more convenient, accessible, and sharable for developers and researchers.
Foundation (bots.foundation)
---------------------------
The core of the Bots library is built on a robust foundation:
- Tool handling capabilities - any well-structured Python function can be used by a bot
- Simple primary interface: ``bot.respond()``, with supporting operations ``add_tool(s)``, ``save()``, ``load()``, and ``chat()``
- Tree-based conversation management:
    - Implements a linked tree structure for conversation histories
    - Allows branching conversations and exploring multiple dialogue paths
    - Efficiently manages context by only sending path to root
    - Enables saving and loading specific conversation states
- Abstract base classes for wrapping LLM API interfaces into a unified "bot" interface
- Pre-built implementations for ChatGPT and Anthropic bots
- Complete bot portability - save and share bots with their full context and tools
Contents
--------
.. toctree::
   :maxdepth: 2
   :caption: Documentation:
   source/modules
Key Features
-----------
Auto Terminal (bots.dev.auto_terminal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: bash
   python -m bots.dev.auto_terminal
- Advanced terminal interface for autonomous coding
- Full conversation tree navigation (/up, /down, /left, /right)
- Autonomous mode (/auto) - bot works until task completion
- Tool usage visibility controls (/verbose, /quiet)
- Save/load bot states for different tasks
- Integrated Python and PowerShell execution
Tool System (bots.tools)
~~~~~~~~~~~~~~~~~~~~~~
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
Functional Prompts (bots.flows.functional_prompts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Core operations: chain(), branch(), tree_of_thought()
- Composable patterns for complex tasks
- Iteration control (prompt_while, chain_while)
- Support for parallel exploration
- Parallel execution functions
API Reference
------------
.. toctree::
   :maxdepth: 3
   :caption: API Documentation:
   source/bots
Indices and Tables
-----------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

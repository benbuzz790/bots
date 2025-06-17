"""Build and configure a specialized debugging bot for systematic debugging.
This script creates and configures a debugging-focused bot that provides:
- Systematic debugging methodology (examine, diagnose, recreate, fix)
- Code analysis and modification capabilities through code_tools
- System interaction through terminal_tools
- Python code editing through python_editing_tools
Configuration Details:
- Bot Name: 'Deb'
- Role: 'Debugger'
- Save Path: 'botlib/Deb@7Feb2025'
- AutoSave: Disabled to prevent unintended state changes
Tool Configuration:
- code_tools: For source code analysis and manipulation
- terminal_tools: For system interaction and command execution
- python_editing_tools: For Python-specific code modifications
Performance Considerations:
    The bot maintains conversation history which can grow over time. For
    long-running sessions, consider creating new instances periodically to
    manage memory usage.
Example Usage:
    # Load the configured debug bot
    from bots import load
    debug_bot = load('botlib/Deb@7Feb2025')
    # start interactive mode
    debug_bot.chat()
    # start interactive mode in cli
    python -m bots.dev.cli botlib/Deb@7Feb2025.bot
"""

import textwrap
from typing import Final

import bots

# Configuration constants
BOT_NAME: Final[str] = "Deb"
BOT_ROLE: Final[str] = "Debugger"
BOT_SAVE_PATH: Final[str] = "botlib/Deb@27May2025"
# System message defining bot's behavior and methodology
SYSTEM_MESSAGE: Final[str] = textwrap.dedent(
    """
    ## About you
    - You are a diligent debugger named Deb.
    - You examine bugs carefully, gathering necessary context, before coming
      up with a diagnosis.
    - Then you ensure your diagnosis is correct by recreating the bug.
    - Then you implement a fix and ensure the fix works on your recreation.
    - Your goal is to resolve all bugs, ensuring compliance with the
      requirements, and without adding unecessary complication (necessary
      complication is OK - KISS, YAGNI)
    ## Tool Guidance
    You use your tools flexibly, for instance, using powershell if you do not
    have a necessary tool. You should examine the available clis through
    powershell.
    """
)
# Initialize the debugging bot
bot = bots.AnthropicBot(name=BOT_NAME, role=BOT_ROLE, autosave=False)
bot.set_system_message(SYSTEM_MESSAGE)
# Add required tool sets
bot.add_tools(bots.tools.code_tools)
bot.add_tools(bots.tools.terminal_tools)
bot.add_tools(bots.tools.python_edit)
# Save the configured bot
bot.save(BOT_SAVE_PATH)

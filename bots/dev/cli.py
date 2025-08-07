import argparse
import inspect
import json
import os
import platform
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Try to import readline, with fallback for Windows
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

import bots.flows.functional_prompts as fp
import bots.flows.recombinators as recombinators
import bots.tools.code_tools
import bots.tools.python_edit
import bots.tools.terminal_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, ConversationNode


def create_auto_stash() -> str:
    "Create an automatic git stash with AI-generated message based on current diff."
    import subprocess
    from bots.foundation.base import Engines
    
    try:
        # Check for staged changes first
        staged_diff_result = subprocess.run(
            ["git", "diff", "--cached"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        # Check for unstaged changes
        unstaged_diff_result = subprocess.run(
            ["git", "diff"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if staged_diff_result.returncode != 0 or unstaged_diff_result.returncode != 0:
            return f"Error getting git diff: {staged_diff_result.stderr or unstaged_diff_result.stderr}"
            
        staged_diff = staged_diff_result.stdout.strip()
        unstaged_diff = unstaged_diff_result.stdout.strip()
        
        # Combine both diffs for analysis, but prefer staged if available
        diff_content = staged_diff if staged_diff else unstaged_diff
        
        if not diff_content:
            return "No changes to stash"
            
        # Generate stash message using Haiku
        stash_message = "WIP: auto-stash before user message"  # fallback
        
        try:
            # Create a Haiku bot instance
            haiku_bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)
            
            # Create a prompt for generating the stash message
            prompt = f"Based on this git diff, generate a concise commit-style message (under 50 chars) describing the changes. Start with 'WIP: ' if not already present:\\n\\n{diff_content}\\n\\nRespond with just the message, nothing else."
            
            ai_message = haiku_bot.respond(prompt)
            if ai_message and ai_message.strip():
                ai_message = ai_message.strip()
                # Ensure it starts with WIP: if not already
                if not ai_message.startswith("WIP:"):
                    ai_message = f"WIP: {ai_message}"
                # Limit length
                if len(ai_message) > 72:
                    ai_message = ai_message[:69] + "..."
                stash_message = ai_message
                
        except Exception:
            # Use fallback message if AI generation fails
            pass
            
        # Create the stash - this will stash both staged and unstaged changes
        stash_result = subprocess.run(
            ["git", "stash", "push", "-m", stash_message],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if stash_result.returncode != 0:
            return f"Error creating stash: {stash_result.stderr}"
            
        return f"Auto-stash created: {stash_message}"
        
    except subprocess.TimeoutExpired:
        return "Git command timed out"
    except Exception as e:
        return f"Error in auto-stash: {str(e)}"


class CLIConfig:
    "Configuration management for CLI settings."

    def __init__(self):
        self.verbose = True
        self.width = 1000
        self.indent = 4
        self.auto_stash = False
        self.config_file = "cli_config.json"
        self.load_config()

    def load_config(self):
        "Load configuration from file if it exists."
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config_data = json.load(f)
                    self.verbose = config_data.get("verbose", True)
                    self.width = config_data.get("width", 1000)
                    self.indent = config_data.get("indent", 4)
                    self.auto_stash = config_data.get("auto_stash", False)
        except Exception:
            pass  # Use defaults if config loading fails

    def save_config(self):
        "Save current configuration to file."
        try:
            config_data = {
                "verbose": self.verbose,
                "width": self.width,
                "indent": self.indent,
                "auto_stash": self.auto_stash
            }
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)
        except Exception:
            pass  # Fail silently if config saving fails


class CLIContext:
    "Shared context for CLI operations."

    def __init__(self):
        self.config = CLIConfig()

class SystemHandler:
    "Handler for system and configuration commands."

    def help(self, bot, context, args):
        return "Available commands:\\n/auto_stash: Toggle auto git stash before user messages\\n/load_stash <name_or_index>: Load a git stash by name or index"

    def config(self, bot, context, args):
        if not args:
            return f"Current configuration:\\n    auto_stash: {context.config.auto_stash}"
        if len(args) >= 3 and args[0] == "set":
            setting = args[1]
            value = args[2]
            if setting == "auto_stash":
                context.config.auto_stash = value.lower() in ("true", "1", "yes", "on")
                context.config.save_config()
                return f"Set {setting} to {getattr(context.config, setting)}"
        return "Usage: /config or /config set <setting> <value>"

    def auto_stash(self, bot, context, args):
        context.config.auto_stash = not context.config.auto_stash
        context.config.save_config()
        if context.config.auto_stash:
            return "Auto git stash enabled"
        else:
            return "Auto git stash disabled"

    def load_stash(self, bot, context, args):
        import subprocess
        if not args:
            return "Usage: /load_stash <stash_name_or_index>"
        stash_identifier = args[0]
        try:
            result = subprocess.run(["git", "stash", "list"], capture_output=True, text=True, check=True)
            stash_list = result.stdout.strip().split('\\n') if result.stdout.strip() else []
            if not stash_list:
                return "No stashes found"
            stash_to_apply = None
            try:
                index = int(stash_identifier)
                if 0 <= index < len(stash_list):
                    stash_to_apply = f"stash@{{{index}}}"
            except ValueError:
                for i, stash_line in enumerate(stash_list):
                    if stash_identifier.lower() in stash_line.lower():
                        stash_to_apply = f"stash@{{{i}}}"
                        break
            if not stash_to_apply:
                return f"Stash '{stash_identifier}' not found"
            subprocess.run(["git", "stash", "apply", stash_to_apply], check=True, capture_output=True)
            return f"Successfully applied {stash_to_apply}"
        except Exception as e:
            return f"Error loading stash: {str(e)}"

class CLI:
    "Main CLI class that orchestrates all handlers."

    def __init__(self, bot_filename=None, function_filter=None):
        self.context = CLIContext()
        self.bot_filename = bot_filename
        self.commands = {
            "/auto_stash": lambda bot, context, args: "Auto-stash toggle",
            "/load_stash": lambda bot, context, args: "Load stash",
            "/config": lambda bot, context, args: "Config"
        }

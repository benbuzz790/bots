"""Prompt management command handlers for the CLI."""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from bots.dev.cli_modules.config import CLIContext
from bots.dev.cli_modules.utils import EscapeException, input_with_esc
from bots.foundation.base import Bot

try:
    import readline

    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False


class PromptManager:
    """Manager for saving, loading, and editing prompts with recency tracking."""

    def __init__(self, prompts_file: str = "bots/prompts.json"):
        self.prompts_file = Path(prompts_file)
        self.prompts_data = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from file or create empty structure."""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"recents": [], "prompts": {}}

    def _save_prompts(self):
        """Save prompts to file."""
        try:
            # Ensure directory exists
            self.prompts_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.prompts_file, "w", encoding="utf-8") as f:
                json.dump(self.prompts_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise Exception(f"Failed to save prompts: {e}")

    def _update_recents(self, prompt_name: str):
        """Update recency list, moving prompt to front."""
        recents = self.prompts_data["recents"]
        if prompt_name in recents:
            recents.remove(prompt_name)
        recents.insert(0, prompt_name)
        # Keep only first 5
        self.prompts_data["recents"] = recents[:5]

    def _generate_prompt_name(self, prompt_text: str) -> str:
        """Generate a name for the prompt using Claude Haiku."""
        try:
            from bots.foundation.anthropic_bots import AnthropicBot
            from bots.foundation.base import Engines

            # Create a quick Haiku bot for naming
            naming_bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)

            # Truncate prompt if too long for naming
            truncated_prompt = prompt_text[:500] + "..." if len(prompt_text) > 500 else prompt_text

            naming_prompt = f"""Generate a short, descriptive name (2-4 words, snake_case) for this prompt:

{truncated_prompt}

Respond with just the name, no explanation."""

            response = naming_bot.respond(naming_prompt)
            # Clean up the response - extract just the name
            name = response.strip().lower()
            # Remove any non-alphanumeric characters except underscores
            name = re.sub(r"[^a-z0-9_]", "", name)
            # Ensure it's not empty
            if not name:
                name = "unnamed_prompt"
            return name

        except Exception:
            # Fallback to timestamp-based name
            return f"prompt_{int(time.time())}"

    def search_prompts(self, query: str) -> List[tuple]:
        """Search prompts by name and content. Returns list of (name, content) tuples."""
        if not query:
            # Return recents if no query
            results = []
            for name in self.prompts_data["recents"]:
                if name in self.prompts_data["prompts"]:
                    results.append((name, self.prompts_data["prompts"][name]))
            return results

        query_lower = query.lower()
        results = []

        for name, content in self.prompts_data["prompts"].items():
            # Search in name and content
            if query_lower in name.lower() or query_lower in content.lower():
                results.append((name, content))

        return results

    def save_prompt(self, prompt_text: str, name: str = None) -> str:
        """Save a prompt with optional name. If no name, generate one."""
        if not name:
            name = self._generate_prompt_name(prompt_text)

        # Ensure unique name
        original_name = name
        counter = 1
        while name in self.prompts_data["prompts"]:
            name = f"{original_name}_{counter}"
            counter += 1

        self.prompts_data["prompts"][name] = prompt_text
        self._update_recents(name)
        self._save_prompts()
        return name

    def load_prompt(self, name: str) -> str:
        """Load a prompt by name and update recency."""
        if name not in self.prompts_data["prompts"]:
            raise KeyError(f"Prompt '{name}' not found")

        self._update_recents(name)
        self._save_prompts()
        return self.prompts_data["prompts"][name]

    def get_prompt_names(self) -> List[str]:
        """Get all prompt names."""
        return list(self.prompts_data["prompts"].keys())

    def delete_prompt(self, name: str) -> bool:
        """Delete a prompt by name. Returns True if deleted, False if not found."""
        if name not in self.prompts_data["prompts"]:
            return False

        # Remove from prompts
        del self.prompts_data["prompts"][name]

        # Remove from recents if present
        if name in self.prompts_data["recents"]:
            self.prompts_data["recents"].remove(name)

        self._save_prompts()
        return True

    def get_recents(self) -> List[tuple]:
        """Get recent prompts as list of (name, content) tuples."""
        results = []
        for name in self.prompts_data["recents"]:
            if name in self.prompts_data["prompts"]:
                results.append((name, self.prompts_data["prompts"][name]))
        return results


class PromptHandler:
    """Handler for prompt management commands."""

    def __init__(self):
        self.prompt_manager = PromptManager()

    def _get_input_with_prefill(self, prompt_text: str, prefill: str = "") -> str:
        """Get input with pre-filled text using readline if available."""
        if not HAS_READLINE or not prefill:
            return input(prompt_text)

        def startup_hook():
            readline.insert_text(prefill)
            readline.redisplay()

        readline.set_startup_hook(startup_hook)
        try:
            user_input = input(prompt_text)
            return user_input
        finally:
            readline.set_startup_hook(None)

    def load_prompt(self, bot: "Bot", context: "CLIContext", args: List[str]) -> tuple:
        """Load a saved prompt by name or search query.

        Returns tuple of (status_message, prompt_content) for use by CLI.
        """
        if not args:
            # Show recent prompts
            recents = self.prompt_manager.get_recents()
            if recents:
                print("\nRecent prompts:")
                for i, (name, _content) in enumerate(recents[:10], 1):
                    print(f"  {i}. {name}")

                try:
                    selection = input_with_esc("\nEnter number or name to load (ESC to cancel): ").strip()
                    if selection.isdigit():
                        idx = int(selection) - 1
                        if 0 <= idx < len(recents):
                            name = recents[idx][0]
                        else:
                            return ("Invalid selection.", None)
                    else:
                        name = selection
                except EscapeException:
                    return ("Load cancelled.", None)
            else:
                # No recents, prompt for search query
                try:
                    name = input_with_esc("\nEnter prompt name or search query: ").strip()
                    if not name:
                        return ("Load cancelled.", None)
                except EscapeException:
                    return ("Load cancelled.", None)
        else:
            name = " ".join(args)

        # Try exact match first
        try:
            content = self.prompt_manager.load_prompt(name)
            return (f"Loaded prompt: {name}", content)
        except KeyError:
            pass

        # Try fuzzy search
        matches = self.prompt_manager.search_prompts(name)

        if not matches:
            return ("No prompts found matching your search.", None)

        if len(matches) == 1:
            # Single match - load directly
            name, content = matches[0]
            self.prompt_manager.load_prompt(name)  # Update recency
            return (f"Loaded prompt: {name}", content)

        # Multiple matches - show selection with best match highlighted
        print(f"\nFound {len(matches)} matches (best match first):")
        for i, (name, content) in enumerate(matches[:10], 1):  # Limit to 10 results
            # Show preview of content
            preview = content[:80] + "..." if len(content) > 80 else content
            preview = preview.replace("\n", " ")  # Single line preview
            marker = "Ã¢â€ â€™" if i == 1 else " "
            print(f"  {marker} {i}. {name}: {preview}")

        if len(matches) > 10:
            print(f"  ... and {len(matches) - 10} more matches")

        try:
            selection = input_with_esc("\nEnter number or name to load (ESC to cancel): ").strip()
            if selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(matches):
                    name, content = matches[idx]
                else:
                    return ("Invalid selection.", None)
            else:
                # Try to find by name in matches
                name = selection
                content = None
                for match_name, match_content in matches:
                    if match_name == name:
                        content = match_content
                        break
                if content is None:
                    return (f"'{name}' not in search results.", None)

            self.prompt_manager.load_prompt(name)  # Update recency
            return (f"Loaded prompt: {name}", content)
        except EscapeException:
            return ("Load cancelled.", None)

    def save_prompt(self, bot: "Bot", context: "CLIContext", args: List[str], last_user_message: str = None) -> str:
        """Save a prompt. If args provided, save the args. Otherwise save last user message."""
        try:
            if args:
                # Save the provided text
                prompt_text = " ".join(args)
            elif last_user_message:
                # Save the last user message
                prompt_text = last_user_message
            else:
                return "No prompt to save. Either provide text with /s or use /s after sending a message."

            if not prompt_text.strip():
                return "Cannot save empty prompt."

            # Generate name and save
            name = self.prompt_manager.save_prompt(prompt_text)
            return f"Saved prompt as: {name}"

        except Exception as e:
            return f"Error saving prompt: {str(e)}"

    def delete_prompt(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Delete a saved prompt."""
        try:
            # Get prompt name
            if args:
                query = " ".join(args)
            else:
                query = input("Enter prompt name or search: ").strip()

            if not query:
                return "Delete cancelled."

            # Search for matching prompts
            matches = self.prompt_manager.search_prompts(query)

            if not matches:
                return "No prompts found matching your search."

            if len(matches) == 1:
                # Single match - confirm and delete
                name, content = matches[0]
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")
                print(f"\nPrompt to delete: {name}")
                print(f"Content: {preview}")
                confirm = input("Delete this prompt? (y/n): ").strip().lower()

                if confirm == "y":
                    if self.prompt_manager.delete_prompt(name):
                        return f"Deleted prompt: {name}"
                    else:
                        return f"Failed to delete prompt: {name}"
                else:
                    return "Delete cancelled."

            # Multiple matches - show selection
            print(f"\nFound {len(matches)} matches:")
            for i, (name, content) in enumerate(matches[:10], 1):
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")
                print(f"  {i}. {name}: {preview}")

            if len(matches) > 10:
                print(f"  ... and {len(matches) - 10} more matches")

            # Get selection
            try:
                choice = input(f"\nSelect prompt to delete (1-{min(len(matches), 10)}): ").strip()
                if not choice:
                    return "Delete cancelled."

                choice_num = int(choice) - 1
                if choice_num < 0 or choice_num >= min(len(matches), 10):
                    return f"Invalid selection. Must be between 1 and {min(len(matches), 10)}."

                name, content = matches[choice_num]
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")
                print(f"\nPrompt to delete: {name}")
                print(f"Content: {preview}")
                confirm = input("Delete this prompt? (y/n): ").strip().lower()

                if confirm == "y":
                    if self.prompt_manager.delete_prompt(name):
                        return f"Deleted prompt: {name}"
                    else:
                        return f"Failed to delete prompt: {name}"
                else:
                    return "Delete cancelled."

            except ValueError:
                return "Invalid selection. Must be a number."

        except Exception as e:
            return f"Error deleting prompt: {str(e)}"

    def recent_prompts(self, bot: "Bot", context: "CLIContext", args: List[str]) -> tuple:
        """Show recent prompts and optionally select one. Returns (message, prefill_text)."""
        try:
            recents = self.prompt_manager.get_recents()

            if not recents:
                return ("No recent prompts.", None)

            # Show recents
            print(f"\nRecent prompts ({len(recents)}):")
            for i, (name, content) in enumerate(recents, 1):
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")
                print(f"  {i}. {name}: {preview}")

            # Get selection
            try:
                choice = input(f"\nSelect prompt (1-{len(recents)}, or Enter to cancel): ").strip()
                if not choice:
                    return ("Selection cancelled.", None)

                choice_num = int(choice) - 1
                if choice_num < 0 or choice_num >= len(recents):
                    return (f"Invalid selection. Must be between 1 and {len(recents)}.", None)

                name, content = recents[choice_num]
                self.prompt_manager.load_prompt(name)  # Update recency

                return (f"Loaded prompt: {name}", content)

            except ValueError:
                return ("Invalid selection. Must be a number.", None)

        except Exception as e:
            return (f"Error loading recent prompts: {str(e)}", None)

"""
Conversation navigation handler for CLI.

This module handles all conversation tree navigation commands including
up/down/left/right movement, fork navigation, labeling, and leaf operations.
"""

from collections import deque
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from bots.dev.cli.config import CLIContext
    from bots.foundation.base import Bot

from bots.dev.cli.display import pretty
from bots.dev.cli.utils import (
    COLOR_ASSISTANT,
    EscapeException,
    find_leaves,
    input_with_esc,
)
from bots.flows import functional_prompts as fp
from bots.flows import recombinators
from bots.foundation.base import ConversationNode


class ConversationHandler:
    """Handler for conversation navigation commands."""

    def up(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Move up in conversation tree."""
        if bot.conversation.parent and bot.conversation.parent.parent:
            context.conversation_backup = bot.conversation
            bot.conversation = bot.conversation.parent.parent
            if not self._ensure_assistant_node(bot):
                return "Warning: Ended up on user node with no assistant response. Bumped to previous assistant node."
            self._display_conversation_context(bot, context)
            return "Moved up conversation tree"
        return "At root - can't go up"

    def down(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Move down in conversation tree."""
        if bot.conversation.replies:
            max_index = len(bot.conversation.replies) - 1
            idx = 0
            if max_index > 0:
                try:
                    try:
                        idx = int(input_with_esc(f"Reply index (max {max_index}): "))
                    except EscapeException:
                        return "Selection cancelled"
                    if idx < 0 or idx > max_index:
                        return f"Invalid index. Must be between 0 and " f"{max_index}"
                except ValueError:
                    return "Invalid index. Must be a number"
            context.conversation_backup = bot.conversation
            next_node = bot.conversation.replies[idx]
            if next_node.replies:
                bot.conversation = next_node.replies[0]
            else:
                bot.conversation = next_node
            if not self._ensure_assistant_node(bot):
                return "Warning: Ended up on user node with no assistant response"  # noqa: E501
            self._display_conversation_context(bot, context)
            return "Moved down conversation tree"
        return "At leaf - can't go down"

    def left(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Move left to sibling in conversation tree."""
        if not bot.conversation.parent:
            return "At root - can't go left"
        replies = bot.conversation.parent.replies
        if not replies or len(replies) <= 1:
            return "Conversation has no siblings at this point"
        current_index = next((i for i, reply in enumerate(replies) if reply is bot.conversation))
        next_index = (current_index - 1) % len(replies)
        context.conversation_backup = bot.conversation
        bot.conversation = replies[next_index]
        if not self._ensure_assistant_node(bot):
            return "Warning: Ended up on user node with no assistant response"  # noqa: E501
        self._display_conversation_context(bot, context)
        return "Moved left in conversation tree"

    def right(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Move right to sibling in conversation tree."""
        if not bot.conversation.parent:
            return "At root - can't go right"
        replies = bot.conversation.parent.replies
        if not replies or len(replies) <= 1:
            return "Conversation has no siblings at this point"
        current_index = next((i for i, reply in enumerate(replies) if reply is bot.conversation))
        next_index = (current_index + 1) % len(replies)
        context.conversation_backup = bot.conversation
        bot.conversation = replies[next_index]
        if not self._ensure_assistant_node(bot):
            return "Warning: Ended up on user node with no assistant response"  # noqa: E501
        self._display_conversation_context(bot, context)
        return "Moved right in conversation tree"

    def root(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Move to root of conversation tree."""
        context.conversation_backup = bot.conversation
        while bot.conversation.parent:
            bot.conversation = bot.conversation.parent
        if not self._ensure_assistant_node(bot):
            return "Warning: Ended up on user node with no assistant response"  # noqa: E501
        self._display_conversation_context(bot, context)
        return "Moved to root of conversation tree"

    def lastfork(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Move to the previous node (going up) that has multiple replies."""
        current = bot.conversation

        # Traverse up the tree looking for a fork
        while current.parent:
            current = current.parent
            # Check if this node has multiple replies (is a fork)
            if len(current.replies) > 1:
                context.conversation_backup = bot.conversation
                bot.conversation = current
                if not self._ensure_assistant_node(bot):
                    return "Warning: Moved to fork but ended up on user node " "with no assistant response"
                self._display_conversation_context(bot, context)
                return f"Moved to previous fork ({len(current.replies)} branches)"  # noqa: E501

        return "No fork found going up the tree"

    def nextfork(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Move to the next node (going down) that has multiple replies."""
        # Use BFS to search down the tree for the first fork
        queue = deque([bot.conversation])
        visited = {bot.conversation}

        while queue:
            current = queue.popleft()

            # Check all replies of the current node
            for reply in current.replies:
                if reply not in visited:
                    visited.add(reply)

                    # Check if this reply has multiple replies (is a fork)
                    if len(reply.replies) > 1:
                        context.conversation_backup = bot.conversation
                        bot.conversation = reply
                        if not self._ensure_assistant_node(bot):
                            return "Warning: Moved to fork but ended up on " "user node with no assistant response"
                        self._display_conversation_context(bot, context)
                        return f"Moved to next fork ({len(reply.replies)} branches)"  # noqa: E501

                    # Add to queue to continue searching
                    queue.append(reply)

        return "No fork found going down the tree"

    def label(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Show all labels and create new label or jump to existing one."""
        # First, show all existing labels (like showlabels)
        if context.labeled_nodes:
            print("Existing labels:")
            for label_name, node in context.labeled_nodes.items():
                content_preview = node.content[:100] + "..." if len(node.content) > 100 else node.content
                print(f"  '{label_name}': {content_preview}")
            print()
        else:
            print("No labels saved yet.")
            print()

        # Get label input from user
        try:
            label = input_with_esc("Enter label name (new to create, existing to jump): ").strip()
        except EscapeException:
            return "Label operation cancelled"
        if not label:
            return "No label entered"

        # Check if label already exists
        if label in context.labeled_nodes:
            # Jump to existing label (like goto)
            context.conversation_backup = bot.conversation
            bot.conversation = context.labeled_nodes[label]
            if not self._ensure_assistant_node(bot):
                return f"Warning: Moved to node labeled '{label}' but ended up on user node with no assistant response"
            self._display_conversation_context(bot, context)
            return f"Jumped to existing label: {label}"
        else:
            # Create new label (like original label behavior)
            context.labeled_nodes[label] = bot.conversation
            if not hasattr(bot.conversation, "labels"):
                bot.conversation.labels = []
            if label not in bot.conversation.labels:
                bot.conversation.labels.append(label)
            return f"Created new label: {label}"

    def leaf(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Show all leaf nodes and optionally jump to one by number."""
        leaves = self._find_leaves(bot.conversation)
        if not leaves:
            return "No leaves found from current node"
        context.cached_leaves = leaves
        if args:
            try:
                leaf_index = int(args[0]) - 1  # Convert to 0-based index
                if leaf_index < 0 or leaf_index >= len(leaves):
                    return f"Invalid leaf number. Must be between 1 and {len(leaves)}"
                context.conversation_backup = bot.conversation
                bot.conversation = leaves[leaf_index]
                if not self._ensure_assistant_node(bot):
                    return f"Warning: Jumped to leaf {leaf_index + 1} but ended up on user node"  # noqa: E501
                self._display_conversation_context(bot, context)
                content_preview = self._get_leaf_preview(leaves[leaf_index])
                return f"Jumped to leaf {leaf_index + 1}: {content_preview}"
            except ValueError:
                return "Invalid leaf number. Must be a number."
        result = f"Found {len(leaves)} leaf nodes:\n"
        for i, leaf in enumerate(leaves):
            content_preview = self._get_leaf_preview(leaf)
            depth = self._calculate_depth(bot.conversation, leaf)
            labels = getattr(leaf, "labels", [])
            label_str = f" (labels: {', '.join(labels)})" if labels else ""
            result += f"  {i+1}. [depth {depth}]{label_str}: {content_preview}\n"
        result += f"\nEnter a number (1-{len(leaves)}) to jump to that leaf, " f"or press Enter to stay: "
        try:
            choice = input(result).strip()
            if choice:
                leaf_index = int(choice) - 1
                if 0 <= leaf_index < len(leaves):
                    context.conversation_backup = bot.conversation
                    bot.conversation = leaves[leaf_index]
                    if not self._ensure_assistant_node(bot):
                        return (
                            f"Warning: Jumped to leaf {leaf_index + 1} but "
                            f"ended up on user node with no assistant "
                            f"response"
                        )
                    self._display_conversation_context(bot, context)
                    content_preview = self._get_leaf_preview(leaves[leaf_index])
                    return f"Jumped to leaf {leaf_index + 1}: {content_preview}"
                else:
                    return f"Invalid choice. Must be between 1 and " f"{len(leaves)}"
            else:
                return "Staying at current position"
        except ValueError:
            return "Invalid input. Staying at current position"
        except (EOFError, KeyboardInterrupt):
            return "Cancelled. Staying at current position"

    def _get_leaf_preview(self, leaf: ConversationNode, max_length: int = 300) -> str:
        """Get a preview of leaf content, cutting from middle if too long."""
        content = leaf.content.strip()
        if len(content) <= max_length:
            return content
        half_length = (max_length - 5) // 2  # Account for " ... "
        start = content[:half_length].strip()
        end = content[-half_length:].strip()
        return f"{start} ... {end}"

    def combine_leaves(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Combine all leaves below current node using a recombinator."""
        leaves = self._find_leaves(bot.conversation)
        if not leaves:
            return "No leaves found from current node"
        if len(leaves) < 2:
            return "Need at least 2 leaves to combine"
        print(f"\nFound {len(leaves)} leaves to combine.")
        print("Available recombinators:")
        recombinator_options = {
            "1": ("concatenate", recombinators.recombinators.concatenate),
            "2": ("llm_judge", recombinators.recombinators.llm_judge),
            "3": ("llm_vote", recombinators.recombinators.llm_vote),
            "4": ("llm_merge", recombinators.recombinators.llm_merge),
        }
        for key, (name, _) in recombinator_options.items():
            print(f"  {key}. {name}")
        choice = input("Select recombinator: ").strip()
        if choice not in recombinator_options:
            return "Invalid recombinator selection"
        recombinator_func = recombinator_options[choice][1]
        recombinator_name = recombinator_options[choice][0]
        try:
            responses = [leaf.content for leaf in leaves]
            context.conversation_backup = bot.conversation
            print(f"Combining {len(leaves)} leaves using {recombinator_name}...")  # noqa: E501
            final_response, final_node = fp.recombine(bot, responses, leaves, recombinator_func)
            pretty(
                final_response,
                bot.name,
                context.config.width,
                context.config.indent,
                COLOR_ASSISTANT,
                newline_after_name=False,
            )
            return f"Successfully combined {len(leaves)} leaves using " f"{recombinator_name}"
        except Exception as e:
            return f"Error combining leaves: {str(e)}"

    def _find_leaves(self, node: ConversationNode) -> List[ConversationNode]:
        """Recursively find all leaf nodes from a given node."""
        return find_leaves(node)

    def _calculate_depth(self, start_node: ConversationNode, target_node: ConversationNode) -> int:
        """Calculate the depth/distance from start_node to target_node."""

        def find_path_length(current, target, depth=0):
            if current is target:
                return depth
            for reply in current.replies:
                result = find_path_length(reply, target, depth + 1)
                if result is not None:
                    return result
            return None

        depth = find_path_length(start_node, target_node)
        return depth if depth is not None else 0

    def _ensure_assistant_node(self, bot: "Bot") -> bool:
        """Ensure we're on an assistant node, move to one if needed."""
        if bot.conversation.role == "assistant":
            return True
        if bot.conversation.replies:
            for reply in bot.conversation.replies:
                if reply.role == "assistant":
                    bot.conversation = reply
                    return True
        return False

    def _display_conversation_context(self, bot: "Bot", context: "CLIContext"):
        """Display current conversation context."""
        if bot.conversation.content:
            pretty(
                bot.conversation.content,
                bot.name,
                context.config.width,
                context.config.indent,
                COLOR_ASSISTANT,
                newline_after_name=False,
            )

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext


class SimpleBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bot GUI")
        self.root.geometry("1200x700")

        # Initialize bot (your existing code)
        import bots.tools.code_tools as code_tools
        import bots.tools.python_edit as python_edit
        import bots.tools.terminal_tools as terminal_tools
        from bots.foundation.anthropic_bots import AnthropicBot

        self.bot = AnthropicBot()
        self.bot.add_tools(code_tools, python_edit, terminal_tools)

        self.setup_ui()
        # Auto mode state
        self.auto_running = False

    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left side: Tree view (visual only) - Make it wider
        tree_frame = tk.Frame(main_frame, width=400, bg="#f0f0f0")  # Increased from 250 to 400
        tree_frame.pack(side=tk.LEFT, fill=tk.Y)
        tree_frame.pack_propagate(False)

        tk.Label(tree_frame, text="Conversation Tree", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=5)

        # Tree display with horizontal scrolling
        tree_container = tk.Frame(tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrollbars
        tree_v_scrollbar = tk.Scrollbar(tree_container, orient=tk.VERTICAL)
        tree_h_scrollbar = tk.Scrollbar(tree_container, orient=tk.HORIZONTAL)

        # Tree display (read-only) with scrollbars
        self.tree_display = tk.Text(
            tree_container,
            state=tk.DISABLED,
            wrap=tk.NONE,  # No wrapping so horizontal scroll works
            font=("Courier", 9),
            bg="#f8f8f8",
            yscrollcommand=tree_v_scrollbar.set,
            xscrollcommand=tree_h_scrollbar.set,
        )

        # Configure scrollbars
        tree_v_scrollbar.config(command=self.tree_display.yview)
        tree_h_scrollbar.config(command=self.tree_display.xview)

        # Pack scrollbars and text widget
        tree_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right side: Chat area + controls
        chat_container = tk.Frame(main_frame)
        chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Top: Chat history
        chat_frame = tk.Frame(chat_container)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(chat_frame, text="Chat", font=("Arial", 10, "bold")).pack(pady=5)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, state=tk.DISABLED, wrap=tk.WORD, font=("Consolas", 10))
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5)

        # Bottom: Input and controls
        controls_frame = tk.Frame(chat_container)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        # Message input area
        input_label_frame = tk.Frame(controls_frame)
        input_label_frame.pack(fill=tk.X)
        tk.Label(input_label_frame, text="Message or Command:", font=("Arial", 9)).pack(side=tk.LEFT)
        tk.Label(input_label_frame, text="(Enter to send, Shift+Enter for new line)", font=("Arial", 8), fg="gray").pack(
            side=tk.RIGHT
        )

        self.message_entry = tk.Text(controls_frame, height=3)
        self.message_entry.pack(fill=tk.X, pady=(2, 5))

        # Button row: Send and file operations
        button_row = tk.Frame(controls_frame)
        button_row.pack(fill=tk.X, pady=2)

        tk.Button(button_row, text="Send", command=self.send_message, bg="lightblue", font=("Arial", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        tk.Button(button_row, text="Save Bot", command=self.save_bot).pack(side=tk.LEFT, padx=2)
        tk.Button(button_row, text="Load Bot", command=self.load_bot).pack(side=tk.LEFT, padx=2)

        # Status and help on the right
        right_frame = tk.Frame(button_row)
        right_frame.pack(side=tk.RIGHT)

        tk.Button(right_frame, text="Help", command=self.show_help, bg="lightyellow").pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value="Ready")
        status_frame = tk.Frame(right_frame)
        status_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(status_frame, text="Status:", font=("Arial", 9)).pack(side=tk.LEFT)
        tk.Label(status_frame, textvariable=self.status_var, font=("Arial", 9), fg="blue").pack(side=tk.LEFT, padx=5)

        # Initialize displays
        self.refresh_tree_display()
        self.update_chat_display()

        # Set up proper key bindings
        self.setup_key_bindings()
        self.message_entry.focus()

    def setup_key_bindings(self):
        """Set up proper Enter/Shift+Enter behavior"""

        def on_key_press(event):
            # Enter without shift = send message
            if event.keysym == "Return" and not (event.state & 0x1):  # No shift key
                self.send_message()
                return "break"  # Prevent default behavior (adding newline)

            # Shift+Enter = add newline (default behavior, so we don't need to handle it)
            # Just let it through normally
            return None

        self.message_entry.bind("<KeyPress>", on_key_press)

    def refresh_tree_display(self):
        """Update the visual tree display"""
        self.tree_display.config(state=tk.NORMAL)
        self.tree_display.delete(1.0, tk.END)

        # Find root of conversation
        root_node = self.bot.conversation
        while root_node.parent:
            root_node = root_node.parent

        # Build tree text representation starting at depth 0
        tree_text = self._build_tree_text(root_node, depth=0, is_current=(root_node == self.bot.conversation))
        self.tree_display.insert(tk.END, tree_text)

        self.tree_display.config(state=tk.DISABLED)

    def _build_tree_text(self, node, depth=0, is_current=False, is_last=True, is_first_child=False):
        """Recursively build tree text representation with first child unindented for linear conversations"""
        # Create display text
        content_preview = node.content[:40].replace("\n", " ") if node.content else "[Empty]"
        if len(node.content) > 40:
            content_preview += "..."

        # Add role indicator
        role_indicator = "🤖" if node.role == "assistant" else "👤" if node.role == "user" else "⚙️"

        # Current position indicator
        current_marker = "► " if is_current else ""

        # Build the line with depth-based indentation and tree connectors
        if depth == 0:
            # Root level - no connector
            line = f"{current_marker}{role_indicator} {content_preview}\n"
        elif is_first_child:
            # First child gets no extra indentation - continues the main thread
            line = f"{current_marker}{role_indicator} {content_preview}\n"
        else:
            # Other children get indented with connectors
            indent = "  " * depth
            connector = "└─" if is_last else "├─"
            line = f"{indent}{connector}{current_marker}{role_indicator} {content_preview}\n"

        # Add children with modified logic
        children = node.replies
        if children:
            # First process the main thread (first child - index 0)
            if len(children) > 0:
                main_child = children[0]
                is_child_current = main_child == self.bot.conversation
                line += self._build_tree_text(
                    main_child,
                    depth=depth,  # Main thread continues at same level
                    is_current=is_child_current,
                    is_last=True,  # Not used for main thread
                    is_first_child=True,
                )

            # Then process branches in reverse order (newest first, for proper connectors)
            if len(children) > 1:
                branches = children[1:]  # All children except the first
                for i in range(len(branches) - 1, -1, -1):
                    branch = branches[i]
                    is_child_current = branch == self.bot.conversation

                    # For connector: last branch processed (i=0) gets └─, others get ├─
                    is_branch_last = i == 0

                    # All branches get indented
                    branch_depth = depth + 1

                    line += self._build_tree_text(
                        branch, depth=branch_depth, is_current=is_child_current, is_last=is_branch_last, is_first_child=False
                    )

        return line

    def _is_ancestor_of_current(self, node):
        """Check if node is an ancestor of current conversation node"""
        current = self.bot.conversation
        while current.parent:
            current = current.parent
            if current == node:
                return True
        return False

    def update_chat_display(self):
        """Update the chat display with current conversation context"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)

        # Show conversation path to current node
        path = []
        node = self.bot.conversation
        while node:
            if node.content.strip():  # Only show nodes with content
                path.append(node)
            node = node.parent

        path.reverse()  # Show from root to current

        for i, node in enumerate(path):
            role = "User" if node.role == "user" else "Bot" if node.role == "assistant" else "System"

            # Add some visual separation
            if i > 0:
                self.chat_display.insert(tk.END, "\n" + "─" * 50 + "\n\n")

            self.chat_display.insert(tk.END, f"{role}: {node.content}\n")

            # Show tool usage if available
            if hasattr(node, "tool_calls") and node.tool_calls:
                tools = []
                for call in node.tool_calls:
                    tool_name, _ = self.bot.tool_handler.tool_name_and_input(call)
                    tools.append(tool_name if tool_name else "unknown")
                self.chat_display.insert(tk.END, f"[Used tools: {', '.join(tools)}]\n")

        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def send_message(self):
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            return

        # Check if it's a command
        if message.startswith("/"):
            self.handle_command(message)
        else:
            # Regular chat message
            self.message_entry.delete("1.0", tk.END)
            threading.Thread(target=self._send_message_thread, args=(message,), daemon=True).start()

    def handle_command(self, command):
        """Handle slash commands like the CLI"""
        self.message_entry.delete("1.0", tk.END)

        # Add command to chat display for reference
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n> {command}\n")
        self.chat_display.config(state=tk.DISABLED)

        parts = command.split()
        cmd = parts[0]

        try:
            if cmd == "/help":
                self.show_help()
            elif cmd == "/up":
                self.nav_up()
            elif cmd == "/down":
                self.nav_down()
            elif cmd == "/left":
                self.nav_left()
            elif cmd == "/right":
                self.nav_right()
            elif cmd == "/root":
                self.nav_root()
            elif cmd == "/save":
                self.save_bot()
            elif cmd == "/load":
                self.load_bot()
            elif cmd == "/fp":
                self.show_fp_help()
            elif cmd == "/auto":
                self.handle_auto_command()
            else:
                self.add_system_message(f"Unknown command: {cmd}. Type /help for available commands.")
        except Exception as e:
            self.add_system_message(f"Command error: {str(e)}")

    def add_system_message(self, message):
        """Add a system message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"System: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    # Navigation methods
    def nav_up(self):
        if self.bot.conversation.parent and self.bot.conversation.parent.parent:
            self.bot.conversation = self.bot.conversation.parent.parent
            self.refresh_tree_display()
            self.update_chat_display()
            self.add_system_message("Moved up in conversation tree")
        else:
            self.add_system_message("At root - can't go up")

    def nav_down(self):
        if self.bot.conversation.replies:
            self.bot.conversation = self.bot.conversation.replies[0]  # Go to first reply
            self.refresh_tree_display()
            self.update_chat_display()
            self.add_system_message("Moved down in conversation tree")
        else:
            self.add_system_message("At leaf - can't go down")

    def nav_left(self):
        if self.bot.conversation.parent:
            siblings = self.bot.conversation.parent.replies
            current_idx = siblings.index(self.bot.conversation)
            if current_idx > 0:
                self.bot.conversation = siblings[current_idx - 1]
                self.refresh_tree_display()
                self.update_chat_display()
                self.add_system_message("Moved left to sibling")
            else:
                self.add_system_message("Already at leftmost sibling")
        else:
            self.add_system_message("At root - no siblings")

    def nav_right(self):
        if self.bot.conversation.parent:
            siblings = self.bot.conversation.parent.replies
            current_idx = siblings.index(self.bot.conversation)
            if current_idx < len(siblings) - 1:
                self.bot.conversation = siblings[current_idx + 1]
                self.refresh_tree_display()
                self.update_chat_display()
                self.add_system_message("Moved right to sibling")
            else:
                self.add_system_message("Already at rightmost sibling")
        else:
            self.add_system_message("At root - no siblings")

    def nav_root(self):
        while self.bot.conversation.parent:
            self.bot.conversation = self.bot.conversation.parent
        self.refresh_tree_display()
        self.update_chat_display()
        self.add_system_message("Moved to root of conversation tree")

    def handle_auto_command(self):
        """Handle the /auto command - let bot work autonomously until it stops using tools."""
        if self.auto_running:
            self.auto_running = False
            self.add_system_message("Auto mode stopped by user")
            return

        self.auto_running = True
        self.add_system_message("Bot running autonomously. Type /auto again to stop...")
        threading.Thread(target=self._auto_thread, daemon=True).start()

    def _auto_thread(self):
        """Run the autonomous bot execution in a separate thread."""
        try:
            import bots.flows.functional_prompts as fp

            while self.auto_running:
                # Let the bot continue with "ok" prompt
                responses, nodes = fp.chain(self.bot, ["ok"])

                # Update displays on main thread
                self.root.after(0, self.refresh_tree_display)
                self.root.after(0, self.update_chat_display)

                # Check if bot used tools - if not, we're done
                if not self.bot.tool_handler.requests:
                    self.auto_running = False
                    self.root.after(0, lambda: self.add_system_message("Bot finished autonomous execution"))
                    break

                # Small delay to prevent overwhelming the system
                import time

                time.sleep(0.1)

        except Exception as e:
            self.auto_running = False
            error_msg = f"Auto mode error: {str(e)}"
            self.root.after(0, lambda: self.add_system_message(error_msg))

    def _send_message_thread(self, message):
        self.status_var.set("Bot thinking...")
        try:
            import bots.flows.functional_prompts as fp

            responses, nodes = fp.single_prompt(self.bot, message)

            # Refresh displays
            self.root.after(0, self.refresh_tree_display)
            self.root.after(0, self.update_chat_display)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.status_var.set("Ready")

    def save_bot(self):
        filename = filedialog.asksaveasfilename(defaultextension=".bot", filetypes=[("Bot files", "*.bot")])
        if filename:
            self.bot.save(filename)
            self.status_var.set(f"Saved to {filename}")
            self.add_system_message(f"Bot saved to {filename}")

    def load_bot(self):
        filename = filedialog.askopenfilename(filetypes=[("Bot files", "*.bot")])
        if filename:
            from bots.foundation.base import Bot

            self.bot = Bot.load(filename)
            self.status_var.set(f"Loaded {filename}")
            self.refresh_tree_display()
            self.update_chat_display()
            self.add_system_message(f"Bot loaded from {filename}")

    def show_help(self):
        help_text = """Available Commands:

/help - Show this help
/up - Move up in conversation tree
/down - Move down in conversation tree
/left - Move to left sibling
/right - Move to right sibling
/root - Move to root of conversation
/save - Save bot state
/load - Load bot state
/auto - Run bot autonomously until it stops using tools (type /auto again to stop)
/fp - Show functional prompt info

Navigation: Use arrow commands to move through the conversation tree.
The tree view shows your current position with ►

Type normally to chat with the bot.
Enter to send, Shift+Enter for new line."""

        # Show in a popup window
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("500x400")

        help_display = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        help_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_display.insert(tk.END, help_text)
        help_display.config(state=tk.DISABLED)

    def show_fp_help(self):
        fp_text = """Functional Prompts:

Use functional prompts by typing them as regular messages:
- "chain: prompt1 | prompt2 | prompt3"
- "branch: analyze security | analyze performance"
- "prompt_while: keep working until done"

Or use the CLI directly in a terminal:
python -m bots.dev.cli

The GUI focuses on basic chat and navigation.
For advanced functional prompts, use the CLI."""

        self.add_system_message(fp_text)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = SimpleBotGUI()
    app.run()

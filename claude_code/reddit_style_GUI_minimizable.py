
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, filedialog
import ttkbootstrap as ttk
from bots import BaseBot, Engines
from conversation_node import ConversationNode
from typing import Optional, Callable

class GuiConversationNode(ConversationNode):
    
    def __init__(
        self,
        role: str,
        content: str,
        model_engine: Engines,
        parent: Optional["GuiConversationNode"] = None,
        conversation_frame: Optional[ttk.Frame] = None,
        conversation_canvas: Optional[tk.Canvas] = None,
        on_select: Optional[Callable[["GuiConversationNode"], None]] = None,
    ):
        super().__init__(role, content, parent)
        self.engine = model_engine
        self.conversation_frame = conversation_frame
        self.conversation_canvas = conversation_canvas
        self.on_select = on_select
        self.is_minimized = False

        if not isinstance(model_engine, Engines):
            raise ValueError(f"model_engine must be an instance of Engines Enum, but was {model_engine}")

        self.bot = Engines.get_bot_class(self.engine)(model_engine=self.engine)

        name = "You" if role == "user" else self.bot.model_engine

        self.frame = ttk.Frame(self.conversation_frame)
        self.frame.pack(fill=tk.X, padx=(20*self.depth(), 0), pady=(0, 5))

        self.header_frame = ttk.Frame(self.frame)
        self.header_frame.pack(fill=tk.X)

        self.minimize_button = ttk.Button(self.header_frame, text="-", width=2, command=self.toggle_minimize)
        self.minimize_button.pack(side=tk.LEFT)

        self.name_label = ttk.Label(self.header_frame, text=name, anchor=tk.W)
        self.name_label.pack(side=tk.LEFT, padx=(5, 0))

        self.content_frame = ttk.Frame(self.frame)
        self.content_frame.pack(fill=tk.X, expand=True)

        wraplength = 300  # Default wraplength
        if self.conversation_canvas:
            wraplength = self.conversation_canvas.winfo_width() - 20 * (self.depth() + 1)

        self.content_label = ttk.Label(
            self.content_frame,
            text=self.content,
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=wraplength
        )
        self.content_label.pack(fill=tk.X, pady=(5, 0))

        self.frame.bind("<Button-1>", self.on_click)
        self.frame.bind("<MouseWheel>", self.on_mousewheel)

    def on_click(self, event):
        if self.on_select:
            self.on_select(self)

    def on_mousewheel(self, event):
        if self.conversation_canvas:
            self.conversation_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def add_reply(self, content: str, role: str, model_engine: Engines = None) -> "GuiConversationNode":
        if model_engine is None:
            model_engine = self.engine
        reply = GuiConversationNode(
            role,
            content,
            model_engine=model_engine,
            parent=self,
            conversation_frame=self.conversation_frame,
            conversation_canvas=self.conversation_canvas,
            on_select=self.on_select
        )
        self.replies.append(reply)
        return reply

    def toggle_minimize(self):
        self.is_minimized = not self.is_minimized
        if self.is_minimized:
            self.content_frame.pack_forget()
            self.minimize_button.config(text="+")
            for reply in self.replies:
                reply.frame.pack_forget()
        else:
            self.content_frame.pack(fill=tk.X, expand=True)
            self.minimize_button.config(text="-")
            self.display(self)
        if self.conversation_canvas:
            self.conversation_canvas.config(scrollregion=self.conversation_canvas.bbox("all"))

    def set_background_color(self, selected: bool) -> None:
        style = 'Selected.TFrame' if selected else 'TFrame'
        self.frame.config(style=style)
        self.header_frame.config(style=style)
        self.content_frame.config(style=style)

    def destroy(self) -> None:
        self.frame.destroy()
        for reply in self.replies:
            reply.destroy()

    def display(self, selected_node: Optional["GuiConversationNode"] = None, level: int = 0) -> None:
        is_selected = self == selected_node
        self.set_background_color(is_selected)
        if not self.frame.winfo_viewable():
            self.frame.pack(fill=tk.X, padx=(20*self.depth(), 0), pady=(0, 5))
        if not self.is_minimized:
            for reply in self.replies:
                reply.display(selected_node, level + 1)


class ConversationGUI:
    
    def __init__(self, first_msg_text: Optional[str] = None, first_msg_role: Optional[str] = None):
        if not first_msg_text:
            first_msg_text = "Ready to chat."
        if not first_msg_role:
            first_msg_role = "assistant"

        self.window = ttk.Window(themename="darkly")
        self.window.title("Reddit-style Conversation")

        style = ttk.Style()
        style.configure('Selected.TFrame', background='#3a3a3a')

        self.create_conversation_frame()
        self.create_scrollbar()
        self.create_conversation_canvas()
        self.configure_scrollbar()
        self.create_conversation_inner_frame()
        self.create_reply_frame()
        self.create_reply_entry()
        self.create_reply_button()
        self.create_engine_dropdown()
        self.create_auto_toggle()
        self.create_control_panel()

        self.window.update_idletasks()
        self.create_initial_node(first_msg_text, first_msg_role)

    def create_conversation_frame(self):
        self.conversation_frame = ttk.Frame(self.window)
        self.conversation_frame.pack(fill=tk.BOTH, expand=True)

    def create_scrollbar(self):
        self.scrollbar = ttk.Scrollbar(self.conversation_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_conversation_canvas(self):
        self.conversation_canvas = tk.Canvas(self.conversation_frame, yscrollcommand=self.scrollbar.set)
        self.conversation_canvas.pack(fill=tk.BOTH, expand=True)
        self.conversation_canvas.bind("<Configure>", self.on_canvas_configure)
        self.conversation_canvas.bind("<MouseWheel>", self.on_mousewheel)

    def configure_scrollbar(self):
        self.scrollbar.config(command=self.conversation_canvas.yview)

    def create_conversation_inner_frame(self):
        self.conversation_inner_frame = ttk.Frame(self.conversation_canvas)
        self.conversation_canvas.create_window((0, 0), window=self.conversation_inner_frame, anchor=tk.NW)

    def create_reply_frame(self):
        self.reply_frame = ttk.Frame(self.window)
        self.reply_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

    def create_reply_entry(self):
        self.reply_entry = ttk.Entry(self.reply_frame, font=("Helvetica", 12))
        self.reply_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.reply_entry.bind("<Return>", lambda event: self.add_user_reply())

    def create_reply_button(self):
        self.reply_button = ttk.Button(self.reply_frame, text="Reply", command=self.add_user_reply, style="success")
        self.reply_button.pack(side=tk.RIGHT)

    def create_engine_dropdown(self):
        self.selected_engine = Engines.GPT35
        default_engine = tk.StringVar(value=self.selected_engine.value)
        self.engine_dropdown = ttk.OptionMenu(
            self.window,
            default_engine,
            Engines.GPT35.value,
            *[e.value for e in Engines],
            command=self.on_engine_change
        )
        self.engine_dropdown.pack(side=tk.LEFT, padx=(0, 10))

    def create_auto_toggle(self):
        self.auto_var = tk.BooleanVar()
        self.auto_toggle = ttk.Checkbutton(self.window, text="Auto Reply", variable=self.auto_var, style="success")
        self.auto_toggle.pack(side=tk.LEFT)

    def create_control_panel(self):
        name_event_pairs = [
            ("AI Response", self.generate_ai_response),
            ("Save Bot", self.save_bot),
            ("Load", self.load_bot),
            ("Debug", self.debug_conversation_tree),
            ("Clear", self.clear_conversation),
        ]
        self.control_panel = ttk.Frame()
        for name, event_function in name_event_pairs:
            button = ttk.Button(self.control_panel, text=name, command=event_function)
            button.pack(side=tk.LEFT, padx=(0, 10))
        self.control_panel.pack(fill=tk.X, padx=10, pady=(0, 10))

    def create_initial_node(self, first_msg_text, first_msg_role):
        self.selected_node = GuiConversationNode(
            first_msg_role,
            first_msg_text,
            model_engine=self.selected_engine,
            parent=None,
            conversation_frame=self.conversation_inner_frame,
            conversation_canvas=self.conversation_canvas,
            on_select=self.select_node,
        )

    def on_canvas_configure(self, event):
        self.conversation_canvas.configure(scrollregion=self.conversation_canvas.bbox("all"))

    def on_mousewheel(self, event):
        self.conversation_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_engine_change(self, value):
        for engine in Engines:
            if engine.value == value:
                self.selected_engine = engine
                break
        else:
            self.selected_engine = None

    def add_user_reply(self):
        reply_content = self.reply_entry.get()
        if reply_content.strip():
            new_node = self.selected_node.add_reply(reply_content, role="user", model_engine=self.selected_engine)
            self.select_node(new_node)  # Select the new node
            self.reply_entry.delete(0, tk.END)
            self.display_conversation()
            if self.auto_var.get():
                self.generate_ai_response()
        else:
            ttk.dialogs.Messagebox.show_error("Error", "Please add text to your reply.", parent=self.window)

    def select_node(self, node):
        self.selected_node = node
        self.display_conversation()
        self.reply_entry.focus_set()

    def display_conversation(self):
        self.selected_node.root().display(self.selected_node)
        self.conversation_inner_frame.update_idletasks()
        self.conversation_canvas.config(scrollregion=self.conversation_canvas.bbox("all"))

    def generate_ai_response(self):
        if self.selected_node:
            waiting_node = self.display_waiting_message()
            role = "user" if self.selected_node.role == "assistant" else "assistant"
            model_engine = self.selected_engine
            bot = Engines.get_bot_class(model_engine)(model_engine=model_engine)
            _, node = bot.cvsn_respond(None, self.selected_node, role)
            self.select_node(node)
            waiting_node.destroy()
            self.display_conversation()

    def save_bot(self):
        self.selected_node.bot.conversation = self.selected_node
        self.selected_node.bot.save()

    def load_bot(self):
        self.selected_node.root().destroy()
        filepath = filedialog.askopenfilename(filetypes=[("Bot Files", "*.bot"), ("Conversation Files", "*.csvn")])
        if filepath:
            file_extension = os.path.splitext(filepath)[1]
            if file_extension == ".bot":
                bot = BaseBot.load(filepath)
                node = bot.conversation
                if node is not None:
                    node = node.root()
                self.selected_engine = Engines(bot.model_engine)
                self.selected_node = self.convert_conversation_node(node)
                self.display_conversation()
            elif file_extension == ".csvn":
                with open(filepath, 'r') as file:
                    tree_data = file.read()
                conversation_root = ConversationNode.from_json(tree_data)
                self.selected_node.add_reply(conversation_root.content, conversation_root.role)
                self.display_conversation()

    def debug_conversation_tree(self):
        print("Debug: Conversation Tree")
        print(self.selected_node.root().to_string())

    def clear_conversation(self):
        self.selected_node.root().destroy()
        self.selected_node = GuiConversationNode(
            "assistant",
            "Ready to chat.",
            model_engine=self.selected_engine,
            parent=None,
            conversation_frame=self.conversation_inner_frame,
            conversation_canvas=self.conversation_canvas,
            on_select=self.select_node,
        )
        self.display_conversation()

    def display_waiting_message(self):
        waiting_node = GuiConversationNode(
            self.engine_dropdown.cget("text"),
            "...",
            model_engine=self.selected_engine,
            parent=self.selected_node,
            conversation_frame=self.conversation_inner_frame,
            conversation_canvas=self.conversation_canvas,
            on_select=self.select_node,
        )
        waiting_node.display(self.selected_node)
        self.conversation_inner_frame.update()
        return waiting_node

    def convert_conversation_node(self, node):
        if node is None:
            return None

        gui_node = GuiConversationNode(
            node.role,
            node.content,
            model_engine=self.selected_engine,
            parent=None,
            conversation_frame=self.conversation_inner_frame,
            conversation_canvas=self.conversation_canvas,
            on_select=self.select_node,
        )

        for reply in node.replies:
            gui_reply = self.convert_conversation_node(reply)
            gui_reply.parent = gui_node
            gui_node.replies.append(gui_reply)

        return gui_node

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    gui = ConversationGUI()
    gui.run()

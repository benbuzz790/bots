import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from conversation_node import ConversationNode as CN
from bots import GPTBot, BaseBot, Engine
import os
from tkinter import filedialog

class ConversationGUI:
    """
    Graphical user interface for a Reddit-style conversation.

    Methods:
        - __init__(conversation_root, bot): Initializes a ConversationGUI instance.
        - display_conversation(): Displays the conversation tree in the GUI.
        - display_node(node, level=0): Displays a conversation node and its replies in the GUI.
        - select_message(node): Selects a message in the GUI.
        - deselect_message(): Deselects the currently selected message.
        - add_reply(): Adds a user reply to the conversation.
        - generate_ai_response(): Generates an AI response to the current conversation.
        - copy_message(): Copies the selected message to the clipboard.
        - save_bot(): Saves the bot's linear conversation to a file.
        - save_tree(): Saves the entire conversation tree to a file.
        - load_bot(): Loads a bot from a file.
        - get_linear_conversation(node): Retrieves the linear conversation up to the selected node.
        - on_mousewheel(event): Handles mouse wheel scrolling events.
        - display_waiting_message(): Displays a waiting message while generating an AI response.
        - calculate_node_depth(node): Calculates the depth of a conversation node.
        - on_canvas_configure(event): Configures the canvas when resized.
        - run(): Starts the GUI main loop.
    """

    def __init__(self, conversation, bot: BaseBot):
        self.bot = bot
        self.window = ttk.Window(themename="darkly")
        self.window.title("Reddit-style Conversation")

        self.conversation_frame = ttk.Frame(self.window)
        self.conversation_frame.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.conversation_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.conversation_canvas = tk.Canvas(self.conversation_frame, yscrollcommand=self.scrollbar.set)
        self.conversation_canvas.pack(fill=tk.BOTH, expand=True)
        self.conversation_canvas.bind("<Configure>", self.on_canvas_configure)
        self.conversation_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.conversation_canvas.bind("<Button-4>", self.on_mousewheel)
        self.conversation_canvas.bind("<Button-5>", self.on_mousewheel)

        self.scrollbar.config(command=self.conversation_canvas.yview)

        self.conversation_inner_frame = ttk.Frame(self.conversation_canvas)
        self.conversation_canvas.create_window((0, 0), window=self.conversation_inner_frame, anchor=tk.NW)

        self.reply_frame = ttk.Frame(self.window)
        self.reply_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.reply_entry = ttk.Entry(self.reply_frame, font=("Helvetica", 12))
        self.reply_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.reply_entry.bind("<Return>", lambda event: self.add_reply())

        self.reply_button = ttk.Button(self.reply_frame, text="Reply", command=self.add_reply, style="success")
        self.reply_button.pack(side=tk.RIGHT)

        self.message_labels = {}

        self.current_node = conversation
        self.selected_node = self.current_node

        self.button_frame = ttk.Frame(self.window)
        self.button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.engine_var = tk.StringVar(value=Engine.GPT35.name)
        self.engine_dropdown = ttk.OptionMenu(self.button_frame, self.engine_var, Engine.GPT35.name, *[e.name for e in Engine])
        self.engine_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        self.ai_response_button = ttk.Button(self.button_frame, text="AI Response", command=self.generate_ai_response, style="primary")
        self.ai_response_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_bot_button = ttk.Button(self.button_frame, text="Save Bot", command=self.save_bot, style="info")
        self.save_bot_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_tree_button = ttk.Button(self.button_frame, text="Save Text", command=self.save_tree, style="info")
        self.save_tree_button.pack(side=tk.LEFT, padx=(0, 10))

        self.load_bot_button = ttk.Button(self.button_frame, text="Load", command=self.load_bot, style="info")
        self.load_bot_button.pack(side=tk.LEFT, padx=(0, 10))

        self.auto_var = tk.BooleanVar()
        self.auto_toggle = ttk.Checkbutton(self.button_frame, text="Auto Reply", variable=self.auto_var, style="success")
        self.auto_toggle.pack(side=tk.LEFT)

        self.display_conversation()

    def display_conversation(self):
        for widget in self.conversation_inner_frame.winfo_children():
            widget.destroy()
        self.message_labels.clear()  # Clear the message_labels dictionary
        self.display_node(self.current_node.root())
        self.conversation_inner_frame.update_idletasks()
        self.conversation_canvas.config(scrollregion=self.conversation_canvas.bbox("all"))

    def display_node(self, node, level=0):
        if node.role == 'user':
            role = 'User'
        else:
            bot = node.bot if hasattr(node, 'bot') else self.bot
            role = bot.engine.value.capitalize() if hasattr(bot, 'engine') else 'Assistant'

        message_text = f"{role}: {node.content}"
        message_label = ttk.Label(self.conversation_inner_frame, text=message_text, justify=tk.LEFT, anchor=tk.W, wraplength=self.conversation_canvas.winfo_width() - 20 * (level + 1))
        message_label.pack(fill=tk.X, padx=(20*level, 0), pady=(0, 5))
        message_label.bind("<Button-1>", lambda event, node=node: self.select_message(node))
        message_label.bind("<MouseWheel>", self.on_mousewheel)
        self.message_labels[node] = message_label

        for reply in node.replies:
            self.display_node(reply, level + 1)

    def select_message(self, node):
        if self.selected_node:
            self.deselect_message()
        self.selected_node = node
        self.current_node = node
        self.message_labels[node].config(background="black")
        self.reply_entry.focus_set()

    def deselect_message(self):
        if self.selected_node:
            self.message_labels[self.selected_node].config(background="")
            self.selected_node = None

    def add_reply(self):
        reply_content = self.reply_entry.get()
        if reply_content.strip():
            self.current_node = self.current_node.add_reply(reply_content, role="user")
            self.reply_entry.delete(0, tk.END)
            self.display_conversation()
            self.select_message(self.current_node)
            if self.auto_var.get():
                self.generate_ai_response()
        else:
            ttk.dialogs.Messagebox.show_error("Error", "Please enter a valid reply.", parent=self.window)

    def generate_ai_response(self):
        if self.current_node:
            self.display_waiting_message()
            role = "user" if self.current_node.role == "assistant" else "assistant"
            self.bot.engine = Engine[self.engine_var.get()]
            _, cvsn = self.bot.cvsn_respond(None, self.current_node, role)
            self.current_node = cvsn
            self.display_conversation()
            self.select_message(self.current_node)

    def copy_message(self):
        if self.selected_node:
            message_text = self.message_labels[self.selected_node].cget("text")
            self.window.clipboard_clear()
            self.window.clipboard_append(message_text)

    def save_bot(self):
        self.bot.conversation = self.current_node
        self.bot.save()
        
    def save_tree(self):
        data = self.current_node.to_json()
        filename = f'{self.bot.name}@{self.bot.formatted_datetime()}.csvn'       
        with open(filename, 'w') as file:
            file.write(data)

    def load_bot(self):
        filepath = filedialog.askopenfilename(filetypes=[("Bot Files", "*.bot"), ("Conversation Files", "*.csvn")])
        if filepath:
            file_extension = os.path.splitext(filepath)[1]
            if file_extension == ".bot":
                self.bot = self.bot.load(filepath)
                self.current_node = self.bot.conversation.root() if self.bot.conversation else CN("system", "New conversation")
                self.display_conversation()
            elif file_extension == ".csvn":
                # Load conversation tree from file
                with open(filepath, 'r') as file:
                    tree_data = file.read()
                conversation_root = CN.from_json(tree_data)
                self.current_node = conversation_root
                self.display_conversation()

    def on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.conversation_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.conversation_canvas.yview_scroll(1, "units")

    def display_waiting_message(self):
        depth = self.calculate_node_depth(self.current_node)
        waiting_label = ttk.Label(self.conversation_inner_frame, text="@.......", justify=tk.LEFT, anchor=tk.W)
        waiting_label.pack(fill=tk.X, padx=(20*depth, 0), pady=(0, 5))
        self.conversation_inner_frame.update()

    def calculate_node_depth(self, node):
        depth = 0
        while node.parent is not None:
            depth += 1
            node = node.parent
        return depth

    def on_canvas_configure(self, event):
        self.conversation_canvas.configure(scrollregion=self.conversation_canvas.bbox("all"))
        self.display_conversation()

    def run(self):
        self.window.mainloop()

# Example usage
conversation = CN("user", "Hi there!")

bot = GPTBot(api_key=os.getenv('OPENAI_API_KEY'), 
                   name="ChatGPT", 
                   role="assistant", 
                   role_description="assists")

gui = ConversationGUI(conversation, bot)
gui.run()
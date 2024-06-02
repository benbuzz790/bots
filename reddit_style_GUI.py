import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from bots import BaseBot, Engines
import os
from tkinter import filedialog
from conversation_node import ConversationNode

class GuiConversationNode(ConversationNode):
    def __init__(self, role: str, content: str, model_engine: Engines, parent: 'GuiConversationNode' = None, conversation_frame=None, conversation_canvas=None, on_select=None):
        super().__init__(role, content, parent)

        if not isinstance(model_engine, Engines):
            raise ValueError("model_engine must be an instance of Engines Enum")

        self.engine = model_engine
        self.bot = Engines.get_bot_class(self.engine)(model_engine=self.engine)
        # TODO use the type() function and **kwargs syntax to dynamically type the bot
        
        name = self.bot.model_engine
        if role == "user":
            name = "You"

        self.conversation_frame = conversation_frame
        self.conversation_canvas = conversation_canvas
        self.on_select = on_select
        self.message_text = f"{name}: {self.content}"
        print(f"Creating label for node with message: {self.message_text}")
        self.label = ttk.Label(self.conversation_frame, 
                               text=self.message_text, 
                               justify=tk.LEFT, 
                               anchor=tk.W, 
                               wraplength=self.conversation_canvas.winfo_width() - 20 * (self.depth() + 1))
        self.label.bind("<Button-1>", lambda event: self.on_select(self) if self.on_select else None)
        self.label.bind("<MouseWheel>", lambda event: self.conversation_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

    def set_background_color(self, selected):
        if selected:
            self.label.config(background="black")
        else:
            self.label.config(background="")

    def add_reply(self, content: str, role: str, model_engine: Engines=None):
        if model_engine is None:
            model_engine = self.engine
        print(model_engine)
        # TODO the **kwargs thing
        reply = self.__class__(role, content, parent=self,
                               model_engine=model_engine, 
                               conversation_frame=self.conversation_frame,
                               conversation_canvas=self.conversation_canvas, 
                               on_select=self.on_select)
        self.replies.append(reply)
        return reply

    def display(self, selected_node=None, level=0):
        # TODO alternate colors based on level
        # TODO display lower level nodes as being "inside" the parent node
        # TODO create a minimize/maximize button to hide/show lower level nodes
        # TODO add a button to delete a node and all its children
        is_selected = self == selected_node
        self.set_background_color(is_selected)
        if not self.label.winfo_viewable():
            self.label.pack(fill=tk.X, padx=(20*self.depth(), 0), pady=(0, 5))
        for reply in self.replies:
            reply.display(selected_node, level + 1)

    def destroy(self):
        self.label.destroy()
        for reply in self.replies:
            reply.destroy()

class ConversationGUI:
    def __init__(self, first_msg_text=None, first_msg_role=None):
        if not first_msg_text:
            first_msg_text = "Ready to chat."
        if not first_msg_role:
            first_msg_role = "assistant"

        self.window = ttk.Window(themename="darkly")
        self.window.title("Reddit-style Conversation")

        # TODO ensure window updates properly when resizing

        def create_conversation_frame():
            self.conversation_frame = ttk.Frame(self.window)
            self.conversation_frame.pack(fill=tk.BOTH, expand=True)

        def create_scrollbar():
            self.scrollbar = ttk.Scrollbar(self.conversation_frame)
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def create_conversation_canvas():
            self.conversation_canvas = tk.Canvas(self.conversation_frame, yscrollcommand=self.scrollbar.set)
            self.conversation_canvas.pack(fill=tk.BOTH, expand=True)
            self.conversation_canvas.bind("<Configure>", self.on_canvas_configure)
            self.conversation_canvas.bind("<MouseWheel>", self.on_mousewheel)
            self.conversation_canvas.bind("<Button-4>", self.on_mousewheel)
            self.conversation_canvas.bind("<Button-5>", self.on_mousewheel)

        def configure_scrollbar():
            self.scrollbar.config(command=self.conversation_canvas.yview)

        def create_conversation_inner_frame():
            self.conversation_inner_frame = ttk.Frame(self.conversation_canvas)
            self.conversation_canvas.create_window((0, 0), window=self.conversation_inner_frame, anchor=tk.NW)

        def on_engine_change(_):
            value = self.engine_dropdown.cget("text")
            for engine in Engines:
                if engine.value == value:
                    self.selected_engine = engine
                    break
            else:
                self.selected_engine = None
            print(f"Selected engine: {self.selected_engine}")

        def create_engine_dropdown():
            self.selected_engine = Engines.GPT35            
            default_engine = tk.StringVar(value = self.selected_engine.value)
            self.engine_dropdown = ttk.OptionMenu(self.window, default_engine, Engines.GPT35.value, *[e.value for e in Engines], command=on_engine_change)
            self.engine_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        def create_initial_node():
            self.selected_node = GuiConversationNode(first_msg_role, first_msg_text, 
                                                     model_engine=self.selected_engine,
                                                     parent=None,
                                                     conversation_frame=self.conversation_inner_frame,
                                                     conversation_canvas=self.conversation_canvas,
                                                     on_select=self.select_node)

        def create_reply_frame():
            self.reply_frame = ttk.Frame(self.window)
            self.reply_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def create_reply_entry():
            self.reply_entry = ttk.Entry(self.reply_frame, font=("Helvetica", 12))
            self.reply_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.reply_entry.bind("<Return>", lambda event: self.add_user_reply())

        def create_reply_button():
            self.reply_button = ttk.Button(self.reply_frame, text="Reply", command=self.add_user_reply, style="success")
            self.reply_button.pack(side=tk.RIGHT)

        def create_auto_toggle():
            self.auto_var = tk.BooleanVar()
            self.auto_toggle = ttk.Checkbutton(self.window, text="Auto Reply", variable=self.auto_var, style="success")
            self.auto_toggle.pack(side=tk.LEFT)

        def create_control_panel():
            name_event_pairs = [
                ("AI Response", self.generate_ai_response),
                ("Save Bot", self.save_bot),
                ("Save Text", self.save_tree),
                ("Load", self.load_bot),
                ("Debug", self.debug_conversation_tree),
                ("Clear", self.clear_conversation)  
            ]
            self.control_panel = ttk.Frame()
            for name, event_function in name_event_pairs:
                button = ttk.Button(self.control_panel, text=name, command=event_function)
                button.pack(side=tk.LEFT, padx=(0, 10))
            self.control_panel.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Call sub-functions to create and configure widgets
        create_conversation_frame()
        create_scrollbar()
        create_conversation_canvas()
        configure_scrollbar()
        create_conversation_inner_frame()
        create_reply_frame()
        create_reply_entry()
        create_reply_button()
        create_engine_dropdown()
        create_auto_toggle()
        create_control_panel()

        self.window.update_idletasks()  # Update the window to ensure proper geometry
        create_initial_node()  # Create the initial node after updating the window

    def display_conversation(self):
        self.selected_node.root().display(self.selected_node)
        self.conversation_inner_frame.update_idletasks()
        self.conversation_canvas.config(scrollregion=self.conversation_canvas.bbox("all"))

    def select_node(self, node):
        print(f"Selecting node: {node.message_text}")
        self.selected_node = node
        self.display_conversation()
        self.reply_entry.focus_set()

    def add_user_reply(self):
        reply_content = self.reply_entry.get()
        if reply_content.strip():
            self.selected_node.add_reply(reply_content, role="user", model_engine=self.selected_engine)
            self.select_node(self.selected_node.replies[-1])
            self.reply_entry.delete(0, tk.END)
            self.display_conversation()
            if self.auto_var.get():
                self.generate_ai_response()
        else:
            ttk.dialogs.Messagebox.show_error("Error", "Please add text to your reply.", parent=self.window)

    def debug_conversation_tree(self):
        print("Debug: Conversation Tree")
        print(self.selected_node.root().to_string())

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
    
    def clear_conversation(self):
        self.selected_node.root().destroy()
        self.selected_node = GuiConversationNode("assistant", "Ready to chat.", 
                                                model_engine=self.selected_engine,
                                                parent=None,
                                                conversation_frame=self.conversation_inner_frame,
                                                conversation_canvas=self.conversation_canvas,
                                                on_select=self.select_node)
        self.display_conversation()
    
    def save_bot(self):
        self.selected_node.bot.conversation = self.selected_node
        self.selected_node.bot.save()

    def save_tree(self):
        data = self.selected_node.to_json()
        filename = f'{self.selected_node.bot.name}@{self.selected_node.bot.formatted_datetime()}.csvn'
        with open(filename, 'w') as file:
            file.write(data)

    def load_bot(self):
        filepath = filedialog.askopenfilename(filetypes=[("Bot Files", "*.bot"), ("Conversation Files", "*.csvn")])
        if filepath:
            file_extension = os.path.splitext(filepath)[1]
            if file_extension == ".bot":
                bot = BaseBot.load(filepath)
                self.selected_node.add_reply(bot.conversation.content, bot.conversation.role, bot)
                self.display_conversation()
            elif file_extension == ".csvn":
                with open(filepath, 'r') as file:
                    tree_data = file.read()
                conversation_root = ConversationNode.from_json(tree_data)
                self.selected_node.add_reply(conversation_root.content, conversation_root.role)
                self.display_conversation()

    def on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.conversation_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.conversation_canvas.yview_scroll(1, "units")

    def display_waiting_message(self):
        waiting_node = GuiConversationNode(self.engine_dropdown.cget("text"), "...", 
                                           model_engine=self.selected_engine,
                                           parent=self.selected_node,
                                           conversation_frame=self.conversation_inner_frame,
                                           conversation_canvas=self.conversation_canvas,
                                           on_select=self.select_node)
        waiting_node.display(self.selected_node)
        self.conversation_inner_frame.update()
        return waiting_node

    def on_canvas_configure(self, event):
        self.conversation_canvas.configure(scrollregion=self.conversation_canvas.bbox("all"))
        self.selected_node.display()

    def run(self):
        self.window.mainloop()

# Example usage
gui = ConversationGUI()
gui.run()

# TODO document the code with comments and docstrings and ensure it is PEP8 compliant
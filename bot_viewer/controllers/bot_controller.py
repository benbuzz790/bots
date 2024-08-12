from models.bot_file import BotFile
from views.conversation_tree import ConversationTreeWidget
from views.bot_info_panel import BotInfoPanel

class BotController:
    def __init__(self, conversation_tree: ConversationTreeWidget, bot_info_panel: BotInfoPanel):
        self.conversation_tree = conversation_tree
        self.bot_info_panel = bot_info_panel
        self.bot_file = None

    def load_bot_file(self, file_path: str):
        self.bot_file = BotFile(file_path)
        self.update_ui()

    def update_ui(self):
        if self.bot_file:
            # Update conversation tree
            self.conversation_tree.load_conversation(self.bot_file.get_conversation())
            self.conversation_tree.expand_all()

            # Update bot info panel
            self.bot_info_panel.update_info(self.bot_file.get_bot_info())

    def save_bot_file(self):
        if self.bot_file:
            self.bot_file.save()

    def expand_all_conversations(self):
        self.conversation_tree.expand_all()

    def collapse_all_conversations(self):
        self.conversation_tree.collapse_all()
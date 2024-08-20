from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QLabel, QTextEdit, QSplitter
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from models.bot_file import ConversationNode
from utils.formatting import format_content, get_brief_content
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ConversationTreeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Create a splitter for resizable panes
        self.splitter = QSplitter(Qt.Vertical)
        self.layout.addWidget(self.splitter)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Role", "Preview"])
        self.splitter.addWidget(self.tree)

        msg_widget = QWidget()
        msg_layout = QVBoxLayout(msg_widget)
        self.msg_label = QLabel("Message:")
        msg_layout.addWidget(self.msg_label)
        self.msg_text = QTextEdit()
        self.msg_text.setReadOnly(True)
        
        # Set monospaced font
        self.font = QFont("Courier")
        self.font.setPointSize(16)
        self.font.setStyleHint(QFont.Monospace)
        self.msg_text.setFont(self.font)
        
        # Preserve whitespace
        #self.details_text.setLineWrapMode(QTextEdit.NoWrap)
        
        msg_layout.addWidget(self.msg_text)
        self.splitter.addWidget(msg_widget)

        self.tree.itemClicked.connect(self.show_details)

    def resizeEvent(self, event):
        # Adjust column widths when widget is resized
        total_width = self.tree.width()
        self.tree.setColumnWidth(0, int(total_width * 0.7))
        self.tree.setColumnWidth(1, int(total_width * 0.3))
        super().resizeEvent(event)

    def load_conversation(self, conversation: ConversationNode):
        self.tree.clear()
        self._add_conversation_node(conversation, self.tree.invisibleRootItem())

    def _add_conversation_node(self, node: ConversationNode, parent_item: QTreeWidgetItem):
        item = QTreeWidgetItem(parent_item)
        item.setText(0, node.role)
        
        content = get_brief_content(node.content)
        
        # Remove leading whitespace and newlines
        content = content.lstrip()
        
        # Find the first newline after any initial whitespace
        newline_index = content.find('\n')
        
        if newline_index == -1:
            # No newlines, show up to 100 characters
            display_content = content[:100] + "..." if len(content) > 100 else content
        else:
            # Show text up to the first newline
            display_content = content[:newline_index]
        
        item.setText(1, display_content)
        item.setData(0, Qt.UserRole, node)

        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        item.setFont(0, font)

        for reply in node.replies:
            self._add_conversation_node(reply, item)

    def show_details(self, item: QTreeWidgetItem, column: int):
        node = item.data(0, Qt.UserRole)
        details = f"Role: {node.role}\n\nContent:\n"
        formatted_content = format_content(node.content)
        logger.debug(f"Formatted content:\n{formatted_content}")
        details += formatted_content
        details += "\n\nAttributes:\n"
        for key, value in node.attributes.items():
            details += f"{key}:\n{format_content(value, 2)}\n"
        self.msg_text.setPlainText(details)

    def expand_all(self):
        self.tree.expandAll()

    def collapse_all(self):
        self.tree.collapseAll()

    def change_font_size(self, delta):
        # Change font size for the tree
        tree_font = self.tree.font()
        tree_size = tree_font.pointSize() + delta
        if tree_size > 0:
            tree_font.setPointSize(tree_size)
            self.tree.setFont(tree_font)

        # Change font size for the details text
        details_size = self.font.pointSize() + delta
        if details_size > 0:
            self.font.setPointSize(details_size)
            self.msg_text.setFont(self.font)

        # Update the current item to refresh the details pane
        current_item = self.tree.currentItem()
        if current_item:
            self.show_details(current_item, 0)

        logger.debug(f"Font size changed by {delta}. New sizes - Tree: {tree_size}, Details: {details_size}")
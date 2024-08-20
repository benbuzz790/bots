import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QTabWidget, QMessageBox, QAction, QMenu, QShortcut
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QFont
from .conversation_tree import ConversationTreeWidget
from .bot_info_panel import BotInfoPanel
from controllers.bot_controller import BotController
from utils.file_handler import FileHandler
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bot Viewer")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Create toolbar
        toolbar = QHBoxLayout()
        self.open_button = QPushButton("Open Bot File")
        self.open_button.clicked.connect(self.open_bot_file)
        toolbar.addWidget(self.open_button)

        self.save_button = QPushButton("Save Bot File")
        self.save_button.clicked.connect(self.save_bot_file)
        toolbar.addWidget(self.save_button)

        self.expand_all_button = QPushButton("Expand All")
        self.expand_all_button.clicked.connect(self.expand_all_conversations)
        toolbar.addWidget(self.expand_all_button)

        self.collapse_all_button = QPushButton("Collapse All")
        self.collapse_all_button.clicked.connect(self.collapse_all_conversations)
        toolbar.addWidget(self.collapse_all_button)

        self.layout.addLayout(toolbar)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Create conversation tree widget
        self.conversation_tree = ConversationTreeWidget()
        self.tab_widget.addTab(self.conversation_tree, "Conversation")

        # Create bot info panel
        self.bot_info_panel = BotInfoPanel()
        self.tab_widget.addTab(self.bot_info_panel, "Bot Info")

        # Create bot controller
        self.bot_controller = BotController(self.conversation_tree, self.bot_info_panel)

        # Create menu and shortcuts
        self.create_menu()
        self.create_shortcuts()

        # Set initial font
        self.base_font = QFont("Courier", 16)
        self.base_font.setStyleHint(QFont.Monospace)
        self.apply_font()

        logger.debug("MainWindow initialized")

    def create_menu(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu('View')

        # Toggle word wrap action
        self.toggle_wrap_action = QAction('Toggle Word Wrap', self)
        self.toggle_wrap_action.setCheckable(True)
        self.toggle_wrap_action.setChecked(False)
        self.toggle_wrap_action.triggered.connect(self.toggle_word_wrap)
        view_menu.addAction(self.toggle_wrap_action)

        # Increase font size action
        self.increase_font_action = QAction('Increase Font Size', self)
        self.increase_font_action.triggered.connect(lambda: self.change_font_size(1))
        view_menu.addAction(self.increase_font_action)

        # Decrease font size action
        self.decrease_font_action = QAction('Decrease Font Size', self)
        self.decrease_font_action.triggered.connect(lambda: self.change_font_size(-1))
        view_menu.addAction(self.decrease_font_action)

    def create_shortcuts(self):
        # Ctrl++ for increasing font size
        increase_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        increase_shortcut.activated.connect(lambda: self.change_font_size(1))

        # Ctrl+= as an alternative for increasing font size
        increase_shortcut_alt = QShortcut(QKeySequence("Ctrl+="), self)
        increase_shortcut_alt.activated.connect(lambda: self.change_font_size(1))

        # Ctrl+- for decreasing font size
        decrease_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        decrease_shortcut.activated.connect(lambda: self.change_font_size(-1))

    def toggle_word_wrap(self):
        wrap_mode = Qt.TextWordWrap if self.toggle_wrap_action.isChecked() else Qt.TextElideRight
        self.conversation_tree.msg_text.setWordWrapMode(wrap_mode)
        self.bot_info_panel.info_text.setWordWrapMode(wrap_mode)

    def change_font_size(self, delta):
        new_size = self.base_font.pointSize() + delta
        if new_size > 0:
            self.base_font.setPointSize(new_size)
            self.apply_font()
            logger.debug(f"Font size changed to {new_size}")

    def apply_font(self):
        # Apply font to conversation tree
        self.conversation_tree.tree.setFont(self.base_font)
        self.conversation_tree.msg_text.setFont(self.base_font)
        
        # Apply font to bot info panel
        self.bot_info_panel.info_text.setFont(self.base_font)
        
        # Force update
        self.conversation_tree.tree.update()
        self.conversation_tree.msg_text.update()
        self.bot_info_panel.info_text.update()

    def open_bot_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Bot File", "", "Bot Files (*.bot)")
        if file_name:
            logger.debug(f"Opening file: {file_name}")
            if FileHandler.is_valid_bot_file(file_name):
                self.bot_controller.load_bot_file(file_name)
            else:
                QMessageBox.warning(self, "Invalid File", "The selected file is not a valid bot file.")

    def save_bot_file(self):
        self.bot_controller.save_bot_file()
        QMessageBox.information(self, "File Saved", "The bot file has been saved successfully.")

    def expand_all_conversations(self):
        self.bot_controller.expand_all_conversations()

    def collapse_all_conversations(self):
        self.bot_controller.collapse_all_conversations()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
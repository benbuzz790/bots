from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utils.formatting import format_content
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BotInfoPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)

        # Set monospaced font
        font = QFont("Courier")
        font.setStyleHint(QFont.Monospace)
        self.info_text.setFont(font)
        
        # Preserve whitespace
        self.info_text.setLineWrapMode(QTextEdit.NoWrap)

        self.layout.addWidget(self.info_text)

    def update_info(self, bot_info):
        info_text = ""
        for key, value in bot_info.items():
            formatted_value = format_content(value)
            logger.debug(f"Formatted {key}:\n{formatted_value}")
            info_text += f"{key}:\n{formatted_value}\n\n"
        self.info_text.setPlainText(info_text)

    def clear_info(self):
        self.info_text.clear()

    def change_font_size(self, delta):
        font = self.info_text.font()
        size = font.pointSize() + delta
        if size > 0:
            font.setPointSize(size)
            self.info_text.setFont(font)
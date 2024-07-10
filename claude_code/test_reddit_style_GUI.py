
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from bots import Engines
from claude_code.reddit_style_GUI_minimizable import GuiConversationNode, ConversationGUI

class TestGuiConversationNode(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.frame = ttk.Frame(self.root)
        self.canvas = tk.Canvas(self.frame)
        self.on_select = MagicMock()
        self.node = GuiConversationNode(
            "user", "Test message", Engines.GPT35, 
            conversation_frame=self.frame, 
            conversation_canvas=self.canvas,
            on_select=self.on_select
        )

    def tearDown(self):
        self.root.withdraw()  # Hide the window instead of destroying it
        self.root.update()  # Process any pending events

    def test_initialization(self):
        self.assertEqual(self.node.role, "user")
        self.assertEqual(self.node.content, "Test message")
        self.assertEqual(self.node.engine, Engines.GPT35)
        self.assertFalse(self.node.is_minimized)

    def test_toggle_minimize(self):
        self.assertFalse(self.node.is_minimized)
        self.node.toggle_minimize()
        self.assertTrue(self.node.is_minimized)
        self.node.toggle_minimize()
        self.assertFalse(self.node.is_minimized)

    def test_set_background_color(self):
        self.node.set_background_color(True)
        self.assertEqual(self.node.frame.cget('style'), 'Selected.TFrame')
        self.node.set_background_color(False)
        self.assertEqual(self.node.frame.cget('style'), 'TFrame')

    def test_on_click(self):
        event = MagicMock()
        self.node.on_click(event)
        self.on_select.assert_called_once_with(self.node)

        event = MagicMock()
        self.node.on_click(event)
        self.on_select.assert_called_once_with(self.node)

    def test_add_reply(self):
        reply = self.node.add_reply("Reply content", "assistant", Engines.GPT35)
        self.assertIsInstance(reply, GuiConversationNode)
        self.assertEqual(reply.content, "Reply content")
        self.assertEqual(reply.role, "assistant")
        self.assertEqual(len(self.node.replies), 1)

    def tearDown(self):
        self.root.destroy()

class TestConversationGUI(unittest.TestCase):
    def setUp(self):
        self.gui = ConversationGUI()

    def tearDown(self):
        self.gui.window.destroy()
        self.gui.window.update()  # Process any pending events

    @patch('tkinter.Tk.mainloop')
    def test_initialization(self, mock_mainloop):
        self.assertIsInstance(self.gui.selected_node, GuiConversationNode)
        self.assertEqual(self.gui.selected_node.content, "Ready to chat.")
        self.assertEqual(self.gui.selected_node.role, "assistant")

    def test_add_user_reply(self):
        initial_reply_count = len(self.gui.selected_node.replies)
        self.gui.reply_entry.insert(0, "User reply")
        self.gui.add_user_reply()
        self.assertEqual(len(self.gui.selected_node.replies), initial_reply_count + 1)
        self.assertEqual(self.gui.selected_node.content, "User reply")
        self.assertEqual(self.gui.selected_node.role, "user")

        self.gui.reply_entry.insert(0, "User reply")
        self.gui.add_user_reply()
        self.assertEqual(len(self.gui.selected_node.replies), 1)
        self.assertEqual(self.gui.selected_node.replies[0].content, "User reply")
        self.assertEqual(self.gui.selected_node.replies[0].role, "user")

    @patch('claude_code.reddit_style_GUI_minimizable.Engines.get_bot_class')
    def test_generate_ai_response(self, mock_get_bot_class):
        mock_bot = MagicMock()
        mock_bot.cvsn_respond.return_value = (None, GuiConversationNode("assistant", "AI response", Engines.GPT35, conversation_frame=self.gui.conversation_inner_frame))
        mock_get_bot_class.return_value.return_value = mock_bot

        initial_reply_count = len(self.gui.selected_node.replies)
        self.gui.generate_ai_response()
        self.assertEqual(len(self.gui.selected_node.replies), initial_reply_count + 1)
        self.assertEqual(self.gui.selected_node.content, "AI response")
        self.assertEqual(self.gui.selected_node.role, "assistant")

    def test_generate_ai_response(self, mock_get_bot_class):
        mock_bot = MagicMock()
        mock_bot.cvsn_respond.return_value = (None, GuiConversationNode("assistant", "AI response", Engines.GPT35))
        mock_get_bot_class.return_value.return_value = mock_bot

        self.gui.generate_ai_response()
        self.assertEqual(len(self.gui.selected_node.replies), 1)
        self.assertEqual(self.gui.selected_node.replies[0].content, "AI response")
        self.assertEqual(self.gui.selected_node.replies[0].role, "assistant")

    def test_select_node(self):
        new_node = self.gui.selected_node.add_reply("New node", "user", Engines.GPT35)
        self.gui.select_node(new_node)
        self.assertEqual(self.gui.selected_node, new_node)

    def test_clear_conversation(self):
        self.gui.selected_node.add_reply("Reply", "user", Engines.GPT35)
        self.gui.clear_conversation()
        self.assertEqual(len(self.gui.selected_node.replies), 0)
        self.assertEqual(self.gui.selected_node.content, "Ready to chat.")

    def tearDown(self):
        self.gui.window.destroy()

    def test_on_engine_change(self):
        self.gui.on_engine_change(Engines.GPT4.value)
        self.assertEqual(self.gui.selected_engine, Engines.GPT4)
        
        self.gui.on_engine_change("Invalid Engine")
        self.assertIsNone(self.gui.selected_engine)

if __name__ == '__main__':
    unittest.main()

import tkinter as tk
from typing import Callable
import unittest
from unittest.mock import Mock

class Menu:
    def __init__(self, parent, new_game_callback: Callable[[], None], reset_game_callback: Callable[[], None], quit_callback: Callable[[], None]):
        self.parent = parent
        self.menu_frame = tk.Frame(parent)
        self.menu_frame.pack(side=tk.TOP, fill=tk.X)

        self.new_game_button = tk.Button(self.menu_frame, text="New Game", command=new_game_callback)
        self.reset_game_button = tk.Button(self.menu_frame, text="Reset Game", command=reset_game_callback)
        self.quit_button = tk.Button(self.menu_frame, text="Quit", command=quit_callback)

        self.new_game_button.pack(side=tk.LEFT, padx=5)
        self.reset_game_button.pack(side=tk.LEFT, padx=5)
        self.quit_button.pack(side=tk.RIGHT, padx=5)

        self.items = {
            "new_game": self.new_game_button,
            "reset_game": self.reset_game_button,
            "quit": self.quit_button
        }

        self.keyboard_shortcuts_enabled = False

    def enable_item(self, item_name: str) -> None:
        if item_name in self.items:
            self.items[item_name].config(state=tk.NORMAL)

    def disable_item(self, item_name: str) -> None:
        if item_name in self.items:
            self.items[item_name].config(state=tk.DISABLED)

    def update_item_label(self, item_name: str, new_label: str) -> None:
        if item_name in self.items:
            self.items[item_name].config(text=new_label)

    def simulate_click(self, item_name: str) -> None:
        if item_name in self.items:
            self.items[item_name].invoke()

    def set_keyboard_shortcuts(self, enabled: bool) -> None:
        self.keyboard_shortcuts_enabled = enabled
        if enabled:
            self.parent.bind('<n>', lambda e: self.simulate_click("new_game"))
            self.parent.bind('<r>', lambda e: self.simulate_click("reset_game"))
            self.parent.bind('<q>', lambda e: self.simulate_click("quit"))
        else:
            self.parent.unbind('<n>')
            self.parent.unbind('<r>')
            self.parent.unbind('<q>')

    def get_menu_state(self) -> dict:
        return {
            item_name: {
                "text": item.cget("text"),
                "state": item.cget("state")
            }
            for item_name, item in self.items.items()
        }

def create_menu(parent, new_game_callback: Callable[[], None], reset_game_callback: Callable[[], None], quit_callback: Callable[[], None]) -> Menu:
    return Menu(parent, new_game_callback, reset_game_callback, quit_callback)

class TestMenu(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.new_game_mock = Mock()
        self.reset_game_mock = Mock()
        self.quit_mock = Mock()
        self.menu = create_menu(self.root, self.new_game_mock, self.reset_game_mock, self.quit_mock)

    def tearDown(self):
        self.root.destroy()

    def test_enable_disable_item(self):
        self.menu.disable_item("new_game")
        self.assertEqual(self.menu.items["new_game"].cget("state"), tk.DISABLED)
        self.menu.enable_item("new_game")
        self.assertEqual(self.menu.items["new_game"].cget("state"), tk.NORMAL)

    def test_update_item_label(self):
        new_label = "Start Game"
        self.menu.update_item_label("new_game", new_label)
        self.assertEqual(self.menu.items["new_game"].cget("text"), new_label)

    def test_simulate_click(self):
        self.menu.simulate_click("new_game")
        self.new_game_mock.assert_called_once()

    def test_set_keyboard_shortcuts(self):
        self.menu.set_keyboard_shortcuts(True)
        self.assertTrue(self.menu.keyboard_shortcuts_enabled)
        self.menu.set_keyboard_shortcuts(False)
        self.assertFalse(self.menu.keyboard_shortcuts_enabled)

    def test_get_menu_state(self):
        state = self.menu.get_menu_state()
        self.assertIn("new_game", state)
        self.assertIn("reset_game", state)
        self.assertIn("quit", state)
        self.assertEqual(state["new_game"]["text"], "New Game")
        self.assertEqual(state["new_game"]["state"], tk.NORMAL)

if __name__ == "__main__":
    unittest.main()
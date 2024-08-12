import unittest
from typing import Optional
import tkinter as tk
from gui.gui_utils import PLAYER_1_COLOR, PLAYER_2_COLOR, BACKGROUND_COLOR, text_to_speech, set_timeout

class StatusDisplay:
    def __init__(self, parent_widget: tk.Widget):
        self.frame = tk.Frame(parent_widget, bg=BACKGROUND_COLOR)
        self.frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = tk.Label(self.frame, text="", font=("Arial", 14), bg=BACKGROUND_COLOR)
        self.status_label.pack()

        self.message_label = tk.Label(self.frame, text="", font=("Arial", 12), bg=BACKGROUND_COLOR)
        self.message_label.pack()

        self.test_mode = False

    def update_current_player(self, player: int) -> None:
        color = PLAYER_1_COLOR if player == 1 else PLAYER_2_COLOR
        text = f"Player {player}'s turn"
        self.status_label.config(text=text, fg=color)
        if not self.test_mode:
            text_to_speech(text)

    def show_game_outcome(self, outcome: str, winner: Optional[int] = None) -> None:
        if winner:
            text = f"Player {winner} wins!"
            color = PLAYER_1_COLOR if winner == 1 else PLAYER_2_COLOR
        else:
            text = "It's a draw!"
            color = "black"
        self.status_label.config(text=text, fg=color)
        if not self.test_mode:
            text_to_speech(text)

    def reset_display(self) -> None:
        self.status_label.config(text="", fg="black")
        self.message_label.config(text="")

    def set_message(self, message: str) -> None:
        self.message_label.config(text=message)
        if not self.test_mode:
            text_to_speech(message)

    def clear_message(self) -> None:
        self.message_label.config(text="")

    def set_test_mode(self, enabled: bool) -> None:
        self.test_mode = enabled
        if enabled:
            set_timeout(self.frame, 1000)  # 1 second timeout for testing

def create_status_display(parent_widget: tk.Widget) -> StatusDisplay:
    return StatusDisplay(parent_widget)

class TestStatusDisplay(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.status_display = create_status_display(self.root)
        self.status_display.set_test_mode(True)

    def tearDown(self):
        self.root.destroy()

    def test_update_current_player(self):
        self.status_display.update_current_player(1)
        self.assertEqual(self.status_display.status_label.cget("text"), "Player 1's turn")
        self.assertEqual(self.status_display.status_label.cget("fg"), PLAYER_1_COLOR)

        self.status_display.update_current_player(2)
        self.assertEqual(self.status_display.status_label.cget("text"), "Player 2's turn")
        self.assertEqual(self.status_display.status_label.cget("fg"), PLAYER_2_COLOR)

    def test_show_game_outcome(self):
        self.status_display.show_game_outcome("win", 1)
        self.assertEqual(self.status_display.status_label.cget("text"), "Player 1 wins!")
        self.assertEqual(self.status_display.status_label.cget("fg"), PLAYER_1_COLOR)

        self.status_display.show_game_outcome("draw")
        self.assertEqual(self.status_display.status_label.cget("text"), "It's a draw!")
        self.assertEqual(self.status_display.status_label.cget("fg"), "black")

    def test_reset_display(self):
        self.status_display.update_current_player(1)
        self.status_display.set_message("Test message")
        self.status_display.reset_display()
        self.assertEqual(self.status_display.status_label.cget("text"), "")
        self.assertEqual(self.status_display.message_label.cget("text"), "")

    def test_set_and_clear_message(self):
        test_message = "Test message"
        self.status_display.set_message(test_message)
        self.assertEqual(self.status_display.message_label.cget("text"), test_message)

        self.status_display.clear_message()
        self.assertEqual(self.status_display.message_label.cget("text"), "")

    def test_test_mode(self):
        self.status_display.set_test_mode(False)
        self.assertFalse(self.status_display.test_mode)

        self.status_display.set_test_mode(True)
        self.assertTrue(self.status_display.test_mode)

if __name__ == "__main__":
    unittest.main()
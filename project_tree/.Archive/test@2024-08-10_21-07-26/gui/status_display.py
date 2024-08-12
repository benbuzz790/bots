import tkinter as tk
from typing import Optional, Dict
import unittest

class StatusDisplay(tk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.current_player_label = tk.Label(self, text="Current Player: ")
        self.current_player_label.pack()
        
        self.result_label = tk.Label(self, text="")
        self.result_label.pack()
        
        self.scores_label = tk.Label(self, text="Scores: Player 1: 0 | Player 2: 0")
        self.scores_label.pack()
        
        self.custom_message_label = tk.Label(self, text="")
        self.custom_message_label.pack()
        
        self.error_label = tk.Label(self, text="", fg="red")
        self.error_label.pack()
        
        self.player1_color = "blue"
        self.player2_color = "red"

    def update_current_player(self, player_name: str) -> None:
        self.current_player_label.config(text=f"Current Player: {player_name}", 
                                         fg=self.player1_color if player_name == "Player 1" else self.player2_color)

    def display_game_result(self, result: str, winner: Optional[str] = None) -> None:
        if winner:
            self.result_label.config(text=f"Game Over: {winner} wins!")
        else:
            self.result_label.config(text=f"Game Over: {result}")

    def update_game_state(self, state: Dict[str, any]) -> None:
        if 'current_player' in state:
            self.update_current_player(state['current_player'])
        if 'result' in state:
            self.display_game_result(state['result'], state.get('winner'))
        if 'scores' in state:
            self.update_scores(state['scores']['player1'], state['scores']['player2'])

    def reset_display(self) -> None:
        self.current_player_label.config(text="Current Player: ")
        self.result_label.config(text="")
        self.scores_label.config(text="Scores: Player 1: 0 | Player 2: 0")
        self.custom_message_label.config(text="")
        self.error_label.config(text="")

    def set_player_colors(self, player1_color: str, player2_color: str) -> None:
        self.player1_color = player1_color
        self.player2_color = player2_color

    def update_scores(self, player1_score: int, player2_score: int) -> None:
        self.scores_label.config(text=f"Scores: Player 1: {player1_score} | Player 2: {player2_score}")

    def get_displayed_player(self) -> str:
        return self.current_player_label.cget("text").split(": ")[-1]

    def get_displayed_result(self) -> str:
        return self.result_label.cget("text")

    def get_displayed_scores(self) -> Dict[str, int]:
        scores_text = self.scores_label.cget("text")
        player1_score = int(scores_text.split("|")[0].split(":")[-1].strip())
        player2_score = int(scores_text.split("|")[1].split(":")[-1].strip())
        return {"Player 1": player1_score, "Player 2": player2_score}

    def set_custom_message(self, message: str) -> None:
        self.custom_message_label.config(text=message)

    def clear_custom_message(self) -> None:
        self.custom_message_label.config(text="")

    def set_error_state(self, error: bool, message: Optional[str] = None) -> None:
        if error:
            self.error_label.config(text=message if message else "An error occurred")
        else:
            self.error_label.config(text="")

class TestStatusDisplay(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.status_display = StatusDisplay(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_update_current_player(self):
        self.status_display.update_current_player("Player 1")
        self.assertEqual(self.status_display.get_displayed_player(), "Player 1")

    def test_display_game_result(self):
        self.status_display.display_game_result("Draw")
        self.assertEqual(self.status_display.get_displayed_result(), "Game Over: Draw")
        
        self.status_display.display_game_result("Win", "Player 2")
        self.assertEqual(self.status_display.get_displayed_result(), "Game Over: Player 2 wins!")

    def test_update_game_state(self):
        state = {
            'current_player': 'Player 2',
            'result': 'Win',
            'winner': 'Player 2',
            'scores': {'player1': 1, 'player2': 2}
        }
        self.status_display.update_game_state(state)
        self.assertEqual(self.status_display.get_displayed_player(), "Player 2")
        self.assertEqual(self.status_display.get_displayed_result(), "Game Over: Player 2 wins!")
        self.assertEqual(self.status_display.get_displayed_scores(), {"Player 1": 1, "Player 2": 2})

    def test_reset_display(self):
        self.status_display.update_current_player("Player 1")
        self.status_display.display_game_result("Win", "Player 1")
        self.status_display.update_scores(2, 1)
        self.status_display.set_custom_message("Test message")
        self.status_display.set_error_state(True, "Test error")
        
        self.status_display.reset_display()
        
        self.assertEqual(self.status_display.get_displayed_player(), "")
        self.assertEqual(self.status_display.get_displayed_result(), "")
        self.assertEqual(self.status_display.get_displayed_scores(), {"Player 1": 0, "Player 2": 0})
        self.assertEqual(self.status_display.custom_message_label.cget("text"), "")
        self.assertEqual(self.status_display.error_label.cget("text"), "")

    def test_set_player_colors(self):
        self.status_display.set_player_colors("green", "yellow")
        self.status_display.update_current_player("Player 1")
        self.assertEqual(self.status_display.current_player_label.cget("fg"), "green")
        
        self.status_display.update_current_player("Player 2")
        self.assertEqual(self.status_display.current_player_label.cget("fg"), "yellow")

    def test_update_scores(self):
        self.status_display.update_scores(3, 4)
        self.assertEqual(self.status_display.get_displayed_scores(), {"Player 1": 3, "Player 2": 4})

    def test_set_custom_message(self):
        self.status_display.set_custom_message("Test custom message")
        self.assertEqual(self.status_display.custom_message_label.cget("text"), "Test custom message")

    def test_clear_custom_message(self):
        self.status_display.set_custom_message("Test custom message")
        self.status_display.clear_custom_message()
        self.assertEqual(self.status_display.custom_message_label.cget("text"), "")

    def test_set_error_state(self):
        self.status_display.set_error_state(True, "Test error message")
        self.assertEqual(self.status_display.error_label.cget("text"), "Test error message")
        
        self.status_display.set_error_state(False)
        self.assertEqual(self.status_display.error_label.cget("text"), "")

if __name__ == "__main__":
    unittest.main()
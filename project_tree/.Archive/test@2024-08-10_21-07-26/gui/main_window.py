import tkinter as tk
from typing import Optional
import unittest
from gui.game_board import GameBoard
from gui.status_display import StatusDisplay
from gui.gui_utils import center_window, create_styled_button, set_timeout
from src.game import Game
from src.player import Player

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Connect Four")
        self.root.geometry("600x500")
        center_window(self.root, 600, 500)

        self.game = Game([Player("Player 1", 1), Player("Player 2", 2)])
        self.game_board = GameBoard(self.root, self.make_move)
        self.status_display = StatusDisplay(self.root)

        self.setup_gui()

    def setup_gui(self):
        self.game_board.pack(expand=True, fill=tk.BOTH)
        self.status_display.pack(fill=tk.X)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        create_styled_button(button_frame, "New Game", self.start_new_game).pack(side=tk.LEFT, padx=5)
        create_styled_button(button_frame, "Quit", self.quit_game).pack(side=tk.RIGHT, padx=5)

    def run(self) -> None:
        self.root.mainloop()

    def start_new_game(self) -> None:
        self.game.reset_game()
        self.game_board.reset_board()
        self.status_display.reset_display()
        self.update_gui()

    def make_move(self, column: int) -> None:
        current_player = self.game.get_current_player()
        if self.game.make_move(current_player, column):
            self.update_gui()
            if self.is_game_over():
                self.handle_game_over()

    def quit_game(self) -> None:
        self.root.quit()

    def update_gui(self) -> None:
        board_state = self.game.get_board_state().get_board_state()
        self.game_board.update_board(board_state)
        current_player = self.game.get_current_player()
        self.status_display.update_current_player(current_player.get_name())

    def get_current_game_state(self) -> dict:
        return {
            "board_state": self.game.get_board_state().get_board_state(),
            "current_player": self.game.get_current_player().get_name(),
            "is_game_over": self.is_game_over(),
            "winner": self.get_winner()
        }

    def set_player_names(self, player1: str, player2: str) -> None:
        self.game.players[0] = Player(player1, 1)
        self.game.players[1] = Player(player2, 2)
        self.update_gui()

    def set_ai_difficulty(self, difficulty: str) -> None:
        # This method is a placeholder as AI is not implemented in this version
        pass

    def get_winner(self) -> Optional[str]:
        is_win, winner = self.game.check_win()
        return winner.get_name() if is_win else None

    def is_game_over(self) -> bool:
        return self.game.is_game_over()

    def reset_gui(self) -> None:
        self.game_board.reset_board()
        self.status_display.reset_display()

    def simulate_click(self, x: int, y: int) -> None:
        column = x // (self.game_board.winfo_width() // 7)
        self.make_move(column)

    def get_board_state(self) -> list:
        return self.game.get_board_state().get_board_state()

    def get_current_player(self) -> str:
        return self.game.get_current_player().get_name()

    def set_timeout(self, seconds: float) -> None:
        set_timeout(self.root, seconds, self.root.quit)

    def handle_game_over(self):
        winner = self.get_winner()
        if winner:
            self.status_display.display_game_result("Game Over", winner)
        else:
            self.status_display.display_game_result("Game Over", "Draw")
        self.game_board.disable_board()

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.window = MainWindow()

    def test_initialization(self):
        self.assertIsNotNone(self.window.game)
        self.assertIsNotNone(self.window.game_board)
        self.assertIsNotNone(self.window.status_display)

    def test_start_new_game(self):
        self.window.start_new_game()
        self.assertFalse(self.window.is_game_over())
        self.assertIsNone(self.window.get_winner())

    def test_make_move(self):
        initial_state = self.window.get_board_state()
        self.window.make_move(0)
        new_state = self.window.get_board_state()
        self.assertNotEqual(initial_state, new_state)

    def test_get_current_game_state(self):
        state = self.window.get_current_game_state()
        self.assertIn("board_state", state)
        self.assertIn("current_player", state)
        self.assertIn("is_game_over", state)
        self.assertIn("winner", state)

    def test_set_player_names(self):
        self.window.set_player_names("Alice", "Bob")
        self.assertEqual(self.window.game.players[0].get_name(), "Alice")
        self.assertEqual(self.window.game.players[1].get_name(), "Bob")

    def test_get_winner(self):
        self.assertIsNone(self.window.get_winner())
        # Simulate a win condition
        for i in range(4):
            self.window.game.make_move(self.window.game.players[0], 0)
        self.assertEqual(self.window.get_winner(), "Player 1")

    def test_is_game_over(self):
        self.assertFalse(self.window.is_game_over())
        # Simulate a win condition
        for i in range(4):
            self.window.game.make_move(self.window.game.players[0], 0)
        self.assertTrue(self.window.is_game_over())

    def test_reset_gui(self):
        self.window.make_move(0)
        self.window.reset_gui()
        self.assertEqual(self.window.get_board_state(), [[0] * 7 for _ in range(6)])

    def test_get_current_player(self):
        self.assertEqual(self.window.get_current_player(), "Player 1")
        self.window.make_move(0)
        self.assertEqual(self.window.get_current_player(), "Player 2")

if __name__ == "__main__":
    unittest.main()
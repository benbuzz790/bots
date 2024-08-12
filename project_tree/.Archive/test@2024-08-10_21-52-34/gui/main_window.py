import tkinter as tk
from typing import Callable, Tuple
import unittest
from unittest.mock import Mock

from gui.game_board import GameBoard, create_game_board
from gui.status_display import StatusDisplay, create_status_display
from gui.gui_utils import set_timeout

class MainWindow:
    def __init__(self, game_logic: 'ConnectFourGame'):
        self.root = tk.Tk()
        self.root.title("Connect Four")
        self.game_logic = game_logic
        
        self.game_board = create_game_board(self.root)
        self.status_display = create_status_display(self.root)
        
        self.reset_button = tk.Button(self.root, text="Reset Game", command=self.reset_game)
        self.reset_button.pack(pady=10)
        
        set_timeout(self.reset_button, 1000)  # 1 second timeout for testing

    def run(self) -> None:
        self.root.mainloop()

    def update_board(self, board_state: Tuple[Tuple[int, ...], ...]) -> None:
        self.game_board.update_board(board_state)

    def update_status(self, current_player: int, game_over: bool, winner: int | None) -> None:
        if game_over:
            if winner is None:
                self.status_display.show_game_outcome("Draw")
            else:
                self.status_display.show_game_outcome(f"Player {winner} wins!")
        else:
            self.status_display.update_current_player(current_player)

    def reset_game(self) -> None:
        self.game_board.reset_board()
        self.status_display.reset_display()
        if self.game_logic:
            self.game_logic.reset_game()

    def set_column_click_handler(self, handler: Callable[[int], None]) -> None:
        self.game_board.set_column_click_handler(handler)

    def set_reset_click_handler(self, handler: Callable[[], None]) -> None:
        self.reset_button.config(command=lambda: [handler(), self.reset_game()])

def create_main_window(game_logic: 'ConnectFourGame') -> MainWindow:
    return MainWindow(game_logic)

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.mock_game_logic = Mock()
        self.main_window = create_main_window(self.mock_game_logic)

    def test_update_board(self):
        board_state = ((0, 0, 0), (0, 1, 0), (0, 2, 0))
        self.main_window.update_board(board_state)
        # Assert that the game_board's update_board method was called with the correct state
        self.main_window.game_board.update_board.assert_called_with(board_state)

    def test_update_status_in_progress(self):
        self.main_window.update_status(1, False, None)
        self.main_window.status_display.update_current_player.assert_called_with(1)

    def test_update_status_game_over_win(self):
        self.main_window.update_status(2, True, 2)
        self.main_window.status_display.show_game_outcome.assert_called_with("Player 2 wins!")

    def test_update_status_game_over_draw(self):
        self.main_window.update_status(1, True, None)
        self.main_window.status_display.show_game_outcome.assert_called_with("Draw")

    def test_reset_game(self):
        self.main_window.reset_game()
        self.main_window.game_board.reset_board.assert_called()
        self.main_window.status_display.reset_display.assert_called()
        self.mock_game_logic.reset_game.assert_called()

    def test_set_column_click_handler(self):
        mock_handler = Mock()
        self.main_window.set_column_click_handler(mock_handler)
        self.main_window.game_board.set_column_click_handler.assert_called_with(mock_handler)

    def test_set_reset_click_handler(self):
        mock_handler = Mock()
        self.main_window.set_reset_click_handler(mock_handler)
        # Simulate a click on the reset button
        self.main_window.reset_button.invoke()
        mock_handler.assert_called()
        self.mock_game_logic.reset_game.assert_called()

if __name__ == "__main__":
    unittest.main()
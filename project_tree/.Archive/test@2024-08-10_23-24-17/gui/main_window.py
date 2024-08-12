import tkinter as tk
from typing import Tuple
import unittest
from unittest.mock import Mock, patch
from src.game import Game
from gui.board_widget import BoardWidget
from gui.menu import Menu

class MainWindow:
    def __init__(self, game: Game):
        self.game = game
        self.root = tk.Tk()
        self.root.title("Connect Four")
        
        self.board_widget = BoardWidget(self.root, 400, 350, self.handle_move)
        self.board_widget.pack(pady=10)
        
        self.menu = Menu(self.root, self.reset_game, self.reset_game, self.root.quit)
        
        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack(pady=5)

    def run(self) -> None:
        self.update_display()
        self.root.mainloop()

    def update_display(self) -> None:
        board, current_player, is_game_over, is_draw = self.game.get_game_state()
        self.board_widget.update_board(board.get_board_state())
        
        if is_game_over:
            if is_draw:
                status = "It's a draw!"
            else:
                status = f"{current_player.get_state()[0]} wins!"
            self.menu.disable_item("Reset")
        else:
            status = f"Current player: {current_player.get_state()[0]}"
        
        self.status_label.config(text=status)

    def reset_game(self) -> None:
        self.game.reset_game()
        self.board_widget.reset_board()
        self.menu.enable_item("Reset")
        self.update_display()

    def handle_move(self, column: int) -> None:
        if self.game.make_move(column):
            self.update_display()

    def get_game_state(self) -> Tuple[str, str, bool]:
        board, current_player, is_game_over, is_draw = self.game.get_game_state()
        return (
            str(board),
            current_player.get_state()[0],
            is_game_over
        )

    def simulate_move(self, column: int) -> None:
        self.handle_move(column)

    def simulate_reset(self) -> None:
        self.reset_game()

def create_main_window(game: Game) -> MainWindow:
    return MainWindow(game)

def run_gui_game() -> None:
    from src.player import create_player
    player1 = create_player("human", "Player 1", 1)
    player2 = create_player("human", "Player 2", 2)
    game = Game(player1, player2)
    main_window = create_main_window(game)
    main_window.run()

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.game = Mock(spec=Game)
        self.main_window = MainWindow(self.game)

    def test_init(self):
        self.assertIsInstance(self.main_window.board_widget, BoardWidget)
        self.assertIsInstance(self.main_window.menu, Menu)
        self.assertIsInstance(self.main_window.status_label, tk.Label)

    def test_update_display(self):
        mock_board = Mock()
        mock_board.get_board_state.return_value = [[0] * 7 for _ in range(6)]
        mock_player = Mock()
        mock_player.get_state.return_value = ("Player 1", 1, "Red")
        self.game.get_game_state.return_value = (mock_board, mock_player, False, False)
        
        self.main_window.update_display()
        
        self.assertEqual(self.main_window.status_label.cget("text"), "Current player: Player 1")

    def test_reset_game(self):
        self.main_window.reset_game()
        self.game.reset_game.assert_called_once()
        self.main_window.board_widget.reset_board.assert_called_once()

    def test_handle_move(self):
        self.game.make_move.return_value = True
        self.main_window.handle_move(3)
        self.game.make_move.assert_called_with(3)

    def test_get_game_state(self):
        mock_board = Mock()
        mock_board.__str__.return_value = "Board"
        mock_player = Mock()
        mock_player.get_state.return_value = ("Player 1", 1, "Red")
        self.game.get_game_state.return_value = (mock_board, mock_player, False, False)
        
        state = self.main_window.get_game_state()
        self.assertEqual(state, ("Board", "Player 1", False))

    def test_simulate_move(self):
        with patch.object(MainWindow, 'handle_move') as mock_handle_move:
            self.main_window.simulate_move(3)
            mock_handle_move.assert_called_with(3)

    def test_simulate_reset(self):
        with patch.object(MainWindow, 'reset_game') as mock_reset_game:
            self.main_window.simulate_reset()
            mock_reset_game.assert_called_once()

@patch('tkinter.Tk')
def test_create_main_window(mock_tk):
    game = Mock(spec=Game)
    main_window = create_main_window(game)
    assert isinstance(main_window, MainWindow)

@patch('src.player.create_player')
@patch('src.game.Game')
@patch('main_window.create_main_window')
def test_run_gui_game(mock_create_main_window, mock_game, mock_create_player):
    run_gui_game()
    mock_create_player.assert_called()
    mock_game.assert_called()
    mock_create_main_window.assert_called()
    mock_create_main_window.return_value.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
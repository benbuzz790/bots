import unittest
from unittest.mock import Mock, patch
from typing import Tuple
from gui.main_window import MainWindow
from gui.game_board import GameBoard
from gui.status_display import StatusDisplay
from gui.gui_utils import simulate_click, set_timeout, scale_widget
from src.game import ConnectFourGame

class TestGUIComponents(unittest.TestCase):
    def setUp(self) -> None:
        self.game_logic = Mock(spec=ConnectFourGame)
        self.main_window = MainWindow(self.game_logic)
        self.game_board = self.main_window.game_board
        self.status_display = self.main_window.status_display

    def tearDown(self) -> None:
        self.main_window = None
        self.game_board = None
        self.status_display = None

class TestMainWindow(TestGUIComponents):
    def test_initialization(self):
        self.assertIsInstance(self.main_window, MainWindow)
        self.assertIsInstance(self.main_window.game_board, GameBoard)
        self.assertIsInstance(self.main_window.status_display, StatusDisplay)

    def test_update_board(self):
        board_state = ((0, 0, 0), (0, 1, 0), (0, 2, 0))
        self.main_window.update_board(board_state)
        self.game_board.update_board.assert_called_once_with(board_state)

    def test_update_status(self):
        self.main_window.update_status(1, False, None)
        self.status_display.update_current_player.assert_called_once_with(1)

class TestGameBoard(TestGUIComponents):
    def test_column_click(self):
        handler = Mock()
        self.game_board.set_column_click_handler(handler)
        simulate_click(self.game_board.columns[0])
        handler.assert_called_once_with(0)

    def test_keyboard_navigation(self):
        self.game_board.enable_keyboard_navigation()
        self.assertTrue(self.game_board.keyboard_navigation_enabled)
        self.game_board.disable_keyboard_navigation()
        self.assertFalse(self.game_board.keyboard_navigation_enabled)

class TestStatusDisplay(TestGUIComponents):
    def test_update_current_player(self):
        self.status_display.update_current_player(1)
        self.assertEqual(self.status_display.current_player_label.text(), "Current Player: 1")

    def test_show_game_outcome(self):
        self.status_display.show_game_outcome("Player 1 wins!", 1)
        self.assertEqual(self.status_display.outcome_label.text(), "Player 1 wins!")

class TestUserInteractions(TestGUIComponents):
    def test_column_selection(self):
        handler = Mock()
        self.main_window.set_column_click_handler(handler)
        simulate_click(self.game_board.columns[3])
        handler.assert_called_once_with(3)

    def test_reset_game(self):
        handler = Mock()
        self.main_window.set_reset_click_handler(handler)
        simulate_click(self.main_window.reset_button)
        handler.assert_called_once()

class TestGameStateResponses(TestGUIComponents):
    def test_player_turn_update(self):
        self.main_window.update_status(2, False, None)
        self.assertEqual(self.status_display.current_player_label.text(), "Current Player: 2")

    def test_game_win(self):
        self.main_window.update_status(1, True, 1)
        self.assertEqual(self.status_display.outcome_label.text(), "Player 1 wins!")

    def test_game_draw(self):
        self.main_window.update_status(2, True, None)
        self.assertEqual(self.status_display.outcome_label.text(), "It's a draw!")

class TestGUIScalability(TestGUIComponents):
    def test_window_scaling(self):
        original_size = self.main_window.size()
        scale_widget(self.main_window, 1.5)
        self.assertEqual(self.main_window.size().width(), int(original_size.width() * 1.5))
        self.assertEqual(self.main_window.size().height(), int(original_size.height() * 1.5))

class TestAccessibilityFeatures(TestGUIComponents):
    def test_keyboard_navigation(self):
        self.game_board.enable_keyboard_navigation()
        self.assertTrue(self.game_board.keyboard_navigation_enabled)

    @patch('gui.gui_utils.text_to_speech')
    def test_screen_reader_compatibility(self, mock_tts):
        self.status_display.update_current_player(1)
        mock_tts.assert_called_with("Current Player: 1")

class TestErrorHandling(TestGUIComponents):
    @patch('gui.gui_utils.handle_gui_error')
    def test_invalid_move(self, mock_error_handler):
        self.game_logic.make_move.side_effect = ValueError("Invalid move")
        self.main_window.column_clicked(3)
        mock_error_handler.assert_called_once()

class TestVisualFeedback(TestGUIComponents):
    def test_column_highlight(self):
        self.game_board.highlight_column(3)
        self.assertTrue(self.game_board.columns[3].property("highlighted"))
        self.game_board.highlight_column(3, False)
        self.assertFalse(self.game_board.columns[3].property("highlighted"))

def run_gui_tests() -> None:
    unittest.main(verbosity=2, exit=False)

if __name__ == "__main__":
    run_gui_tests()
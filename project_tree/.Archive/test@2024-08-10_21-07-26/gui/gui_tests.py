import unittest
import tkinter as tk
from typing import Callable
from main_window import MainWindow
from game_board import GameBoard
from status_display import StatusDisplay
from gui_utils import simulate_click, set_timeout

class TestMainWindow(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.main_window = MainWindow()

    def tearDown(self) -> None:
        self.root.destroy()

    def test_initialization(self) -> None:
        self.assertIsNotNone(self.main_window)
        self.assertIsInstance(self.main_window.game_board, GameBoard)
        self.assertIsInstance(self.main_window.status_display, StatusDisplay)

    def test_game_start(self) -> None:
        self.main_window.start_new_game()
        self.assertFalse(self.main_window.is_game_over())
        self.assertEqual(self.main_window.get_current_player(), "Player 1")

    def test_make_move(self) -> None:
        self.main_window.start_new_game()
        self.main_window.make_move(3)
        board_state = self.main_window.get_board_state()
        self.assertEqual(board_state[5][3], 1)  # Assuming player 1's piece is represented by 1

    def test_game_over(self) -> None:
        self.main_window.start_new_game()
        for i in range(4):
            self.main_window.make_move(i)
            self.main_window.make_move(i)
        self.assertTrue(self.main_window.is_game_over())
        self.assertIsNotNone(self.main_window.get_winner())

    def test_reset_game(self) -> None:
        self.main_window.start_new_game()
        self.main_window.make_move(0)
        self.main_window.reset_gui()
        self.assertFalse(self.main_window.is_game_over())
        self.assertEqual(self.main_window.get_current_player(), "Player 1")
        self.assertEqual(self.main_window.get_board_state(), [[0] * 7 for _ in range(6)])

    def test_window_resizing(self) -> None:
        original_size = self.root.winfo_geometry()
        self.root.geometry("800x600")
        self.root.update()
        new_size = self.root.winfo_geometry()
        self.assertNotEqual(original_size, new_size)

class TestGameBoard(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.game_board = GameBoard(self.root, lambda x: None)

    def tearDown(self) -> None:
        self.root.destroy()

    def test_board_creation(self) -> None:
        self.assertEqual(self.game_board.get_board_dimensions(), (6, 7))

    def test_piece_placement(self) -> None:
        self.game_board.update_board([[0] * 7 for _ in range(6)])
        self.game_board.update_board([[0] * 7 for _ in range(5)] + [[1, 0, 0, 0, 0, 0, 0]])
        self.assertEqual(self.game_board.get_cell_state(5, 0), 1)

    def test_winning_highlight(self) -> None:
        winning_cells = [(5, 0), (5, 1), (5, 2), (5, 3)]
        self.game_board.highlight_winning_combination(winning_cells)
        for row, col in winning_cells:
            self.assertNotEqual(self.game_board.get_cell_state(row, col), 0)

    def test_board_reset(self) -> None:
        self.game_board.update_board([[1] * 7 for _ in range(6)])
        self.game_board.reset_board()
        for row in range(6):
            for col in range(7):
                self.assertEqual(self.game_board.get_cell_state(row, col), 0)

    def test_column_full(self) -> None:
        self.game_board.update_board([[1] * 7 for _ in range(6)])
        for col in range(7):
            self.assertTrue(self.game_board.is_column_full(col))

class TestStatusDisplay(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.status_display = StatusDisplay(self.root)

    def tearDown(self) -> None:
        self.root.destroy()

    def test_player_turn_display(self) -> None:
        self.status_display.update_current_player("Player 1")
        self.assertEqual(self.status_display.get_displayed_player(), "Player 1")

    def test_game_result_display(self) -> None:
        self.status_display.display_game_result("Player 1 wins!")
        self.assertEqual(self.status_display.get_displayed_result(), "Player 1 wins!")

    def test_score_update(self) -> None:
        self.status_display.update_scores(3, 2)
        scores = self.status_display.get_displayed_scores()
        self.assertEqual(scores["Player 1"], 3)
        self.assertEqual(scores["Player 2"], 2)

    def test_custom_message(self) -> None:
        custom_message = "Test message"
        self.status_display.set_custom_message(custom_message)
        self.assertEqual(self.status_display.get_displayed_result(), custom_message)

class TestGUIIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.main_window = MainWindow()

    def tearDown(self) -> None:
        self.main_window.quit_game()

    def test_full_game_simulation(self) -> None:
        self.main_window.start_new_game()
        for col in range(4):
            self.main_window.make_move(col)
            self.main_window.make_move(col)
        self.assertTrue(self.main_window.is_game_over())
        self.assertIsNotNone(self.main_window.get_winner())

    def test_error_handling(self) -> None:
        self.main_window.start_new_game()
        for _ in range(6):
            self.main_window.make_move(0)
        with self.assertRaises(ValueError):
            self.main_window.make_move(0)

    def test_timeout_behavior(self) -> None:
        def timeout_callback():
            self.timeout_triggered = True

        self.timeout_triggered = False
        self.main_window.set_timeout(0.5)
        set_timeout(self.main_window, 0.5, timeout_callback)
        self.main_window.root.after(600, self.main_window.root.quit)
        self.main_window.root.mainloop()
        self.assertTrue(self.timeout_triggered)

def run_all_tests() -> None:
    unittest.main()

def run_performance_tests(iterations: int = 100) -> dict:
    import time
    start_time = time.time()
    main_window = MainWindow()
    for _ in range(iterations):
        main_window.start_new_game()
        for col in range(7):
            main_window.make_move(col)
        main_window.reset_gui()
    end_time = time.time()
    return {"total_time": end_time - start_time, "average_time": (end_time - start_time) / iterations}

def simulate_user_interaction(interaction: Callable) -> None:
    main_window = MainWindow()
    interaction(main_window)
    main_window.quit_game()

if __name__ == "__main__":
    run_all_tests()
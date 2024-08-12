import unittest
import time
from unittest.mock import Mock, patch
from gui.main_window import MainWindow
from gui.board_widget import BoardWidget
from gui.menu import Menu
from src.game import Game
from src.player import HumanPlayer, AIPlayer

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.game = Game(HumanPlayer("Player 1", 1), AIPlayer("AI", 2))
        self.main_window = MainWindow(self.game)

    def test_update_display(self):
        self.main_window.update_display()
        self.assertTrue(self.main_window.get_game_state()[2])  # Check if display is updated

    def test_reset_game(self):
        self.main_window.reset_game()
        self.assertEqual(self.main_window.get_game_state()[0], "Player 1's turn")

    def test_handle_move(self):
        self.main_window.handle_move(3)
        self.assertEqual(self.main_window.get_game_state()[1], "Move made in column 3")

class TestBoardWidget(unittest.TestCase):
    def setUp(self):
        self.on_click = Mock()
        self.board_widget = BoardWidget(None, 400, 400, self.on_click)

    def test_update_board(self):
        board_state = [[0] * 7 for _ in range(6)]
        self.board_widget.update_board(board_state)
        self.assertEqual(self.board_widget.get_current_state(), board_state)

    def test_simulate_click(self):
        self.board_widget.simulate_click(3)
        self.on_click.assert_called_with(3)

class TestMenu(unittest.TestCase):
    def setUp(self):
        self.new_game_callback = Mock()
        self.reset_game_callback = Mock()
        self.quit_callback = Mock()
        self.menu = Menu(None, self.new_game_callback, self.reset_game_callback, self.quit_callback)

    def test_simulate_click(self):
        self.menu.simulate_click("new_game")
        self.new_game_callback.assert_called_once()

    def test_get_menu_state(self):
        state = self.menu.get_menu_state()
        self.assertIn("new_game", state)
        self.assertIn("reset_game", state)
        self.assertIn("quit", state)

class TestGUIIntegration(unittest.TestCase):
    def setUp(self):
        self.game = Game(HumanPlayer("Player 1", 1), AIPlayer("AI", 2))
        self.main_window = MainWindow(self.game)

    def test_game_flow(self):
        self.main_window.handle_move(3)
        state = self.main_window.get_game_state()
        self.assertIn("AI's turn", state[0])

class TestGUIPerformance(unittest.TestCase):
    def setUp(self):
        self.game = Game(HumanPlayer("Player 1", 1), AIPlayer("AI", 2))
        self.main_window = MainWindow(self.game)

    def test_update_display_performance(self):
        start_time = time.time()
        self.main_window.update_display()
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.1)  # Ensure update takes less than 100ms

class TestGUIAccessibility(unittest.TestCase):
    def setUp(self):
        self.game = Game(HumanPlayer("Player 1", 1), AIPlayer("AI", 2))
        self.main_window = MainWindow(self.game)

    def test_keyboard_navigation(self):
        self.main_window.board_widget.set_keyboard_navigation(True)
        self.assertTrue(self.main_window.board_widget.keyboard_navigation_enabled)

def run_all_gui_tests() -> None:
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMainWindow))
    suite.addTest(unittest.makeSuite(TestBoardWidget))
    suite.addTest(unittest.makeSuite(TestMenu))
    suite.addTest(unittest.makeSuite(TestGUIIntegration))
    suite.addTest(unittest.makeSuite(TestGUIPerformance))
    suite.addTest(unittest.makeSuite(TestGUIAccessibility))
    unittest.TextTestRunner(verbosity=2).run(suite)

def run_performance_tests() -> None:
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestGUIPerformance))
    unittest.TextTestRunner(verbosity=2).run(suite)

def run_integration_tests() -> None:
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestGUIIntegration))
    unittest.TextTestRunner(verbosity=2).run(suite)

def simulate_game_scenario(scenario_type: str) -> None:
    game = Game(HumanPlayer("Player 1", 1), AIPlayer("AI", 2))
    main_window = MainWindow(game)
    
    if scenario_type == "new_game":
        main_window.reset_game()
    elif scenario_type == "win":
        for i in range(4):
            main_window.handle_move(i)
            main_window.handle_move(i)
    elif scenario_type == "draw":
        for i in range(7):
            for _ in range(6):
                main_window.handle_move(i)

def verify_gui_state(expected_state: dict) -> bool:
    game = Game(HumanPlayer("Player 1", 1), AIPlayer("AI", 2))
    main_window = MainWindow(game)
    actual_state = main_window.get_game_state()
    return all(actual_state[k] == v for k, v in expected_state.items())

def measure_gui_response_time(action: callable) -> float:
    start_time = time.time()
    action()
    end_time = time.time()
    return end_time - start_time

if __name__ == "__main__":
    run_all_gui_tests()
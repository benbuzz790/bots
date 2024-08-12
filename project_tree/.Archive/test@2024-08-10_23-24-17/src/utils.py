import unittest
import logging
from typing import List, Dict, Any
import random
import json
import os

# Constants
BOARD_ROWS: int = 6
BOARD_COLUMNS: int = 7
PLAYER_SYMBOLS: Dict[int, str] = {1: 'X', 2: 'O', 0: '.'}

# Input validation
def validate_column_input(input_value: str) -> int:
    try:
        column = int(input_value)
        if 0 <= column < BOARD_COLUMNS:
            return column
        raise ValueError
    except ValueError:
        raise ConnectFourError(f"Invalid column. Please enter a number between 0 and {BOARD_COLUMNS - 1}.")

# Error handling
class ConnectFourError(Exception):
    pass

def handle_game_exception(error: Exception) -> str:
    if isinstance(error, ConnectFourError):
        return str(error)
    return f"An unexpected error occurred: {str(error)}"

# Logging
def setup_logger() -> logging.Logger:
    logger = logging.getLogger('connect_four')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Data conversion
def board_to_string(board: List[List[int]]) -> str:
    return '\n'.join(' '.join(PLAYER_SYMBOLS[cell] for cell in row) for row in board)

# Game rule checks
def is_valid_move(board: List[List[int]], column: int) -> bool:
    return 0 <= column < BOARD_COLUMNS and board[0][column] == 0

# AI utilities
def evaluate_board_state(board: List[List[int]], player: int) -> int:
    # Simple evaluation: count player's pieces minus opponent's pieces
    opponent = 3 - player
    return sum(row.count(player) for row in board) - sum(row.count(opponent) for row in board)

# Message formatting
def format_game_message(message_type: str, **kwargs) -> str:
    messages = {
        'welcome': "Welcome to Connect Four!",
        'turn': f"Player {kwargs.get('player', '')} ({PLAYER_SYMBOLS[kwargs.get('player', 0)]}), it's your turn.",
        'win': f"Player {kwargs.get('player', '')} ({PLAYER_SYMBOLS[kwargs.get('player', 0)]}) wins!",
        'draw': "The game is a draw!",
        'invalid_move': f"Invalid move. {kwargs.get('reason', '')}"
    }
    return messages.get(message_type, "")

# Configuration management
def load_game_config(config_file: str) -> Dict[str, Any]:
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'difficulty': 'medium', 'player1': 'Human', 'player2': 'AI'}

# Performance profiling
def profile_function(func: callable) -> callable:
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Function {func.__name__} took {end_time - start_time:.4f} seconds to execute.")
        return result
    return wrapper

# Testing utilities
def generate_random_board() -> List[List[int]]:
    return [[random.choice([0, 1, 2]) for _ in range(BOARD_COLUMNS)] for _ in range(BOARD_ROWS)]

# File I/O
def save_game_state(game_state: Dict[str, Any], filename: str) -> None:
    with open(filename, 'w') as f:
        json.dump(game_state, f)

def load_game_state(filename: str) -> Dict[str, Any]:
    with open(filename, 'r') as f:
        return json.load(f)

# Random scenario generation
def generate_test_scenario() -> Dict[str, Any]:
    board = generate_random_board()
    return {
        'board': board,
        'current_player': random.choice([1, 2]),
        'moves': random.randint(0, BOARD_ROWS * BOARD_COLUMNS)
    }

# Unit tests
class TestUtils(unittest.TestCase):
    def test_validate_column_input(self):
        self.assertEqual(validate_column_input("3"), 3)
        with self.assertRaises(ConnectFourError):
            validate_column_input("7")
        with self.assertRaises(ConnectFourError):
            validate_column_input("invalid")

    def test_handle_game_exception(self):
        error = ConnectFourError("Test error")
        self.assertEqual(handle_game_exception(error), "Test error")
        error = ValueError("Unexpected error")
        self.assertTrue(handle_game_exception(error).startswith("An unexpected error occurred"))

    def test_setup_logger(self):
        logger = setup_logger()
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'connect_four')

    def test_board_to_string(self):
        board = [[0, 1, 2], [1, 2, 0]]
        expected = ". X O\nX O ."
        self.assertEqual(board_to_string(board), expected)

    def test_is_valid_move(self):
        board = [[0, 0, 1], [1, 2, 0]]
        self.assertTrue(is_valid_move(board, 0))
        self.assertFalse(is_valid_move(board, 2))

    def test_evaluate_board_state(self):
        board = [[1, 1, 2], [2, 1, 0]]
        self.assertEqual(evaluate_board_state(board, 1), 1)
        self.assertEqual(evaluate_board_state(board, 2), -1)

    def test_format_game_message(self):
        self.assertEqual(format_game_message('welcome'), "Welcome to Connect Four!")
        self.assertEqual(format_game_message('turn', player=1), "Player 1 (X), it's your turn.")

    def test_load_game_config(self):
        config = load_game_config('non_existent_file.json')
        self.assertIsInstance(config, dict)
        self.assertIn('difficulty', config)

    @profile_function
    def dummy_function(self):
        return sum(range(1000000))

    def test_profile_function(self):
        result = self.dummy_function()
        self.assertEqual(result, 499999500000)

    def test_generate_random_board(self):
        board = generate_random_board()
        self.assertEqual(len(board), BOARD_ROWS)
        self.assertEqual(len(board[0]), BOARD_COLUMNS)
        self.assertTrue(all(cell in [0, 1, 2] for row in board for cell in row))

    def test_save_and_load_game_state(self):
        state = {'board': generate_random_board(), 'current_player': 1}
        filename = 'test_game_state.json'
        save_game_state(state, filename)
        loaded_state = load_game_state(filename)
        self.assertEqual(state, loaded_state)
        os.remove(filename)

    def test_generate_test_scenario(self):
        scenario = generate_test_scenario()
        self.assertIn('board', scenario)
        self.assertIn('current_player', scenario)
        self.assertIn('moves', scenario)

if __name__ == '__main__':
    unittest.main()
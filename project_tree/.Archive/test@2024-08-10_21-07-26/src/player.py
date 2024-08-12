import random
from typing import List, Optional
import unittest

class Player:
    def __init__(self, name: str, piece: int, is_ai: bool = False, difficulty: str = "easy"):
        self.name = name
        self.piece = piece
        self.is_ai = is_ai
        self.difficulty = difficulty
        self.score = 0
        self.move_history = []

    def make_move(self, board_state: List[List[int]]) -> int:
        if not self.is_ai:
            raise ValueError("Human players should not use the make_move method")
        
        valid_moves = [col for col in range(len(board_state[0])) if self.validate_move(col, board_state)]
        
        if self.difficulty == "easy":
            return random.choice(valid_moves)
        else:  # "hard" difficulty
            # Simple strategy: prefer center columns
            center = len(board_state[0]) // 2
            sorted_moves = sorted(valid_moves, key=lambda x: abs(x - center))
            return sorted_moves[0]

    def validate_move(self, column: int, board_state: List[List[int]]) -> bool:
        if column < 0 or column >= len(board_state[0]):
            return False
        return board_state[0][column] == 0

    def reset_player(self) -> None:
        self.score = 0
        self.move_history.clear()

    def get_name(self) -> str:
        return self.name

    def get_piece(self) -> int:
        return self.piece

    def is_ai_player(self) -> bool:
        return self.is_ai

    def get_score(self) -> int:
        return self.score

    def get_move_history(self) -> List[int]:
        return self.move_history.copy()

    def set_difficulty(self, difficulty: str) -> None:
        if difficulty not in ["easy", "hard"]:
            raise ValueError("Difficulty must be 'easy' or 'hard'")
        self.difficulty = difficulty

    def get_difficulty(self) -> str:
        return self.difficulty


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.human_player = Player("Alice", 1)
        self.ai_player_easy = Player("AI Easy", 2, is_ai=True, difficulty="easy")
        self.ai_player_hard = Player("AI Hard", 2, is_ai=True, difficulty="hard")

    def test_initialization(self):
        self.assertEqual(self.human_player.get_name(), "Alice")
        self.assertEqual(self.human_player.get_piece(), 1)
        self.assertFalse(self.human_player.is_ai_player())
        self.assertEqual(self.ai_player_easy.get_difficulty(), "easy")

    def test_make_move(self):
        board_state = [[0] * 7 for _ in range(6)]
        with self.assertRaises(ValueError):
            self.human_player.make_move(board_state)
        
        move = self.ai_player_easy.make_move(board_state)
        self.assertTrue(0 <= move < 7)

    def test_validate_move(self):
        board_state = [[0] * 7 for _ in range(6)]
        board_state[0][3] = 1  # Column 3 is full
        self.assertTrue(self.human_player.validate_move(0, board_state))
        self.assertFalse(self.human_player.validate_move(3, board_state))
        self.assertFalse(self.human_player.validate_move(7, board_state))

    def test_reset_player(self):
        self.human_player.score = 10
        self.human_player.move_history = [1, 2, 3]
        self.human_player.reset_player()
        self.assertEqual(self.human_player.get_score(), 0)
        self.assertEqual(self.human_player.get_move_history(), [])

    def test_difficulty(self):
        self.ai_player_easy.set_difficulty("hard")
        self.assertEqual(self.ai_player_easy.get_difficulty(), "hard")
        with self.assertRaises(ValueError):
            self.ai_player_easy.set_difficulty("medium")

    def test_ai_strategy(self):
        board_state = [[0] * 7 for _ in range(6)]
        easy_moves = [self.ai_player_easy.make_move(board_state) for _ in range(100)]
        hard_moves = [self.ai_player_hard.make_move(board_state) for _ in range(100)]
        
        # Easy AI should use all columns
        self.assertTrue(len(set(easy_moves)) > 1)
        
        # Hard AI should prefer center columns
        self.assertTrue(easy_moves.count(3) < hard_moves.count(3))


if __name__ == "__main__":
    unittest.main()
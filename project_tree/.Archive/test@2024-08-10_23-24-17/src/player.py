import unittest
import random
from typing import List, Tuple
from board import Board

class Player:
    def __init__(self, name: str, color: int):
        self.name = name
        self.color = color

    def make_move(self, board: Board) -> int:
        raise NotImplementedError("Subclass must implement abstract method")

    def get_state(self) -> Tuple[str, int, str]:
        return self.name, self.color, self.__class__.__name__

    def reset(self) -> None:
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name}, {self.color})"

class HumanPlayer(Player):
    def __init__(self, name: str, color: int):
        super().__init__(name, color)

    def make_move(self, board: Board) -> int:
        while True:
            try:
                column = int(input(f"{self.name}, enter column (0-6): "))
                if 0 <= column <= 6 and board.is_valid_move(column):
                    return column
                print("Invalid move. Try again.")
            except ValueError:
                print("Please enter a valid number.")

class AIPlayer(Player):
    def __init__(self, name: str, color: int):
        super().__init__(name, color)

    def make_move(self, board: Board) -> int:
        valid_moves = board.get_valid_moves()
        return random.choice(valid_moves)

def create_player(player_type: str, name: str, color: int) -> Player:
    if player_type.lower() == "human":
        return HumanPlayer(name, color)
    elif player_type.lower() == "ai":
        return AIPlayer(name, color)
    else:
        raise ValueError("Invalid player type. Choose 'human' or 'ai'.")

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.human = HumanPlayer("Alice", 1)
        self.ai = AIPlayer("Bot", 2)

    def test_player_initialization(self):
        self.assertEqual(self.human.name, "Alice")
        self.assertEqual(self.human.color, 1)
        self.assertEqual(self.ai.name, "Bot")
        self.assertEqual(self.ai.color, 2)

    def test_get_state(self):
        self.assertEqual(self.human.get_state(), ("Alice", 1, "HumanPlayer"))
        self.assertEqual(self.ai.get_state(), ("Bot", 2, "AIPlayer"))

    def test_reset(self):
        self.human.reset()
        self.ai.reset()
        # Reset doesn't change anything in the current implementation
        self.assertEqual(self.human.get_state(), ("Alice", 1, "HumanPlayer"))
        self.assertEqual(self.ai.get_state(), ("Bot", 2, "AIPlayer"))

    def test_str_representation(self):
        self.assertEqual(str(self.human), "HumanPlayer(Alice, 1)")
        self.assertEqual(str(self.ai), "AIPlayer(Bot, 2)")

    def test_ai_make_move(self):
        move = self.ai.make_move(self.board)
        self.assertTrue(0 <= move <= 6)
        self.assertTrue(self.board.is_valid_move(move))

    def test_create_player(self):
        human = create_player("human", "Bob", 1)
        ai = create_player("ai", "AIBot", 2)
        self.assertIsInstance(human, HumanPlayer)
        self.assertIsInstance(ai, AIPlayer)
        with self.assertRaises(ValueError):
            create_player("invalid", "Invalid", 3)

if __name__ == "__main__":
    unittest.main()
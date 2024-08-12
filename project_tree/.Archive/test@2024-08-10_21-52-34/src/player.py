import unittest
from typing import Tuple

class Player:
    def __init__(self, player_number: int, piece_color: str):
        if player_number not in (1, 2):
            raise ValueError("Player number must be 1 or 2")
        self.player_number = player_number
        self.piece_color = piece_color
        self.moves_made = 0
        self.last_move = None

    def make_move(self, column: int) -> bool:
        if not 0 <= column <= 6:
            return False
        self.moves_made += 1
        self.last_move = column
        return True

    def get_player_number(self) -> int:
        return self.player_number

    def get_piece_color(self) -> str:
        return self.piece_color

    def get_state(self) -> Tuple[int, int]:
        return self.moves_made, self.last_move if self.last_move is not None else -1

    def reset(self) -> None:
        self.moves_made = 0
        self.last_move = None

class HumanPlayer(Player):
    def get_move_input(self) -> int:
        while True:
            try:
                move = int(input(f"Player {self.player_number}, enter your move (0-6): "))
                if 0 <= move <= 6:
                    return move
                print("Invalid move. Please enter a number between 0 and 6.")
            except ValueError:
                print("Invalid input. Please enter a number.")

def create_player(player_number: int, piece_color: str, is_human: bool = True) -> Player:
    if is_human:
        return HumanPlayer(player_number, piece_color)
    return Player(player_number, piece_color)

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player(1, "Red")
        self.human_player = HumanPlayer(2, "Yellow")

    def test_player_initialization(self):
        self.assertEqual(self.player.get_player_number(), 1)
        self.assertEqual(self.player.get_piece_color(), "Red")
        self.assertEqual(self.player.get_state(), (0, -1))

    def test_make_move(self):
        self.assertTrue(self.player.make_move(3))
        self.assertFalse(self.player.make_move(7))
        self.assertEqual(self.player.get_state(), (1, 3))

    def test_reset(self):
        self.player.make_move(3)
        self.player.reset()
        self.assertEqual(self.player.get_state(), (0, -1))

    def test_create_player(self):
        human = create_player(1, "Red", True)
        ai = create_player(2, "Yellow", False)
        self.assertIsInstance(human, HumanPlayer)
        self.assertIsInstance(ai, Player)
        self.assertNotIsInstance(ai, HumanPlayer)

    def test_invalid_player_number(self):
        with self.assertRaises(ValueError):
            Player(3, "Green")

if __name__ == "__main__":
    unittest.main()
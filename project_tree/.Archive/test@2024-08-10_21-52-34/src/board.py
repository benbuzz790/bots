import unittest
from typing import List, Tuple

class Board:
    def __init__(self):
        self.rows = 6
        self.columns = 7
        self.board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]

    def place_piece(self, column: int, player: int) -> bool:
        if not self.is_valid_move(column):
            return False
        for row in range(self.rows - 1, -1, -1):
            if self.board[row][column] == 0:
                self.board[row][column] = player
                return True
        return False

    def is_valid_move(self, column: int) -> bool:
        return 0 <= column < self.columns and self.board[0][column] == 0

    def check_win(self, player: int) -> bool:
        # Check horizontal
        for row in range(self.rows):
            for col in range(self.columns - 3):
                if all(self.board[row][col+i] == player for i in range(4)):
                    return True

        # Check vertical
        for row in range(self.rows - 3):
            for col in range(self.columns):
                if all(self.board[row+i][col] == player for i in range(4)):
                    return True

        # Check diagonal (top-left to bottom-right)
        for row in range(self.rows - 3):
            for col in range(self.columns - 3):
                if all(self.board[row+i][col+i] == player for i in range(4)):
                    return True

        # Check diagonal (top-right to bottom-left)
        for row in range(self.rows - 3):
            for col in range(3, self.columns):
                if all(self.board[row+i][col-i] == player for i in range(4)):
                    return True

        return False

    def is_full(self) -> bool:
        return all(self.board[0][col] != 0 for col in range(self.columns))

    def reset(self) -> None:
        self.board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]

    def get_state(self) -> List[List[int]]:
        return [row[:] for row in self.board]

    def __str__(self) -> str:
        return '\n'.join(' '.join(str(cell) for cell in row) for row in self.board)

def create_board() -> Board:
    return Board()

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = create_board()

    def test_initial_board(self):
        self.assertEqual(self.board.get_state(), [[0] * 7 for _ in range(6)])

    def test_place_piece(self):
        self.assertTrue(self.board.place_piece(0, 1))
        self.assertEqual(self.board.get_state()[5][0], 1)

    def test_invalid_move(self):
        for _ in range(6):
            self.board.place_piece(0, 1)
        self.assertFalse(self.board.place_piece(0, 1))

    def test_is_valid_move(self):
        self.assertTrue(self.board.is_valid_move(0))
        for _ in range(6):
            self.board.place_piece(0, 1)
        self.assertFalse(self.board.is_valid_move(0))

    def test_check_win_horizontal(self):
        for i in range(4):
            self.board.place_piece(i, 1)
        self.assertTrue(self.board.check_win(1))

    def test_check_win_vertical(self):
        for _ in range(4):
            self.board.place_piece(0, 1)
        self.assertTrue(self.board.check_win(1))

    def test_check_win_diagonal(self):
        for i in range(4):
            for j in range(i):
                self.board.place_piece(i, 2)
            self.board.place_piece(i, 1)
        self.assertTrue(self.board.check_win(1))

    def test_is_full(self):
        for col in range(7):
            for _ in range(6):
                self.board.place_piece(col, 1)
        self.assertTrue(self.board.is_full())

    def test_reset(self):
        self.board.place_piece(0, 1)
        self.board.reset()
        self.assertEqual(self.board.get_state(), [[0] * 7 for _ in range(6)])

    def test_str_representation(self):
        expected = "0 0 0 0 0 0 0\n" * 5 + "0 0 0 0 0 0 0"
        self.assertEqual(str(self.board), expected)

if __name__ == "__main__":
    unittest.main()
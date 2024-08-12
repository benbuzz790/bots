from typing import List, Tuple, Optional
import unittest

class Board:
    def __init__(self, rows: int = 6, columns: int = 7):
        self.rows = rows
        self.columns = columns
        self.board = [[0 for _ in range(columns)] for _ in range(rows)]

    def place_piece(self, column: int, player: int) -> bool:
        if column < 0 or column >= self.columns:
            return False
        for row in range(self.rows - 1, -1, -1):
            if self.board[row][column] == 0:
                self.board[row][column] = player
                return True
        return False

    def is_column_full(self, column: int) -> bool:
        return self.board[0][column] != 0

    def get_board_state(self) -> List[List[int]]:
        return [row[:] for row in self.board]

    def is_board_full(self) -> bool:
        return all(self.is_column_full(col) for col in range(self.columns))

    def get_cell_state(self, row: int, column: int) -> Optional[int]:
        if 0 <= row < self.rows and 0 <= column < self.columns:
            return self.board[row][column]
        return None

    def reset_board(self) -> None:
        self.board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]

    def get_dimensions(self) -> Tuple[int, int]:
        return self.rows, self.columns

    def __str__(self) -> str:
        return '\n'.join(' '.join(str(cell) for cell in row) for row in self.board)

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_init(self):
        self.assertEqual(self.board.get_dimensions(), (6, 7))
        self.assertEqual(len(self.board.get_board_state()), 6)
        self.assertEqual(len(self.board.get_board_state()[0]), 7)

    def test_place_piece(self):
        self.assertTrue(self.board.place_piece(0, 1))
        self.assertEqual(self.board.get_cell_state(5, 0), 1)
        self.assertFalse(self.board.place_piece(-1, 1))
        self.assertFalse(self.board.place_piece(7, 1))

    def test_is_column_full(self):
        for i in range(6):
            self.board.place_piece(0, 1)
        self.assertTrue(self.board.is_column_full(0))
        self.assertFalse(self.board.is_column_full(1))

    def test_get_board_state(self):
        self.board.place_piece(0, 1)
        state = self.board.get_board_state()
        self.assertEqual(state[5][0], 1)
        state[5][0] = 2
        self.assertEqual(self.board.get_cell_state(5, 0), 1)

    def test_is_board_full(self):
        self.assertFalse(self.board.is_board_full())
        for col in range(7):
            for _ in range(6):
                self.board.place_piece(col, 1)
        self.assertTrue(self.board.is_board_full())

    def test_get_cell_state(self):
        self.board.place_piece(0, 1)
        self.assertEqual(self.board.get_cell_state(5, 0), 1)
        self.assertEqual(self.board.get_cell_state(0, 0), 0)
        self.assertIsNone(self.board.get_cell_state(-1, 0))
        self.assertIsNone(self.board.get_cell_state(6, 0))

    def test_reset_board(self):
        self.board.place_piece(0, 1)
        self.board.reset_board()
        self.assertEqual(self.board.get_cell_state(5, 0), 0)

    def test_str_representation(self):
        self.board.place_piece(0, 1)
        self.board.place_piece(0, 2)
        expected = "0 0 0 0 0 0 0\n0 0 0 0 0 0 0\n0 0 0 0 0 0 0\n0 0 0 0 0 0 0\n2 0 0 0 0 0 0\n1 0 0 0 0 0 0"
        self.assertEqual(str(self.board), expected)

if __name__ == "__main__":
    unittest.main()
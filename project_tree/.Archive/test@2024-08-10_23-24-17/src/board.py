import unittest
from typing import List, Tuple
from threading import Lock

BOARD_COLUMNS = 7
BOARD_ROWS = 6

class Board:
    def __init__(self):
        self._board = [[0 for _ in range(BOARD_COLUMNS)] for _ in range(BOARD_ROWS)]
        self._lock = Lock()

    def place_piece(self, column: int, player: int) -> bool:
        """Place a piece in the specified column for the given player."""
        with self._lock:
            if not self.is_valid_move(column):
                return False
            for row in range(BOARD_ROWS - 1, -1, -1):
                if self._board[row][column] == 0:
                    self._board[row][column] = player
                    return True
            return False

    def is_valid_move(self, column: int) -> bool:
        """Check if a move is valid for the given column."""
        return 0 <= column < BOARD_COLUMNS and self._board[0][column] == 0

    def get_cell(self, row: int, column: int) -> int:
        """Get the value of a cell at the specified row and column."""
        if 0 <= row < BOARD_ROWS and 0 <= column < BOARD_COLUMNS:
            return self._board[row][column]
        raise ValueError("Invalid row or column")

    def check_win(self, player: int) -> bool:
        """Check if the given player has won."""
        # Check horizontal
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLUMNS - 3):
                if all(self._board[row][col+i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(BOARD_ROWS - 3):
            for col in range(BOARD_COLUMNS):
                if all(self._board[row+i][col] == player for i in range(4)):
                    return True
        
        # Check diagonal (positive slope)
        for row in range(BOARD_ROWS - 3):
            for col in range(BOARD_COLUMNS - 3):
                if all(self._board[row+i][col+i] == player for i in range(4)):
                    return True
        
        # Check diagonal (negative slope)
        for row in range(3, BOARD_ROWS):
            for col in range(BOARD_COLUMNS - 3):
                if all(self._board[row-i][col+i] == player for i in range(4)):
                    return True
        
        return False

    def reset(self) -> None:
        """Reset the board to its initial state."""
        with self._lock:
            self._board = [[0 for _ in range(BOARD_COLUMNS)] for _ in range(BOARD_ROWS)]

    def __str__(self) -> str:
        """Return a string representation of the board."""
        return '\n'.join(' '.join(str(cell) for cell in row) for row in self._board)

    def get_board_state(self) -> List[List[int]]:
        """Return the current state of the board."""
        return [row[:] for row in self._board]

    def is_full(self) -> bool:
        """Check if the board is full."""
        return all(self._board[0][col] != 0 for col in range(BOARD_COLUMNS))

    def get_valid_moves(self) -> List[int]:
        """Return a list of valid moves (column indices)."""
        return [col for col in range(BOARD_COLUMNS) if self.is_valid_move(col)]

def create_board() -> Board:
    """Create and return a new Board instance."""
    return Board()

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = create_board()

    def test_initial_board_state(self):
        self.assertEqual(str(self.board).count('0'), BOARD_ROWS * BOARD_COLUMNS)

    def test_place_piece(self):
        self.assertTrue(self.board.place_piece(0, 1))
        self.assertEqual(self.board.get_cell(BOARD_ROWS - 1, 0), 1)

    def test_invalid_move(self):
        for _ in range(BOARD_ROWS):
            self.board.place_piece(0, 1)
        self.assertFalse(self.board.place_piece(0, 1))

    def test_get_cell(self):
        self.board.place_piece(0, 1)
        self.assertEqual(self.board.get_cell(BOARD_ROWS - 1, 0), 1)
        with self.assertRaises(ValueError):
            self.board.get_cell(BOARD_ROWS, 0)

    def test_check_win_horizontal(self):
        for col in range(4):
            self.board.place_piece(col, 1)
        self.assertTrue(self.board.check_win(1))

    def test_check_win_vertical(self):
        for _ in range(4):
            self.board.place_piece(0, 1)
        self.assertTrue(self.board.check_win(1))

    def test_check_win_diagonal(self):
        for col in range(4):
            for _ in range(col):
                self.board.place_piece(col, 2)
            self.board.place_piece(col, 1)
        self.assertTrue(self.board.check_win(1))

    def test_reset(self):
        self.board.place_piece(0, 1)
        self.board.reset()
        self.assertEqual(str(self.board).count('0'), BOARD_ROWS * BOARD_COLUMNS)

    def test_is_full(self):
        for col in range(BOARD_COLUMNS):
            for _ in range(BOARD_ROWS):
                self.board.place_piece(col, 1)
        self.assertTrue(self.board.is_full())

    def test_get_valid_moves(self):
        self.assertEqual(len(self.board.get_valid_moves()), BOARD_COLUMNS)
        for _ in range(BOARD_ROWS):
            self.board.place_piece(0, 1)
        self.assertEqual(len(self.board.get_valid_moves()), BOARD_COLUMNS - 1)

if __name__ == "__main__":
    unittest.main()
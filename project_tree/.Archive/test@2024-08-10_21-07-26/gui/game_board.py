import tkinter as tk
from typing import List, Tuple, Callable
import unittest

class GameBoard(tk.Frame):
    def __init__(self, master: tk.Tk, click_callback: Callable[[int], None]):
        super().__init__(master)
        self.master = master
        self.click_callback = click_callback
        self.rows, self.columns = 6, 7
        self.cell_size = 50
        self.canvas = tk.Canvas(self, width=self.columns*self.cell_size, height=self.rows*self.cell_size, bg='blue')
        self.canvas.pack()
        self.cells = [[None for _ in range(self.columns)] for _ in range(self.rows)]
        self.player1_color = 'red'
        self.player2_color = 'yellow'
        self.create_grid()
        self.canvas.bind('<Button-1>', self.on_click)

    def create_grid(self):
        for row in range(self.rows):
            for col in range(self.columns):
                x1, y1 = col * self.cell_size, row * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.cells[row][col] = self.canvas.create_oval(x1+2, y1+2, x2-2, y2-2, fill='white', outline='black')

    def on_click(self, event):
        col = event.x // self.cell_size
        self.click_callback(col)

    def update_board(self, board_state: List[List[int]]) -> None:
        for row in range(self.rows):
            for col in range(self.columns):
                color = 'white'
                if board_state[row][col] == 1:
                    color = self.player1_color
                elif board_state[row][col] == 2:
                    color = self.player2_color
                self.canvas.itemconfig(self.cells[row][col], fill=color)

    def highlight_winning_combination(self, winning_cells: List[Tuple[int, int]]) -> None:
        for row, col in winning_cells:
            self.canvas.itemconfig(self.cells[row][col], outline='green', width=3)

    def reset_board(self) -> None:
        for row in range(self.rows):
            for col in range(self.columns):
                self.canvas.itemconfig(self.cells[row][col], fill='white', outline='black', width=1)

    def simulate_click(self, column: int) -> None:
        self.click_callback(column)

    def get_cell_state(self, row: int, column: int) -> int:
        color = self.canvas.itemcget(self.cells[row][column], 'fill')
        if color == self.player1_color:
            return 1
        elif color == self.player2_color:
            return 2
        return 0

    def set_piece_colors(self, player1_color: str, player2_color: str) -> None:
        self.player1_color = player1_color
        self.player2_color = player2_color

    def enable_board(self) -> None:
        self.canvas.bind('<Button-1>', self.on_click)

    def disable_board(self) -> None:
        self.canvas.unbind('<Button-1>')

    def get_board_dimensions(self) -> Tuple[int, int]:
        return self.rows, self.columns

    def is_column_full(self, column: int) -> bool:
        return self.get_cell_state(0, column) != 0

    def set_error_state(self, column: int, error: bool) -> None:
        color = 'red' if error else 'black'
        for row in range(self.rows):
            self.canvas.itemconfig(self.cells[row][column], outline=color)

class TestGameBoard(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.click_callback = lambda x: None
        self.game_board = GameBoard(self.root, self.click_callback)

    def tearDown(self):
        self.root.destroy()

    def test_initialization(self):
        self.assertEqual(self.game_board.get_board_dimensions(), (6, 7))

    def test_update_board(self):
        board_state = [[0] * 7 for _ in range(6)]
        board_state[5][3] = 1
        self.game_board.update_board(board_state)
        self.assertEqual(self.game_board.get_cell_state(5, 3), 1)

    def test_highlight_winning_combination(self):
        winning_cells = [(0, 0), (1, 1), (2, 2), (3, 3)]
        self.game_board.highlight_winning_combination(winning_cells)
        for row, col in winning_cells:
            self.assertEqual(self.game_board.canvas.itemcget(self.game_board.cells[row][col], 'outline'), 'green')

    def test_reset_board(self):
        board_state = [[1] * 7 for _ in range(6)]
        self.game_board.update_board(board_state)
        self.game_board.reset_board()
        for row in range(6):
            for col in range(7):
                self.assertEqual(self.game_board.get_cell_state(row, col), 0)

    def test_set_piece_colors(self):
        self.game_board.set_piece_colors('blue', 'green')
        self.assertEqual(self.game_board.player1_color, 'blue')
        self.assertEqual(self.game_board.player2_color, 'green')

    def test_is_column_full(self):
        board_state = [[0] * 7 for _ in range(6)]
        board_state[0][3] = 1
        self.game_board.update_board(board_state)
        self.assertTrue(self.game_board.is_column_full(3))
        self.assertFalse(self.game_board.is_column_full(0))

    def test_set_error_state(self):
        self.game_board.set_error_state(3, True)
        self.assertEqual(self.game_board.canvas.itemcget(self.game_board.cells[0][3], 'outline'), 'red')
        self.game_board.set_error_state(3, False)
        self.assertEqual(self.game_board.canvas.itemcget(self.game_board.cells[0][3], 'outline'), 'black')

if __name__ == '__main__':
    unittest.main()
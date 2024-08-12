import tkinter as tk
from typing import List, Tuple, Callable
import unittest
from unittest.mock import MagicMock

class BoardWidget:
    def __init__(self, parent, width: int, height: int, on_click: Callable[[int], None]):
        self.parent = parent
        self.width = width
        self.height = height
        self.on_click = on_click
        self.canvas = tk.Canvas(parent, width=width, height=height)
        self.canvas.pack()
        self.cells = []
        self.create_grid()
        self.canvas.bind("<Button-1>", self.handle_click)
        self.keyboard_navigation_enabled = False
        self.current_column = 0

    def create_grid(self):
        cell_width = self.width // 7
        cell_height = self.height // 6
        for row in range(6):
            for col in range(7):
                x1 = col * cell_width
                y1 = row * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height
                cell = self.canvas.create_oval(x1, y1, x2, y2, fill="white", outline="blue")
                self.cells.append(cell)

    def update_board(self, board_state: List[List[int]]) -> None:
        for row in range(6):
            for col in range(7):
                index = row * 7 + col
                color = "white"
                if board_state[row][col] == 1:
                    color = "red"
                elif board_state[row][col] == 2:
                    color = "yellow"
                self.canvas.itemconfig(self.cells[index], fill=color)

    def highlight_column(self, column: int) -> None:
        for row in range(6):
            index = row * 7 + column
            self.canvas.itemconfig(self.cells[index], outline="green")

    def unhighlight_column(self, column: int) -> None:
        for row in range(6):
            index = row * 7 + column
            self.canvas.itemconfig(self.cells[index], outline="blue")

    def show_invalid_move(self, column: int) -> None:
        for row in range(6):
            index = row * 7 + column
            self.canvas.itemconfig(self.cells[index], outline="red")
        self.parent.after(500, lambda: self.unhighlight_column(column))

    def highlight_winning_combination(self, winning_positions: List[Tuple[int, int]]) -> None:
        for row, col in winning_positions:
            index = row * 7 + col
            self.canvas.itemconfig(self.cells[index], outline="green", width=3)

    def reset_board(self) -> None:
        for cell in self.cells:
            self.canvas.itemconfig(cell, fill="white", outline="blue", width=1)

    def simulate_click(self, column: int) -> None:
        self.on_click(column)

    def set_keyboard_navigation(self, enabled: bool) -> None:
        self.keyboard_navigation_enabled = enabled
        if enabled:
            self.parent.bind("<Left>", lambda e: self.on_click(max(0, self.current_column - 1)))
            self.parent.bind("<Right>", lambda e: self.on_click(min(6, self.current_column + 1)))
            self.parent.bind("<space>", lambda e: self.on_click(self.current_column))
        else:
            self.parent.unbind("<Left>")
            self.parent.unbind("<Right>")
            self.parent.unbind("<space>")

    def get_current_state(self) -> List[List[int]]:
        state = [[0 for _ in range(7)] for _ in range(6)]
        for row in range(6):
            for col in range(7):
                index = row * 7 + col
                color = self.canvas.itemcget(self.cells[index], "fill")
                if color == "red":
                    state[row][col] = 1
                elif color == "yellow":
                    state[row][col] = 2
        return state

    def handle_click(self, event):
        cell_width = self.width // 7
        column = event.x // cell_width
        self.on_click(column)

def create_board_widget(parent, width: int, height: int, on_click: Callable[[int], None]) -> BoardWidget:
    return BoardWidget(parent, width, height, on_click)

class TestBoardWidget(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.on_click_mock = MagicMock()
        self.board_widget = create_board_widget(self.root, 700, 600, self.on_click_mock)

    def tearDown(self):
        self.root.destroy()

    def test_update_board(self):
        board_state = [[0, 1, 2, 0, 0, 0, 0] for _ in range(6)]
        self.board_widget.update_board(board_state)
        self.assertEqual(self.board_widget.get_current_state(), board_state)

    def test_highlight_column(self):
        self.board_widget.highlight_column(3)
        for row in range(6):
            index = row * 7 + 3
            self.assertEqual(self.board_widget.canvas.itemcget(self.board_widget.cells[index], "outline"), "green")

    def test_unhighlight_column(self):
        self.board_widget.highlight_column(3)
        self.board_widget.unhighlight_column(3)
        for row in range(6):
            index = row * 7 + 3
            self.assertEqual(self.board_widget.canvas.itemcget(self.board_widget.cells[index], "outline"), "blue")

    def test_show_invalid_move(self):
        self.board_widget.show_invalid_move(3)
        for row in range(6):
            index = row * 7 + 3
            self.assertEqual(self.board_widget.canvas.itemcget(self.board_widget.cells[index], "outline"), "red")
        self.root.after(600, self.root.quit)
        self.root.mainloop()
        for row in range(6):
            index = row * 7 + 3
            self.assertEqual(self.board_widget.canvas.itemcget(self.board_widget.cells[index], "outline"), "blue")

    def test_highlight_winning_combination(self):
        winning_positions = [(0, 0), (1, 1), (2, 2), (3, 3)]
        self.board_widget.highlight_winning_combination(winning_positions)
        for row, col in winning_positions:
            index = row * 7 + col
            self.assertEqual(self.board_widget.canvas.itemcget(self.board_widget.cells[index], "outline"), "green")
            self.assertAlmostEqual(float(self.board_widget.canvas.itemcget(self.board_widget.cells[index], "width")), 3.0)

    def test_reset_board(self):
        board_state = [[1, 2, 1, 2, 1, 2, 1] for _ in range(6)]
        self.board_widget.update_board(board_state)
        self.board_widget.reset_board()
        empty_state = [[0 for _ in range(7)] for _ in range(6)]
        self.assertEqual(self.board_widget.get_current_state(), empty_state)

    def test_simulate_click(self):
        self.board_widget.simulate_click(3)
        self.on_click_mock.assert_called_once_with(3)

    def test_set_keyboard_navigation(self):
        self.board_widget.set_keyboard_navigation(True)
        self.assertTrue(self.board_widget.keyboard_navigation_enabled)
        self.board_widget.set_keyboard_navigation(False)
        self.assertFalse(self.board_widget.keyboard_navigation_enabled)

    def test_get_current_state(self):
        board_state = [[0, 1, 2, 0, 0, 0, 0] for _ in range(6)]
        self.board_widget.update_board(board_state)
        self.assertEqual(self.board_widget.get_current_state(), board_state)

if __name__ == "__main__":
    unittest.main()
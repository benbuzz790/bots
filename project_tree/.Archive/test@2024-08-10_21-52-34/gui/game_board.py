import unittest
import tkinter as tk
from typing import Callable, Tuple, List
from gui.gui_utils import (
    PLAYER_1_COLOR, PLAYER_2_COLOR, EMPTY_SLOT_COLOR, BACKGROUND_COLOR, HIGHLIGHT_COLOR,
    calculate_grid_position, create_widget, AnimationHelper, set_timeout
)

class GameBoard:
    def __init__(self, parent_widget: tk.Widget, rows: int = 6, columns: int = 7):
        self.parent = parent_widget
        self.rows = rows
        self.columns = columns
        self.cell_size = 50
        self.canvas = create_widget(self.parent, 'Canvas', bg=BACKGROUND_COLOR)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.slots: List[List[tk.Canvas]] = []
        self.column_click_handler: Callable[[int], None] = lambda _: None
        self.test_mode = False
        self._create_grid()
        self.canvas.bind("<Configure>", self._on_resize)
        self.keyboard_navigation_enabled = False

    def _create_grid(self):
        for row in range(self.rows):
            slot_row = []
            for col in range(self.columns):
                x, y = calculate_grid_position(row, col, self.cell_size)
                slot = self.canvas.create_oval(x, y, x + self.cell_size, y + self.cell_size, fill=EMPTY_SLOT_COLOR)
                slot_row.append(slot)
            self.slots.append(slot_row)

        for col in range(self.columns):
            self.canvas.tag_bind(f"column_{col}", "<Button-1>", lambda e, c=col: self.column_click_handler(c))

    def _on_resize(self, event):
        width, height = event.width, event.height
        self.cell_size = min(width // self.columns, height // self.rows)
        self._update_grid_positions()

    def _update_grid_positions(self):
        for row in range(self.rows):
            for col in range(self.columns):
                x, y = calculate_grid_position(row, col, self.cell_size)
                self.canvas.coords(self.slots[row][col], x, y, x + self.cell_size, y + self.cell_size)

    def update_board(self, board_state: Tuple[Tuple[int, ...], ...]) -> None:
        for row in range(self.rows):
            for col in range(self.columns):
                color = EMPTY_SLOT_COLOR
                if board_state[row][col] == 1:
                    color = PLAYER_1_COLOR
                elif board_state[row][col] == 2:
                    color = PLAYER_2_COLOR
                self.canvas.itemconfig(self.slots[row][col], fill=color)

    def highlight_column(self, column: int, highlight: bool = True) -> None:
        color = HIGHLIGHT_COLOR if highlight else BACKGROUND_COLOR
        for row in range(self.rows):
            x, y = calculate_grid_position(row, column, self.cell_size)
            self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size, fill=color, tags=f"column_{column}")

    def set_column_click_handler(self, handler: Callable[[int], None]) -> None:
        self.column_click_handler = handler

    def enable_keyboard_navigation(self) -> None:
        self.keyboard_navigation_enabled = True
        self.parent.bind("<Left>", lambda e: self._move_selection(-1))
        self.parent.bind("<Right>", lambda e: self._move_selection(1))
        self.parent.bind("<Return>", lambda e: self._select_column())

    def disable_keyboard_navigation(self) -> None:
        self.keyboard_navigation_enabled = False
        self.parent.unbind("<Left>")
        self.parent.unbind("<Right>")
        self.parent.unbind("<Return>")

    def _move_selection(self, direction: int):
        if not self.keyboard_navigation_enabled:
            return
        current_column = getattr(self, 'selected_column', 0)
        new_column = (current_column + direction) % self.columns
        self.highlight_column(current_column, False)
        self.highlight_column(new_column, True)
        self.selected_column = new_column

    def _select_column(self):
        if not self.keyboard_navigation_enabled:
            return
        if hasattr(self, 'selected_column'):
            self.column_click_handler(self.selected_column)

    def reset_board(self) -> None:
        for row in range(self.rows):
            for col in range(self.columns):
                self.canvas.itemconfig(self.slots[row][col], fill=EMPTY_SLOT_COLOR)

    def set_test_mode(self, enabled: bool) -> None:
        self.test_mode = enabled
        if enabled:
            set_timeout(self.canvas, 1000)  # 1 second timeout for testing

def create_game_board(parent_widget: tk.Widget, rows: int = 6, columns: int = 7) -> GameBoard:
    return GameBoard(parent_widget, rows, columns)

class TestGameBoard(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.game_board = create_game_board(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_create_game_board(self):
        self.assertIsInstance(self.game_board, GameBoard)
        self.assertEqual(self.game_board.rows, 6)
        self.assertEqual(self.game_board.columns, 7)

    def test_update_board(self):
        board_state = tuple(tuple(0 for _ in range(7)) for _ in range(6))
        self.game_board.update_board(board_state)
        # Check that all slots are empty (visual inspection would be needed for full verification)
        self.assertTrue(all(self.game_board.canvas.itemcget(slot, 'fill') == EMPTY_SLOT_COLOR
                            for row in self.game_board.slots for slot in row))

    def test_highlight_column(self):
        self.game_board.highlight_column(3, True)
        # Visual inspection would be needed for full verification
        self.assertTrue(self.game_board.canvas.find_withtag("column_3"))

    def test_set_column_click_handler(self):
        clicked_column = None
        def handler(column):
            nonlocal clicked_column
            clicked_column = column
        
        self.game_board.set_column_click_handler(handler)
        self.game_board.column_click_handler(3)
        self.assertEqual(clicked_column, 3)

    def test_keyboard_navigation(self):
        self.game_board.enable_keyboard_navigation()
        self.assertTrue(self.game_board.keyboard_navigation_enabled)
        self.game_board.disable_keyboard_navigation()
        self.assertFalse(self.game_board.keyboard_navigation_enabled)

    def test_reset_board(self):
        board_state = tuple(tuple(1 for _ in range(7)) for _ in range(6))
        self.game_board.update_board(board_state)
        self.game_board.reset_board()
        # Check that all slots are empty (visual inspection would be needed for full verification)
        self.assertTrue(all(self.game_board.canvas.itemcget(slot, 'fill') == EMPTY_SLOT_COLOR
                            for row in self.game_board.slots for slot in row))

    def test_set_test_mode(self):
        self.game_board.set_test_mode(True)
        self.assertTrue(self.game_board.test_mode)
        self.game_board.set_test_mode(False)
        self.assertFalse(self.game_board.test_mode)

if __name__ == "__main__":
    unittest.main()
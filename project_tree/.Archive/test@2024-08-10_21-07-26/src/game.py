from typing import List, Tuple
import unittest
from board import Board
from player import Player

class Game:
    def __init__(self, players: List[Player]):
        if len(players) != 2:
            raise ValueError("Game requires exactly 2 players")
        self.players = players
        self.board = Board()
        self.current_player_index = 0
        self.game_over = False
        self.winner = None

    def start_game(self) -> None:
        self.board.reset_board()
        self.current_player_index = 0
        self.game_over = False
        self.winner = None

    def make_move(self, player: Player, column: int) -> bool:
        print(f"Current player index before move: {self.current_player_index}")
        print(f"Attempting move for player {player.get_name()} in column {column}")
        if self.game_over or player != self.get_current_player():
            print("Move rejected: game over or wrong player")
            return False
        if self.board.place_piece(column, player.get_piece()):
            print("Piece placed successfully")
            if self.check_win()[0]:
                self.game_over = True
                self.winner = player
                print("Win detected")
            elif self.check_draw():
                self.game_over = True
                print("Draw detected")
            else:
                self.current_player_index = 1 - self.current_player_index
                print(f"Switching player. New index: {self.current_player_index}")
            return True
        print("Failed to place piece")
        return False

    def check_win(self) -> Tuple[bool, Player]:
        for row in range(6):
            for col in range(7):
                if self._check_win_from_cell(row, col):
                    return True, self.get_current_player()
        return False, None

    def _check_win_from_cell(self, row: int, col: int) -> bool:
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            if self._check_line(row, col, dr, dc):
                return True
        return False

    def _check_line(self, row: int, col: int, dr: int, dc: int) -> bool:
        player = self.board.get_cell_state(row, col)
        if player is None:
            return False
        for i in range(1, 4):
            r, c = row + i * dr, col + i * dc
            if not (0 <= r < 6 and 0 <= c < 7) or self.board.get_cell_state(r, c) != player:
                return False
        return True

    def check_draw(self) -> bool:
        return all(self.board.get_cell_state(0, col) is not None for col in range(7))

    def is_game_over(self) -> bool:
        return self.game_over

    def reset_game(self) -> None:
        self.start_game()

    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    def get_board_state(self) -> Board:
        return self.board

class TestGame(unittest.TestCase):
    def setUp(self):
        self.player1 = Player("Player 1", 1)
        self.player2 = Player("Player 2", 2)
        self.game = Game([self.player1, self.player2])

    def test_initialization(self):
        self.assertEqual(len(self.game.players), 2)
        self.assertIsInstance(self.game.board, Board)
        self.assertFalse(self.game.game_over)

    def test_start_game(self):
        self.game.start_game()
        self.assertEqual(self.game.current_player_index, 0)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)

    def test_make_move(self):
        initial_player = self.game.get_current_player()
        print(f"Initial player: {initial_player.get_name()}")
        self.assertTrue(self.game.make_move(initial_player, 0))
        new_player = self.game.get_current_player()
        print(f"New player after move: {new_player.get_name()}")
        self.assertNotEqual(new_player, initial_player)
        self.assertFalse(self.game.make_move(initial_player, 0))  # Wrong player
        self.assertTrue(self.game.make_move(new_player, 1))
        self.assertEqual(self.game.get_current_player(), initial_player)

    def test_check_win(self):
        for i in range(4):
            self.game.make_move(self.player1, i)
            if i < 3:
                self.game.make_move(self.player2, i)
        self.assertTrue(self.game.check_win()[0])
        self.assertEqual(self.game.check_win()[1], self.player1)

    def test_check_draw(self):
        for col in range(7):
            for _ in range(5):
                self.game.make_move(self.game.get_current_player(), col)
        # Fill the last row to ensure a draw
        for col in range(7):
            self.game.make_move(self.game.get_current_player(), col)
        self.assertTrue(self.game.check_draw())

    def test_is_game_over(self):
        self.assertFalse(self.game.is_game_over())
        for i in range(4):
            self.game.make_move(self.player1, i)
            if i < 3:
                self.game.make_move(self.player2, i)
        self.assertTrue(self.game.is_game_over())

    def test_reset_game(self):
        self.game.make_move(self.player1, 0)
        self.game.reset_game()
        self.assertEqual(self.game.current_player_index, 0)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)

    def test_get_current_player(self):
        initial_player = self.game.get_current_player()
        print(f"Initial player: {initial_player.get_name()}")
        self.game.make_move(initial_player, 0)
        new_player = self.game.get_current_player()
        print(f"New player after move: {new_player.get_name()}")
        self.assertNotEqual(new_player, initial_player)
        self.assertEqual(new_player, self.player2 if initial_player == self.player1 else self.player1)

    def test_get_board_state(self):
        self.assertIsInstance(self.game.get_board_state(), Board)

if __name__ == "__main__":
    unittest.main()
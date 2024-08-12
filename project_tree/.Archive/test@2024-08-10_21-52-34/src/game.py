import unittest
from typing import Tuple
from board import Board, create_board
from player import Player, create_player

class ConnectFourGame:
    def __init__(self):
        self.board = create_board()
        self.players = [create_player(1, "Red"), create_player(2, "Yellow")]
        self.current_player_index = 0

    def start_game(self) -> None:
        self.board.reset()
        self.current_player_index = 0

    def make_move(self, column: int) -> bool:
        if not self.board.is_valid_move(column):
            return False
        player = self.players[self.current_player_index]
        success = self.board.place_piece(column, player.get_player_number())
        if success:
            self.current_player_index = (self.current_player_index + 1) % 2
        return success

    def check_win(self) -> bool:
        return self.board.check_win(self.players[self.current_player_index].get_player_number())

    def check_draw(self) -> bool:
        return self.board.is_full()

    def get_current_player(self) -> int:
        return self.players[self.current_player_index].get_player_number()

    def get_board_state(self) -> Tuple[Tuple[int, ...], ...]:
        return tuple(tuple(row) for row in self.board.get_state())

    def reset_game(self) -> None:
        self.start_game()

def run_game() -> None:
    game = ConnectFourGame()
    game.start_game()
    while True:
        print(game.board)
        current_player = game.get_current_player()
        column = int(input(f"Player {current_player}, choose a column (0-6): "))
        if game.make_move(column):
            if game.check_win():
                print(f"Player {current_player} wins!")
                break
            elif game.check_draw():
                print("It's a draw!")
                break
        else:
            print("Invalid move. Try again.")

class TestConnectFourGame(unittest.TestCase):
    def setUp(self):
        self.game = ConnectFourGame()

    def test_start_game(self):
        self.game.start_game()
        self.assertEqual(self.game.get_current_player(), 1)
        self.assertEqual(self.game.get_board_state(), tuple(tuple(0 for _ in range(7)) for _ in range(6)))

    def test_make_move(self):
        self.game.start_game()
        self.assertTrue(self.game.make_move(3))
        self.assertEqual(self.game.get_board_state()[5][3], 1)
        self.assertEqual(self.game.get_current_player(), 2)

    def test_invalid_move(self):
        self.game.start_game()
        self.assertFalse(self.game.make_move(7))
        self.assertEqual(self.game.get_current_player(), 1)

    def test_check_win(self):
        self.game.start_game()
        for i in range(4):
            self.game.make_move(i)
            self.game.make_move(i)
        self.assertTrue(self.game.check_win())

    def test_check_draw(self):
        self.game.start_game()
        for col in range(7):
            for _ in range(6):
                self.game.make_move(col)
        self.assertTrue(self.game.check_draw())

    def test_reset_game(self):
        self.game.start_game()
        self.game.make_move(0)
        self.game.reset_game()
        self.assertEqual(self.game.get_current_player(), 1)
        self.assertEqual(self.game.get_board_state(), tuple(tuple(0 for _ in range(7)) for _ in range(6)))

if __name__ == "__main__":
    unittest.main()
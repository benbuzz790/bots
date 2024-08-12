import unittest
from typing import List, Tuple
from board import Board, create_board, BOARD_COLUMNS, BOARD_ROWS
from player import Player, create_player
from utils import ConnectFourError, handle_game_exception, validate_column_input

class Game:
    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2
        self.board = create_board()
        self.current_player = self.player1
        self.game_over = False
        self.winner = None
        self.move_count = 0

    def initialize_game(self) -> None:
        self.board.reset()
        self.current_player = self.player1
        self.game_over = False
        self.winner = None
        self.move_count = 0

    def make_move(self, column: int) -> bool:
        if self.game_over or not self.board.is_valid_move(column):
            return False
        
        success = self.board.place_piece(column, self.current_player.get_state()[1])
        if success:
            self.move_count += 1
            self.update_game_state(column)
        return success

    def update_game_state(self, last_move_column: int) -> None:
        print(f"Updating game state after move {self.move_count} in column {last_move_column}")
        if self.check_draw():
            self.game_over = True
            self.winner = None
            print("Draw detected")
        elif self.check_win(last_move_column):
            self.game_over = True
            self.winner = self.current_player
            print(f"Win detected for {self.current_player}")
        else:
            self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            print(f"Switching to {self.current_player}")
        
        print(f"Move count: {self.move_count}, Game over: {self.game_over}, Winner: {self.winner}")
        print(f"Current board state:\n{self.board}")

    def check_win(self, last_move_column: int) -> bool:
        return self.board.check_win(self.current_player.get_state()[1])

    def check_draw(self) -> bool:
        is_draw = self.move_count == BOARD_COLUMNS * BOARD_ROWS or self.board.is_full()
        print(f"Checking draw: move_count={self.move_count}, BOARD_COLUMNS*BOARD_ROWS={BOARD_COLUMNS*BOARD_ROWS}, board.is_full()={self.board.is_full()}, is_draw={is_draw}")
        return is_draw

    def reset_game(self) -> None:
        self.initialize_game()

    def get_current_player(self) -> Player:
        return self.current_player

    def get_game_state(self) -> Tuple[Board, Player, bool, bool]:
        return (self.board, self.current_player, self.game_over, self.winner is not None)

    def play_game(self) -> None:
        self.initialize_game()
        while not self.game_over:
            try:
                column = self.current_player.make_move(self.board)
                if not self.make_move(column):
                    print(f"Invalid move by {self.current_player}. Try again.")
            except ConnectFourError as e:
                print(handle_game_exception(e))
        
        if self.winner:
            print(f"{self.winner} wins!")
        else:
            print("It's a draw!")

def run_console_game() -> None:
    player1 = create_player("human", "Player 1", 1)
    player2 = create_player("human", "Player 2", 2)
    game = Game(player1, player2)
    game.play_game()

class TestGame(unittest.TestCase):
    def setUp(self):
        self.player1 = create_player("human", "Player 1", 1)
        self.player2 = create_player("human", "Player 2", 2)
        self.game = Game(self.player1, self.player2)

    def test_initialization(self):
        self.assertEqual(self.game.get_current_player(), self.player1)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)

    def test_make_move(self):
        self.assertTrue(self.game.make_move(0))
        self.assertEqual(self.game.get_current_player(), self.player2)

    def test_invalid_move(self):
        self.assertFalse(self.game.make_move(-1))
        self.assertEqual(self.game.get_current_player(), self.player1)

    def test_win_condition(self):
        for i in range(4):
            self.game.make_move(i)
            self.game.make_move(i) if i < 3 else None
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.winner, self.player1)

    def test_draw_condition(self):
        print("\nStarting draw condition test")
        moves = [0, 1, 0, 1, 0, 1, 2, 3, 2, 3, 2, 3, 4, 5, 4, 5, 4, 5, 1, 0, 6, 6, 6, 6, 5, 4, 3, 2, 6, 5, 4, 3, 2, 0, 3, 2, 1, 0, 6, 5, 4]
        for i, move in enumerate(moves, 1):
            print(f"Making move {i}: {move}")
            self.game.make_move(move)
        
        print(f"Final move count: {self.game.move_count}")
        print(f"Board state:\n{self.game.board}")
        print(f"Game over: {self.game.game_over}")
        print(f"Winner: {self.game.winner}")
        self.assertTrue(self.game.game_over)
        self.assertIsNone(self.game.winner)

    def test_reset_game(self):
        self.game.make_move(0)
        self.game.reset_game()
        self.assertEqual(self.game.get_current_player(), self.player1)
        self.assertFalse(self.game.game_over)
        self.assertIsNone(self.game.winner)

    def test_get_game_state(self):
        state = self.game.get_game_state()
        self.assertIsInstance(state[0], Board)
        self.assertEqual(state[1], self.player1)
        self.assertFalse(state[2])
        self.assertFalse(state[3])

if __name__ == "__main__":
    unittest.main()
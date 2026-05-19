from .ChessPiece import ChessPiece
from .Colors import Color


class King(ChessPiece):
    """Class for King piece"""
    text = ["♔", "♚"]
    char = 'K'
    diagonals = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    axis = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def get_possible_moves(self):
        possible_moves = []
        for dx, dy in self.axis + self.diagonals:
            new_x, new_y = self.x + dx, self.y + dy
            if not self.is_inside_board(new_x, new_y):
                continue
            if self.board.is_empty_at(new_x, new_y) or self.is_enemy_at(new_x, new_y):
                possible_moves.append((new_x, new_y))
        return possible_moves

    def calculate_valid_moves(self):
        super().calculate_valid_moves()

        game_state = self.board.get_state()

        # Король під час рокіровки не може бути під шахом
        if self.color == Color.WHITE and game_state.white_king_under_attack:
            return
        if self.color == Color.BLACK and game_state.black_king_under_attack:
            return

        if self.color == Color.WHITE:
            # Біла рокіровка (Y = 7)
            if self.position != (4, 7): return  # Король має бути на стартовій

            # Коротка рокіровка
            if self.board.castling_state.white_king_side:
                if self.board.is_empty_at(5, 7) and self.board.is_empty_at(6, 7):
                    if (5, 7) not in game_state.black_attack and (6, 7) not in game_state.black_attack:
                        self.moves.append((6, 7))
            # Довга рокіровка
            if self.board.castling_state.white_queen_side:
                if self.board.is_empty_at(3, 7) and self.board.is_empty_at(2, 7) and self.board.is_empty_at(1, 7):
                    if (3, 7) not in game_state.black_attack and (2, 7) not in game_state.black_attack:
                        self.moves.append((2, 7))
        else:
            # Чорна рокіровка (Y = 0)
            if self.position != (4, 0): return  # Король має бути на стартовій

            # Коротка рокіровка
            if self.board.castling_state.black_king_side:
                if self.board.is_empty_at(5, 0) and self.board.is_empty_at(6, 0):
                    if (5, 0) not in game_state.white_attack and (6, 0) not in game_state.white_attack:
                        self.moves.append((6, 0))
            # Довга рокіровка
            if self.board.castling_state.black_queen_side:
                if self.board.is_empty_at(3, 0) and self.board.is_empty_at(2, 0) and self.board.is_empty_at(1, 0):
                    if (3, 0) not in game_state.white_attack and (2, 0) not in game_state.white_attack:
                        self.moves.append((2, 0))


__all__ = ['King']
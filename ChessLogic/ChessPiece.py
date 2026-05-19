from .Colors import Color


class ChessPiece:
    """Class for chess piece"""
    text = ["", ""]
    char = ""

    def __init__(self, x, y, color, board):
        self.x, self.y = x, y
        self.color = color
        self.board = board
        self.moves = []

    @property
    def position(self):
        return self.x, self.y

    @property
    def char_repr(self):
        return self.char.upper() if self.color == Color.WHITE else self.char.lower()

    @property
    def text_repr(self):
        return self.text[self.color == Color.BLACK]

    def set_position(self, new_x, new_y):
        self.x, self.y = new_x, new_y

    def get_possible_moves(self):
        return []

    def set_moves(self, moves):
        self.moves.clear()
        self.moves.extend(moves)

    def calculate_valid_moves(self):
        moves = self.get_possible_moves()
        valid_moves = []
        for new_x, new_y in moves:
            position_after_move = self.board.generate_position_after_move(self.x, self.y, new_x, new_y)
            state_after_move = position_after_move.get_state()

            if self.color == Color.WHITE and state_after_move.white_king_under_attack:
                continue
            if self.color == Color.BLACK and state_after_move.black_king_under_attack:
                continue

            valid_moves.append((new_x, new_y))
        self.set_moves(valid_moves)

    def get_attack_moves(self):
        return self.get_possible_moves()

    def can_move(self, new_x, new_y):
        return (new_x, new_y) in self.moves

    def copy(self, promotion, new_board):
        piece_class = promotion if promotion else self.__class__
        return piece_class(self.x, self.y, self.color, new_board)

    def is_enemy_at(self, new_x, new_y):
        piece = self.board.get_piece_at(new_x, new_y)
        return piece is not None and piece.color != self.color

    @staticmethod
    def is_inside_board(x, y):
        return 0 <= x < 8 and 0 <= y < 8

    def __str__(self):
        return '{} {} at ({}, {})'.format(self.color, self.__class__.__name__, self.x, self.y)


__all__ = ['ChessPiece']
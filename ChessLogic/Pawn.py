from .ChessPiece import ChessPiece
from .Colors import Color


class Pawn(ChessPiece):
    """Class for Pawn piece"""
    text = ["♙", "♟"]
    char = 'P'

    def get_possible_moves(self):
        possible_moves = []
        if self.color == Color.WHITE:
            # Білі пішаки (рух вгору: Y - 1)
            if self.y == 6:
                if self.board.is_empty_at(self.x, 5):
                    possible_moves.append((self.x, 5))
                if self.board.is_empty_at(self.x, 4) and self.board.is_empty_at(self.x, 5):
                    possible_moves.append((self.x, 4))

            # Звичайний хід
            if self.board.is_empty_at(self.x, self.y - 1):
                possible_moves.append((self.x, self.y - 1))

            # Атака по діагоналі ТА ВЗЯТТЯ НА ПРОХОДІ
            if self.is_enemy_at(self.x - 1, self.y - 1) or self.board.en_passant == (self.x - 1, self.y - 1):
                possible_moves.append((self.x - 1, self.y - 1))
            if self.is_enemy_at(self.x + 1, self.y - 1) or self.board.en_passant == (self.x + 1, self.y - 1):
                possible_moves.append((self.x + 1, self.y - 1))
        else:
            # Чорні пішаки (рух вниз: Y + 1)
            if self.y == 1:
                if self.board.is_empty_at(self.x, 2):
                    possible_moves.append((self.x, 2))
                if self.board.is_empty_at(self.x, 3) and self.board.is_empty_at(self.x, 2):
                    possible_moves.append((self.x, 3))

            # Звичайний хід
            if self.board.is_empty_at(self.x, self.y + 1):
                possible_moves.append((self.x, self.y + 1))

            # Атака по діагоналі ТА ВЗЯТТЯ НА ПРОХОДІ
            if self.is_enemy_at(self.x - 1, self.y + 1) or self.board.en_passant == (self.x - 1, self.y + 1):
                possible_moves.append((self.x - 1, self.y + 1))
            if self.is_enemy_at(self.x + 1, self.y + 1) or self.board.en_passant == (self.x + 1, self.y + 1):
                possible_moves.append((self.x + 1, self.y + 1))

        return possible_moves

    def get_attack_moves(self):
        attack_moves = []
        if self.color == Color.WHITE:
            attack_moves.append((self.x - 1, self.y - 1))
            attack_moves.append((self.x + 1, self.y - 1))
        else:
            attack_moves.append((self.x - 1, self.y + 1))
            attack_moves.append((self.x + 1, self.y + 1))
        return attack_moves


__all__ = ['Pawn']
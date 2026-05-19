from .ChessPiece import ChessPiece

class Rook(ChessPiece):
    """Class for Rook piece"""
    text = ["♖", "♜"]
    char = 'R'
    axis = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def get_possible_moves(self):
        """Rook can move any number of cells horizontally or vertically without jumping"""
        possible_moves = []
        for dx, dy in self.axis:
            for i in range(1, 8):
                new_x, new_y = self.x + i * dx, self.y + i * dy
                if not self.is_inside_board(new_x, new_y):
                    break
                if self.board.is_empty_at(new_x, new_y):
                    possible_moves.append((new_x, new_y))
                else:
                    if self.is_enemy_at(new_x, new_y):
                        possible_moves.append((new_x, new_y))
                    break
        return possible_moves

__all__ = ['Rook']
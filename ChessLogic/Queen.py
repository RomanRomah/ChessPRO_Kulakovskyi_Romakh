from .ChessPiece import ChessPiece

class Queen(ChessPiece):
    """Class for Queen piece"""
    text = ["♕", "♛"]
    char = 'Q'
    diagonals = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    axis = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def get_possible_moves(self):
        """Queen movement combines Rook and Bishop movements"""
        possible_moves = []
        for dx, dy in self.axis + self.diagonals:
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

__all__ = ['Queen']
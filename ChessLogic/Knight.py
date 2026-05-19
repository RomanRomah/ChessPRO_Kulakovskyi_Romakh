from .ChessPiece import ChessPiece

class Knight(ChessPiece):
    """Class for Knight piece"""
    text = ["♘", "♞"]
    char = 'N'
    L_jumps = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (-2, 1), (2, -1), (-2, -1)]

    def get_possible_moves(self):
        """Knight can move by jumping in an L-shape"""
        possible_moves = []
        for dx, dy in self.L_jumps:
            new_x, new_y = self.x + dx, self.y + dy
            if not self.is_inside_board(new_x, new_y):
                continue
            if self.board.is_empty_at(new_x, new_y) or self.is_enemy_at(new_x, new_y):
                possible_moves.append((new_x, new_y))
        return possible_moves

__all__ = ['Knight']
from .ChessPiece import ChessPiece

class Bishop(ChessPiece):
    """Class for Bishop piece"""
    text = ["♗", "♝"]
    char = 'B'
    diagonals = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    def get_possible_moves(self):
        """Bishop can move diagonally at any amount of cells without jumping"""
        possible_moves = []
        for dx, dy in self.diagonals:
            for i in range(1, 8):
                new_x, new_y = self.x + i * dx, self.y + i * dy
                if not self.is_inside_board(new_x, new_y):
                    break # New position must be inside chess board
                if self.board.is_empty_at(new_x, new_y):
                    possible_moves.append((new_x, new_y)) # If cell is empty, continue moving
                else:
                    if self.is_enemy_at(new_x, new_y):
                        possible_moves.append((new_x, new_y)) # If cell containing enemy, attack
                    break
        return possible_moves

__all__ = ['Bishop']
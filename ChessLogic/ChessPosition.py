import copy
from .Colors import Color


class GameState:
    """Зберігає інформацію про те, які клітинки знаходяться під атакою"""

    def __init__(self):
        self.white_attack = set()
        self.black_attack = set()
        self.white_king_under_attack = False
        self.black_king_under_attack = False


class CastlingState:
    """Зберігає права на рокіровку (чи рухався вже король або тури)"""

    def __init__(self):
        self.white_king_side = True
        self.white_queen_side = True
        self.black_king_side = True
        self.black_queen_side = True


class ChessPosition:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.en_passant = None
        self.castling_state = CastlingState()

    def is_empty_at(self, x, y):
        if 0 <= x < 8 and 0 <= y < 8:
            return self.board[y][x] is None
        return False

    def get_piece_at(self, x, y):
        if 0 <= x < 8 and 0 <= y < 8:
            return self.board[y][x]
        return None

    def place_piece(self, piece, x, y):
        if 0 <= x < 8 and 0 <= y < 8:
            self.board[y][x] = piece
            if piece:
                piece.set_position(x, y)

    def get_state(self):
        """Обчислює всі можливі атаки на дошці та перевіряє наявність шаху"""
        state = GameState()
        white_king_pos = None
        black_king_pos = None

        # Знаходимо королів та збираємо всі атаки
        for y in range(8):
            for x in range(8):
                piece = self.board[y][x]
                if piece:
                    if piece.char == 'K':
                        if piece.color == Color.WHITE:
                            white_king_pos = (x, y)
                        else:
                            black_king_pos = (x, y)

                    attacks = piece.get_attack_moves()
                    if piece.color == Color.WHITE:
                        state.white_attack.update(attacks)
                    else:
                        state.black_attack.update(attacks)

        # Перевіряємо чи є шах
        if white_king_pos in state.black_attack:
            state.white_king_under_attack = True
        if black_king_pos in state.white_attack:
            state.black_king_under_attack = True

        return state

    def generate_position_after_move(self, start_x, start_y, end_x, end_y):
        """Створює тимчасову дошку для перевірки легальності ходу"""
        new_pos = ChessPosition()
        new_pos.en_passant = self.en_passant
        new_pos.castling_state = copy.deepcopy(self.castling_state)

        # Копіюємо фігури на нову дошку
        for y in range(8):
            for x in range(8):
                p = self.board[y][x]
                if p:
                    new_p = p.copy(None, new_pos)
                    new_pos.place_piece(new_p, x, y)

        moving_piece = new_pos.get_piece_at(start_x, start_y)

        # ТУТ ДОДАНО: Правильно симулюємо зникнення пішака при взятті на проході
        if moving_piece and moving_piece.char == 'P' and start_x != end_x and new_pos.board[end_y][end_x] is None:
            new_pos.board[start_y][end_x] = None

        # Робимо симуляцію ходу
        new_pos.board[start_y][start_x] = None
        new_pos.place_piece(moving_piece, end_x, end_y)

        return new_pos


__all__ = ['ChessPosition', 'GameState', 'CastlingState']
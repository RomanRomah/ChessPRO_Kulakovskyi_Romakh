from .ChessPosition import ChessPosition
from .Colors import Color
from .Pieces import Pawn, Knight, Bishop, Rook, Queen, King


class ChessGame:
    def __init__(self):
        self.position = ChessPosition()
        self.current_turn = Color.WHITE
        self.move_history = []
        self.start_game()

    def start_game(self):
        self.position.board = [[None for _ in range(8)] for _ in range(8)]

        # Розстановка чорних
        self.position.place_piece(Rook(0, 0, Color.BLACK, self.position), 0, 0)
        self.position.place_piece(Knight(1, 0, Color.BLACK, self.position), 1, 0)
        self.position.place_piece(Bishop(2, 0, Color.BLACK, self.position), 2, 0)
        self.position.place_piece(Queen(3, 0, Color.BLACK, self.position), 3, 0)
        self.position.place_piece(King(4, 0, Color.BLACK, self.position), 4, 0)
        self.position.place_piece(Bishop(5, 0, Color.BLACK, self.position), 5, 0)
        self.position.place_piece(Knight(6, 0, Color.BLACK, self.position), 6, 0)
        self.position.place_piece(Rook(7, 0, Color.BLACK, self.position), 7, 0)
        for i in range(8):
            self.position.place_piece(Pawn(i, 1, Color.BLACK, self.position), i, 1)

        # Розстановка білих
        self.position.place_piece(Rook(0, 7, Color.WHITE, self.position), 0, 7)
        self.position.place_piece(Knight(1, 7, Color.WHITE, self.position), 1, 7)
        self.position.place_piece(Bishop(2, 7, Color.WHITE, self.position), 2, 7)
        self.position.place_piece(Queen(3, 7, Color.WHITE, self.position), 3, 7)
        self.position.place_piece(King(4, 7, Color.WHITE, self.position), 4, 7)
        self.position.place_piece(Bishop(5, 7, Color.WHITE, self.position), 5, 7)
        self.position.place_piece(Knight(6, 7, Color.WHITE, self.position), 6, 7)
        self.position.place_piece(Rook(7, 7, Color.WHITE, self.position), 7, 7)
        for i in range(8):
            self.position.place_piece(Pawn(i, 6, Color.WHITE, self.position), i, 6)

    def switch_turn(self):
        self.current_turn = self.current_turn.opposite()

    def check_game_over(self):
        """Перевіряє, чи закінчилась гра (Мат, Пат, Недостатньо фігур)"""
        has_valid_moves = False
        pieces_on_board = []

        # Шукаємо ходи та збираємо всі живі фігури
        for y in range(8):
            for x in range(8):
                piece = self.position.get_piece_at(x, y)
                if piece:
                    pieces_on_board.append(piece)
                    if piece.color == self.current_turn:
                        piece.calculate_valid_moves()
                        if len(piece.moves) > 0:
                            has_valid_moves = True

        # 1. Нічия: Недостатньо матеріалу для мату
        if len(pieces_on_board) == 2:  # Тільки два королі
            return "ПАТ! Недостатньо фігур"
        elif len(pieces_on_board) == 3:  # Королі + один Кінь або Слон
            for p in pieces_on_board:
                if p.char in ['B', 'N']:
                    return "ПАТ! Недостатньо фігур"

        # 2. Мат або класичний Пат
        if not has_valid_moves:
            state = self.position.get_state()
            if self.current_turn == Color.WHITE and state.white_king_under_attack:
                return "МАТ! Чорні перемогли"
            elif self.current_turn == Color.BLACK and state.black_king_under_attack:
                return "МАТ! Білі перемогли"
            else:
                return "ПАТ! Нічия"  # Класичний пат (немає ходів, але немає шаху)

        return None  # Гра триває
import random
from .Colors import Color


class ChessAI:
    # Базова цінність фігур
    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

    # Карти позиційної переваги (чим більше число, тим краще фігурі стояти в цій точці)
    # Для пішаків (бонус за просування вперед)
    pawn_pst = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ]

    # Для коней (бонус за перебування в центрі)
    knight_pst = [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20, 0, 0, 0, 0, -20, -40],
        [-30, 0, 10, 15, 15, 10, 0, -30],
        [-30, 5, 15, 20, 20, 15, 5, -30],
        [-30, 0, 15, 20, 20, 15, 0, -30],
        [-30, 5, 10, 15, 15, 10, 5, -30],
        [-40, -20, 0, 5, 5, 0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50]
    ]

    @staticmethod
    def get_all_moves(position, color):
        moves = []
        for y in range(8):
            for x in range(8):
                piece = position.get_piece_at(x, y)
                if piece and piece.color == color:
                    piece.calculate_valid_moves()
                    for m in piece.moves:
                        moves.append(((x, y), m))
        return moves

    @staticmethod
    def score_board(position):
        score = 0
        for y in range(8):
            for x in range(8):
                piece = position.get_piece_at(x, y)
                if piece:
                    # Базова ціна
                    val = ChessAI.piece_values.get(piece.char, 0)

                    # Позиційна ціна (тільки для пішаків і коней для швидкості)
                    pst_val = 0
                    if piece.char == 'P':
                        pst_val = ChessAI.pawn_pst[y if piece.color == Color.BLACK else 7 - y][x]
                    elif piece.char == 'N':
                        pst_val = ChessAI.knight_pst[y if piece.color == Color.BLACK else 7 - y][x]

                    val += pst_val

                    if piece.color == Color.WHITE:
                        score += val
                    else:
                        score -= val
        return score

    @staticmethod
    def minimax(position, depth, alpha, beta, is_maximizing):
        color = Color.WHITE if is_maximizing else Color.BLACK
        moves = ChessAI.get_all_moves(position, color)

        # Перевірка на кінець гри
        if not moves:
            state = position.get_state()
            if is_maximizing and state.white_king_under_attack: return -100000
            if not is_maximizing and state.black_king_under_attack: return 100000
            return 0

        if depth == 0:
            return ChessAI.score_board(position)

        if is_maximizing:
            max_eval = -float('inf')
            # Сортування ходів: спочатку ті, де ми щось їмо (для швидшого відсічення)
            moves.sort(key=lambda m: ChessAI.piece_values.get(
                position.get_piece_at(m[1][0], m[1][1]).char if position.get_piece_at(m[1][0], m[1][1]) else ' ', 0),
                       reverse=True)
            for move in moves:
                new_pos = position.generate_position_after_move(move[0][0], move[0][1], move[1][0], move[1][1])
                eval = ChessAI.minimax(new_pos, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            moves.sort(key=lambda m: ChessAI.piece_values.get(
                position.get_piece_at(m[1][0], m[1][1]).char if position.get_piece_at(m[1][0], m[1][1]) else ' ', 0),
                       reverse=True)
            for move in moves:
                new_pos = position.generate_position_after_move(move[0][0], move[0][1], move[1][0], move[1][1])
                eval = ChessAI.minimax(new_pos, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    @staticmethod
    def find_best_move(position, color, depth=2):
        best_move = None
        is_maximizing = (color == Color.WHITE)
        best_eval = -float('inf') if is_maximizing else float('inf')
        moves = ChessAI.get_all_moves(position, color)

        # Сортуємо для швидкості
        moves.sort(key=lambda m: ChessAI.piece_values.get(
            position.get_piece_at(m[1][0], m[1][1]).char if position.get_piece_at(m[1][0], m[1][1]) else ' ', 0),
                   reverse=True)

        alpha, beta = -float('inf'), float('inf')

        for move in moves:
            new_pos = position.generate_position_after_move(move[0][0], move[0][1], move[1][0], move[1][1])
            eval = ChessAI.minimax(new_pos, depth - 1, alpha, beta, not is_maximizing)

            if is_maximizing:
                if eval > best_eval: best_eval, best_move = eval, move
                alpha = max(alpha, eval)
            else:
                if eval < best_eval: best_eval, best_move = eval, move
                beta = min(beta, eval)
        return best_move

    # Залишаємо старі методи для сумісності з GUI
    @staticmethod
    def find_random_move(position, color):
        moves = ChessAI.get_all_moves(position, color)
        return random.choice(moves) if moves else None

    @staticmethod
    def find_greedy_move(position, color):
        best_move = None
        is_maximizing = (color == Color.WHITE)
        best_eval = -float('inf') if is_maximizing else float('inf')
        moves = ChessAI.get_all_moves(position, color)
        for move in moves:
            temp_pos = position.generate_position_after_move(move[0][0], move[0][1], move[1][0], move[1][1])
            eval = ChessAI.score_board(temp_pos)
            if is_maximizing:
                if eval > best_eval: best_eval, best_move = eval, move
            else:
                if eval < best_eval: best_eval, best_move = eval, move
        return best_move
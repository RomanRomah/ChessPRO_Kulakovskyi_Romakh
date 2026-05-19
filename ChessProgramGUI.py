import pygame
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

from ChessLogic.ChessGame import ChessGame
from ChessLogic.Colors import Color
from ChessLogic.Pieces import Queen, Rook, Bishop, Knight, Pawn, King
from ChessLogic.ChessAI import ChessAI
from SoundEffects import SoundEffects
from Database.DbManager import DbManager


class ChessProgramGUI:
    def __init__(self):
        pygame.init()

        self.db = DbManager()
        self.db.connect()

        self.board_size = 800
        self.panel_width = 350
        self.bottom_bar_height = 50
        self.width = self.board_size + self.panel_width
        self.height = self.board_size + self.bottom_bar_height
        self.square_size = self.board_size // 8

        self.screen_width = self.width
        self.screen_height = self.height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Chess Pro")

        self.internal_surface = pygame.Surface((self.width, self.height))
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.game = ChessGame()
        self.sounds = SoundEffects()
        self.clock = pygame.time.Clock()

        self.coord_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.panel_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.sidebar_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.user_font = pygame.font.SysFont("Arial", 19, bold=True)
        self.history_font = pygame.font.SysFont("Consolas", 16)
        self.timer_font = pygame.font.SysFont("Consolas", 32, bold=True)
        self.tag_font = pygame.font.SysFont("Arial", 11, bold=True)

        self.images = {}
        self.load_images()

        self.selected_piece = None
        self.valid_moves = []
        self.last_move = None
        self.game_over_message = None
        self.promotion_pending = None
        self.move_history_list = []
        self.game_saved = False

        self.player_color = Color.WHITE
        self.opponent_type = "HUMAN"
        self.time_control = None
        self.white_time = 0
        self.black_time = 0
        self.timer_started = False
        self.last_tick = pygame.time.get_ticks()

        self.ai_is_thinking = False
        self.ai_move_result = None
        self.is_fullscreen = False

        self.sidebar_open = False
        self.current_user = "Гість"
        self.user_id = None
        self.history_scroll = 0

        self.toast_text = None
        self.toast_color = (200, 50, 50)
        self.toast_timer = 0

    def load_images(self):
        pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
        for p in pieces:
            try:
                img = pygame.image.load(f"Sprites/{p}.png").convert_alpha()
                self.images[p] = pygame.transform.smoothscale(img, (self.square_size, self.square_size))
                if p == 'wP': pygame.display.set_icon(img)
            except:
                pass

    def trigger_toast(self, text, is_error=True):
        self.toast_text = text
        self.toast_color = (180, 40, 40) if is_error else (40, 150, 40)
        self.toast_timer = pygame.time.get_ticks() + 3000

    def draw_toast(self):
        if self.toast_text and pygame.time.get_ticks() < self.toast_timer:
            surf = self.panel_font.render(self.toast_text, True, (255, 255, 255))
            rect = surf.get_rect(center=(self.width // 2, 40))
            bg_rect = rect.inflate(40, 20)
            pygame.draw.rect(self.internal_surface, self.toast_color, bg_rect, border_radius=10)
            self.internal_surface.blit(surf, rect)

    def handle_save_state(self):
        if not self.user_id:
            self.trigger_toast("Спочатку увійдіть у профіль!")
            return
        if self.game_over_message:
            self.trigger_toast("Гра вже завершена!")
            return

        pieces_data = []
        for r in range(8):
            for c in range(8):
                p = self.game.position.get_piece_at(c, r)
                if p:
                    color_char = 'w' if p.color == Color.WHITE else 'b'
                    pieces_data.append(f"{color_char}{p.char},{c},{r}")

        turn_char = 'w' if self.game.current_turn == Color.WHITE else 'b'
        custom_fen = f"{turn_char}|" + ";".join(pieces_data)

        opp = self.opponent_type
        col = "White" if self.player_color == Color.WHITE else "Black"
        tc = self.time_control if self.time_control else 0
        moves_str = ",".join(self.move_history_list)

        if self.db.save_current_state(self.user_id, custom_fen, opp, col, tc, self.white_time, self.black_time,
                                      moves_str):
            self.trigger_toast("Гру збережено!", False)
            self.sidebar_open = False
        else:
            self.trigger_toast("Помилка збереження")

    def handle_load_state(self):
        if not self.user_id:
            self.trigger_toast("Спочатку увійдіть у профіль!")
            return

        data = self.db.load_saved_state(self.user_id)
        if not data:
            self.trigger_toast("Збережень не знайдено")
            return

        custom_fen, opp, col, tc, w_t, b_t, moves_str = data
        self.game = ChessGame()

        for r in range(8):
            for c in range(8):
                self.game.position.board[r][c] = None

        parts = custom_fen.split("|")
        self.game.current_turn = Color.WHITE if parts[0] == 'w' else Color.BLACK

        if len(parts) > 1 and parts[1]:
            piece_classes = {'P': Pawn, 'R': Rook, 'N': Knight, 'B': Bishop, 'Q': Queen, 'K': King}
            for p_str in parts[1].split(";"):
                p_code, pc, pr = p_str.split(",")
                p_color = Color.WHITE if p_code[0] == 'w' else Color.BLACK
                p_char = p_code[1]
                c, r = int(pc), int(pr)
                self.game.position.board[r][c] = piece_classes[p_char](c, r, p_color, self.game.position)

        self.opponent_type = opp
        self.player_color = Color.WHITE if col == "White" else Color.BLACK
        self.time_control = tc if tc > 0 else None
        self.white_time, self.black_time = w_t, b_t
        self.move_history_list = moves_str.split(",") if moves_str else []

        self.game_over_message = None
        self.game_saved = False
        self.timer_started = False
        self.sidebar_open = False
        self.trigger_toast("Гру відновлено!", False)

    def handle_registration(self):
        login_win = tk.Tk()
        login_win.title("Авторизація")
        login_win.configure(bg="#222222")

        main_frame = tk.Frame(login_win, bg="#222222", padx=30, pady=20)
        main_frame.pack()

        tk.Label(main_frame, text="ЛОГІН:", bg="#222222", fg="white", font=("Arial", 10, "bold")).pack(pady=(5, 2))
        e_u = tk.Entry(main_frame, justify="center", font=("Arial", 12))
        e_u.pack()

        tk.Label(main_frame, text="ПАРОЛЬ:", bg="#222222", fg="white", font=("Arial", 10, "bold")).pack(pady=(15, 2))
        e_p = tk.Entry(main_frame, show="*", justify="center", font=("Arial", 12))
        e_p.pack()

        res = {}

        def do_l():
            d = self.db.login_user(e_u.get().strip(), e_p.get().strip())
            if isinstance(d, dict):
                res['u'] = d;
                login_win.destroy()
            else:
                messagebox.showerror("Помилка", "Невірний логін або пароль", parent=login_win)

        def do_r():
            d = self.db.register_user(e_u.get().strip(), e_p.get().strip())
            if isinstance(d, dict):
                res['u'] = d;
                login_win.destroy()
            elif d == "USER_EXISTS":
                messagebox.showwarning("Увага", "Логін вже зайнятий", parent=login_win)
            else:
                messagebox.showerror("Помилка", "Помилка реєстрації", parent=login_win)

        btn_frame = tk.Frame(main_frame, bg="#222222")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="УВІЙТИ", bg="#3498db", fg="white", width=12, font=("Arial", 10, "bold"),
                  command=do_l).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="РЕЄСТРАЦІЯ", bg="#27ae60", fg="white", width=12, font=("Arial", 10, "bold"),
                  command=do_r).pack(side=tk.LEFT, padx=5)

        login_win.eval('tk::PlaceWindow . center')
        login_win.mainloop()

        if 'u' in res:
            self.user_id, self.current_user = res['u']['id'], res['u']['name']
            self.sidebar_open = False
            self.trigger_toast(f"Привіт, {self.current_user}!", False)

    def show_history(self):
        if not self.user_id: self.trigger_toast("Спочатку увійдіть у профіль!"); return
        win = tk.Tk()
        win.title("Історія матчів")
        win.configure(bg="#222222")

        frame = tk.Frame(win, bg="#222222", padx=20, pady=20)
        frame.pack()

        tk.Label(frame, text="Останні зіграні партії", font=("Arial", 14, "bold"), bg="#222222", fg="#3498db").pack(
            pady=(0, 10))

        listb = tk.Listbox(frame, font=("Consolas", 10), width=65, height=12, bg="#1e1e1e", fg="white",
                           selectbackground="#3498db")
        listb.pack()

        games_data = self.db.get_user_games(self.user_id)

        for g in games_data:
            date_str = g[3].strftime('%d.%m %H:%M')
            opp_str = "ЛЮДИНА" if g[0] == "HUMAN" else g[0]
            col_str = "Білі" if g[1] == "White" else "Чорні"
            res_short = g[2].split("!")[0] if "!" in g[2] else g[2]
            listb.insert(tk.END, f"[{date_str}] {col_str} vs {opp_str} | {res_short[:15]}")

        def on_double_click(event):
            selection = listb.curselection()
            if selection:
                self.show_game_details(games_data[selection[0]])

        listb.bind('<Double-1>', on_double_click)

        tk.Label(frame, text="* Двічі клікніть на партію, щоб переглянути деталі", font=("Arial", 9), bg="#222222",
                 fg="#aaaaaa").pack(pady=5)
        tk.Button(frame, text="ЗАКРИТИ", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                  command=win.destroy).pack(pady=10)

        win.eval('tk::PlaceWindow . center')
        win.mainloop()

    def show_game_details(self, game_data):
        opp, col, res, date, tc, moves_str = game_data
        det_win = tk.Toplevel()
        det_win.title("Деталі партії")
        det_win.configure(bg="#222222")
        det_win.geometry("350x450")

        tk.Label(det_win, text="🏆 РЕЗУЛЬТАТ:", bg="#222222", fg="#3498db", font=("Arial", 11, "bold")).pack(
            pady=(15, 0))
        tk.Label(det_win, text=res, bg="#222222", fg="white", font=("Arial", 10)).pack()

        tc_str = f"{tc // 60} хв" if tc and tc > 0 else "Безліміт"
        info_text = f"Супротивник: {opp}\nВаш колір: {'Білі' if col == 'White' else 'Чорні'}\nЧас: {tc_str}\nДата: {date.strftime('%d.%m.%Y %H:%M')}"
        tk.Label(det_win, text=info_text, bg="#222222", fg="#aaaaaa", font=("Arial", 10), justify="left").pack(pady=10)

        tk.Label(det_win, text="📜 ІСТОРІЯ ХОДІВ:", bg="#222222", fg="#27ae60", font=("Arial", 11, "bold")).pack(
            pady=(10, 0))

        moves_frame = tk.Frame(det_win, bg="#222222")
        moves_frame.pack(fill="both", expand=True, padx=20, pady=5)

        scrollbar = tk.Scrollbar(moves_frame)
        scrollbar.pack(side="right", fill="y")

        moves_text = tk.Text(moves_frame, bg="#1e1e1e", fg="white", font=("Consolas", 10), yscrollcommand=scrollbar.set,
                             width=30, height=8)
        moves_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=moves_text.yview)

        if moves_str:
            moves_list = moves_str.split(",")
            formatted_moves = ""
            for i in range(0, len(moves_list), 2):
                formatted_moves += f"{i // 2 + 1}. {moves_list[i]} "
                if i + 1 < len(moves_list):
                    formatted_moves += f"{moves_list[i + 1]}\n"
                else:
                    formatted_moves += "\n"
            moves_text.insert(tk.END, formatted_moves)
        else:
            moves_text.insert(tk.END, "Історія ходів відсутня.")

        moves_text.config(state="disabled")
        tk.Button(det_win, text="ОК", bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                  command=det_win.destroy).pack(pady=10)

        det_win.tk.eval(f'tk::PlaceWindow {det_win._w} center')

    def show_achievements(self):
        if not self.user_id: self.trigger_toast("Спочатку увійдіть у профіль!"); return
        win = tk.Tk()
        win.title("Відзнаки")
        win.configure(bg="#222222")

        frame = tk.Frame(win, bg="#222222", padx=20, pady=20)
        frame.pack()

        listb = tk.Listbox(frame, font=("Arial", 11), width=45, height=10, bg="#1e1e1e", fg="gold")
        listb.pack(pady=10)

        achs = self.db.get_user_achievements(self.user_id)
        if not achs:
            listb.insert(tk.END, "Відзнак поки немає. Грайте більше!")
        else:
            for a in achs: listb.insert(tk.END, f"★ {a[0]} ({a[1].strftime('%d.%m')})")

        tk.Button(frame, text="ЗАКРИТИ", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                  command=win.destroy).pack(pady=10)
        win.eval('tk::PlaceWindow . center')
        win.mainloop()

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            info = pygame.display.Info()
            self.screen_width, self.screen_height = info.current_w, info.current_h
        else:
            self.screen_width, self.screen_height = self.width, self.height
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

    def reset_game(self, color="KEEP", time_control="KEEP", opp_type="KEEP"):
        if color != "KEEP": self.player_color = color
        if opp_type != "KEEP": self.opponent_type = opp_type
        if time_control != "KEEP": self.time_control = time_control

        self.game = ChessGame();
        self.selected_piece = None;
        self.valid_moves = []
        self.last_move = None;
        self.game_over_message = None;
        self.promotion_pending = None
        self.move_history_list = [];
        self.game_saved = False;
        self.ai_is_thinking = False
        self.ai_move_result = None;
        self.history_scroll = 0

        if self.time_control is not None: self.white_time = self.black_time = self.time_control
        self.timer_started = False;
        self.last_tick = pygame.time.get_ticks()

    def format_time(self, seconds):
        if seconds <= 0: return "00:00"
        return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"

    def update_timers(self):
        current_tick = pygame.time.get_ticks()
        dt = (current_tick - self.last_tick) / 1000.0
        self.last_tick = current_tick

        if not self.timer_started or self.game_over_message or not self.time_control: return

        if self.game.current_turn == Color.WHITE:
            self.white_time -= dt
            if self.white_time <= 0: self.white_time = 0; self.game_over_message = "ЧАС ВИЙШОВ! Чорні перемогли"; self.play_snd(
                self.sounds.victory_sound)
        else:
            self.black_time -= dt
            if self.black_time <= 0: self.black_time = 0; self.game_over_message = "ЧАС ВИЙШОВ! Білі перемогли"; self.play_snd(
                self.sounds.victory_sound)

    def play_snd(self, snd):
        if snd: snd.play()

    def v_coord(self, c, r):
        return (7 - c, 7 - r) if self.player_color == Color.BLACK else (c, r)

    def l_coord(self, vc, vr):
        return (7 - vc, 7 - vr) if self.player_color == Color.BLACK else (vc, vr)

    def draw_icons(self, surface, type, x, y):
        if type == '5m':
            pygame.draw.polygon(surface, (255, 215, 0),
                                [(x - 3, y - 8), (x + 5, y - 8), (x + 1, y - 1), (x + 6, y - 1), (x - 4, y + 9),
                                 (x - 1, y + 1), (x - 6, y + 1)])
        elif type == '10m':
            pygame.draw.polygon(surface, (255, 255, 255),
                                [(x - 6, y - 8), (x + 6, y - 8), (x, y), (x + 6, y + 8), (x - 6, y + 8), (x, y)])
            pygame.draw.line(surface, (255, 255, 255), (x - 6, y - 8), (x + 6, y - 8), 2)
            pygame.draw.line(surface, (255, 255, 255), (x - 6, y + 8), (x + 6, y + 8), 2)
        elif type == 'inf':
            pygame.draw.circle(surface, (255, 255, 255), (x - 5, y), 5, 2)
            pygame.draw.circle(surface, (255, 255, 255), (x + 5, y), 5, 2)
        elif type == 'human':
            pygame.draw.circle(surface, (220, 220, 220), (x, y - 4), 5)
            pygame.draw.polygon(surface, (220, 220, 220),
                                [(x - 8, y + 7), (x + 8, y + 7), (x + 5, y + 2), (x - 5, y + 2)])
        elif type == 'bot':
            pygame.draw.rect(surface, (220, 220, 220), (x - 6, y - 3, 12, 10), border_radius=2)
            pygame.draw.line(surface, (220, 220, 220), (x - 4, y - 3), (x - 4, y - 7), 2)
            pygame.draw.line(surface, (220, 220, 220), (x + 4, y - 3), (x + 4, y - 7), 2)
            pygame.draw.circle(surface, (255, 100, 100), (x - 2, y + 1), 2)
            pygame.draw.circle(surface, (255, 100, 100), (x + 2, y + 1), 2)
        elif type == 'save':
            pygame.draw.rect(surface, (100, 200, 100), (x - 7, y - 7, 14, 14), border_radius=2)
            pygame.draw.rect(surface, (255, 255, 255), (x - 4, y - 7, 8, 5))
        elif type == 'load':
            pygame.draw.arc(surface, (100, 150, 255), (x - 7, y - 7, 14, 14), 0, 4.7, 2)
            pygame.draw.polygon(surface, (100, 150, 255), [(x + 3, y - 3), (x + 8, y + 1), (x + 3, y + 3)])
        elif type == 'key':
            pygame.draw.circle(surface, (220, 220, 220), (x - 5, y), 4, 2)
            pygame.draw.line(surface, (220, 220, 220), (x - 1, y), (x + 7, y), 2)
            pygame.draw.line(surface, (220, 220, 220), (x + 4, y), (x + 4, y + 3), 2)
            pygame.draw.line(surface, (220, 220, 220), (x + 7, y), (x + 7, y + 3), 2)
        elif type == 'hist':
            pygame.draw.rect(surface, (220, 220, 220), (x - 6, y - 7, 12, 14), 2, border_radius=2)
            pygame.draw.line(surface, (220, 220, 220), (x - 3, y - 3), (x + 3, y - 3), 2)
            pygame.draw.line(surface, (220, 220, 220), (x - 3, y + 1), (x + 3, y + 1), 2)
            pygame.draw.line(surface, (220, 220, 220), (x - 3, y + 5), (x, y + 5), 2)
        elif type == 'star':
            pts = [(x, y - 7), (x + 2, y - 2), (x + 7, y - 2), (x + 3, y + 1), (x + 5, y + 6), (x, y + 3),
                   (x - 5, y + 6), (x - 3, y + 1), (x - 7, y - 2), (x - 2, y - 2)]
            pygame.draw.polygon(surface, (255, 215, 0), pts)

    def draw_bottom_bar(self):
        pygame.draw.rect(self.internal_surface, (20, 20, 20),
                         pygame.Rect(0, self.board_size, self.width, self.bottom_bar_height))
        pygame.draw.line(self.internal_surface, (60, 60, 60), (0, self.board_size), (self.width, self.board_size), 2)

        self.draw_icons(self.internal_surface, 'human', 30, self.board_size + 25)
        status = "" if self.user_id else " (Гість)"
        text_surf = self.user_font.render(f"ПРОФІЛЬ: {self.current_user}{status}", True, (200, 200, 200))
        self.internal_surface.blit(text_surf, (45, self.board_size + 14))

    def draw_ui_panel(self):
        pygame.draw.rect(self.internal_surface, (35, 35, 35),
                         pygame.Rect(self.board_size, 0, self.panel_width, self.board_size))

        self.btn_menu = pygame.Rect(self.width - 45, 15, 30, 25)
        for i in range(3): pygame.draw.line(self.internal_surface, (200, 200, 200),
                                            (self.btn_menu.x, self.btn_menu.y + i * 10),
                                            (self.btn_menu.right, self.btn_menu.y + i * 10), 3)

        self.internal_surface.blit(self.panel_font.render("ЧАС:", True, (170, 170, 170)),
                                   (self.board_size + 20, 45 + 30))
        self.btn_5m = pygame.Rect(self.board_size + 20, 70 + 30, 100, 35)
        self.btn_10m = pygame.Rect(self.board_size + 125, 70 + 30, 100, 35)
        self.btn_inf = pygame.Rect(self.board_size + 230, 70 + 30, 100, 35)

        pygame.draw.rect(self.internal_surface, (80, 140, 80) if self.time_control == 300 else (60, 60, 60),
                         self.btn_5m, border_radius=5)
        pygame.draw.rect(self.internal_surface, (80, 140, 80) if self.time_control == 600 else (60, 60, 60),
                         self.btn_10m, border_radius=5)
        pygame.draw.rect(self.internal_surface, (80, 140, 80) if self.time_control is None else (60, 60, 60),
                         self.btn_inf, border_radius=5)

        self.draw_icons(self.internal_surface, '5m', self.btn_5m.centerx, self.btn_5m.centery)
        self.draw_icons(self.internal_surface, '10m', self.btn_10m.centerx, self.btn_10m.centery)
        self.draw_icons(self.internal_surface, 'inf', self.btn_inf.centerx, self.btn_inf.centery)

        pygame.draw.line(self.internal_surface, (60, 60, 60), (self.board_size + 20, 115 + 30),
                         (self.width - 20, 115 + 30), 2)
        self.internal_surface.blit(self.panel_font.render("СУПРОТИВНИК:", True, (170, 170, 170)),
                                   (self.board_size + 20, 125 + 30))

        self.btn_h = pygame.Rect(self.board_size + 20, 150 + 30, 150, 45)
        self.btn_b1 = pygame.Rect(self.board_size + 180, 150 + 30, 150, 45)
        self.btn_b2 = pygame.Rect(self.board_size + 20, 205 + 30, 150, 45)
        self.btn_b3 = pygame.Rect(self.board_size + 180, 205 + 30, 150, 45)

        pygame.draw.rect(self.internal_surface, (60, 120, 180) if self.opponent_type == "HUMAN" else (40, 80, 120),
                         self.btn_h, border_radius=5)
        pygame.draw.rect(self.internal_surface, (80, 180, 80) if self.opponent_type == "BOT1" else (50, 120, 50),
                         self.btn_b1, border_radius=5)
        pygame.draw.rect(self.internal_surface, (220, 130, 40) if self.opponent_type == "BOT2" else (160, 80, 20),
                         self.btn_b2, border_radius=5)
        pygame.draw.rect(self.internal_surface, (200, 40, 40) if self.opponent_type == "BOT3" else (120, 20, 20),
                         self.btn_b3, border_radius=5)

        surf_h = self.panel_font.render("ЛЮДИНА", True, (255, 255, 255))
        surf_b1 = self.panel_font.render("БОТ 1", True, (255, 255, 255))
        surf_b2 = self.panel_font.render("БОТ 2", True, (255, 255, 255))
        surf_b3 = self.panel_font.render("БОТ 3", True, (255, 255, 255))

        for btn, txt, icon in [(self.btn_h, surf_h, 'human'), (self.btn_b1, surf_b1, 'bot'),
                               (self.btn_b2, surf_b2, 'bot'), (self.btn_b3, surf_b3, 'bot')]:
            self.draw_icons(self.internal_surface, icon, btn.x + 35, btn.centery)
            self.internal_surface.blit(txt, (btn.x + 55, btn.centery - 8))

        pygame.draw.line(self.internal_surface, (60, 60, 60), (self.board_size + 20, 265 + 30),
                         (self.width - 20, 265 + 30), 2)

        self.btn_w = pygame.Rect(self.board_size + 20, 280 + 30, 150, 40)
        self.btn_b = pygame.Rect(self.board_size + 180, 280 + 30, 150, 40)
        pygame.draw.rect(self.internal_surface,
                         (240, 240, 240) if self.player_color == Color.WHITE else (100, 100, 100), self.btn_w,
                         border_radius=5)
        pygame.draw.rect(self.internal_surface, (20, 20, 20) if self.player_color == Color.BLACK else (100, 100, 100),
                         self.btn_b, border_radius=5)
        surf_w = self.panel_font.render("БІЛІ", True,
                                        (0, 0, 0) if self.player_color == Color.WHITE else (200, 200, 200))
        self.internal_surface.blit(surf_w, surf_w.get_rect(center=self.btn_w.center))
        surf_b_txt = self.panel_font.render("ЧОРНІ", True, (255, 255, 255))
        self.internal_surface.blit(surf_b_txt, surf_b_txt.get_rect(center=self.btn_b.center))

        self.btn_resign = pygame.Rect(self.board_size + 20, 330 + 30, 150, 40)
        self.btn_res = pygame.Rect(self.board_size + 180, 330 + 30, 150, 40)

        is_game_active = not self.game_over_message and len(self.move_history_list) > 0
        pygame.draw.rect(self.internal_surface, (120, 120, 120) if is_game_active else (60, 60, 60), self.btn_resign,
                         border_radius=5)
        resign_txt = self.panel_font.render("ЗДАТИСЯ", True, (255, 255, 255) if is_game_active else (150, 150, 150))
        self.internal_surface.blit(resign_txt, resign_txt.get_rect(center=self.btn_resign.center))

        pygame.draw.rect(self.internal_surface, (200, 50, 50), self.btn_res, border_radius=5)
        res_txt = self.panel_font.render("НОВА ГРА", True, (255, 255, 255))
        self.internal_surface.blit(res_txt, res_txt.get_rect(center=self.btn_res.center))

        hist_y = 455 + 30 if self.time_control else 395 + 30
        if self.time_control:
            pygame.draw.line(self.internal_surface, (60, 60, 60), (self.board_size + 20, 385 + 30),
                             (self.width - 20, 385 + 30), 2)
            pygame.draw.rect(self.internal_surface, (45, 45, 45), pygame.Rect(self.board_size + 20, 395 + 30, 150, 45),
                             border_radius=6)
            b_t = self.timer_font.render(self.format_time(self.black_time), True, (240, 240, 240))
            self.internal_surface.blit(b_t, b_t.get_rect(center=(self.board_size + 95, 417 + 30)))

            pygame.draw.rect(self.internal_surface, (240, 240, 240),
                             pygame.Rect(self.board_size + 180, 395 + 30, 150, 45), border_radius=6)
            w_t = self.timer_font.render(self.format_time(self.white_time), True, (20, 20, 20))
            self.internal_surface.blit(w_t, w_t.get_rect(center=(self.board_size + 255, 417 + 30)))

        pygame.draw.line(self.internal_surface, (60, 60, 60), (self.board_size + 20, hist_y - 15),
                         (self.width - 20, hist_y - 15), 2)
        self.internal_surface.blit(self.panel_font.render("ІСТОРІЯ ХОДІВ", True, (170, 170, 170)),
                                   (self.board_size + 20, hist_y))

        total_height = ((len(self.move_history_list) + 1) // 2) * 25
        visible_height = self.board_size - (hist_y + 30)
        max_scroll = max(0, total_height - visible_height)

        if self.history_scroll > max_scroll: self.history_scroll = max_scroll
        if self.history_scroll < 0: self.history_scroll = 0

        self.internal_surface.set_clip(
            pygame.Rect(self.board_size, hist_y + 25, self.panel_width, self.board_size - (hist_y + 25)))

        y_offset = hist_y + 30 - self.history_scroll
        for i in range(0, len(self.move_history_list), 2):
            if y_offset + 25 > hist_y + 25 and y_offset < self.board_size:
                txt = f"{i // 2 + 1}. {self.move_history_list[i]}"
                if i + 1 < len(self.move_history_list): txt += f"  {self.move_history_list[i + 1]}"
                self.internal_surface.blit(self.history_font.render(txt, True, (200, 200, 200)),
                                           (self.board_size + 25, y_offset))
            y_offset += 25

        self.internal_surface.set_clip(None)

    def draw_sidebar(self):
        if not self.sidebar_open: return
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.internal_surface.blit(overlay, (0, 0))

        self.sidebar_rect = pygame.Rect(self.width - 300, 0, 300, self.height)
        pygame.draw.rect(self.internal_surface, (25, 25, 25), self.sidebar_rect)

        self.btn_login = pygame.Rect(self.width - 280, 80, 260, 45)
        self.btn_save = pygame.Rect(self.width - 280, 140, 260, 45)
        self.btn_load = pygame.Rect(self.width - 280, 200, 260, 45)
        self.btn_hist = pygame.Rect(self.width - 280, 260, 260, 45)
        self.btn_achs = pygame.Rect(self.width - 280, 320, 260, 45)
        self.btn_close = pygame.Rect(self.width - 40, 10, 30, 30)

        for btn, col, txt, icon in [
            (self.btn_login, (50, 50, 50), "УВІЙТИ / РЕЄСТРАЦІЯ", 'key'),
            (self.btn_save, (60, 120, 60), "ЗБЕРЕГТИ ГРУ", 'save'),
            (self.btn_load, (60, 80, 150), "ПРОДОВЖИТИ ГРУ", 'load'),
            (self.btn_hist, (50, 50, 50), "ІСТОРІЯ МАТЧІВ", 'hist'),
            (self.btn_achs, (50, 50, 50), "ВІДЗНАКИ", 'star')
        ]:
            pygame.draw.rect(self.internal_surface, col, btn, border_radius=5)
            self.internal_surface.blit(self.sidebar_font.render(txt, True, (255, 255, 255)), (btn.x + 45, btn.y + 12))
            if icon: self.draw_icons(self.internal_surface, icon, btn.x + 22, btn.centery)

        pygame.draw.line(self.internal_surface, (200, 50, 50), (self.btn_close.x, 10), (self.btn_close.right, 40), 3)
        pygame.draw.line(self.internal_surface, (200, 50, 50), (self.btn_close.right, 10), (self.btn_close.x, 40), 3)

    def draw_board(self):
        colors = [(235, 235, 210), (120, 150, 85)]
        for r in range(8):
            for c in range(8):
                pygame.draw.rect(self.internal_surface, colors[(r + c) % 2],
                                 pygame.Rect(c * self.square_size, r * self.square_size, self.square_size,
                                             self.square_size))

        if self.last_move:
            s = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            s.fill((255, 255, 51, 150))
            for pos in self.last_move:
                vc, vr = self.v_coord(pos[0], pos[1])
                self.internal_surface.blit(s, (vc * self.square_size, vr * self.square_size))

    def draw_coordinates(self):
        letters = ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a'] if self.player_color == Color.BLACK else ['a', 'b', 'c', 'd',
                                                                                                     'e', 'f', 'g', 'h']
        light_c, dark_c = (238, 238, 210), (118, 150, 86)

        for i in range(8):
            num_color = dark_c if i % 2 == 0 else light_c
            num_str = str(i + 1) if self.player_color == Color.BLACK else str(8 - i)
            self.internal_surface.blit(self.coord_font.render(num_str, True, num_color), (5, i * self.square_size + 2))

            let_color = dark_c if (7 + i) % 2 == 0 else light_c
            self.internal_surface.blit(self.coord_font.render(letters[i], True, let_color),
                                       ((i + 1) * self.square_size - 18, 8 * self.square_size - 25))

    def draw_highlights(self):
        state = self.game.position.get_state()
        king_pos, curr_col = None, self.game.current_turn

        if not self.game_over_message and ((curr_col == Color.WHITE and state.white_king_under_attack) or (
                curr_col == Color.BLACK and state.black_king_under_attack)):
            for y in range(8):
                for x in range(8):
                    p = self.game.position.get_piece_at(x, y)
                    if p and p.char == 'K' and p.color == curr_col: king_pos = (x, y)
        if king_pos:
            vk_c, vk_r = self.v_coord(king_pos[0], king_pos[1])
            s = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 0, 0, 160), (self.square_size // 2, self.square_size // 2),
                               self.square_size // 2)
            self.internal_surface.blit(s, (vk_c * self.square_size, vk_r * self.square_size))

        if self.selected_piece and not self.game_over_message and not self.promotion_pending:
            vs_c, vs_r = self.v_coord(self.selected_piece.x, self.selected_piece.y)
            s = pygame.Surface((self.square_size, self.square_size))
            s.set_alpha(100);
            s.fill((255, 255, 100))
            self.internal_surface.blit(s, (vs_c * self.square_size, vs_r * self.square_size))

            for m in self.valid_moves:
                vm_c, vm_r = self.v_coord(m[0], m[1])
                circle_surf = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                is_cap = self.game.position.get_piece_at(m[0], m[1]) or (
                        self.selected_piece.char == 'P' and m[0] != self.selected_piece.x)
                if is_cap:
                    pygame.draw.circle(circle_surf, (0, 0, 0, 40), (self.square_size // 2, self.square_size // 2),
                                       self.square_size // 2 - 5, 8)
                else:
                    pygame.draw.circle(circle_surf, (0, 0, 0, 40), (self.square_size // 2, self.square_size // 2),
                                       self.square_size // 6)
                self.internal_surface.blit(circle_surf, (vm_c * self.square_size, vm_r * self.square_size))

    def draw_pieces(self):
        for r in range(8):
            for c in range(8):
                p = self.game.position.get_piece_at(c, r)
                if p:
                    code = ('w' if p.color == Color.WHITE else 'b') + p.char
                    if code in self.images:
                        vc, vr = self.v_coord(c, r)
                        self.internal_surface.blit(self.images[code], (vc * self.square_size, vr * self.square_size))

    def draw_game_over_tags(self):
        if not self.game_over_message: return
        is_draw = "ПАТ" in self.game_over_message.upper() or "НІЧИЯ" in self.game_over_message.upper()
        is_resign = "здалися" in self.game_over_message.lower()
        w_col, l_col, r_txt = None, None, "МАТ"

        if not is_draw:
            if "Білі перемогли" in self.game_over_message:
                w_col, l_col, r_txt = Color.WHITE, Color.BLACK, "ЗДАВСЯ" if is_resign else (
                    "ЧАС" if "ЧАС" in self.game_over_message else "МАТ")
            elif "Чорні перемогли" in self.game_over_message:
                w_col, l_col, r_txt = Color.BLACK, Color.WHITE, "ЗДАВСЯ" if is_resign else (
                    "ЧАС" if "ЧАС" in self.game_over_message else "МАТ")

        for y in range(8):
            for x in range(8):
                p = self.game.position.get_piece_at(x, y)
                if p and p.char == 'K':
                    vx, vy = self.v_coord(x, y)
                    tag_y = vy * self.square_size + self.square_size - 24
                    c_x = vx * self.square_size + self.square_size // 2

                    if is_draw:
                        txt = self.tag_font.render("НІЧИЯ", True, (255, 255, 255))
                        bg_w = txt.get_width() + 25
                        pygame.draw.rect(self.internal_surface, (139, 69, 19), (c_x - bg_w // 2, tag_y, bg_w, 22),
                                         border_radius=4)
                        self.internal_surface.blit(txt, (c_x - bg_w // 2 + 6, tag_y + 3))
                        self.draw_little_crown(self.internal_surface, c_x - bg_w // 2 + bg_w - 16, tag_y + 5, 12, 10, 2)
                    else:
                        if p.color == w_col:
                            txt = self.tag_font.render("ПЕРЕМОЖЕЦЬ", True, (255, 255, 255))
                            bg_w = txt.get_width() + 25
                            pygame.draw.rect(self.internal_surface, (60, 160, 60), (c_x - bg_w // 2, tag_y, bg_w, 22),
                                             border_radius=4)
                            self.internal_surface.blit(txt, (c_x - bg_w // 2 + 6, tag_y + 3))
                            self.draw_little_crown(self.internal_surface, c_x - bg_w // 2 + bg_w - 16, tag_y + 5, 12,
                                                   10, 0)
                        elif p.color == l_col:
                            txt = self.tag_font.render(r_txt, True, (255, 255, 255))
                            bg_w = txt.get_width() + 25
                            pygame.draw.rect(self.internal_surface, (200, 50, 50), (c_x - bg_w // 2, tag_y, bg_w, 22),
                                             border_radius=4)
                            self.internal_surface.blit(txt, (c_x - bg_w // 2 + 6, tag_y + 3))
                            self.draw_little_crown(self.internal_surface, c_x - bg_w // 2 + bg_w - 16, tag_y + 5, 12,
                                                   10, 1)

    def draw_little_crown(self, s, x, y, w, h, state=0):
        if state == 0:
            pts = [(x, y + h), (x + w, y + h), (x + w, y), (x + w * .7, y + h * .5), (x + w * .5, y),
                   (x + w * .3, y + h * .5), (x, y)]
        elif state == 1:
            pts = [(x, y), (x + w, y), (x + w, y + h), (x + w * .7, y + h * .5), (x + w * .5, y + h),
                   (x + w * .3, y + h * .5), (x, y + h)]
        elif state == 2:
            pts = [(x, y), (x, y + h), (x + w, y + h), (x + w * .5, y + h * .7), (x + w, y + h * .5),
                   (x + w * .5, y + h * .3), (x + w, y)]
        pygame.draw.polygon(s, (255, 255, 255), pts)

    def draw_promotion_menu(self):
        if self.promotion_pending:
            o = pygame.Surface((self.board_size, self.board_size), pygame.SRCALPHA);
            o.fill((0, 0, 0, 180));
            self.internal_surface.blit(o, (0, 0))
            m = pygame.Rect(self.board_size // 2 - 200, self.height // 2 - 70, 400, 140);
            pygame.draw.rect(self.internal_surface, (245, 245, 245), m, border_radius=15)
            c = 'w' if self.promotion_pending[2] == Color.WHITE else 'b'
            for i, p in enumerate(['Q', 'R', 'B', 'N']):
                self.internal_surface.blit(pygame.transform.smoothscale(self.images[c + p], (90, 90)),
                                           (m.x + i * 100 + 5, m.y + 25))

    def get_notation(self, p, c, r):
        return f"{p.char if p.char != 'P' else ''}{chr(97 + c)}{8 - r}"

    def select_piece(self, col, row):
        p = self.game.position.get_piece_at(col, row)
        if p and p.color == self.game.current_turn:
            self.selected_piece = p;
            p.calculate_valid_moves();
            self.valid_moves = p.moves
        else:
            self.selected_piece = None;
            self.valid_moves = []

    def execute_move(self, old_x, old_y, col, row):
        piece = self.game.position.get_piece_at(old_x, old_y)
        char, color = piece.char, piece.color

        self.move_history_list.append(self.get_notation(piece, col, row))
        self.history_scroll = 999999

        if char == 'P' and col != old_x and self.game.position.is_empty_at(col, row): self.game.position.board[old_y][
            col] = None
        if char == 'K' and abs(col - old_x) == 2:
            r_col, t_col = (7, 5) if col == 6 else (0, 3)
            rook = self.game.position.get_piece_at(r_col, row)
            self.game.position.board[row][r_col] = None
            if rook: self.game.position.place_piece(rook, t_col, row)

        self.last_move = ((old_x, old_y), (col, row))
        self.game.position.board[old_y][old_x] = None
        self.game.position.place_piece(piece, col, row)

        if char == 'K':
            if color == Color.WHITE:
                self.game.position.castling_state.white_king_side = self.game.position.castling_state.white_queen_side = False
            else:
                self.game.position.castling_state.black_king_side = self.game.position.castling_state.black_queen_side = False
        elif char == 'R':
            if old_x == 0 and old_y == 7:
                self.game.position.castling_state.white_queen_side = False
            elif old_x == 7 and old_y == 7:
                self.game.position.castling_state.white_king_side = False
            elif old_x == 0 and old_y == 0:
                self.game.position.castling_state.black_queen_side = False
            elif old_x == 7 and old_y == 0:
                self.game.position.castling_state.black_king_side = False

        self.game.position.en_passant = (col, (row + old_y) // 2) if char == 'P' and abs(row - old_y) == 2 else None
        if self.sounds.move_sound: self.sounds.move_sound.play()

        if char == 'P' and (row == 0 or row == 7):
            if self.opponent_type != "HUMAN" and color != self.player_color:
                self.game.position.board[row][col] = Queen(col, row, color, self.game.position)
                self.finish_turn()
            else:
                self.promotion_pending = (col, row, color)
        else:
            self.finish_turn()

    def calculate_ai_move_bg(self):
        time.sleep(0.2)
        if self.opponent_type == "BOT1":
            move = ChessAI.find_random_move(self.game.position, self.game.current_turn)
        elif self.opponent_type == "BOT2":
            move = ChessAI.find_greedy_move(self.game.position, self.game.current_turn)
        else:
            move = ChessAI.find_best_move(self.game.position, self.game.current_turn, depth=2)
        self.ai_move_result = move

    def finish_turn(self):
        self.game.switch_turn()
        self.selected_piece = None
        self.valid_moves = []
        if not self.timer_started: self.timer_started = True
        self.game_over_message = self.game.check_game_over()
        if self.game_over_message and "МАТ" in self.game_over_message:
            if self.sounds.victory_sound: self.sounds.victory_sound.play()

    def handle_click(self, x, y):
        if self.sidebar_open:
            if self.btn_close.collidepoint(x, y):
                self.sidebar_open = False
            elif self.btn_login.collidepoint(x, y):
                self.handle_registration()
            elif self.btn_save.collidepoint(x, y):
                self.handle_save_state()
            elif self.btn_load.collidepoint(x, y):
                self.handle_load_state()
            elif self.btn_hist.collidepoint(x, y):
                if self.user_id:
                    self.show_history()
                else:
                    self.trigger_toast("⚠️ Спочатку увійдіть або зареєструйтесь!")
            elif self.btn_achs.collidepoint(x, y):
                if self.user_id:
                    self.show_achievements()
                else:
                    self.trigger_toast("⚠️ Спочатку увійдіть або зареєструйтесь!")
            return

        if self.ai_is_thinking and y < self.board_size: return
        if hasattr(self, 'btn_menu') and self.btn_menu.collidepoint(x, y): self.sidebar_open = True; return
        if y >= self.board_size: return

        if x >= self.board_size:
            if self.btn_5m.collidepoint(x, y):
                self.reset_game(self.player_color, 300, "KEEP")
            elif self.btn_10m.collidepoint(x, y):
                self.reset_game(self.player_color, 600, "KEEP")
            elif self.btn_inf.collidepoint(x, y):
                self.reset_game(self.player_color, None, "KEEP")
            elif self.btn_h.collidepoint(x, y):
                self.reset_game(self.player_color, "KEEP", "HUMAN")
            elif self.btn_b1.collidepoint(x, y):
                self.reset_game(self.player_color, "KEEP", "BOT1")
            elif self.btn_b2.collidepoint(x, y):
                self.reset_game(self.player_color, "KEEP", "BOT2")
            elif self.btn_b3.collidepoint(x, y):
                self.reset_game(self.player_color, "KEEP", "BOT3")
            elif self.btn_w.collidepoint(x, y):
                self.reset_game(Color.WHITE, "KEEP", "KEEP")
            elif self.btn_b.collidepoint(x, y):
                self.reset_game(Color.BLACK, "KEEP", "KEEP")
            elif self.btn_res.collidepoint(x, y):
                self.reset_game(self.player_color, "KEEP", "KEEP")
            elif hasattr(self, 'btn_resign') and self.btn_resign.collidepoint(x, y):
                if not self.game_over_message and len(self.move_history_list) > 0:
                    loser = self.player_color
                    winner = Color.BLACK if loser == Color.WHITE else Color.WHITE
                    self.game_over_message = f"{'Білі' if loser == Color.WHITE else 'Чорні'} здалися! {'Білі' if winner == Color.WHITE else 'Чорні'} перемогли"
                    if self.sounds.victory_sound: self.sounds.victory_sound.play()
            return

        if self.game_over_message or self.promotion_pending: return
        if self.opponent_type != "HUMAN" and self.game.current_turn != self.player_color: return

        v_col, v_row = x // self.square_size, y // self.square_size
        col, row = self.l_coord(v_col, v_row)

        if self.selected_piece and (col, row) in self.valid_moves:
            self.execute_move(self.selected_piece.x, self.selected_piece.y, col, row)
        else:
            self.select_piece(col, row)

    def run(self):
        while True:
            self.update_timers()

            if self.game_over_message and not getattr(self, 'game_saved', False):
                self.game_saved = True
                if self.user_id:
                    color_str = "White" if self.player_color == Color.WHITE else "Black"
                    tc = self.time_control if self.time_control else 0

                    moves_str = ",".join(self.move_history_list)

                    self.db.save_game(self.user_id, self.opponent_type, color_str, tc, self.game_over_message,
                                      moves_str)
                    self.db.delete_saved_state(self.user_id)
                    self.db.add_achievement(self.user_id, "Перший бій (Зіграно партію)")

                    if "перемогли" in self.game_over_message:
                        is_white_win = "Білі перемогли" in self.game_over_message
                        user_won = (is_white_win and self.player_color == Color.WHITE) or (
                                not is_white_win and self.player_color == Color.BLACK)

                        if user_won:
                            self.db.add_achievement(self.user_id, "Смак перемоги (Перша перемога)")
                            if "BOT" in self.opponent_type: self.db.add_achievement(self.user_id,
                                                                                    "Кібер-воїн (Перемога над ботом)")
                            if "ЧАС" in self.game_over_message: self.db.add_achievement(self.user_id,
                                                                                        "Майстер часу (Перемога по часу)")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                    self.screen_width, self.screen_height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.type == pygame.MOUSEWHEEL:
                    mx, my = pygame.mouse.get_pos()
                    vx = int((mx - self.offset_x) / self.scale_factor)
                    if vx > self.board_size: self.history_scroll -= event.y * 30
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    vx = int((mx - self.offset_x) / self.scale_factor)
                    vy = int((my - self.offset_y) / self.scale_factor)

                    if 0 <= vx <= self.width and 0 <= vy <= self.height:
                        if self.promotion_pending:
                            s_x, s_y = self.board_size // 2 - 200, self.height // 2 - 70
                            if pygame.Rect(s_x, s_y, 400, 140).collidepoint(vx, vy):
                                c, r, clr = self.promotion_pending
                                self.game.position.board[r][c] = [Queen, Rook, Bishop, Knight][(vx - s_x) // 100](c, r,
                                                                                                                  clr,
                                                                                                                  self.game.position)
                                self.promotion_pending = None;
                                self.finish_turn()
                        else:
                            self.handle_click(vx, vy)

            if self.opponent_type != "HUMAN" and self.game.current_turn != self.player_color and not self.game_over_message and not self.promotion_pending:
                if not self.ai_is_thinking:
                    self.ai_is_thinking = True;
                    threading.Thread(target=self.calculate_ai_move_bg, daemon=True).start()

            if self.ai_move_result is not None:
                move = self.ai_move_result;
                self.ai_move_result = None;
                self.ai_is_thinking = False
                if move: self.execute_move(move[0][0], move[0][1], move[1][0], move[1][1])

            self.internal_surface.fill((25, 25, 25))
            self.draw_board()
            self.draw_coordinates()
            self.draw_highlights()
            self.draw_pieces()
            self.draw_ui_panel()
            self.draw_bottom_bar()
            self.draw_promotion_menu()
            self.draw_game_over_tags()
            self.draw_sidebar()
            self.draw_toast()

            scale_x = self.screen_width / self.width
            scale_y = self.screen_height / self.height
            self.scale_factor = min(scale_x, scale_y)
            new_w = int(self.width * self.scale_factor)
            new_h = int(self.height * self.scale_factor)

            scaled_surf = pygame.transform.smoothscale(self.internal_surface, (new_w, new_h))
            self.screen.fill((0, 0, 0))
            self.offset_x = (self.screen_width - new_w) // 2
            self.offset_y = (self.screen_height - new_h) // 2
            self.screen.blit(scaled_surf, (self.offset_x, self.offset_y))

            pygame.display.flip()
            self.clock.tick(60)


__all__ = ['ChessProgramGUI']
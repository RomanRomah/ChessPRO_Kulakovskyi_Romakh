import psycopg2
from psycopg2 import errors
import hashlib


class DbManager:
    def __init__(self, db_name="chess", user="postgres", password="ro040798ha", host="127.0.0.1", port="5432"):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.db_name, user=self.user, password=self.password, host=self.host, port=self.port
            )
            self.cursor = self.conn.cursor()
            print("✅ DATABASE: CONNECTED")
            self.create_tables()
            return True
        except Exception as e:
            print(f"❌ DATABASE: CONNECTION ERROR {e}")
            return False

    def create_tables(self):
        try:
            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS Users
                                (
                                    user_id
                                    SERIAL
                                    PRIMARY
                                    KEY,
                                    username
                                    VARCHAR
                                (
                                    50
                                ) UNIQUE NOT NULL,
                                    password_hash VARCHAR
                                (
                                    256
                                ) NOT NULL, registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                ''')

            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS Games
                                (
                                    game_id
                                    SERIAL
                                    PRIMARY
                                    KEY,
                                    user_id
                                    INT
                                    REFERENCES
                                    Users
                                (
                                    user_id
                                ) ON DELETE CASCADE,
                                    opponent_type VARCHAR
                                (
                                    50
                                ), player_color VARCHAR
                                (
                                    10
                                ),
                                    time_control INT, result VARCHAR
                                (
                                    100
                                ), moves_history TEXT,
                                    game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                ''')
            try:
                self.cursor.execute("ALTER TABLE Games ADD COLUMN moves_history TEXT")
                self.conn.commit()
            except:
                self.conn.rollback()

            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS SavedGames
                                (
                                    user_id
                                    INT
                                    PRIMARY
                                    KEY
                                    REFERENCES
                                    Users
                                (
                                    user_id
                                ) ON DELETE CASCADE,
                                    fen_state TEXT NOT NULL, opponent_type VARCHAR
                                (
                                    50
                                ), player_color VARCHAR
                                (
                                    10
                                ),
                                    time_control INT, white_time FLOAT, black_time FLOAT, moves_history TEXT,
                                    save_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                ''')
            try:
                self.cursor.execute("ALTER TABLE SavedGames ADD COLUMN moves_history TEXT")
                self.conn.commit()
            except:
                self.conn.rollback()

            self.cursor.execute('''
                                CREATE TABLE IF NOT EXISTS Achievements
                                (
                                    achievement_id
                                    SERIAL
                                    PRIMARY
                                    KEY,
                                    user_id
                                    INT
                                    REFERENCES
                                    Users
                                (
                                    user_id
                                ) ON DELETE CASCADE,
                                    achievement_name VARCHAR
                                (
                                    100
                                ), date_earned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                ''')
            self.conn.commit()
        except Exception as e:
            print(f"TABLES ERROR: {e}")
            self.conn.rollback()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login_user(self, username, password):
        try:
            hashed_pw = self.hash_password(password)
            self.cursor.execute("SELECT user_id, username, password_hash FROM Users WHERE username = %s", (username,))
            user = self.cursor.fetchone()
            if user and user[2] == hashed_pw:
                return {"id": user[0], "name": user[1]}
            return None
        except:
            return None

    def register_user(self, username, password):
        try:
            hashed_pw = self.hash_password(password)
            self.cursor.execute(
                "INSERT INTO Users (username, password_hash) VALUES (%s, %s) RETURNING user_id, username",
                (username, hashed_pw)
            )
            new_user = self.cursor.fetchone()
            self.conn.commit()
            return {"id": new_user[0], "name": new_user[1]}
        except errors.UniqueViolation:
            self.conn.rollback()
            return "USER_EXISTS"
        except:
            self.conn.rollback()
            return None

    def save_current_state(self, user_id, fen, opp, col, tc, w_t, b_t, moves):
        try:
            self.cursor.execute("DELETE FROM SavedGames WHERE user_id = %s", (user_id,))
            self.cursor.execute(
                "INSERT INTO SavedGames (user_id, fen_state, opponent_type, player_color, time_control, white_time, black_time, moves_history) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (user_id, fen, opp, col, tc, w_t, b_t, moves)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"SAVE ERROR: {e}")
            self.conn.rollback()
            return False

    def load_saved_state(self, user_id):
        try:
            self.cursor.execute(
                "SELECT fen_state, opponent_type, player_color, time_control, white_time, black_time, moves_history FROM SavedGames WHERE user_id = %s",
                (user_id,))
            return self.cursor.fetchone()
        except:
            return None

    def delete_saved_state(self, user_id):
        try:
            self.cursor.execute("DELETE FROM SavedGames WHERE user_id = %s", (user_id,))
            self.conn.commit()
        except:
            self.conn.rollback()

    def save_game(self, user_id, opp, col, tc, res, moves):
        try:
            self.cursor.execute(
                "INSERT INTO Games (user_id, opponent_type, player_color, time_control, result, moves_history) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, opp, col, tc, res, moves)
            )
            self.conn.commit()
        except Exception as e:
            print("SAVE GAME ERROR:", e)
            self.conn.rollback()

    def get_user_games(self, user_id):
        try:
            self.cursor.execute(
                "SELECT opponent_type, player_color, result, game_date, time_control, moves_history FROM Games WHERE user_id = %s ORDER BY game_date DESC LIMIT 15",
                (user_id,)
            )
            return self.cursor.fetchall()
        except Exception as e:
            print("GET GAMES ERROR:", e)
            return []

    def add_achievement(self, user_id, name):
        try:
            self.cursor.execute("SELECT 1 FROM Achievements WHERE user_id = %s AND achievement_name = %s",
                                (user_id, name))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO Achievements (user_id, achievement_name) VALUES (%s, %s)",
                                    (user_id, name))
                self.conn.commit()
        except:
            self.conn.rollback()

    def get_user_achievements(self, user_id):
        try:
            self.cursor.execute("SELECT achievement_name, date_earned FROM Achievements WHERE user_id = %s", (user_id,))
            return self.cursor.fetchall()
        except:
            return []

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("🔌 З'єднання з БД закрито.")
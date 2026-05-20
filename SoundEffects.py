import pygame
import os


class SoundEffects:
    def __init__(self):
        # Ініціалізація мікшера для звуку
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.move_sound = None
        self.capture_sound = None
        self.victory_sound = None

        self.load_sounds()

    def load_sounds(self):
        # Перевіряємо, чи існує папка Sounds та файли в ній
        folder = "Sounds"

        if not os.path.exists(folder):
            print(f"Попередження: Папку '{folder}' не знайдено. Звук буде вимкнено.")
            return

        missing_files = False

        # Завантажуємо звук ходу
        if os.path.exists(f"{folder}/move.wav"):
            self.move_sound = pygame.mixer.Sound(f"{folder}/move.wav")
        else:
            missing_files = True

        # Завантажуємо звук перемоги/мату
        if os.path.exists(f"{folder}/victory.wav"):
            self.victory_sound = pygame.mixer.Sound(f"{folder}/victory.wav")
        else:
            missing_files = True

        # Завантажуємо звук взяття фігури (якщо є)
        if os.path.exists(f"{folder}/capture.wav"):
            self.capture_sound = pygame.mixer.Sound(f"{folder}/capture.wav")

        if missing_files:
            print("Попередження: Деякі звукові файли не знайдені в папці Sounds. Вони не будуть відтворюватись.")
        else:
            print("🔊 Звуки успішно завантажено!")
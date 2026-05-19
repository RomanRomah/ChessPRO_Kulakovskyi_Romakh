import pygame
import os


class SoundEffects:
    def __init__(self):
        # Ініціалізуємо мікшер для звуків
        pygame.mixer.init()

        # Завантажуємо звуки (з перевіркою чи існують файли)
        try:
            self.move_sound = pygame.mixer.Sound('Sounds/move_sound.mp3')
            self.capture_sound = pygame.mixer.Sound('Sounds/capture_sound.mp3')
            self.stalemate_sound = pygame.mixer.Sound('Sounds/stalemate_sound.mp3')
            self.check_sound = pygame.mixer.Sound('Sounds/check_sound.mp3')
            self.victory_sound = pygame.mixer.Sound('Sounds/victory_sound.mp3')
        except FileNotFoundError:
            print("Попередження: Звукові файли не знайдені в папці Sounds. Звук буде вимкнено.")
            self.move_sound = None
            self.capture_sound = None
            self.stalemate_sound = None
            self.check_sound = None
            self.victory_sound = None


__all__ = ['SoundEffects']
import pygame


class Button:
    """Базовий клас для створення кнопок у графічному інтерфейсі"""

    def __init__(self, x, y, width, height, text, color=(200, 200, 200), text_color=(0, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        # Використовуємо стандартний шрифт Pygame
        self.font = pygame.font.SysFont(None, 30)

    def draw(self, surface):
        """Малює кнопку на заданій поверхні (екрані)"""
        # Малюємо фон кнопки
        pygame.draw.rect(surface, self.color, self.rect)
        # Малюємо рамку кнопки (товщина 2 пікселі)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)

        # Рендеримо текст і центруємо його на кнопці
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def is_clicked(self, pos):
        """Перевіряє, чи клікнули по кнопці (pos - координати миші)"""
        return self.rect.collidepoint(pos)


# Заглушки для конкретних кнопок з PDF, які ми розширимо пізніше
class RestartButton(Button):
    pass


class ExitButton(Button):
    pass


__all__ = ['Button', 'RestartButton', 'ExitButton']
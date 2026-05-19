from enum import Enum

class Color(Enum):
    """Enum class for colors"""
    WHITE = 0
    BLACK = 1

    def opposite(self):
        return [Color.WHITE, Color.BLACK][self is Color.WHITE]

    def __str__(self):
        return self.name

__all__ = ['Color']
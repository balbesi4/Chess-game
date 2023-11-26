import pygame
from color import Color


class GameConfig:
    def __init__(self):
        pygame.init()
        self.bg_color = Color((234, 235, 200), (119, 154, 88))
        self.trace_color = Color((244, 247, 116), (172, 195, 51))
        self.moves_color = Color('#C86464', '#C84646')
        self.check_color = Color('#A84848', '#AB2B2B')
        self.font = pygame.font.SysFont('monospace', 18, bold=True)

from collections.abc import Callable

import pygame

from data_science_arcade.ui import colors
from data_science_arcade.ui.text import draw_centered_text

BUTTON_TEXT_SIZE = 24


class Button:
    def __init__(self, rect: pygame.Rect, label: str, on_activate: Callable[[], None]) -> None:
        self.rect = rect
        self.label = label
        self.on_activate = on_activate

    def draw(self, surface: pygame.Surface, focused: bool) -> None:
        fill = colors.BUTTON_HOVER if focused else colors.BUTTON_IDLE
        pygame.draw.rect(surface, fill, self.rect, border_radius=6)
        if focused:
            pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, self.rect, width=2, border_radius=6)
        draw_centered_text(surface, self.label, self.rect.center, BUTTON_TEXT_SIZE, colors.BUTTON_TEXT)

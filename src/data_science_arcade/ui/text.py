import pygame

from data_science_arcade.core.fonts import get_font


def draw_centered_text(
    surface: pygame.Surface,
    text: str,
    center: tuple[int, int],
    size: int,
    color: tuple[int, int, int],
) -> pygame.Rect:
    image = get_font(size).render(text, True, color)
    rect = image.get_rect(center=center)
    surface.blit(image, rect)
    return rect

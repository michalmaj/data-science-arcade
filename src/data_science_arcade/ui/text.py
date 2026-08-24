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


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Greedy word-wrap: breaks text into lines that each fit max_width."""
    lines: list[str] = []
    current = ""
    for word in text.split(" "):
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped_text(
    surface: pygame.Surface,
    text: str,
    top_left: tuple[int, int],
    max_width: int,
    size: int,
    color: tuple[int, int, int],
    line_spacing: int = 4,
) -> None:
    font = get_font(size)
    x, y = top_left
    line_height = font.get_linesize() + line_spacing
    for index, line in enumerate(wrap_text(text, font, max_width)):
        surface.blit(font.render(line, True, color), (x, y + index * line_height))

import pygame


def category_x(index: int, count: int, rect: pygame.Rect) -> int:
    """Evenly spaces `count` categories across rect's horizontal span,
    each centered in its own slice - shared by bar placement, line
    points, and axis labels so they always line up with each other."""
    if count <= 1:
        return rect.centerx
    slice_width = rect.width / count
    return rect.left + round(slice_width * (index + 0.5))


def value_to_y(value: float, min_value: float, max_value: float, rect: pygame.Rect) -> int:
    if max_value == min_value:
        return rect.bottom
    fraction = (value - min_value) / (max_value - min_value)
    y = rect.bottom - round(fraction * rect.height)
    return min(max(y, rect.top), rect.bottom)


def draw_bar_chart(
    surface: pygame.Surface,
    rect: pygame.Rect,
    values: list[float],
    min_value: float,
    max_value: float,
    color: tuple[int, int, int],
) -> None:
    count = len(values)
    bar_width = max(1, round(rect.width / count * 0.6))
    for index, value in enumerate(values):
        x = category_x(index, count, rect)
        top_y = value_to_y(value, min_value, max_value, rect)
        bar_rect = pygame.Rect(0, 0, bar_width, max(1, rect.bottom - top_y))
        bar_rect.midtop = (x, top_y)
        pygame.draw.rect(surface, color, bar_rect)


def draw_line_chart(
    surface: pygame.Surface,
    rect: pygame.Rect,
    values: list[float],
    min_value: float,
    max_value: float,
    color: tuple[int, int, int],
) -> None:
    count = len(values)
    points = [(category_x(index, count, rect), value_to_y(value, min_value, max_value, rect)) for index, value in enumerate(values)]
    if len(points) >= 2:
        pygame.draw.lines(surface, color, False, points, 2)
    for point in points:
        pygame.draw.circle(surface, color, point, 3)

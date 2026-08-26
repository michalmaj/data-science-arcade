import pygame


def compute_bin_counts(values: list[float], min_value: float, max_value: float, bin_count: int) -> list[int]:
    """How many values fall in each of bin_count equal-width bins spanning
    [min_value, max_value]. Bins are half-open ([lo, hi)) except the last,
    which is closed on both ends so a value exactly at max_value still
    counts instead of falling just past every bin."""
    counts = [0] * bin_count
    width = (max_value - min_value) / bin_count
    for value in values:
        index = int((value - min_value) / width) if width else 0
        index = min(max(index, 0), bin_count - 1)
        counts[index] += 1
    return counts


def value_to_x(value: float, min_value: float, max_value: float, rect: pygame.Rect) -> int:
    """Maps a data value onto rect's horizontal span - shared by bar
    placement and the overlay marker, so a marker always lines up with
    the bar its value falls inside."""
    if max_value == min_value:
        return rect.centerx
    fraction = (value - min_value) / (max_value - min_value)
    x = rect.left + round(fraction * rect.width)
    return min(max(x, rect.left), rect.right - 1)


def draw_histogram(
    surface: pygame.Surface,
    rect: pygame.Rect,
    values: list[float],
    min_value: float,
    max_value: float,
    bin_count: int,
    color: tuple[int, int, int],
) -> None:
    counts = compute_bin_counts(values, min_value, max_value, bin_count)
    peak = max(counts) if counts else 0
    bin_width = rect.width / bin_count
    for index, count in enumerate(counts):
        bar_height = round((count / peak) * rect.height) if peak else 0
        if bar_height == 0:
            continue
        bar_rect = pygame.Rect(
            rect.left + round(index * bin_width),
            rect.bottom - bar_height,
            max(1, round(bin_width) - 2),
            bar_height,
        )
        pygame.draw.rect(surface, color, bar_rect)


def draw_value_marker(
    surface: pygame.Surface,
    rect: pygame.Rect,
    value: float,
    min_value: float,
    max_value: float,
    color: tuple[int, int, int],
    width: int = 3,
) -> None:
    x = value_to_x(value, min_value, max_value, rect)
    pygame.draw.line(surface, color, (x, rect.top - 10), (x, rect.bottom), width)

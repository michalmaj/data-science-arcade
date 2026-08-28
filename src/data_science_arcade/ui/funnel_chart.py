import pygame

from data_science_arcade.lessons.framework.funnel import FunnelStep


def step_percent_of_top(steps: tuple[FunnelStep, ...], index: int) -> float:
    if steps[0].count == 0:
        return 0.0
    return steps[index].count / steps[0].count


def step_percent_of_previous(steps: tuple[FunnelStep, ...], index: int) -> float:
    if index == 0:
        return 1.0
    if steps[index - 1].count == 0:
        return 0.0
    return steps[index].count / steps[index - 1].count


def step_percent(steps: tuple[FunnelStep, ...], index: int, basis: str) -> float:
    """basis='previous' answers "how many of the people at the last step
    made it here" (the right question for spotting a local bottleneck);
    basis='top' answers "how many of everyone who ever entered the funnel
    made it here" (always shrinks, regardless of how efficient a given
    step actually is) - the same two counts, read two different ways."""
    return step_percent_of_previous(steps, index) if basis == "previous" else step_percent_of_top(steps, index)


def draw_funnel_bar(surface: pygame.Surface, row_rect: pygame.Rect, fraction: float, color: tuple[int, int, int]) -> None:
    """A bar centered in row_rect, its width proportional to `fraction`
    of row_rect's own width - always driven by share-of-top (never
    share-of-previous), so a funnel's visual taper reflects the real,
    unchanging counts even when the *displayed* percentage text is
    reading a different denominator."""
    width = max(4, round(row_rect.width * max(0.0, min(1.0, fraction))))
    bar_rect = pygame.Rect(0, 0, width, row_rect.height)
    bar_rect.center = row_rect.center
    pygame.draw.rect(surface, color, bar_rect, border_radius=4)

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.lessons.framework.funnel import FunnelStep
from data_science_arcade.ui.funnel_chart import draw_funnel_bar, step_percent, step_percent_of_previous, step_percent_of_top

STEPS = (
    FunnelStep("top", "app.title", 1000),
    FunnelStep("middle", "app.title", 400),
    FunnelStep("bottom", "app.title", 100),
)


def test_top_step_is_always_100_percent_of_top():
    assert step_percent_of_top(STEPS, 0) == 1.0


def test_percent_of_top_divides_by_the_first_steps_count():
    assert step_percent_of_top(STEPS, 1) == 0.4
    assert step_percent_of_top(STEPS, 2) == 0.1


def test_top_step_is_always_100_percent_of_previous():
    assert step_percent_of_previous(STEPS, 0) == 1.0


def test_percent_of_previous_divides_by_the_immediately_prior_steps_count():
    assert step_percent_of_previous(STEPS, 1) == 0.4
    assert step_percent_of_previous(STEPS, 2) == 0.25


def test_percent_of_previous_and_percent_of_top_diverge_past_the_first_step():
    # The whole point of percent_basis: the same underlying counts read
    # very differently depending on which denominator is used.
    assert step_percent_of_previous(STEPS, 2) != step_percent_of_top(STEPS, 2)


@pytest.mark.parametrize("basis,index,expected", [("top", 2, 0.1), ("previous", 2, 0.25)])
def test_step_percent_dispatches_on_basis(basis, index, expected):
    assert step_percent(STEPS, index, basis) == expected


def test_zero_count_top_step_does_not_divide_by_zero():
    steps = (FunnelStep("top", "app.title", 0), FunnelStep("middle", "app.title", 0))
    assert step_percent_of_top(steps, 1) == 0.0
    assert step_percent_of_previous(steps, 1) == 0.0


def test_draw_funnel_bar_does_not_crash_at_the_edges():
    pygame.init()
    surface = pygame.Surface((200, 100))
    row_rect = pygame.Rect(0, 0, 200, 40)
    draw_funnel_bar(surface, row_rect, 1.0, (255, 255, 255))
    draw_funnel_bar(surface, row_rect, 0.0, (255, 255, 255))
    draw_funnel_bar(surface, row_rect, 0.4, (255, 255, 255))
    pygame.quit()

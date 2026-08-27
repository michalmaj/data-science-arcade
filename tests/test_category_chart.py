import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.ui.category_chart import category_x, draw_bar_chart, draw_line_chart, value_to_y


def test_category_x_spaces_categories_evenly_across_the_rect():
    rect = pygame.Rect(0, 0, 300, 50)
    positions = [category_x(index, 3, rect) for index in range(3)]
    assert positions == sorted(positions)
    assert positions[0] > rect.left
    assert positions[-1] < rect.right


def test_category_x_centers_a_single_category():
    rect = pygame.Rect(100, 0, 200, 50)
    assert category_x(0, 1, rect) == rect.centerx


def test_value_to_y_places_the_minimum_at_the_rect_bottom():
    rect = pygame.Rect(0, 0, 100, 200)
    assert value_to_y(0.0, min_value=0.0, max_value=10.0, rect=rect) == rect.bottom


def test_value_to_y_places_the_maximum_at_the_rect_top():
    rect = pygame.Rect(0, 0, 100, 200)
    assert value_to_y(10.0, min_value=0.0, max_value=10.0, rect=rect) == rect.top


def test_value_to_y_never_places_a_value_outside_the_rect():
    rect = pygame.Rect(0, 0, 100, 200)
    assert value_to_y(-5.0, min_value=0.0, max_value=10.0, rect=rect) <= rect.bottom
    assert value_to_y(15.0, min_value=0.0, max_value=10.0, rect=rect) >= rect.top


def test_a_zoomed_scale_exaggerates_the_visual_gap_between_close_values():
    rect = pygame.Rect(0, 0, 100, 200)
    zero_based_gap = value_to_y(4000.0, 0.0, 6600.0, rect) - value_to_y(6000.0, 0.0, 6600.0, rect)
    zoomed_gap = value_to_y(4000.0, 3600.0, 6300.0, rect) - value_to_y(6000.0, 3600.0, 6300.0, rect)
    assert zoomed_gap > zero_based_gap


@pytest.fixture(autouse=True)
def _pygame_session():
    pygame.init()
    yield
    pygame.quit()


def test_draw_bar_chart_runs_without_crashing_on_a_real_surface():
    surface = pygame.Surface((960, 540))
    rect = pygame.Rect(150, 90, 660, 180)
    draw_bar_chart(surface, rect, [4000.0, 6000.0, 5000.0], min_value=0.0, max_value=6600.0, color=(255, 255, 255))


def test_draw_line_chart_runs_without_crashing_on_a_real_surface():
    surface = pygame.Surface((960, 540))
    rect = pygame.Rect(150, 90, 660, 180)
    draw_line_chart(surface, rect, [500.0, 200.0, 520.0, 510.0, 530.0], min_value=0.0, max_value=580.0, color=(58, 214, 255))

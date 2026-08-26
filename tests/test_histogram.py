import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.ui.histogram import compute_bin_counts, draw_histogram, draw_value_marker, value_to_x


def test_bin_counts_sum_to_the_total_number_of_values():
    values = [1.0, 2.0, 3.0, 4.0, 15.0, 27.0, 30.0]
    counts = compute_bin_counts(values, min_value=0.0, max_value=30.0, bin_count=3)
    assert sum(counts) == len(values)


def test_bin_counts_place_values_in_the_expected_bin():
    values = [0.0, 5.0, 10.0]
    counts = compute_bin_counts(values, min_value=0.0, max_value=15.0, bin_count=3)
    assert counts == [1, 1, 1]


def test_a_value_exactly_at_max_lands_in_the_last_bin_not_past_it():
    counts = compute_bin_counts([10.0], min_value=0.0, max_value=10.0, bin_count=5)
    assert counts == [0, 0, 0, 0, 1]


def test_bin_counts_reveal_an_empty_gap_between_two_clusters():
    low_cluster = [1.0, 1.5, 2.0]
    high_cluster = [28.0, 28.5, 30.0]
    counts = compute_bin_counts(low_cluster + high_cluster, min_value=0.0, max_value=30.0, bin_count=10)
    assert counts[0] == 3
    assert counts[-1] == 3
    assert sum(counts[1:-1]) == 0


def test_value_to_x_places_the_minimum_at_the_rect_left_edge():
    rect = pygame.Rect(100, 0, 200, 50)
    assert value_to_x(0.0, min_value=0.0, max_value=10.0, rect=rect) == rect.left


def test_value_to_x_places_the_maximum_at_the_rect_right_edge():
    rect = pygame.Rect(100, 0, 200, 50)
    assert value_to_x(10.0, min_value=0.0, max_value=10.0, rect=rect) == rect.right - 1


def test_value_to_x_places_the_midpoint_at_the_rect_center():
    rect = pygame.Rect(100, 0, 200, 50)
    assert value_to_x(5.0, min_value=0.0, max_value=10.0, rect=rect) == rect.centerx


def test_value_to_x_never_places_a_value_outside_the_rect():
    rect = pygame.Rect(100, 0, 200, 50)
    assert value_to_x(-5.0, min_value=0.0, max_value=10.0, rect=rect) >= rect.left
    assert value_to_x(15.0, min_value=0.0, max_value=10.0, rect=rect) <= rect.right - 1


def test_value_to_x_handles_a_single_repeated_value_without_dividing_by_zero():
    rect = pygame.Rect(100, 0, 200, 50)
    assert value_to_x(5.0, min_value=5.0, max_value=5.0, rect=rect) == rect.centerx


@pytest.fixture(autouse=True)
def _pygame_session():
    pygame.init()
    yield
    pygame.quit()


def test_draw_histogram_runs_without_crashing_on_a_real_surface():
    surface = pygame.Surface((960, 540))
    rect = pygame.Rect(80, 68, 800, 150)
    draw_histogram(surface, rect, [1.0, 2.0, 2.0, 30.0], min_value=0.0, max_value=30.0, bin_count=10, color=(255, 255, 255))


def test_draw_value_marker_runs_without_crashing_on_a_real_surface():
    surface = pygame.Surface((960, 540))
    rect = pygame.Rect(80, 68, 800, 150)
    draw_value_marker(surface, rect, 15.0, min_value=0.0, max_value=30.0, color=(58, 214, 255))

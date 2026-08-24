import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.core import fonts
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup


@pytest.fixture(autouse=True)
def _pygame_session():
    pygame.init()
    fonts.clear_cache()
    pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def make_group(count: int) -> tuple[ButtonGroup, list[list[str]]]:
    calls: list[list[str]] = [[] for _ in range(count)]
    buttons = [
        Button(pygame.Rect(0, i * 60, 200, 48), f"button-{i}", lambda i=i: calls[i].append("activated"))
        for i in range(count)
    ]
    return ButtonGroup(buttons), calls


def test_starts_focused_on_the_first_button():
    group, _ = make_group(3)
    assert group.focus_index == 0


def test_down_moves_focus_forward_and_wraps():
    group, _ = make_group(3)
    group.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0))
    group.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0))
    group.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0))
    assert group.focus_index == 0


def test_up_moves_focus_backward_and_wraps_to_the_last_button():
    group, _ = make_group(3)
    group.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP, mod=0))
    assert group.focus_index == 2


def test_enter_activates_the_focused_button():
    group, calls = make_group(3)
    group.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0))
    group.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
    assert calls == [[], ["activated"], []]


def test_mouse_motion_over_a_button_focuses_it():
    group, _ = make_group(3)
    group.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(50, 65)))
    assert group.focus_index == 1


def test_click_on_a_button_activates_it_regardless_of_current_focus():
    group, calls = make_group(3)
    group.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(50, 125), button=1))
    assert calls == [[], [], ["activated"]]


def test_draw_does_not_crash_headless():
    group, _ = make_group(3)
    surface = pygame.Surface((960, 540))
    group.draw(surface)

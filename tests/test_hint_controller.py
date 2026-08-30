import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.ui.hint_controller import HintController

HINT_KEYS = ("common.back", "common.on", "common.off")  # stand-in Direction/Concept/Procedure keys


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_starts_with_no_tier_revealed():
    app = _init_app()
    try:
        controller = HintController(app, HINT_KEYS, button_topleft=(0, 0))
        assert controller.revealed_tier == 0
        assert controller.button.enabled
    finally:
        pygame.quit()


def test_each_click_reveals_exactly_one_more_tier_in_order():
    app = _init_app()
    try:
        controller = HintController(app, HINT_KEYS, button_topleft=(0, 0))

        controller.reveal_next()
        assert controller.revealed_tier == 1

        controller.reveal_next()
        assert controller.revealed_tier == 2
    finally:
        pygame.quit()


def test_cannot_reveal_past_the_last_tier():
    app = _init_app()
    try:
        controller = HintController(app, HINT_KEYS, button_topleft=(0, 0))

        for _ in range(5):
            controller.reveal_next()

        assert controller.revealed_tier == len(HINT_KEYS)
    finally:
        pygame.quit()


def test_button_disables_once_every_tier_is_revealed():
    app = _init_app()
    try:
        controller = HintController(app, HINT_KEYS, button_topleft=(0, 0))

        for _ in range(len(HINT_KEYS)):
            assert controller.button.enabled
            controller.reveal_next()

        assert not controller.button.enabled
    finally:
        pygame.quit()


def test_clicking_the_button_reveals_a_tier():
    app = _init_app()
    try:
        controller = HintController(app, HINT_KEYS, button_topleft=(0, 0))

        controller.button.on_activate()

        assert controller.revealed_tier == 1
    finally:
        pygame.quit()


def test_single_tier_is_supported():
    app = _init_app()
    try:
        controller = HintController(app, ("common.back",), button_topleft=(0, 0))
        controller.reveal_next()
        assert controller.revealed_tier == 1
        assert not controller.button.enabled
    finally:
        pygame.quit()


def test_rejects_zero_or_more_than_three_tiers():
    app = _init_app()
    try:
        with pytest.raises(ValueError):
            HintController(app, (), button_topleft=(0, 0))
        with pytest.raises(ValueError):
            HintController(app, ("a", "b", "c", "d"), button_topleft=(0, 0))
    finally:
        pygame.quit()


def test_draw_does_not_crash_at_any_reveal_level():
    app = _init_app()
    try:
        controller = HintController(app, HINT_KEYS, button_topleft=(50, 50))
        for _ in range(len(HINT_KEYS) + 1):
            controller.draw(app.logical_surface, text_topleft=(50, 100))
            controller.reveal_next()
    finally:
        pygame.quit()

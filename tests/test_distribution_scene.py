import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.distribution import DistributionLens, LensOption
from data_science_arcade.ui.distribution_scene import DistributionScene

VALUES = [1.0, 2.0, 3.0, 4.0, 30.0]

LENSES = (
    DistributionLens(
        key="lens_a",
        prompt_key="app.title",
        hint_key="common.back",
        options=(
            LensOption("a_right", "common.on", marker_value=2.5),
            LensOption("a_wrong", "common.off", marker_value=None),
        ),
    ),
    DistributionLens(
        key="lens_b",
        prompt_key="app.title",
        hint_key="common.back",
        options=(
            LensOption("b_right", "common.on", marker_value=30.0),
            LensOption("b_wrong", "common.off", marker_value=1.0),
        ),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return DistributionScene(app, "app.title", VALUES, LENSES, on_complete, **kwargs)


def test_starts_on_the_first_lens_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.lens_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
        assert scene.min_value == 1.0
        assert scene.max_value == 30.0
    finally:
        pygame.quit()


def test_choosing_an_option_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()

        assert scene.choices == {"lens_a": "a_right"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_is_a_no_op_before_a_choice_is_made():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._next()

        assert scene.lens_index == 0
    finally:
        pygame.quit()


def test_next_advances_to_the_next_lens_and_back_returns():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.lens_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()

        assert scene.lens_index == 0
        # the earlier choice for lens_a survives navigating away and back
        assert scene.choices["lens_a"] == "a_right"
    finally:
        pygame.quit()


def test_next_relabels_to_finish_on_the_last_lens():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.next_button.label == app.localization.t("brief.finish")
    finally:
        pygame.quit()


def test_finishing_the_last_lens_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # lens_b: the "wrong" option

        scene.next_button.on_activate()

        assert collected == [{"lens_a": "a_right", "lens_b": "b_wrong"}]
    finally:
        pygame.quit()


def test_selecting_an_option_with_no_marker_value_does_not_crash_the_draw():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[1].on_activate()  # lens_a's "a_wrong": marker_value=None
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_at_any_lens():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            for index in range(len(LENSES)):
                scene.lens_index = index
                scene._rebuild_buttons()
                scene.draw(app.logical_surface)
    finally:
        pygame.quit()

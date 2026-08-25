import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.flow import FlowEventOption, FlowStep
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene

STEPS = (
    FlowStep(
        key="step_a",
        short_label_key="app.title",
        prompt_key="app.title",
        options=(FlowEventOption("a_right", "common.on"), FlowEventOption("a_wrong", "common.off")),
        hint_key="common.back",
    ),
    FlowStep(
        key="step_b",
        short_label_key="app.title",
        prompt_key="app.title",
        options=(FlowEventOption("b_right", "common.on"), FlowEventOption("b_wrong", "common.off")),
        hint_key="common.back",
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda placement: None, **kwargs):
    return FlowBuilderScene(app, "app.title", STEPS, on_complete, **kwargs)


def test_starts_on_the_first_step_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.step_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_an_option_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()

        assert scene.placement == {"step_a": "a_right"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_is_a_no_op_before_a_choice_is_made():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._next()

        assert scene.step_index == 0
    finally:
        pygame.quit()


def test_next_advances_to_the_next_step_and_back_returns():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.step_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()

        assert scene.step_index == 0
        # the earlier choice for step_a survives navigating away and back
        assert scene.placement["step_a"] == "a_right"
    finally:
        pygame.quit()


def test_next_relabels_to_finish_on_the_last_step():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.next_button.label == app.localization.t("brief.finish")
    finally:
        pygame.quit()


def test_finishing_the_last_step_calls_on_complete_with_the_full_placement():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda placement: collected.append(placement))
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # step_b: the "wrong" option

        scene.next_button.on_activate()

        assert collected == [{"step_a": "a_right", "step_b": "b_wrong"}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_at_any_step():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            for index in range(len(STEPS)):
                scene.step_index = index
                scene._rebuild_buttons()
                scene.draw(app.logical_surface)
    finally:
        pygame.quit()

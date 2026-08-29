import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pandas as pd
import pygame

from data_science_arcade.app.game import App
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.survey import ChannelOption, SurveyRequest, WordingOption
from data_science_arcade.ui.survey_builder_scene import SurveyBuilderScene

SCHEMA = Schema(columns=(ColumnSchema("group", "object"), ColumnSchema("value", "float64")))
FRAME = pd.DataFrame([("a", 0.2), ("a", 0.4), ("b", 0.9)], columns=["group", "value"])
DATASET = Dataset(name="synthetic", frame=FRAME, schema=SCHEMA, history=())

REQUESTS = (
    SurveyRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        wording_options=(WordingOption("neutral", "common.on", bias=0.0), WordingOption("leading", "common.off", bias=0.3)),
        channel_options=(ChannelOption("all", "common.on", reach_query=None), ChannelOption("a_only", "common.off", reach_query="group == 'a'")),
    ),
    SurveyRequest(
        key="request_b",
        prompt_key="app.title",
        wording_options=(WordingOption("neutral", "common.on", bias=0.0), WordingOption("leading", "common.off", bias=0.3)),
        channel_options=(ChannelOption("all", "common.on", reach_query=None), ChannelOption("a_only", "common.off", reach_query="group == 'a'")),
    ),
)


def _simulate(dataset: Dataset, channel: ChannelOption, wording: WordingOption) -> tuple[int, float]:
    reached = dataset.frame.query(channel.reach_query) if channel.reach_query else dataset.frame
    if reached.empty:
        return 0, 0.0
    mean_value = min(1.0, float(reached["value"].mean()) + wording.bias)
    return len(reached), mean_value


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return SurveyBuilderScene(app, "app.title", DATASET, REQUESTS, _simulate, on_complete, **kwargs)


def test_starts_on_the_first_request_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_only_wording_does_not_enable_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # wording: neutral

        assert scene.next_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_both_wording_and_channel_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # wording: neutral
        scene.buttons.buttons[2].on_activate()  # channel: all

        assert scene.choices == {"request_a": ("neutral", "all")}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_is_a_no_op_before_both_choices_are_made():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene._next()

        assert scene.request_index == 0
    finally:
        pygame.quit()


def test_next_advances_and_back_restores_the_earlier_full_choice():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[2].on_activate()
        scene.next_button.on_activate()

        assert scene.request_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()

        assert scene.request_index == 0
        assert scene._wording_choice == "neutral"
        assert scene._channel_choice == "all"
    finally:
        pygame.quit()


def test_finishing_the_last_request_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[2].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # request_b wording: leading
        scene.buttons.buttons[3].on_activate()  # request_b channel: a_only

        scene.next_button.on_activate()

        assert collected == [{"request_a": ("neutral", "all"), "request_b": ("leading", "a_only")}]
    finally:
        pygame.quit()


def test_the_live_preview_reflects_the_injected_simulation():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # wording: neutral
        scene.buttons.buttons[3].on_activate()  # channel: a_only

        request = scene._current_request()
        wording = scene._selected_wording(request)
        channel = scene._selected_channel(request)
        count, mean_value = _simulate(DATASET, channel, wording)

        assert (count, round(mean_value, 4)) == (2, 0.3)  # group "a" is 0.2 and 0.4
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_with_or_without_a_full_choice():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # no choice yet - the "pick both" placeholder path
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # only wording chosen
            scene.buttons.buttons[2].on_activate()
            scene.draw(app.logical_surface)  # both chosen - the live result path
    finally:
        pygame.quit()

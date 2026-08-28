import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.timeseries import DailyPoint, LensOption, TimeSeries, TimeSeriesRequest
from data_science_arcade.ui.timeseries_scene import TimeSeriesScene

CURRENT = TimeSeries(label_key="app.title", points=(DailyPoint(1, 0.10), DailyPoint(2, 0.20), DailyPoint(3, 0.30)))
PREVIOUS = TimeSeries(label_key="app.title", points=(DailyPoint(1, 0.11), DailyPoint(2, 0.19), DailyPoint(3, 0.31)))
REQUESTS = (
    TimeSeriesRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        highlight_days=(2,),
        options=(
            LensOption("nearby", "common.on", show_previous_period=False),
            LensOption("same_days", "common.off", show_previous_period=True),
        ),
    ),
    TimeSeriesRequest(
        key="request_b",
        prompt_key="app.title",
        highlight_days=(1, 3),
        options=(LensOption("only_one", "common.on", show_previous_period=False),),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return TimeSeriesScene(app, "app.title", CURRENT, PREVIOUS, REQUESTS, on_complete, **kwargs)


def test_starts_on_the_first_request_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_min_and_max_value_span_both_series_with_padding():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert round(scene.min_value, 2) == 0.08  # 0.10 is the lowest current value, minus 0.02 padding
        assert round(scene.max_value, 2) == 0.33  # 0.31 is the highest previous value, plus 0.02 padding
    finally:
        pygame.quit()


def test_choosing_an_option_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()

        assert scene.choices == {"request_a": "nearby"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_selected_option_controls_whether_the_previous_period_shows():
    app = _init_app()
    try:
        scene = _make_scene(app)
        request = scene._current_request()

        scene.buttons.buttons[0].on_activate()  # "nearby"
        assert scene._selected_option(request).show_previous_period is False

        scene.buttons.buttons[1].on_activate()  # "same_days"
        assert scene._selected_option(request).show_previous_period is True
    finally:
        pygame.quit()


def test_average_computes_the_mean_of_only_the_highlighted_days():
    app = _init_app()
    try:
        scene = _make_scene(app)
        request = scene._current_request()  # request_a, highlight_days=(2,)
        assert scene._average(CURRENT, request.highlight_days) == 0.20

        other_request = REQUESTS[1]  # highlight_days=(1, 3)
        assert round(scene._average(CURRENT, other_request.highlight_days), 2) == 0.20  # mean of 0.10 and 0.30
    finally:
        pygame.quit()


def test_next_advances_to_the_next_request_and_back_returns():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.request_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()

        assert scene.request_index == 0
        assert scene.choices["request_a"] == "nearby"
    finally:
        pygame.quit()


def test_finishing_the_last_request_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[1].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[0].on_activate()

        scene.next_button.on_activate()

        assert collected == [{"request_a": "same_days", "request_b": "only_one"}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_a_choice():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # before any choice - no overlay
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # after a choice - overlay may show
    finally:
        pygame.quit()

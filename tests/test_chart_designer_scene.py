import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.chart import ChartOption, ChartRequest
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene

REQUESTS = (
    ChartRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        categories=("X", "Y", "Z"),
        values=(4000.0, 6000.0, 5000.0),
        options=(
            ChartOption("bar_zero", "common.on", "bar", "zero_based"),
            ChartOption("bar_zoomed", "common.off", "bar", "zoomed"),
            ChartOption("line", "common.back", "line", "zero_based"),
        ),
    ),
    ChartRequest(
        key="request_b",
        prompt_key="app.title",
        hint_key="common.back",
        categories=("Mon", "Tue", "Wed"),
        values=(500.0, 200.0, 520.0),
        options=(
            ChartOption("bar_zero", "common.on", "bar", "zero_based"),
            ChartOption("line", "common.back", "line", "zero_based"),
        ),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return ChartDesignerScene(app, "app.title", REQUESTS, on_complete, **kwargs)


def test_starts_on_the_first_request_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_an_option_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()

        assert scene.choices == {"request_a": "bar_zero"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_zoomed_scale_range_is_narrower_than_zero_based_range():
    app = _init_app()
    try:
        scene = _make_scene(app)
        request = scene._current_request()
        zero_based = next(o for o in request.options if o.key == "bar_zero")
        zoomed = next(o for o in request.options if o.key == "bar_zoomed")

        zero_min, zero_max = scene._chart_range(zero_based, request.values)
        zoom_min, zoom_max = scene._chart_range(zoomed, request.values)

        assert zero_min == 0.0
        assert (zoom_max - zoom_min) < (zero_max - zero_min)
    finally:
        pygame.quit()


def test_line_option_always_uses_a_zero_based_range():
    app = _init_app()
    try:
        scene = _make_scene(app)
        request = scene._current_request()
        line_option = next(o for o in request.options if o.chart_type == "line")

        min_value, _max_value = scene._chart_range(line_option, request.values)

        assert min_value == 0.0
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
        assert scene.choices["request_a"] == "bar_zero"
    finally:
        pygame.quit()


def test_finishing_the_last_request_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()

        scene.next_button.on_activate()

        assert collected == [{"request_a": "bar_zero", "request_b": "line"}]
    finally:
        pygame.quit()


def test_an_option_without_an_override_uses_the_requests_own_series():
    app = _init_app()
    try:
        scene = _make_scene(app)
        request = scene._current_request()
        option = next(o for o in request.options if o.key == "bar_zero")

        categories, values = scene._effective_series(request, option)

        assert categories == request.categories
        assert values == request.values
    finally:
        pygame.quit()


def test_an_option_with_an_override_uses_its_own_series_instead():
    app = _init_app()
    try:
        request = ChartRequest(
            key="request_c",
            prompt_key="app.title",
            categories=("Jan", "Feb", "Mar"),
            values=(100.0, 90.0, 80.0),
            options=(
                ChartOption("full", "common.on", "line", "zero_based"),
                ChartOption("cherry_picked", "common.off", "line", "zero_based", categories=("Feb", "Mar"), values=(90.0, 80.0)),
            ),
        )
        scene = _make_scene(app)
        cherry_picked = request.options[1]

        categories, values = scene._effective_series(request, cherry_picked)

        assert categories == ("Feb", "Mar")
        assert values == (90.0, 80.0)
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_a_choice():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # before any choice - the "pick a chart" placeholder path
            for option_index in range(3):
                scene.request_index = 0
                scene._rebuild_buttons()
                if option_index < len(scene._current_request().options):
                    scene.buttons.buttons[option_index].on_activate()
                    scene.draw(app.logical_surface)
    finally:
        pygame.quit()

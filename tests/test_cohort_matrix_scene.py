import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.cohort import CohortMatrix, CohortRequest, CohortRow, ComparisonOption
from data_science_arcade.ui.cohort_matrix_scene import CohortMatrixScene

MATRIX = CohortMatrix(
    rows=(
        CohortRow("jan", "common.on", months_observed=3, retention_by_month=(1.0, 0.68, 0.58)),
        CohortRow("feb", "common.off", months_observed=2, retention_by_month=(1.0, 0.76)),
    ),
    month_count=3,
)
REQUESTS = (
    CohortRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        options=(
            ComparisonOption("mismatched", "common.on", cohort_a="feb", month_a=1, cohort_b="jan", month_b=2),
            ComparisonOption("same_month", "common.off", cohort_a="feb", month_a=1, cohort_b="jan", month_b=1),
        ),
    ),
    CohortRequest(
        key="request_b",
        prompt_key="app.title",
        options=(ComparisonOption("only_one", "common.on", cohort_a="jan", month_a=0, cohort_b="feb", month_b=0),),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return CohortMatrixScene(app, "app.title", MATRIX, REQUESTS, on_complete, **kwargs)


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

        assert scene.choices == {"request_a": "mismatched"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_selected_option_highlights_its_own_two_cells():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[1].on_activate()  # "same_month"

        request = scene._current_request()
        assert scene._highlighted_cells(request) == {("feb", 1), ("jan", 1)}
    finally:
        pygame.quit()


def test_cell_value_is_none_for_a_month_not_yet_observed():
    app = _init_app()
    try:
        scene = _make_scene(app)
        row = MATRIX.rows[1]  # feb, only months_observed=2 (months 0-1)
        assert scene._cell_value(row, 2) is None
        assert scene._cell_value(row, 1) == 0.76
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
        assert scene.choices["request_a"] == "mismatched"
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

        assert collected == [{"request_a": "same_month", "request_b": "only_one"}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_a_choice():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # before any choice - no cells highlighted
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # after a choice - two cells highlighted
    finally:
        pygame.quit()

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pandas as pd
import pygame

from data_science_arcade.app.game import App
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.alerting import MetricOption, MonitoringRequest, ThresholdOption
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.workbench.context import LessonContext

SCHEMA = Schema(columns=(ColumnSchema("day", "int64"), ColumnSchema("metric_key", "object"), ColumnSchema("value", "float64")))
FRAME = pd.DataFrame(
    [(1, "good", 1.0), (2, "good", 1.0), (3, "good", 9.0), (1, "noisy", 1.0), (2, "noisy", 5.0), (3, "noisy", 1.0)],
    columns=["day", "metric_key", "value"],
)
DATASET = Dataset(name="synthetic", frame=FRAME, schema=SCHEMA, history=())

REQUESTS = (
    MonitoringRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        target_incident_day=3,
        metric_options=(MetricOption("good", "common.on", metric_key="good"), MetricOption("noisy", "common.off", metric_key="noisy")),
        threshold_options=(ThresholdOption("tight", "common.on", multiplier=1.0), ThresholdOption("balanced", "common.off", multiplier=3.0)),
    ),
    MonitoringRequest(
        key="request_b",
        prompt_key="app.title",
        target_incident_day=3,
        metric_options=(MetricOption("good", "common.on", metric_key="good"), MetricOption("noisy", "common.off", metric_key="noisy")),
        threshold_options=(ThresholdOption("tight", "common.on", multiplier=1.0), ThresholdOption("balanced", "common.off", multiplier=3.0)),
    ),
)


def _simulate(dataset: Dataset, metric: MetricOption, threshold: ThresholdOption, target_incident_day: int) -> tuple[int, bool]:
    values = list(dataset.frame[dataset.frame["metric_key"] == metric.metric_key].sort_values("day")["value"])
    mean = sum(values) / len(values)
    spread = max(values) - min(values)
    flagged = {day for day, value in enumerate(values, start=1) if value > mean + threshold.multiplier * spread / 4}
    false_alarms = len(flagged - {target_incident_day})
    return false_alarms, target_incident_day in flagged


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return AlertConfigScene(app, "app.title", DATASET, REQUESTS, _simulate, on_complete, **kwargs)


def test_starts_on_the_first_request_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_only_metric_does_not_enable_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # metric: good

        assert scene.next_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_both_metric_and_threshold_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # metric: good
        scene.buttons.buttons[2].on_activate()  # threshold: tight

        assert scene.choices == {"request_a": ("good", "tight")}
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
        assert scene._metric_choice == "good"
        assert scene._threshold_choice == "tight"
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
        scene.buttons.buttons[1].on_activate()  # request_b metric: noisy
        scene.buttons.buttons[3].on_activate()  # request_b threshold: balanced

        scene.next_button.on_activate()

        assert collected == [{"request_a": ("good", "tight"), "request_b": ("noisy", "balanced")}]
    finally:
        pygame.quit()


def test_the_live_preview_reflects_the_injected_simulation():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # metric: good
        scene.buttons.buttons[2].on_activate()  # threshold: tight

        request = scene._current_request()
        metric = scene._selected_metric(request)
        threshold = scene._selected_threshold(request)
        result = _simulate(DATASET, metric, threshold, request.target_incident_day)

        assert result == (0, True)  # "good" metric's day-3 spike is the real incident, no other days flagged
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_with_or_without_a_full_choice():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # no choice yet - the "pick both" placeholder path
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # only metric chosen
            scene.buttons.buttons[2].on_activate()
            scene.draw(app.logical_surface)  # both chosen - the live result path
    finally:
        pygame.quit()


def test_initial_choices_seeds_the_starting_state():
    app = _init_app()
    try:
        scene = _make_scene(app, initial_choices={"request_a": ("good", "tight")})
        assert scene.choices == {"request_a": ("good", "tight")}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_a_request_records_only_an_action_never_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(
            app,
            context=context,
            mirror_python_code_for=lambda metric, threshold, target_day, var_name: f"{var_name} = '{metric.key}:{threshold.key}:{target_day}'",
        )
        scene.buttons.buttons[0].on_activate()  # metric: good
        scene.buttons.buttons[2].on_activate()  # threshold: tight
        scene.next_button.on_activate()

        assert len(context.actions) == 1
        action = context.actions[0]
        assert action.key == "alert_pick_request_a"
        assert action.python_code == "request_a_alert = 'good:tight:3'"
        assert len(context.evidence) == 0
    finally:
        pygame.quit()


def test_revisiting_a_request_after_back_updates_the_same_action_in_place():
    """The exact scenario that motivates action-only (never Evidence)
    recording: pick, advance, come back, flip to a different combo,
    advance again - the Python Mirror must reflect only the real, final
    pick, never a stale first one."""
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(
            app,
            context=context,
            mirror_python_code_for=lambda metric, threshold, target_day, var_name: f"{var_name} = '{metric.key}:{threshold.key}'",
        )
        scene.buttons.buttons[0].on_activate()  # metric: good
        scene.buttons.buttons[2].on_activate()  # threshold: tight
        scene.next_button.on_activate()
        scene.back_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # metric: noisy
        scene.buttons.buttons[3].on_activate()  # threshold: balanced
        scene.next_button.on_activate()

        assert len(context.actions) == 1  # updated in place, never doubled
        assert context.actions[0].python_code == "request_a_alert = 'noisy:balanced'"
    finally:
        pygame.quit()


def test_no_context_or_no_mirror_callback_records_nothing():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context)  # no mirror_python_code_for
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[2].on_activate()
        scene.next_button.on_activate()
        assert len(context.actions) == 0
    finally:
        pygame.quit()

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.brief import BriefOption
from data_science_arcade.ui.experiment_monitor_scene import ExperimentCheckpoint, ExperimentMetricRow, ExperimentMonitorScene
from data_science_arcade.workbench.context import LessonContext

RECOMMENDATION_OPTIONS = (
    BriefOption("ship_now", "app.title"),
    BriefOption("hold_keep_running", "common.back"),
    BriefOption("not_sure_yet", "dialogue.continue_hint"),
)


def _row(*, warn: bool = False, threshold_cleared: bool = False, evidence_key: str | None = None) -> ExperimentMetricRow:
    return ExperimentMetricRow(
        label_key="app.title",
        control_rate=0.24,
        treatment_rate=0.26,
        diff=0.02,
        ci_lower=0.005,
        ci_upper=0.035,
        threshold_cleared=threshold_cleared,
        warn=warn,
        status_label_key="app.title",
        evidence_key=evidence_key,
    )


def _checkpoint(week: int, is_final: bool, *, rows=None, evidence_key: str | None = None) -> ExperimentCheckpoint:
    return ExperimentCheckpoint(
        week=week,
        is_final=is_final,
        rows=rows if rows is not None else (_row(evidence_key=evidence_key),),
        mirror_action_label_key="app.title",
        mirror_python_code=f"week{week}_x = 1",
        record_key=f"week{week}_checkpoint_read",
        recommendation_record_key=None if is_final else f"week{week}_recommendation",
    )


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, checkpoints, context=None, on_complete=lambda recs: None):
    return ExperimentMonitorScene(
        app,
        title_key="app.title",
        checkpoints=checkpoints,
        total_planned_weeks=7,
        context=context if context is not None else LessonContext(),
        on_complete=on_complete,
        recommendation_prompt_key="app.title",
        recommendation_options=RECOMMENDATION_OPTIONS,
        recommendation_action_label_key="app.title",
        final_continue_label_key="app.title",
    )


def test_continue_is_disabled_until_a_recommendation_is_picked_on_a_non_final_checkpoint():
    app = _init_app()
    try:
        scene = _make_scene(app, (_checkpoint(1, is_final=False), _checkpoint(7, is_final=True)))
        assert scene.continue_button.enabled is False

        scene.buttons.buttons[0].on_activate()

        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_final_checkpoint_has_no_recommendation_widget_and_continue_is_always_enabled():
    app = _init_app()
    try:
        scene = _make_scene(app, (_checkpoint(7, is_final=True),))
        # Only the Continue button exists - no recommendation options.
        assert len(scene.buttons.buttons) == 1
        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_a_recommendation_choice_never_branches_flow_every_checkpoint_is_still_visited():
    app = _init_app()
    try:
        checkpoints = (_checkpoint(1, is_final=False), _checkpoint(3, is_final=False), _checkpoint(7, is_final=True))
        completions = []
        scene = _make_scene(app, checkpoints, on_complete=lambda recs: completions.append(recs))

        assert scene._current_checkpoint().week == 1
        scene.buttons.buttons[0].on_activate()  # "ship now" - even the most premature choice
        scene.continue_button.on_activate()

        assert scene._current_checkpoint().week == 3
        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()

        assert scene._current_checkpoint().week == 7
        scene.continue_button.on_activate()

        assert completions == [{1: "ship_now", 3: "ship_now"}]
    finally:
        pygame.quit()


def test_recommendation_is_recorded_as_an_action_never_as_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        checkpoints = (_checkpoint(1, is_final=False), _checkpoint(7, is_final=True))
        scene = _make_scene(app, checkpoints, context=context)

        scene.buttons.buttons[1].on_activate()  # "hold_keep_running"
        scene.continue_button.on_activate()

        assert any(action.key == "week1_recommendation" for action in context.actions)
        assert all(item.key != "week1_recommendation" for item in context.evidence)
    finally:
        pygame.quit()


def test_only_rows_with_an_evidence_key_record_evidence_at_continue():
    app = _init_app()
    try:
        context = LessonContext()
        rows = (_row(evidence_key="lesson.test.evidence_a"), _row(evidence_key=None))
        checkpoints = (_checkpoint(7, is_final=True, rows=rows),)
        scene = _make_scene(app, checkpoints, context=context)

        scene.continue_button.on_activate()

        evidence_keys = {item.key for item in context.evidence}
        assert "lesson.test.evidence_a" in evidence_keys
        assert len(context.evidence) == 1
    finally:
        pygame.quit()


def test_mirror_python_code_is_recorded_for_every_checkpoint_visited():
    app = _init_app()
    try:
        context = LessonContext()
        checkpoints = (_checkpoint(1, is_final=False), _checkpoint(3, is_final=False), _checkpoint(7, is_final=True))
        scene = _make_scene(app, checkpoints, context=context)

        for _ in range(2):
            scene.buttons.buttons[0].on_activate()
            scene.continue_button.on_activate()
        scene.continue_button.on_activate()

        mirror = context.python_mirror()
        assert "week1_x = 1" in mirror
        assert "week3_x = 1" in mirror
        assert "week7_x = 1" in mirror
    finally:
        pygame.quit()

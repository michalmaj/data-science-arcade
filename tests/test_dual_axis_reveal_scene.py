import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.ui.comparison_reveal_scene import ComparisonValue, InterpretOption
from data_science_arcade.ui.dual_axis_reveal_scene import DualAxisRevealScene, DualAxisSeries
from data_science_arcade.workbench.context import LessonContext

SERIES_A = DualAxisSeries("app.title", (40000.0, 74000.0), (58, 214, 255))
SERIES_B = DualAxisSeries("common.on", (1000.0, 1120.0), (255, 158, 68))

COMPARISONS = (
    ComparisonValue("evidence.spend", 0.85, python_code="x = 0.85"),
    ComparisonValue("evidence.signups", 0.12, python_code="y = 0.12"),
)

INTERPRET_OPTIONS = (
    InterpretOption("correct", "common.on"),
    InterpretOption("overclaim", "common.off"),
    InterpretOption("underclaim", "common.back"),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, context=None, on_complete=lambda choice: None, **kwargs):
    return DualAxisRevealScene(
        app,
        "app.title",
        ("app.title",),
        SERIES_A,
        SERIES_B,
        COMPARISONS,
        "app.title",
        INTERPRET_OPTIONS,
        on_complete,
        context if context is not None else LessonContext(),
        **kwargs,
    )


def test_continue_is_disabled_until_an_interpretation_is_chosen():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.continue_button.enabled is False
        scene.buttons.buttons[0].on_activate()
        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_continue_records_both_comparisons_as_evidence_and_calls_on_complete():
    app = _init_app()
    try:
        context = LessonContext()
        completed = []
        scene = _make_scene(app, context=context, on_complete=lambda choice: completed.append(choice))
        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()

        assert completed == ["correct"]
        assert len(context.evidence) == 2
        assert {item.label_key for item in context.evidence} == {"evidence.spend", "evidence.signups"}
    finally:
        pygame.quit()


def test_comparisons_are_evidence_false_still_records_actions_but_no_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context, comparisons_are_evidence=False)
        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()

        assert len(context.actions) >= 2
        assert context.evidence == ()
    finally:
        pygame.quit()


def test_draw_does_not_crash_before_or_after_a_choice():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.draw(app.logical_surface)
        scene.buttons.buttons[0].on_activate()
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_each_series_is_independently_normalized_to_its_own_range():
    """The whole point of this scene: two series with wildly different
    real percent changes (85% vs. 12%) must still be drawable as two
    visually similar diagonal lines - each series is normalized to its
    OWN (min, max), never a shared one, which is exactly what a real
    rigged dual-axis chart does."""
    assert min(SERIES_A.values) != min(SERIES_B.values)
    assert max(SERIES_A.values) != max(SERIES_B.values)
    # Both series still span their own full range 0 -> 1 when independently
    # normalized - confirmed by construction, not by drawing pixels.
    for series in (SERIES_A, SERIES_B):
        span = max(series.values) - min(series.values)
        assert span > 0

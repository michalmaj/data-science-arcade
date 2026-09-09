import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.core.fonts import get_font
from data_science_arcade.localization.service import SUPPORTED_LOCALES, Localization
from data_science_arcade.ui.button import BUTTON_TEXT_SIZE
from data_science_arcade.ui.comparison_reveal_scene import InterpretOption
from data_science_arcade.ui.distribution_explorer_scene import MARKER_BUTTON_SIZE, DistributionExplorerScene, DistributionMarker
from data_science_arcade.workbench.context import LessonContext

VALUES = [1.0, 2.0, 3.0, 4.0, 30.0]

MARKERS = (
    DistributionMarker("mean", "app.title", 8.0, python_code="orders['x'].mean()"),
    DistributionMarker("median", "common.on", 3.0, python_code="orders['x'].median()"),
)

INTERPRET_OPTIONS = (
    InterpretOption("right", "common.on", evidence_key="evidence.example"),
    InterpretOption("wrong", "common.off"),
)

SEGMENT_SERIES = (
    ("a", "app.title", [1.0, 2.0, 3.0]),
    ("b", "common.on", [30.0, 31.0]),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, context=None, on_complete=lambda choice: None, **kwargs):
    return DistributionExplorerScene(
        app, "app.title", VALUES, MARKERS, on_complete, context or LessonContext(), **kwargs
    )


def test_no_markers_active_and_continue_enabled_when_no_interpret_step_is_configured():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.active_markers == set()
        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_continue_is_disabled_until_an_interpretation_is_chosen():
    app = _init_app()
    try:
        scene = _make_scene(app, interpret_prompt_key="app.title", interpret_options=INTERPRET_OPTIONS)
        assert scene.continue_button.enabled is False
        scene.interpret_buttons["right"].on_activate()
        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_toggling_a_marker_shows_its_live_value_and_toggling_again_hides_it():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.marker_buttons["mean"].on_activate()
        assert scene.active_markers == {"mean"}
        assert "8.00" in scene.marker_buttons["mean"].label

        scene.marker_buttons["mean"].on_activate()
        assert scene.active_markers == set()
    finally:
        pygame.quit()


def test_toggling_markers_never_records_an_action_or_evidence_on_its_own():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context)
        scene.marker_buttons["mean"].on_activate()
        scene.marker_buttons["median"].on_activate()
        scene.marker_buttons["mean"].on_activate()  # off again
        assert context.actions == ()
        assert context.evidence == ()
    finally:
        pygame.quit()


def test_continue_without_interpret_records_the_toggled_markers_python_code_once():
    app = _init_app()
    try:
        context = LessonContext()
        completed = []
        scene = _make_scene(app, context=context, on_complete=lambda choice: completed.append(choice))
        scene.marker_buttons["mean"].on_activate()
        scene.continue_button.on_activate()

        assert completed == [None]
        assert len(context.actions) == 1
        assert context.actions[0].python_code == "orders['x'].mean()"
        assert context.evidence == ()
    finally:
        pygame.quit()


def test_continue_with_no_active_markers_and_no_interpret_records_nothing():
    app = _init_app()
    try:
        context = LessonContext()
        completed = []
        scene = _make_scene(app, context=context, on_complete=lambda choice: completed.append(choice))
        scene.continue_button.on_activate()

        assert completed == [None]
        assert context.actions == ()
    finally:
        pygame.quit()


def test_choosing_the_evidence_bearing_interpretation_records_exactly_one_evidence_item():
    app = _init_app()
    try:
        context = LessonContext()
        completed = []
        scene = _make_scene(
            app,
            context=context,
            on_complete=lambda choice: completed.append(choice),
            interpret_prompt_key="app.title",
            interpret_options=INTERPRET_OPTIONS,
        )
        scene.marker_buttons["median"].on_activate()
        scene.interpret_buttons["right"].on_activate()
        scene.continue_button.on_activate()

        assert completed == ["right"]
        assert len(context.actions) == 1
        assert context.actions[0].python_code == "orders['x'].median()"
        assert len(context.evidence) == 1
        assert context.evidence[0].label_key == "evidence.example"
    finally:
        pygame.quit()


def test_choosing_a_non_evidence_interpretation_records_no_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(
            app, context=context, interpret_prompt_key="app.title", interpret_options=INTERPRET_OPTIONS
        )
        scene.interpret_buttons["wrong"].on_activate()
        scene.continue_button.on_activate()
        assert context.evidence == ()
        assert len(context.actions) == 1
    finally:
        pygame.quit()


def test_segment_series_draws_without_a_plain_histogram_and_does_not_crash():
    app = _init_app()
    try:
        scene = DistributionExplorerScene(
            app, "app.title", VALUES, (), lambda choice: None, LessonContext(), segment_series=SEGMENT_SERIES
        )
        assert scene.continue_button.enabled is True
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


# --- Regression: the real toggled-on label (translated name + live value
# suffix) must fit the button, in both locales - not just the untoggled
# bare name. A screenshot first caught this: PL's "Średnia konsumencka:
# $49.00" (235px) didn't fit MARKER_BUTTON_SIZE's old 230px width at all,
# independent of and worse than the indicator-bar-over-text collision
# that screenshot also caught. See distribution_explorer_scene.py's own
# MARKER_BUTTON_SIZE docstring.
BUTTON_PADDING = 40
L11_REAL_MARKER_LABELS_WITH_VALUES = (
    ("lesson.l11.marker.mean_label", 256.80),
    ("lesson.l11.marker.median_label", 60.00),
    ("lesson.l11.segment.consumer_mean_label", 49.00),
    ("lesson.l11.segment.business_mean_label", 741.67),
)


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
@pytest.mark.parametrize("label_key,value", L11_REAL_MARKER_LABELS_WITH_VALUES)
def test_a_real_toggled_marker_label_fits_within_its_button(locale, label_key, value):
    app = _init_app()
    try:
        loc = Localization(locale=locale)
        text = f"{loc.t(label_key)}: ${value:,.2f}"
        font = get_font(BUTTON_TEXT_SIZE)
        width, _height = font.size(text)
        max_width = MARKER_BUTTON_SIZE[0] - BUTTON_PADDING
        assert width <= max_width, f"{locale}/{label_key} toggled label is {width}px wide, button only fits {max_width}px: {text!r}"
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_with_or_without_interpret_options():
    app = _init_app()
    try:
        for guided in (True, False):
            for interpret_options in ((), INTERPRET_OPTIONS):
                scene = _make_scene(
                    app,
                    guided=guided,
                    interpret_prompt_key="app.title" if interpret_options else None,
                    interpret_options=interpret_options,
                    interpret_hint_key="common.back" if interpret_options else None,
                )
                scene.draw(app.logical_surface)
    finally:
        pygame.quit()

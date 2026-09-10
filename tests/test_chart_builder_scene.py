import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.ui.chart_builder_scene import ChartBuilderScene, ChartFormOption
from data_science_arcade.workbench.context import LessonContext

BAR_OPTIONS = (
    ChartFormOption("bar_a", "lesson.l14.builder.stores.option.bar_natural_order", "bar", "store_id vs return rate", labels=("S01", "S02"), values=(15.0, 8.0)),
    ChartFormOption("line_a", "lesson.l14.builder.stores.option.line", "line", "store_id vs return rate", labels=("S01", "S02"), values=(15.0, 8.0)),
)

HISTOGRAM_260_OPTION = ChartFormOption(
    "histogram",
    "lesson.l14.builder.distribution.option.histogram",
    "histogram",
    "delivery_minutes frequency",
    raw_values=tuple(float(20 + (i % 55)) for i in range(260)),
    bin_edges=(15, 30, 45, 60, 75, 90),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _surface() -> pygame.Surface:
    return pygame.Surface(LOGICAL_SIZE)


def test_picking_an_option_enables_continue_and_records_a_mirror_comment():
    app = _init_app()
    try:
        context = LessonContext()
        completed = []
        scene = ChartBuilderScene(
            app, "lesson.l14.builder.stores.title", "lesson.l14.builder.stores.ask", BAR_OPTIONS, completed.append, context
        )
        assert scene.continue_button.enabled is False
        scene.buttons.buttons[0].on_activate()
        assert scene.choice == "bar_a"
        assert scene.continue_button.enabled is True
        scene.continue_button.on_activate()
        assert completed == ["bar_a"]
        assert len(context.actions) == 1
        assert context.actions[0].python_code == "# Visualization intent: bar chart - store_id vs return rate"
    finally:
        pygame.quit()


def test_bar_and_line_forms_render_without_error():
    app = _init_app()
    try:
        context = LessonContext()
        scene = ChartBuilderScene(
            app, "lesson.l14.builder.stores.title", "lesson.l14.builder.stores.ask", BAR_OPTIONS, lambda c: None, context
        )
        surface = _surface()
        scene.draw(surface)  # no selection yet
        scene.buttons.buttons[0].on_activate()
        scene.draw(surface)
        scene.buttons.buttons[1].on_activate()
        scene.draw(surface)
    finally:
        pygame.quit()


def test_histogram_at_the_full_real_260_row_scale_renders_without_overflow():
    # Guardrail: no chart form here may ever need one label per raw
    # observation - the distribution ask's histogram option is the one
    # place raw_values legitimately reaches the full real population
    # size, and it must render safely (fixed bins, not per-row labels).
    app = _init_app()
    try:
        context = LessonContext()
        scene = ChartBuilderScene(
            app,
            "lesson.l14.builder.distribution.title",
            "lesson.l14.builder.distribution.ask",
            (HISTOGRAM_260_OPTION,),
            lambda c: None,
            context,
        )
        scene.buttons.buttons[0].on_activate()
        surface = _surface()
        scene.draw(surface)  # must not raise/crash at full 260-row scale
    finally:
        pygame.quit()


def test_initial_choice_seeds_a_resumed_revision_instance():
    app = _init_app()
    try:
        context = LessonContext()
        scene = ChartBuilderScene(
            app,
            "lesson.l14.builder.stores.title",
            "lesson.l14.builder.stores.ask",
            BAR_OPTIONS,
            lambda c: None,
            context,
            initial_choice="line_a",
        )
        assert scene.choice == "line_a"
        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_chart_form_option_has_no_scale_or_window_or_denominator_field():
    # Structural guardrail: ChartFormOption must stay incapable of the
    # axis-truncation / cherry-picked-window / wrong-denominator moves
    # reserved for L28's own ChartDesignerScene/ChartOption.
    field_names = {f.name for f in ChartFormOption.__dataclass_fields__.values()}
    assert "scale" not in field_names
    assert "min_value" not in field_names
    assert "window" not in field_names
    assert "denominator" not in field_names

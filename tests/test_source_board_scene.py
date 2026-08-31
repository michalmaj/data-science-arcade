import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.source import DataSource, SourceAttribute
from data_science_arcade.ui.source_board_scene import SourceBoardScene
from data_science_arcade.workbench.context import LessonContext

SOURCES = (
    DataSource(
        key="fast",
        name_key="common.back",  # any real key works - content isn't under test here
        attributes=(SourceAttribute("common.back", "common.on"),),
    ),
    DataSource(
        key="complete",
        name_key="common.back",
        attributes=(SourceAttribute("common.back", "common.off"),),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_starts_with_nothing_selected_and_confirm_disabled():
    app = _init_app()
    try:
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None)
        assert scene.selected_key is None
        assert scene.confirm_button.enabled is False
    finally:
        pygame.quit()


def test_selecting_a_source_enables_confirm():
    app = _init_app()
    try:
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None)
        scene.source_buttons["fast"].on_activate()
        assert scene.selected_key == "fast"
        assert scene.confirm_button.enabled is True
    finally:
        pygame.quit()


def test_confirm_does_nothing_until_something_is_selected():
    app = _init_app()
    try:
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None)
        scene._confirm()  # must not raise, must not call on_complete
    finally:
        pygame.quit()


def test_confirm_calls_on_complete_with_the_selected_key():
    app = _init_app()
    try:
        collected = []
        scene = SourceBoardScene(
            app, "app.title", "app.title", SOURCES, on_complete=lambda key: collected.append(key)
        )
        scene.source_buttons["complete"].on_activate()

        scene.confirm_button.on_activate()

        assert collected == ["complete"]
    finally:
        pygame.quit()


def test_switching_the_selection_before_confirming_keeps_only_the_latest_choice():
    app = _init_app()
    try:
        collected = []
        scene = SourceBoardScene(
            app, "app.title", "app.title", SOURCES, on_complete=lambda key: collected.append(key)
        )
        scene.source_buttons["fast"].on_activate()
        scene.source_buttons["complete"].on_activate()

        scene.confirm_button.on_activate()

        assert collected == ["complete"]
    finally:
        pygame.quit()


def test_with_no_context_given_a_fresh_one_is_created():
    app = _init_app()
    try:
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None)
        assert isinstance(scene.context, LessonContext)
        assert scene.context.actions == ()
    finally:
        pygame.quit()


def test_confirming_records_the_pick_as_a_real_action_never_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None, context=context)
        scene.source_buttons["complete"].on_activate()

        scene.confirm_button.on_activate()

        assert len(context.actions) == 1
        assert context.actions[0].label_key == "common.back"  # SOURCES's "complete" source's own name_key
        assert context.actions[0].python_code is None
        assert context.evidence == ()
    finally:
        pygame.quit()


def test_switching_the_selection_before_confirming_records_only_the_final_pick():
    app = _init_app()
    try:
        context = LessonContext()
        scene = SourceBoardScene(app, "app.title", "app.title", SOURCES, on_complete=lambda key: None, context=context)
        scene.source_buttons["fast"].on_activate()
        scene.source_buttons["complete"].on_activate()

        scene.confirm_button.on_activate()

        assert len(context.actions) == 1  # key="source_board_pick" upserts, not appends
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_with_or_without_a_selection():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = SourceBoardScene(
                app,
                "app.title",
                "app.title",
                SOURCES,
                on_complete=lambda key: None,
                guided=guided,
                hint_key="common.back",
            )
            scene.draw(app.logical_surface)
            scene.source_buttons["fast"].on_activate()
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_a_long_attribute_row_grows_taller_than_a_short_one_instead_of_truncating():
    # The original High/Medium/Low tags never needed more than one short
    # word, so this board's row stepping was never validated against real
    # sentence-length fact text - L02's real content ("'Active' means:
    # opened the app in 30 days") overflowed WIDE_COLUMN_WIDTH and
    # rendered as a truncated ellipsis (draw_single_line's own behavior),
    # caught only by a real screenshot. _draw_attributes now wraps instead
    # (draw_wrapped_text), so a row with real long text must actually
    # consume more vertical space than a row that fits on one line -
    # proof the fix is really wrapping, not just failing to crash.
    app = _init_app()
    try:
        short_sources = tuple(
            DataSource(key=f"s{i}", name_key="common.back", attributes=(SourceAttribute("common.back", "common.on"),))
            for i in range(4)  # >3 sources triggers WIDE_COLUMN_WIDTH (150px)
        )
        long_sources = tuple(
            DataSource(
                key=f"s{i}", name_key="common.back", attributes=(SourceAttribute("common.back", "dialogue.continue_hint"),)
            )
            for i in range(4)
        )
        short_scene = SourceBoardScene(app, "app.title", "app.title", short_sources, on_complete=lambda key: None)
        long_scene = SourceBoardScene(app, "app.title", "app.title", long_sources, on_complete=lambda key: None)

        from data_science_arcade.core.fonts import get_font
        from data_science_arcade.ui.source_board_scene import ATTRIBUTE_TEXT_SIZE
        from data_science_arcade.ui.text import wrap_text

        font = get_font(ATTRIBUTE_TEXT_SIZE)
        short_text = f"{app.localization.t('common.back')}: {app.localization.t('common.on')}"
        long_text = f"{app.localization.t('common.back')}: {app.localization.t('dialogue.continue_hint')}"
        assert len(wrap_text(long_text, font, long_scene._column_width())) > len(
            wrap_text(short_text, font, short_scene._column_width())
        )
        short_scene.draw(app.logical_surface)
        long_scene.draw(app.logical_surface)  # must not raise either
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_three_sources_and_several_attributes():
    app = _init_app()
    try:
        three_sources = tuple(
            DataSource(
                key=f"source_{i}",
                name_key="common.back",
                attributes=tuple(SourceAttribute("common.back", "common.on") for _ in range(5)),
            )
            for i in range(3)
        )
        scene = SourceBoardScene(app, "app.title", "app.title", three_sources, on_complete=lambda key: None)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()

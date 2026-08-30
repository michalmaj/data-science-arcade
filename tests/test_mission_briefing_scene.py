import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.ui.mission_briefing_scene import MissionBriefingScene

DEFINITION = LessonDefinition(
    id="fake",
    chapter=1,
    number=1,
    title_key="app.title",
    objective_keys=("common.back", "common.on"),
    scoring_dimensions=(ScoreDimension.REASONING,),
    estimated_minutes=15,
)

LONG_OBJECTIVE_DEFINITION = LessonDefinition(
    id="fake_long",
    chapter=1,
    number=2,
    title_key="app.title",
    objective_keys=(
        "lesson.l30.objective1",  # a genuinely long real sentence, likely to wrap
        "lesson.l30.objective2",
        "lesson.l30.objective3",
    ),
    scoring_dimensions=(ScoreDimension.REASONING,),
    estimated_minutes=25,
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_start_mission_calls_on_start():
    app = _init_app()
    try:
        calls = []
        scene = MissionBriefingScene(app, DEFINITION, on_start=lambda: calls.append("started"))

        scene.buttons.buttons[0].on_activate()

        assert calls == ["started"]
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_short_objectives():
    app = _init_app()
    try:
        scene = MissionBriefingScene(app, DEFINITION, on_start=lambda: None)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_long_wrapping_objectives():
    app = _init_app()
    try:
        scene = MissionBriefingScene(app, LONG_OBJECTIVE_DEFINITION, on_start=lambda: None)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_a_long_objective_actually_wraps_to_more_than_one_line_at_this_width():
    # Doesn't depend on any specific lesson's real (and changeable)
    # translated text length - a hand-built long string, at the exact
    # constants the scene itself uses, confirms wrapping past one line is
    # actually reachable, so the "draw doesn't crash" tests above are
    # exercising real multi-line layout rather than always taking the
    # trivial single-line path.
    app = _init_app()
    try:
        from data_science_arcade.core.fonts import get_font
        from data_science_arcade.ui.mission_briefing_scene import OBJECTIVE_FONT_SIZE, OBJECTIVE_MAX_WIDTH
        from data_science_arcade.ui.text import wrap_text

        font = get_font(OBJECTIVE_FONT_SIZE)
        long_text = "- " + " ".join(["word"] * 40)

        assert len(wrap_text(long_text, font, OBJECTIVE_MAX_WIDTH)) > 1
    finally:
        pygame.quit()

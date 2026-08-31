import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.ui.handbook_scene import HandbookScene
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

WITH_HANDBOOK_LINK_DEFINITION = LessonDefinition(
    id="fake_with_handbook_link",
    chapter=1,
    number=3,
    title_key="app.title",
    objective_keys=("common.back",),
    scoring_dimensions=(ScoreDimension.REASONING,),
    estimated_minutes=15,
    related_handbook_entry_id="asking_an_analytical_question",
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


def test_no_learn_more_button_when_no_handbook_entry_is_related():
    app = _init_app()
    try:
        scene = MissionBriefingScene(app, DEFINITION, on_start=lambda: None)
        assert len(scene.buttons.buttons) == 1  # Start Mission only - the 29 lessons without a link are unaffected
    finally:
        pygame.quit()


def test_learn_more_button_appears_and_pushes_the_handbook_scene_on_the_right_entry():
    app = _init_app()
    try:
        scene = MissionBriefingScene(app, WITH_HANDBOOK_LINK_DEFINITION, on_start=lambda: None)
        app.scenes.push(scene)
        assert len(scene.buttons.buttons) == 2

        scene.buttons.buttons[1].on_activate()

        assert isinstance(app.scenes.current, HandbookScene)
        assert app.scenes.current.selected_article_id == "asking_an_analytical_question"
    finally:
        pygame.quit()


def test_the_required_seam_popping_back_from_the_handbook_leaves_the_briefing_still_functional():
    # The one required contextual-link proof-of-concept, exercised as a
    # real round trip: Learn More -> HandbookScene -> pop back -> the
    # underlying MissionBriefingScene must still work, not just still exist.
    app = _init_app()
    try:
        calls = []
        scene = MissionBriefingScene(app, WITH_HANDBOOK_LINK_DEFINITION, on_start=lambda: calls.append("started"))
        app.scenes.push(scene)

        scene.buttons.buttons[1].on_activate()  # Learn More
        assert isinstance(app.scenes.current, HandbookScene)

        app.scenes.pop()  # back out of the Handbook

        assert app.scenes.current is scene
        scene.buttons.buttons[0].on_activate()  # Start Mission still works
        assert calls == ["started"]
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

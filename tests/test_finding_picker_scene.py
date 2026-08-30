import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.findings import Finding
from data_science_arcade.ui.finding_picker_scene import FindingPickerScene
from data_science_arcade.workbench.context import LessonContext

FINDINGS = (
    Finding("a", "common.on"),
    Finding("b", "common.off"),
    Finding("c", "common.back"),
    Finding("d", "app.title"),
)

FINDINGS_WITH_CODE = (
    Finding("a", "common.on", python_code="x = 1"),
    Finding("b", "common.off", python_code="y = 2"),
    Finding("c", "common.back"),
    Finding("d", "app.title"),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return FindingPickerScene(app, "app.title", "app.title", FINDINGS, target_count=3, on_complete=on_complete, **kwargs)


def test_starts_with_the_full_pool_and_no_picks():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.picked == []
        assert len(scene.buttons.buttons) == len(FINDINGS)
    finally:
        pygame.quit()


def test_picking_a_finding_removes_it_from_the_remaining_pool():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # "a"

        assert scene.picked == ["a"]
        assert scene._remaining_findings() == FINDINGS[1:]
        assert len(scene.buttons.buttons) == len(FINDINGS) - 1
    finally:
        pygame.quit()


def test_picking_does_not_call_on_complete_before_the_target_count_is_reached():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[0].on_activate()  # now picks the pool's new index-0 (was index 1)

        assert collected == []
        assert len(scene.picked) == 2
    finally:
        pygame.quit()


def test_on_complete_fires_automatically_once_target_count_is_reached():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()  # "a"
        scene.buttons.buttons[0].on_activate()  # "b" (shifted to index 0)
        scene.buttons.buttons[0].on_activate()  # "c" (shifted to index 0)

        assert collected == [("a", "b", "c")]
    finally:
        pygame.quit()


def test_there_is_no_back_button_since_picks_are_final():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert not hasattr(scene, "back_button")
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_a_pick():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided, hint_key="common.back")
            scene.draw(app.logical_surface)  # no picks yet - no "picked so far" line
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # one pick - "picked so far" line shows
    finally:
        pygame.quit()


def test_with_no_context_given_a_fresh_one_is_created():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert isinstance(scene.context, LessonContext)
        assert scene.context.actions == ()
    finally:
        pygame.quit()


def test_picking_a_finding_records_a_real_action_and_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        scene = FindingPickerScene(app, "app.title", "app.title", FINDINGS_WITH_CODE, target_count=3, on_complete=lambda choices: None, context=context)

        scene.buttons.buttons[0].on_activate()  # picks "a"

        assert len(context.actions) == 1
        action = context.actions[0]
        assert action.label_key == "common.on"  # Finding("a", ...)'s own label_key
        assert action.python_code == "x = 1"
        assert len(context.evidence) == 1
        assert context.evidence[0].source_action_id == action.id
    finally:
        pygame.quit()


def test_a_finding_with_no_python_code_still_records_evidence_with_none_code():
    app = _init_app()
    try:
        context = LessonContext()
        scene = FindingPickerScene(app, "app.title", "app.title", FINDINGS_WITH_CODE, target_count=3, on_complete=lambda choices: None, context=context)

        for _ in range(3):
            scene.buttons.buttons[0].on_activate()  # "a", then "b" (shifted to index 0), then "c"

        assert len(context.actions) == 3
        assert len(context.evidence) == 3
        assert context.python_mirror() == "x = 1\ny = 2"  # "c" contributed no code, so it's skipped, not blank
    finally:
        pygame.quit()


def test_lesson_29s_own_usage_pattern_is_unaffected_without_a_context():
    # Mirrors exactly how l29_the_executive_brief/scenario.py constructs
    # this scene today - no context kwarg at all - confirming the new
    # param is fully backward compatible with the one real lesson using it.
    app = _init_app()
    try:
        collected = []
        scene = FindingPickerScene(app, "app.title", "app.title", FINDINGS_WITH_CODE, target_count=3, on_complete=lambda choices: collected.append(choices), guided=True, hint_key="common.back")

        for _ in range(3):
            scene.buttons.buttons[0].on_activate()

        assert collected == [("a", "b", "c")]
    finally:
        pygame.quit()

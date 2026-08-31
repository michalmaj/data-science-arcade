import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, InterpretOption
from data_science_arcade.workbench.context import LessonContext

OPTIONS = (
    InterpretOption("higher_recent", "app.title"),
    InterpretOption("lower_recent", "app.title"),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choice: None, context=None, **kwargs):
    return ComparisonRevealScene(
        app,
        title_key="app.title",
        narrative_keys=("app.title",),
        comparisons=(("common.back", 0.3), ("dialogue.continue_hint", 0.5)),  # 2 distinct keys - see dedup note below
        interpret_prompt_key="app.title",
        interpret_options=OPTIONS,
        on_complete=on_complete,
        context=context if context is not None else LessonContext(),
        **kwargs,
    )


def test_continue_is_disabled_until_an_interpretation_is_picked():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.continue_button.enabled is False

        scene.buttons.buttons[0].on_activate()

        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_continue_does_nothing_if_nothing_is_picked():
    app = _init_app()
    try:
        calls = []
        scene = _make_scene(app, on_complete=lambda choice: calls.append(choice))

        scene._continue()

        assert calls == []
    finally:
        pygame.quit()


def test_continue_fires_on_complete_with_the_chosen_key():
    app = _init_app()
    try:
        calls = []
        scene = _make_scene(app, on_complete=lambda choice: calls.append(choice))

        scene.buttons.buttons[1].on_activate()
        scene.continue_button.on_activate()

        assert calls == ["lower_recent"]
    finally:
        pygame.quit()


def test_continue_records_both_comparisons_as_real_evidence_with_the_formatted_value():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context)

        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()

        assert len(context.evidence) == 2
        assert context.evidence[0].detail == "30%"
        assert context.evidence[1].detail == "50%"
        assert context.evidence[0].source_action_id is not None
    finally:
        pygame.quit()


def test_continue_also_records_the_interpretation_itself_as_an_action():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context)

        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()

        assert len(context.actions) == 3  # 2 comparisons + 1 interpretation
    finally:
        pygame.quit()


def test_two_comparisons_sharing_a_label_key_collapse_to_one_evidence_slot():
    # A real caller contract, not a corner case to guard against: since
    # record_evidence(key=label_key) dedupes by that key, the two
    # comparisons passed in a single call MUST use distinct label_keys or
    # they upsert each other - exactly the mechanism that makes recomputing
    # the *same* comparison across two scene instances collapse correctly
    # (see the next test), so it can't be special-cased away here.
    app = _init_app()
    try:
        context = LessonContext()
        scene = ComparisonRevealScene(
            app,
            title_key="app.title",
            narrative_keys=(),
            comparisons=(("common.back", 0.3), ("common.back", 0.5)),
            interpret_prompt_key="app.title",
            interpret_options=OPTIONS,
            on_complete=lambda choice: None,
            context=context,
        )

        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()

        assert len(context.evidence) == 1
        assert context.evidence[0].detail == "50%"  # the second call wins
    finally:
        pygame.quit()


def test_recomputing_the_same_comparisons_twice_updates_the_evidence_slot_instead_of_doubling_it():
    app = _init_app()
    try:
        context = LessonContext()
        first = _make_scene(app, context=context)
        first.buttons.buttons[0].on_activate()
        first.continue_button.on_activate()

        second = _make_scene(app, context=context)
        second.buttons.buttons[1].on_activate()
        second.continue_button.on_activate()

        assert len(context.evidence) == 2  # not 4 - same (label_key) keys upsert in place
    finally:
        pygame.quit()


def test_custom_value_format_is_used_for_both_display_and_recorded_detail():
    app = _init_app()
    try:
        context = LessonContext()
        scene = ComparisonRevealScene(
            app,
            title_key="app.title",
            narrative_keys=(),
            comparisons=(("common.back", 120.0), ("dialogue.continue_hint", 340.0)),
            interpret_prompt_key="app.title",
            interpret_options=OPTIONS,
            on_complete=lambda choice: None,
            context=context,
            value_format=lambda value: f"${value:,.0f}",
        )

        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()

        assert context.evidence[0].detail == "$120"
        assert context.evidence[1].detail == "$340"
    finally:
        pygame.quit()


def test_an_interpret_option_with_an_evidence_key_records_real_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        options = (
            InterpretOption("well_scoped", "app.title", evidence_key="lesson.l02.evidence.legacy_status_unresolved"),
            InterpretOption("its_a_bug", "app.title"),
        )
        scene = ComparisonRevealScene(
            app,
            title_key="app.title",
            narrative_keys=(),
            comparisons=(("common.back", 30.0), ("dialogue.continue_hint", 8.0)),
            interpret_prompt_key="app.title",
            interpret_options=options,
            on_complete=lambda choice: None,
            context=context,
        )
        scene.buttons.buttons[0].on_activate()  # well_scoped
        scene.continue_button.on_activate()

        assert len(context.evidence) == 3  # 2 comparisons + the interpretation's own evidence
        assert context.evidence[2].label_key == "lesson.l02.evidence.legacy_status_unresolved"
        assert context.evidence[2].source_action_id is not None
    finally:
        pygame.quit()


def test_an_interpret_option_without_an_evidence_key_records_no_extra_evidence():
    app = _init_app()
    try:
        context = LessonContext()
        options = (
            InterpretOption("well_scoped", "app.title", evidence_key="lesson.l02.evidence.legacy_status_unresolved"),
            InterpretOption("its_a_bug", "app.title"),
        )
        scene = ComparisonRevealScene(
            app,
            title_key="app.title",
            narrative_keys=(),
            comparisons=(("common.back", 30.0), ("dialogue.continue_hint", 8.0)),
            interpret_prompt_key="app.title",
            interpret_options=options,
            on_complete=lambda choice: None,
            context=context,
        )
        scene.buttons.buttons[1].on_activate()  # its_a_bug - no evidence_key
        scene.continue_button.on_activate()

        assert len(context.evidence) == 2  # only the 2 comparisons, no decoy evidence
    finally:
        pygame.quit()


def test_a_third_narrative_line_grows_the_box_instead_of_overflowing_it():
    # L01's real narrative_keys never exceeds 2 short lines, which is what
    # this scene's fixed BOX_RECT height was implicitly validated against
    # - L02 needed a real 3rd line and it rendered past the box's own
    # bottom border, overlapping the interpret prompt below, caught only
    # by a real screenshot with real 3-line content.
    app = _init_app()
    try:
        two_line_scene = _make_scene(app)
        three_line_scene = ComparisonRevealScene(
            app,
            title_key="app.title",
            narrative_keys=("app.title", "app.title", "app.title"),
            comparisons=(("common.back", 0.3), ("dialogue.continue_hint", 0.5)),
            interpret_prompt_key="app.title",
            interpret_options=OPTIONS,
            on_complete=lambda choice: None,
            context=LessonContext(),
        )

        assert three_line_scene._box_rect().height > two_line_scene._box_rect().height
        assert three_line_scene._first_option_y() > three_line_scene._box_rect().bottom
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_with_or_without_a_hint():
    app = _init_app()
    try:
        for guided in (True, False):
            for hint_key in (None, "app.title"):
                scene = _make_scene(app, guided=guided, interpret_hint_key=hint_key)
                scene.draw(app.logical_surface)
    finally:
        pygame.quit()

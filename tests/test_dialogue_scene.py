import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.narrative.dialogue import Dialogue, DialogueChoice, DialogueLine
from data_science_arcade.narrative.npc import MENTOR
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.workbench.context import LessonContext

TWO_LINE_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line2"),
    )
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_enter_advances_to_the_next_line():
    app = _init_app()
    try:
        scene = DialogueScene(app, TWO_LINE_DIALOGUE, on_complete=lambda: None)
        app.scenes.push(scene)

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))

        assert scene.index == 1
    finally:
        pygame.quit()


def test_advancing_past_the_last_line_runs_on_complete_without_touching_the_stack_itself():
    app = _init_app()
    try:
        hub_stand_in = app.scenes.current
        scene = DialogueScene(app, TWO_LINE_DIALOGUE, on_complete=app.scenes.pop)
        app.scenes.push(scene)

        scene._advance()  # line 0 -> 1
        scene._advance()  # line 1 -> past the end -> on_complete() -> app.scenes.pop()

        assert app.scenes.current is hub_stand_in
    finally:
        pygame.quit()


def test_on_complete_runs_exactly_once_when_the_dialogue_ends():
    app = _init_app()
    try:
        calls = []
        single_line = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line1"),))
        scene = DialogueScene(app, single_line, on_complete=lambda: calls.append("done"))
        app.scenes.push(scene)

        scene._advance()

        assert calls == ["done"]
    finally:
        pygame.quit()


def test_a_line_with_choices_ignores_clicks_that_are_not_on_a_choice():
    app = _init_app()
    try:
        branching = Dialogue(
            lines=(
                DialogueLine(
                    speaker=MENTOR,
                    text_key="dialogue.mentor_greeting.line1",
                    choices=(
                        DialogueChoice(label_key="common.back", next_index=1),
                        DialogueChoice(label_key="common.back", next_index=None),
                    ),
                ),
                DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line2"),
            )
        )
        scene = DialogueScene(app, branching, on_complete=lambda: None)
        app.scenes.push(scene)

        # Unlike a plain line, a click anywhere must NOT advance - only an
        # actual choice button should. (1, 1) is empty space (top-left
        # corner, nowhere near the choice buttons).
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

        assert scene.index == 0
        assert scene.choice_buttons is not None

        scene.choice_buttons.buttons[0].on_activate()

        assert scene.index == 1
        assert scene.choice_buttons is None  # line 1 has no choices
    finally:
        pygame.quit()


def test_enter_activates_the_keyboard_focused_choice():
    app = _init_app()
    try:
        branching = Dialogue(
            lines=(
                DialogueLine(
                    speaker=MENTOR,
                    text_key="dialogue.mentor_greeting.line1",
                    choices=(
                        DialogueChoice(label_key="common.back", next_index=1),
                        DialogueChoice(label_key="common.back", next_index=None),
                    ),
                ),
                DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line2"),
            )
        )
        scene = DialogueScene(app, branching, on_complete=lambda: None)
        app.scenes.push(scene)

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))

        assert scene.index == 1  # activated the first (focused-by-default) choice
    finally:
        pygame.quit()


def test_a_choice_with_next_index_none_runs_on_complete():
    app = _init_app()
    try:
        hub_stand_in = app.scenes.current
        ends_here = Dialogue(
            lines=(
                DialogueLine(
                    speaker=MENTOR,
                    text_key="dialogue.mentor_greeting.line1",
                    choices=(DialogueChoice(label_key="common.back", next_index=None),),
                ),
            )
        )
        scene = DialogueScene(app, ends_here, on_complete=app.scenes.pop)
        app.scenes.push(scene)

        scene.choice_buttons.buttons[0].on_activate()

        assert app.scenes.current is hub_stand_in
    finally:
        pygame.quit()


def test_finishing_with_no_context_records_nothing():
    app = _init_app()
    try:
        single_line = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line1"),))
        scene = DialogueScene(app, single_line, on_complete=lambda: None)
        app.scenes.push(scene)

        scene._advance()  # must not raise even though context is None
    finally:
        pygame.quit()


def test_finishing_with_a_record_label_key_records_a_real_action():
    app = _init_app()
    try:
        context = LessonContext()
        single_line = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line1"),))
        scene = DialogueScene(
            app, single_line, on_complete=lambda: None, context=context, record_label_key="common.back"
        )
        app.scenes.push(scene)

        scene._advance()

        assert len(context.actions) == 1
        assert context.actions[0].label_key == "common.back"
        assert context.evidence == ()  # no record_evidence_key given - action only
    finally:
        pygame.quit()


def test_finishing_with_a_record_evidence_key_records_evidence_too():
    app = _init_app()
    try:
        context = LessonContext()
        single_line = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line1"),))
        scene = DialogueScene(
            app,
            single_line,
            on_complete=lambda: None,
            context=context,
            record_label_key="common.back",
            record_evidence_key="dialogue.continue_hint",
            record_key="confirmed_fact",
        )
        app.scenes.push(scene)

        scene._advance()

        assert len(context.evidence) == 1
        assert context.evidence[0].label_key == "dialogue.continue_hint"
        assert context.evidence[0].source_action_id == context.actions[0].id
    finally:
        pygame.quit()


def test_reaching_finish_twice_via_key_updates_the_same_slot_not_two():
    app = _init_app()
    try:
        context = LessonContext()
        single_line = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.mentor_greeting.line1"),))

        def make_scene():
            return DialogueScene(
                app,
                single_line,
                on_complete=lambda: None,
                context=context,
                record_label_key="common.back",
                record_evidence_key="dialogue.continue_hint",
                record_key="confirmed_fact",
            )

        make_scene()._advance()
        make_scene()._advance()  # e.g. resuming into the same dialogue stage again

        assert len(context.actions) == 1
        assert len(context.evidence) == 1
    finally:
        pygame.quit()


def test_draw_with_a_background_scene_paints_it_before_dimming_and_the_box():
    app = _init_app()
    try:
        background = app.scenes.current
        scene = DialogueScene(app, TWO_LINE_DIALOGUE, on_complete=lambda: None, background=background)

        scene.draw(app.logical_surface)  # must not raise
    finally:
        pygame.quit()


def test_draw_without_a_background_scene_does_not_crash():
    app = _init_app()
    try:
        scene = DialogueScene(app, TWO_LINE_DIALOGUE, on_complete=lambda: None)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()

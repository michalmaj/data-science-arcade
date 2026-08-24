import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.narrative.dialogue import Dialogue, DialogueChoice, DialogueLine
from data_science_arcade.narrative.npc import MENTOR
from data_science_arcade.ui.dialogue_scene import DialogueScene

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
        scene = DialogueScene(app, TWO_LINE_DIALOGUE)
        app.scenes.push(scene)

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))

        assert scene.index == 1
    finally:
        pygame.quit()


def test_advancing_past_the_last_line_closes_the_dialogue_and_pops_it():
    app = _init_app()
    try:
        hub_stand_in = app.scenes.current
        scene = DialogueScene(app, TWO_LINE_DIALOGUE)
        app.scenes.push(scene)

        scene._advance()  # line 0 -> 1
        scene._advance()  # line 1 -> past the end

        assert app.scenes.current is hub_stand_in
    finally:
        pygame.quit()


def test_on_complete_runs_once_the_dialogue_closes():
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
        scene = DialogueScene(app, branching)
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
        scene = DialogueScene(app, branching)
        app.scenes.push(scene)

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))

        assert scene.index == 1  # activated the first (focused-by-default) choice
    finally:
        pygame.quit()


def test_a_choice_with_next_index_none_ends_the_dialogue():
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
        scene = DialogueScene(app, ends_here)
        app.scenes.push(scene)

        scene.choice_buttons.buttons[0].on_activate()

        assert app.scenes.current is hub_stand_in
    finally:
        pygame.quit()


def test_draw_with_a_background_scene_paints_it_before_dimming_and_the_box():
    app = _init_app()
    try:
        background = app.scenes.current
        scene = DialogueScene(app, TWO_LINE_DIALOGUE, background=background)

        scene.draw(app.logical_surface)  # must not raise
    finally:
        pygame.quit()


def test_draw_without_a_background_scene_does_not_crash():
    app = _init_app()
    try:
        scene = DialogueScene(app, TWO_LINE_DIALOGUE)
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()

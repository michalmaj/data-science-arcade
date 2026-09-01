from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.narrative.dialogue import Dialogue
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
BOX_RECT = pygame.Rect(40, 380, 880, 140)
TEXT_MAX_WIDTH = BOX_RECT.width - 40
SPEAKER_NAME_SIZE = 20
LINE_TEXT_SIZE = 20
HINT_TEXT_SIZE = 14
DIM_ALPHA = 150


class DialogueScene(Scene):
    """Plays a Dialogue line by line. No choices on a line: any click/Enter/
    Space/Escape advances. Choices present: pick one (mouse or keyboard) to
    jump to its next_index. Reaching the end (or a choice with next_index
    None) calls on_complete - required, not optional, because this scene
    never touches the scene stack itself (a lesson stage needs replace(),
    not pop(), so it can't assume which one is correct). Callers that just
    want "pop back to whatever pushed me" pass on_complete=app.scenes.pop.

    background, if provided, is drawn (dimmed) behind the dialogue box
    instead of a flat fill, so the scene the conversation is happening in
    stays visible - e.g. the hub behind an NPC's dialogue.

    `context`/`record_label_key`/`record_evidence_key`/`record_key`, when
    given together, record a real fact once the dialogue finishes - for
    the case where an NPC states something authoritatively that the
    student should be able to cite afterward (e.g. confirming a data gap's
    real cause), not just an engagement record. Deliberately unconditional
    on how the dialogue was reached (no per-choice branching support) -
    every real caller today is a linear, choice-less confirmation; a
    dialogue with real choices needing different recording per branch can
    extend this once one actually exists. All four default to None (no
    recording at all), so every other lesson's plain DialogueScene calls
    are unaffected."""

    def __init__(
        self,
        app,
        dialogue: Dialogue,
        on_complete: Callable[[], None],
        background: Scene | None = None,
        context: LessonContext | None = None,
        record_label_key: str | None = None,
        record_evidence_key: str | None = None,
        record_key: str | None = None,
    ) -> None:
        super().__init__(app)
        self.dialogue = dialogue
        self.background = background
        self.on_complete = on_complete
        self.context = context
        self.record_label_key = record_label_key
        self.record_evidence_key = record_evidence_key
        self.record_key = record_key
        self.index = 0
        self.choice_buttons: ButtonGroup | None = None
        self._build_choice_buttons()

    def _current_line(self):
        return self.dialogue.lines[self.index]

    def _build_choice_buttons(self) -> None:
        choices = self._current_line().choices
        if not choices:
            self.choice_buttons = None
            return
        buttons = []
        for i, choice in enumerate(choices):
            rect = pygame.Rect(0, 0, 320, 36)
            rect.center = (CENTER_X, BOX_RECT.bottom - 44 + i * 42)
            label = self.app.localization.t(choice.label_key)
            buttons.append(Button(rect, label, self._make_choose(choice.next_index)))
        self.choice_buttons = ButtonGroup(buttons)

    def _make_choose(self, next_index: int | None) -> Callable[[], None]:
        def choose() -> None:
            self._advance_to(next_index)

        return choose

    def _advance_to(self, index: int | None) -> None:
        if index is None or index >= len(self.dialogue.lines):
            self._finish()
            return
        self.index = index
        self._build_choice_buttons()

    def _advance(self) -> None:
        if self.choice_buttons is not None:
            return  # must pick a choice, not just click through
        next_index = self.index + 1
        self._advance_to(next_index if next_index < len(self.dialogue.lines) else None)

    def _finish(self) -> None:
        if self.context is not None and self.record_label_key is not None:
            action = self.context.record_action(label_key=self.record_label_key, key=self.record_key)
            if self.record_evidence_key is not None:
                self.context.record_evidence(label_key=self.record_evidence_key, source_action=action, key=self.record_key)
        self.on_complete()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.choice_buttons is not None:
            self.choice_buttons.handle_event(event)
            return
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        ):
            self._advance()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._advance()

    def draw(self, surface: pygame.Surface) -> None:
        if self.background is not None:
            self.background.draw(surface)
            dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            dim.fill((0, 0, 0, DIM_ALPHA))
            surface.blit(dim, (0, 0))
        else:
            surface.fill(colors.BACKGROUND)

        pygame.draw.rect(surface, colors.BUTTON_IDLE, BOX_RECT, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, BOX_RECT, width=1, border_radius=8)

        line = self._current_line()
        text_top = BOX_RECT.top + 16
        if line.speaker is not None:
            speaker_name = self.app.localization.t(line.speaker.name_key)
            draw_centered_text(
                surface,
                speaker_name,
                (BOX_RECT.left + 90, BOX_RECT.top + 20),
                SPEAKER_NAME_SIZE,
                line.speaker.avatar_color,
            )
            text_top += 24

        draw_wrapped_text(
            surface,
            self.app.localization.t(line.text_key),
            (BOX_RECT.left + 20, text_top),
            TEXT_MAX_WIDTH,
            LINE_TEXT_SIZE,
            colors.TEXT,
        )

        if self.choice_buttons is not None:
            self.choice_buttons.draw(surface)
        else:
            draw_centered_text(
                surface,
                self.app.localization.t("dialogue.continue_hint"),
                (BOX_RECT.centerx, BOX_RECT.bottom - 16),
                HINT_TEXT_SIZE,
                colors.BUTTON_TEXT_DISABLED,
            )

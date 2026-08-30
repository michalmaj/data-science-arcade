from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.findings import Finding, FindingChoices
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 72
PROMPT_MAX_WIDTH = 820
PICKED_LIST_Y = 100
OPTION_SIZE = (760, 34)
FIRST_OPTION_Y = 132
OPTION_SPACING = 38
HINT_Y = 462
NAV_BUTTON_Y = 495


class FindingPickerScene(Scene):
    """Select a fixed number of key findings from a shared pool (spec §25
    Lesson 29 'The Executive Brief'): unlike every other stage scene's
    fixed sequence of independent requests, there is exactly one pool and
    one target count - picking a finding removes it from the list and,
    once `target_count` are picked, immediately finishes the stage. There
    is no Back button: a real brief-writer doesn't get to "un-pick" a
    finding once it's already been weighed against the others, and
    reordering three unordered picks has no meaningful "previous state"
    to return to the way every other scene's request-by-request Back does.

    guided=True also shows a fixed hint for the whole task; guided=False
    hides it, matching every other stage scene's guided/independent split.

    Picking a finding also records it into `context` (workbench/context.py)
    as an AnalyticalAction plus an EvidenceItem - proof that the model
    isn't tied to Dataset transformations the way Lesson 06's WorkbenchScene
    integration is: a finding pick doesn't transform any Dataset, it
    surfaces a fact already computed elsewhere (findings_data.py's own
    percent_change/point_change). Lesson 29's own scenario.py doesn't pass
    a context and is unaffected - this is proven via a direct test of this
    scene, not a played in-game Workbench path."""

    def __init__(
        self,
        app,
        title_key: str,
        prompt_key: str,
        findings: tuple[Finding, ...],
        target_count: int,
        on_complete: Callable[[FindingChoices], None],
        guided: bool = True,
        hint_key: str | None = None,
        picked_label_key: str = "findings.picked_label",
        context: LessonContext | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.prompt_key = prompt_key
        self.findings = findings
        self.target_count = target_count
        self.on_complete = on_complete
        self.guided = guided
        self.hint_key = hint_key
        self.picked_label_key = picked_label_key
        self.context = context if context is not None else LessonContext()
        self.picked: list[str] = []
        self._rebuild_buttons()

    def _remaining_findings(self) -> tuple[Finding, ...]:
        return tuple(finding for finding in self.findings if finding.key not in self.picked)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons = []
        for index, finding in enumerate(self._remaining_findings()):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(finding.label_key), self._make_pick(finding.key)))
        self.buttons = ButtonGroup(buttons)

    def _make_pick(self, finding_key: str) -> Callable[[], None]:
        def pick() -> None:
            finding = next(f for f in self.findings if f.key == finding_key)
            action = self.context.record_action(label_key=finding.label_key, python_code=finding.python_code)
            self.context.record_evidence(label_key=finding.label_key, source_action=action)

            self.picked.append(finding_key)
            if len(self.picked) == self.target_count:
                self.on_complete(tuple(self.picked))
                return
            self._rebuild_buttons()

        return pick

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        progress = f"{len(self.picked) + 1} / {self.target_count}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)
        draw_centered_wrapped_text(surface, loc.t(self.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, 16, colors.TEXT)

        self._draw_picked_list(surface)
        self.buttons.draw(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_picked_list(self, surface: pygame.Surface) -> None:
        if not self.picked:
            return
        loc = self.app.localization
        picked_labels = ", ".join(loc.t(finding.label_key) for finding in self.findings if finding.key in self.picked)
        text = f"{loc.t(self.picked_label_key)}: {picked_labels}"
        draw_centered_wrapped_text(surface, text, (CENTER_X, PICKED_LIST_Y), PROMPT_MAX_WIDTH, 14, colors.BUTTON_FOCUS_BORDER)

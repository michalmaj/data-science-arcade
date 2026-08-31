from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
BOX_RECT = pygame.Rect(40, 110, 880, 170)
INTERPRET_PROMPT_Y = 300
OPTION_SIZE = (420, 44)
FIRST_OPTION_Y = 330
OPTION_SPACING = 46
CONTINUE_BUTTON_SIZE = (200, 44)
CONTINUE_GAP = 24
"""Vertical gap between the last interpret option and Continue. Both
Continue's and the hint's y are computed from the real option count
(_continue_button_y/_hint_top below) rather than a fixed position - a
fixed y=500 overlapped the 3rd option with 3+ interpret options, caught
by a real screenshot, the same failure mode BriefBuilderScene's own
tiered-hint area just hit and fixed the same way."""
HINT_GAP = 6


@dataclass(frozen=True)
class InterpretOption:
    key: str
    label_key: str
    evidence_key: str | None = None
    """When set, choosing this interpretation also records a real
    EvidenceItem (label_key=evidence_key), not just an AnalyticalAction -
    for the one case where the *correct* interpretation of a reveal is
    itself a fact worth citing later (e.g. "no source resolves this
    population's status"), not just an engagement record. Deliberately
    per-option, not per-comparison like RepairIssue.evidence_key (which
    fires the same evidence regardless of which fix was picked) - here the
    content of the choice IS the fact being asserted, so only the option
    that actually asserts something true and supportable should leave
    evidence behind. Continue still enables regardless of which option is
    picked; this only changes what ends up citable afterward."""


class ComparisonRevealScene(Scene):
    """Shows exactly two real, caller-computed values side by side (e.g.
    the 30-day vs. 12-month repeat rate, holding entity/population fixed -
    or customer-level vs. household-level, holding the window fixed), then
    asks the student to interpret the gap before continuing. Deliberately
    a fixed pair, not TwistRevealScene's variadic N-way comparisons: this
    scene exists specifically for a single-variable sensitivity check
    (change exactly one definition, recompute, interpret), and a 3rd or
    4th value here would mean two things changed at once - the exact
    confound this scene exists to avoid. TwistRevealScene itself (used
    once, for the lesson's own narrative twist reveal showing all the
    student's gathered numbers together) is untouched by this scene.

    Reused across three real moments with the same underlying shape (pick
    nothing here - both values are already computed by the caller; the
    only real decision is the interpret pick): time-window sensitivity,
    entity sensitivity, and the optional mastery challenge's own
    comparison. Recording both comparison values as real AnalyticalAction/
    EvidenceItem pairs (via the required `context`) happens here, not in
    the calling scenario.py, matching every other scene in this codebase -
    record_action/record_evidence are only ever called from inside a
    scene, never from stage-wiring code. Each comparison's `detail` is set
    to the live-formatted value itself (see EvidenceItem's own docstring
    for why that's a plain formatted string, not baked into label_key),
    so Act 8's Evidence Review later shows the real number, not just the
    label. `context` has no default (unlike WorkbenchScene/
    PipelineBuilderScene's `context: LessonContext | None = None`) -
    omitting it here would silently starve the Decision Builder's Evidence
    step of real items to pick from, a soft-lock rather than a crash.

    An interpret option itself can also carry evidence - see
    InterpretOption.evidence_key - for the case where recognizing the
    correct interpretation of a reveal is itself a citable fact."""

    def __init__(
        self,
        app,
        title_key: str,
        narrative_keys: tuple[str, ...],
        comparisons: tuple[tuple[str, float], tuple[str, float]],
        interpret_prompt_key: str,
        interpret_options: tuple[InterpretOption, ...],
        on_complete: Callable[[str], None],
        context: LessonContext,
        value_format: Callable[[float], str] = lambda value: f"{value:.0%}",
        guided: bool = True,
        interpret_hint_key: str | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.narrative_keys = narrative_keys
        self.comparisons = comparisons
        self.interpret_prompt_key = interpret_prompt_key
        self.interpret_options = interpret_options
        self.on_complete = on_complete
        self.context = context
        self.value_format = value_format
        self.guided = guided
        self.interpret_hint_key = interpret_hint_key
        self._interpret_choice: str | None = None
        self._rebuild_buttons()

    def _options_bottom(self) -> int:
        return FIRST_OPTION_Y + (len(self.interpret_options) - 1) * OPTION_SPACING + OPTION_SIZE[1] // 2

    def _hint_top(self) -> int:
        return self._options_bottom() + HINT_GAP

    def _continue_button_y(self) -> int:
        y = self._options_bottom() + CONTINUE_GAP
        if self.guided and self.interpret_hint_key:
            y += 34  # room for one wrapped hint line, see HINT_GAP's own docstring
        return y

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons = []
        for index, option in enumerate(self.interpret_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        continue_rect = pygame.Rect(0, 0, *CONTINUE_BUTTON_SIZE)
        continue_rect.center = (CENTER_X, self._continue_button_y())
        self.continue_button = Button(
            continue_rect, loc.t("runtime.continue_button"), self._continue, enabled=self._interpret_choice is not None
        )
        buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._interpret_choice = option_key
            self._rebuild_buttons()

        return choose

    def _continue(self) -> None:
        if self._interpret_choice is None:
            return
        for label_key, value in self.comparisons:
            action = self.context.record_action(label_key=label_key, key=label_key)
            self.context.record_evidence(
                label_key=label_key, source_action=action, key=label_key, detail=self.value_format(value)
            )
        chosen = next(o for o in self.interpret_options if o.key == self._interpret_choice)
        action = self.context.record_action(label_key=chosen.label_key)
        if chosen.evidence_key is not None:
            self.context.record_evidence(label_key=chosen.evidence_key, source_action=action, key=chosen.evidence_key)
        self.on_complete(self._interpret_choice)

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 60), 28, colors.TEXT)

        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, BOX_RECT, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, BOX_RECT, width=1, border_radius=8)

        left = BOX_RECT.left + 20
        width = BOX_RECT.width - 40
        y = BOX_RECT.top + 16
        for key in self.narrative_keys:
            draw_wrapped_text(surface, loc.t(key), (left, y), width, 16, colors.TEXT)
            y += 40

        y += 10
        for label_key, value in self.comparisons:
            text = f"{loc.t(label_key)} {self.value_format(value)}"
            draw_wrapped_text(surface, text, (left, y), width, 20, colors.BUTTON_FOCUS_BORDER)
            y += 32

        draw_centered_text(surface, loc.t(self.interpret_prompt_key), (CENTER_X, INTERPRET_PROMPT_Y), 18, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)

        if self.guided and self.interpret_hint_key:
            draw_wrapped_text(
                surface, loc.t(self.interpret_hint_key), (CENTER_X - 300, self._hint_top()), 600, 14, colors.BUTTON_TEXT_DISABLED
            )

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        if self._interpret_choice is None:
            return
        selected_index = next(i for i, o in enumerate(self.interpret_options) if o.key == self._interpret_choice)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

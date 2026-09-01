from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text, wrap_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
BOX_LEFT = 40
BOX_TOP = 110
BOX_WIDTH = 880
BOX_PADDING = 16
NARRATIVE_TEXT_SIZE = 16
NARRATIVE_LINE_SPACING = 4
COMPARISON_TEXT_SIZE = 20
COMPARISON_ROW_HEIGHT = 32
NARRATIVE_COMPARISON_GAP = 10
"""The box's height used to be a fixed BOX_RECT constant sized for
whatever narrative_keys happened to be short enough to fit - real content
with a longer or third narrative line (or a longer translation) can wrap
past a fixed single-line-per-key budget, caught only by a real screenshot
overlapping the box's own bottom border. Box height (and everything
below it) is now computed from the real wrapped line count of the actual
narrative_keys/comparisons, the same "advance by however many lines it
actually wrapped to" principle WorkbenchScene._draw_schema already
established for schema descriptions."""
INTERPRET_PROMPT_GAP = 20
FIRST_OPTION_GAP = 30
OPTION_SIZE = (420, 44)
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
class ComparisonValue:
    label_key: str
    value: float
    python_code: str | None = None
    """The real pandas equivalent that produced `value`, shown in the
    Python Mirror once recorded - e.g. "billing.groupby('status')
    ['customer_id'].count()". None for a value that genuinely has no
    single-line equivalent worth showing. When a value depends on a
    dataset not yet referenced anywhere else in the mirror (nothing
    upstream ever showed its own load line), this should be a
    self-contained multi-line string that loads it first - e.g.
    "marketing = pd.read_csv(...)\\nmarketing.customer_id.nunique()" -
    since a bare "marketing.customer_id.nunique()" would otherwise read
    as a script using an undefined variable to anyone reading the
    Evidence Review's own Python tab top to bottom."""


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
    """Shows exactly two real, caller-computed values side by side, then
    asks the student to interpret the gap before continuing. Deliberately
    a fixed pair, not TwistRevealScene's variadic N-way comparisons - a
    3rd or 4th value here would mean the student can no longer tell which
    of several differences actually explains the gap. TwistRevealScene
    itself (a lesson's own narrative twist reveal showing every gathered
    number together at once) is untouched by this scene.

    Two real shapes of "why do these two values differ," both real uses
    today: a single-variable sensitivity check (one definition changed,
    everything else held fixed - e.g. the same rate at two time windows),
    and a cross-source conflict (two different real sources answering a
    related but not identical question - e.g. two systems' own counts of
    "active"). Both share the same mechanics: nothing to pick here besides
    the interpretation, since both values are already computed by the
    caller.

    Recording both comparison values as real AnalyticalAction/EvidenceItem
    pairs (via the required `context`) happens here, not in the calling
    scenario.py, matching every other scene in this codebase -
    record_action/record_evidence are only ever called from inside a
    scene, never from stage-wiring code. Each comparison's `detail` is set
    to the live-formatted value itself (see EvidenceItem's own docstring
    for why that's a plain formatted string, not baked into label_key),
    so a later Evidence Review shows the real number, not just the label;
    `python_code`, when a ComparisonValue sets it, is recorded onto the
    same AnalyticalAction, so the Python Mirror can show real multi-source
    analysis, not just whichever single scene happened to use
    PipelineBuilderScene. `context` has no default (unlike WorkbenchScene/
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
        comparisons: tuple[ComparisonValue, ComparisonValue],
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

    def _content_width(self) -> int:
        return BOX_WIDTH - 40

    def _narrative_height(self) -> int:
        loc = self.app.localization
        font = get_font(NARRATIVE_TEXT_SIZE)
        width = self._content_width()
        line_height = font.get_linesize() + NARRATIVE_LINE_SPACING
        total_lines = sum(len(wrap_text(loc.t(key), font, width)) for key in self.narrative_keys)
        return total_lines * line_height

    def _box_rect(self) -> pygame.Rect:
        height = (
            BOX_PADDING
            + self._narrative_height()
            + NARRATIVE_COMPARISON_GAP
            + len(self.comparisons) * COMPARISON_ROW_HEIGHT
            + BOX_PADDING
        )
        return pygame.Rect(BOX_LEFT, BOX_TOP, BOX_WIDTH, height)

    def _interpret_prompt_y(self) -> int:
        return self._box_rect().bottom + INTERPRET_PROMPT_GAP

    def _first_option_y(self) -> int:
        return self._interpret_prompt_y() + FIRST_OPTION_GAP

    def _options_bottom(self) -> int:
        return self._first_option_y() + (len(self.interpret_options) - 1) * OPTION_SPACING + OPTION_SIZE[1] // 2

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
        first_option_y = self._first_option_y()
        for index, option in enumerate(self.interpret_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, first_option_y + index * OPTION_SPACING)
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
        for item in self.comparisons:
            action = self.context.record_action(label_key=item.label_key, python_code=item.python_code, key=item.label_key)
            self.context.record_evidence(
                label_key=item.label_key, source_action=action, key=item.label_key, detail=self.value_format(item.value)
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

        box = self._box_rect()
        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, box, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, box, width=1, border_radius=8)

        left = box.left + 20
        width = self._content_width()
        font = get_font(NARRATIVE_TEXT_SIZE)
        line_height = font.get_linesize() + NARRATIVE_LINE_SPACING
        y = box.top + BOX_PADDING
        for key in self.narrative_keys:
            text = loc.t(key)
            draw_wrapped_text(surface, text, (left, y), width, NARRATIVE_TEXT_SIZE, colors.TEXT, line_spacing=NARRATIVE_LINE_SPACING)
            y += len(wrap_text(text, font, width)) * line_height

        y += NARRATIVE_COMPARISON_GAP
        for item in self.comparisons:
            text = f"{loc.t(item.label_key)} {self.value_format(item.value)}"
            draw_wrapped_text(surface, text, (left, y), width, COMPARISON_TEXT_SIZE, colors.BUTTON_FOCUS_BORDER)
            y += COMPARISON_ROW_HEIGHT

        draw_centered_text(surface, loc.t(self.interpret_prompt_key), (CENTER_X, self._interpret_prompt_y()), 18, colors.TEXT)

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

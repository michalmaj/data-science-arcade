from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
BOX_RECT = pygame.Rect(40, 110, 880, 130)
OFFER_OPTION_Y = BOX_RECT.bottom + 40
PROMPT_GAP = 30
COMPARISON_LINE_HEIGHT = 28
OPTION_SIZE = (420, 46)
OPTION_SPACING = 56
MIN_OPTION_SPACING = 32
MIN_OPTION_HEIGHT = 26
"""The RESULT phase's option count depends entirely on the calling
lesson's own interpret_options (2 for L01, 3 for L02) - a fixed
OPTION_SPACING/OPTION_SIZE sized for 2 silently ran a 3rd real option
(and the Finish button) past NAV_BUTTON_Y, caught only by a real
screenshot with L02's real 3-option content. Spacing shrinks first (like
BriefBuilderScene's own MIN_OPTION_SPACING); height shrinks alongside it
only once spacing alone still can't fit the real option count above
NAV_BUTTON_Y - shrinking spacing without also shrinking height caps how
much room shrinking spacing alone can actually recover, since the last
button's own half-height still counts against the same budget."""
NAV_BUTTON_Y = 505
OPTION_BOTTOM_MARGIN = 35
"""Both draw() and _rebuild_buttons() must agree on exactly where the
PICK/RESULT phases' prompt text and option buttons land - computed once
via _prompt_y()/_options_top() rather than each method keeping its own
separate fixed constant, the same class of drift that overlapped a real
comparison-result line with the interpret buttons the first time this
was rendered with real content, not synthetic loc keys."""


class _Phase(Enum):
    OFFER = auto()
    PICK = auto()
    RESULT = auto()


@dataclass(frozen=True)
class MasteryOption:
    key: str
    label_key: str


@dataclass(frozen=True)
class MetricValue:
    label_key: str
    value: float
    python_code: str | None = None
    """Same role as ComparisonRevealScene's own ComparisonValue.python_code
    - the real pandas equivalent that produced `value`, recorded onto the
    same AnalyticalAction so a later Evidence Review shows real code, not
    a script referencing an undefined variable. Since `compute` only ever
    runs after the student picks a metric in the PICK phase, and this
    scene is always the last real analytical stage before Feedback, any
    dataset this references will already have been loaded by an earlier
    stage in every current usage - unlike ComparisonValue, there's no
    established case here yet that needs a self-contained load line, but
    the option stays open the same way."""


class MasteryChallengeScene(Scene):
    """The optional bonus act: a real transfer task on the same dataset,
    not a repeat of the required acts. Always exactly one LessonRunner
    stage (one checkpoint) with its own internal Skip path, since the
    stage list LessonRunner drives is static - there's no framework
    support for "skip the next N stages based on a runtime choice," so an
    optional multi-step task has to own its own skip logic internally
    rather than being split across stages, the same reasoning that led
    DecisionBuilderScene to sequence its own steps internally rather than
    as separate stages.

    Three phases in one scene instance: OFFER (engage or skip - skipping
    fires on_complete immediately, with no metric/interpretation choice
    recorded at all) -> PICK (choose which metric to compare, a real,
    ungated decision) -> RESULT (the live comparison for that metric, plus
    a short interpret pick). Skipping never lowers the lesson's four core
    scores; finishing the full path only ever adds a bonus note - neither
    is enforced by this scene itself, which just reports what happened
    via on_complete's `engaged` flag for the caller's own scoring to use."""

    def __init__(
        self,
        app,
        title_key: str,
        narrative_keys: tuple[str, ...],
        metric_prompt_key: str,
        metric_options: tuple[MasteryOption, ...],
        compute: Callable[[str], tuple[MetricValue, MetricValue]],
        interpret_prompt_key: str,
        interpret_options: tuple[MasteryOption, ...],
        on_complete: Callable[[bool, str | None, str | None], None],
        context: LessonContext,
        value_format: Callable[[float], str] = lambda value: f"${value:,.0f}",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.narrative_keys = narrative_keys
        self.metric_prompt_key = metric_prompt_key
        self.metric_options = metric_options
        self.compute = compute
        self.interpret_prompt_key = interpret_prompt_key
        self.interpret_options = interpret_options
        self.on_complete = on_complete
        self.context = context
        self.value_format = value_format
        self._phase = _Phase.OFFER
        self._metric_choice: str | None = None
        self._interpret_choice: str | None = None
        self._comparison: tuple[MetricValue, MetricValue] | None = None
        self._rebuild_buttons()

    def _prompt_y(self) -> int:
        return BOX_RECT.bottom + PROMPT_GAP

    def _options_top(self) -> int:
        if self._phase is _Phase.RESULT:
            assert self._comparison is not None
            return self._prompt_y() + len(self._comparison) * COMPARISON_LINE_HEIGHT + PROMPT_GAP + 20
        return self._prompt_y() + PROMPT_GAP

    def _options_layout(self, top: int, count: int) -> tuple[int, int]:
        """(spacing, height) - shrinks spacing first, then height alongside
        it, only once the real option count is too large for the defaults
        to fit above NAV_BUTTON_Y. Returns the defaults unchanged for any
        count small enough not to need this (every case before L02)."""
        if count <= 1:
            return OPTION_SPACING, OPTION_SIZE[1]
        available = (NAV_BUTTON_Y - OPTION_BOTTOM_MARGIN) - top
        spacing = max(MIN_OPTION_SPACING, min(OPTION_SPACING, (available - OPTION_SIZE[1] // 2) // (count - 1)))
        height = max(MIN_OPTION_HEIGHT, min(OPTION_SIZE[1], spacing - 4))
        return spacing, height

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []

        if self._phase is _Phase.OFFER:
            engage_rect = pygame.Rect(0, 0, *OPTION_SIZE)
            engage_rect.center = (CENTER_X, OFFER_OPTION_Y)
            buttons.append(Button(engage_rect, loc.t("mastery.engage"), self._engage))
            skip_rect = pygame.Rect(0, 0, *OPTION_SIZE)
            skip_rect.center = (CENTER_X, OFFER_OPTION_Y + OPTION_SPACING)
            buttons.append(Button(skip_rect, loc.t("mastery.skip"), self._skip))
        elif self._phase is _Phase.PICK:
            top = self._options_top()
            spacing, height = self._options_layout(top, len(self.metric_options))
            for index, option in enumerate(self.metric_options):
                rect = pygame.Rect(0, 0, OPTION_SIZE[0], height)
                rect.center = (CENTER_X, top + index * spacing)
                buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_metric(option.key)))
        else:
            top = self._options_top()
            spacing, height = self._options_layout(top, len(self.interpret_options))
            for index, option in enumerate(self.interpret_options):
                rect = pygame.Rect(0, 0, OPTION_SIZE[0], height)
                rect.center = (CENTER_X, top + index * spacing)
                buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_interpret(option.key)))

            finish_rect = pygame.Rect(0, 0, 200, 44)
            finish_rect.center = (CENTER_X, NAV_BUTTON_Y)
            self.finish_button = Button(
                finish_rect, loc.t("runtime.continue_button"), self._finish, enabled=self._interpret_choice is not None
            )
            buttons.append(self.finish_button)

        self.buttons = ButtonGroup(buttons)

    def _engage(self) -> None:
        self._phase = _Phase.PICK
        self._rebuild_buttons()

    def _skip(self) -> None:
        self.on_complete(False, None, None)

    def _make_choose_metric(self, metric_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._metric_choice = metric_key
            self._comparison = self.compute(metric_key)
            self._phase = _Phase.RESULT
            self._rebuild_buttons()

        return choose

    def _make_choose_interpret(self, interpret_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._interpret_choice = interpret_key
            self._rebuild_buttons()

        return choose

    def _finish(self) -> None:
        if self._interpret_choice is None or self._comparison is None:
            return
        for item in self._comparison:
            action = self.context.record_action(label_key=item.label_key, python_code=item.python_code, key=item.label_key)
            self.context.record_evidence(
                label_key=item.label_key, source_action=action, key=item.label_key, detail=self.value_format(item.value)
            )
        self.on_complete(True, self._metric_choice, self._interpret_choice)

    def handle_event(self, event: pygame.event.Event) -> None:
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
            y += 32

        if self._phase is _Phase.PICK:
            draw_centered_text(surface, loc.t(self.metric_prompt_key), (CENTER_X, self._prompt_y()), 18, colors.TEXT)
        elif self._phase is _Phase.RESULT:
            assert self._comparison is not None
            result_y = self._prompt_y()
            for item in self._comparison:
                text = f"{loc.t(item.label_key)} {self.value_format(item.value)}"
                draw_wrapped_text(surface, text, (left, result_y), width, 18, colors.BUTTON_FOCUS_BORDER)
                result_y += COMPARISON_LINE_HEIGHT
            draw_centered_text(surface, loc.t(self.interpret_prompt_key), (CENTER_X, result_y + 10), 16, colors.TEXT)

        self.buttons.draw(surface)

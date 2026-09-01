from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.brief import BriefField
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
OPTION_SIZE = (420, 46)
FIRST_OPTION_Y = 190
OPTION_SPACING = 56
NAV_BUTTON_Y = 505
EVIDENCE_OPTION_SIZE = (700, 40)
EVIDENCE_OPTION_SPACING = 46
MIN_EVIDENCE_SPACING = 32
MIN_EVIDENCE_OPTION_HEIGHT = 28
EVIDENCE_BOTTOM_MARGIN = 48
"""A real evidence pool can be much larger than the 2-3 the student
ultimately picks (L02's Evidence Review alone produces 8 real items) - a
fixed 46px spacing at the fixed default height silently ran the last few
buttons past NAV_BUTTON_Y, caught only by a real screenshot with a real
8-item pool, not by any test written against L01's smaller 5-item one.
Spacing shrinks first (like BriefBuilderScene's own MIN_OPTION_SPACING);
button height only shrinks alongside it once spacing alone can't fit the
real pool in the space above NAV_BUTTON_Y."""
FIRST_EVIDENCE_Y = 185
EVIDENCE_COUNT_Y = 155

DecisionChoices = dict[str, str | tuple[str, ...]]
"""step.key -> chosen BriefOption.key for a single-select step, or ->
a tuple of EvidenceItem.id values for the evidence step."""


@dataclass(frozen=True)
class EvidenceField:
    """The one heterogeneous step in an otherwise all-single-select
    sequence: pick min_count-max_count real EvidenceItems directly from
    the LessonContext threaded through this scene, not from a fixed
    options list - unlike every BriefField, this step's real choices
    aren't known until the student has actually gathered evidence
    earlier in the lesson."""

    key: str
    prompt_key: str
    min_count: int = 2
    max_count: int = 3
    hint_key: str | None = None


DecisionStep = BriefField | EvidenceField


class DecisionBuilderScene(Scene):
    """The lesson's final argument, composed step by step and sequenced
    with Back/Next exactly like BriefBuilderScene. `steps` is an arbitrary
    ordered sequence of BriefField/EvidenceField, not a fixed set of named
    params - a lesson's own argument shape (how many steps, what they're
    called, whether a confidence step even exists) is content, not
    something this scene should hardcode after only one lesson used it.
    L01 sequences Claim -> Evidence -> Limitation -> Confidence ->
    Recommendation -> Follow-up; L02's own shape drops Confidence entirely
    and has two steps L01 has no equivalent of (Safe/Not-Safe to claim) -
    both are just different `steps` tuples through the same scene.

    Exactly one step in the sequence must be an EvidenceField: a real
    multi-select (min_count-max_count) toggled directly from
    `context.evidence` - the actual items gathered earlier in the lesson,
    not a fixed options list, which is why this needed a new scene rather
    than an extra BriefBuilderScene param (BriefBuilderScene has no
    `context` visibility at all and is single-select only). It's found by
    scanning `steps` rather than being passed separately; a plain
    `next(...)` would either raise an opaque StopIteration with none, or
    silently pick the first of several with more than one, so the
    constructor validates explicitly and raises a clear ValueError
    instead.

    `context` has no default, unlike WorkbenchScene/PipelineBuilderScene's
    `context: LessonContext | None = None`: a missing/empty context here
    would make the Evidence step's min_count permanently unsatisfiable - a
    silent soft-lock, not a crash, so requiring it turns that mistake into
    an immediate TypeError instead.

    Everything in this scene already operates on self._steps generically
    (_rebuild_buttons, _next, _step_satisfied never hardcode which index
    is which) - only the EvidenceField lookup above needed the explicit
    check."""

    def __init__(
        self,
        app,
        title_key: str,
        steps: tuple[DecisionStep, ...],
        context: LessonContext,
        on_complete: Callable[[DecisionChoices], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        evidence_fields = [step for step in steps if isinstance(step, EvidenceField)]
        if len(evidence_fields) != 1:
            raise ValueError(f"DecisionBuilderScene requires exactly one EvidenceField in steps, got {len(evidence_fields)}")
        self.evidence_field = evidence_fields[0]
        self.context = context
        self.on_complete = on_complete
        self.guided = guided
        self._steps: tuple[DecisionStep, ...] = steps
        self.step_index = 0
        self.single_choices: dict[str, str] = {}
        self._evidence_selected: list[str] = []
        self._rebuild_buttons()

    def _current_step(self) -> DecisionStep:
        return self._steps[self.step_index]

    def _is_last_step(self) -> bool:
        return self.step_index == len(self._steps) - 1

    def _is_evidence_step(self, step: DecisionStep) -> bool:
        return isinstance(step, EvidenceField)

    def _step_satisfied(self, step: DecisionStep) -> bool:
        if isinstance(step, EvidenceField):
            return step.min_count <= len(self._evidence_selected) <= step.max_count
        return step.key in self.single_choices

    def _evidence_layout(self, count: int) -> tuple[int, int]:
        """(item_height, spacing) - shrinks spacing first, then height
        alongside it, only once the real pool is too large for the
        defaults to fit above NAV_BUTTON_Y. Returns the defaults unchanged
        for any pool small enough not to need this (every case before
        L02)."""
        if count <= 1:
            return EVIDENCE_OPTION_SIZE[1], EVIDENCE_OPTION_SPACING
        available = (NAV_BUTTON_Y - EVIDENCE_BOTTOM_MARGIN) - FIRST_EVIDENCE_Y
        spacing = max(MIN_EVIDENCE_SPACING, min(EVIDENCE_OPTION_SPACING, available // (count - 1)))
        height = max(MIN_EVIDENCE_OPTION_HEIGHT, min(EVIDENCE_OPTION_SIZE[1], spacing - 4))
        return height, spacing

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        step = self._current_step()
        buttons: list[Button] = []
        self._evidence_toggle_buttons: dict[str, Button] = {}

        if isinstance(step, EvidenceField):
            height, spacing = self._evidence_layout(len(self.context.evidence))
            for index, item in enumerate(self.context.evidence):
                rect = pygame.Rect(0, 0, EVIDENCE_OPTION_SIZE[0], height)
                rect.center = (CENTER_X, FIRST_EVIDENCE_Y + index * spacing)
                label = loc.t(item.label_key) if item.detail is None else f"{loc.t(item.label_key)} {item.detail}"
                selected = item.id in self._evidence_selected
                enabled = selected or len(self._evidence_selected) < step.max_count
                button = Button(rect, label, self._make_toggle_evidence(item.id), enabled=enabled)
                self._evidence_toggle_buttons[item.id] = button
                buttons.append(button)
        else:
            for index, option in enumerate(step.options):
                rect = pygame.Rect(0, 0, *OPTION_SIZE)
                rect.center = (CENTER_X, FIRST_OPTION_Y + index * OPTION_SPACING)
                buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.step_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_step() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=self._step_satisfied(step))
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.single_choices[self._current_step().key] = option_key
            self._rebuild_buttons()

        return choose

    def _make_toggle_evidence(self, item_id: str) -> Callable[[], None]:
        def toggle() -> None:
            if item_id in self._evidence_selected:
                self._evidence_selected.remove(item_id)
            elif len(self._evidence_selected) < self.evidence_field.max_count:
                self._evidence_selected.append(item_id)
            self._rebuild_buttons()

        return toggle

    def _back(self) -> None:
        if self.step_index > 0:
            self.step_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        step = self._current_step()
        if not self._step_satisfied(step):
            return
        if self._is_last_step():
            result: DecisionChoices = dict(self.single_choices)
            result[self.evidence_field.key] = tuple(self._evidence_selected)
            self.on_complete(result)
            return
        self.step_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed here: LessonRunner wraps every
        # stage in Pausable, which intercepts Escape before this scene ever
        # sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        step = self._current_step()

        progress = f"{self.step_index + 1} / {len(self._steps)}"
        draw_centered_text(surface, progress, (CENTER_X, 60), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 90), 28, colors.TEXT)
        draw_centered_text(surface, loc.t(step.prompt_key), (CENTER_X, 140), 20, colors.TEXT)

        if isinstance(step, EvidenceField):
            count_text = f"{len(self._evidence_selected)} / {step.min_count}-{step.max_count}"
            draw_centered_text(surface, count_text, (CENTER_X, EVIDENCE_COUNT_Y), 14, colors.BUTTON_TEXT_DISABLED)

        self.buttons.draw(surface)
        self._draw_selected_indicators(surface, step)

        if self.guided and step.hint_key:
            draw_wrapped_text(
                surface,
                loc.t(step.hint_key),
                (CENTER_X - 300, NAV_BUTTON_Y - 40),
                600,
                15,
                colors.BUTTON_TEXT_DISABLED,
            )

    def _draw_selected_indicators(self, surface: pygame.Surface, step: DecisionStep) -> None:
        if isinstance(step, EvidenceField):
            buttons = [self._evidence_toggle_buttons[item_id] for item_id in self._evidence_selected]
        else:
            selected_key = self.single_choices.get(step.key)
            if selected_key is None:
                return
            selected_index = next(i for i, option in enumerate(step.options) if option.key == selected_key)
            buttons = [self.buttons.buttons[selected_index]]

        for button in buttons:
            rect = button.rect
            marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
            pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

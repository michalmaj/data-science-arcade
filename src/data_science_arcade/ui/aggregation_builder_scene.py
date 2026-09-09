from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd
import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 84
PROMPT_SIZE = 20
PROMPT_MAX_WIDTH = 820
FIRST_OPTION_Y = 130
OPTION_SIZE = (420, 40)
OPTION_SPACING = 46
RESULT_TOP = 330
HEADER_Y_GAP = 18
ROW_HEIGHT = 20
MAX_PREVIEW_ROWS = 5
"""Real, deliberate: a wrong group key (e.g. customer_id, ~54 real
groups on this lesson's own dataset) must never overflow a 960x540
canvas - capped the same way PipelineBuilderScene's own established
preview already is, but with an explicit real count in the truncation
note rather than a generic "more rows" line, since a wrong-path
screenshot needs to say plainly how many groups actually exist."""
NAV_BUTTON_Y = 500
HINT_Y = 470


@dataclass(frozen=True)
class GroupByOption:
    key: str
    label_key: str
    column: str


@dataclass(frozen=True)
class MetricOption:
    """One complete, real, pre-vetted-safe (source column, aggregate
    function) pair - never composed from two independently-picked lists.
    Two free lists (any source x any function) could reach a genuinely
    crashing pandas call (e.g. mean() on a string column); every
    MetricOption that ever ships must be hand-verified to compute
    without raising against the real dataset before it's offered as a
    button, closing that risk structurally rather than by validating at
    click time."""

    key: str
    label_key: str
    column: str
    func: str


@dataclass(frozen=True)
class MetricSlot:
    key: str  # becomes the output column name, e.g. "orders" | "revenue" | "unique_customers" | "aov"
    label_key: str
    options: tuple[MetricOption, ...]


def _format_cell(value: object) -> str:
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float):
        return f"{value:,.0f}" if value.is_integer() else f"{value:,.2f}"
    return str(value)


class AggregationBuilderScene(Scene):
    """Compose one real, named-aggregation groupby pipeline as a single,
    continuous build - a group key, then each of `metric_slots` in
    order - rather than PipelineBuilderScene's own one-group-by-plus-
    one-aggregate-per-screen shape, which can't compose several named
    output columns into one wide result table without restructuring its
    own data model. The live preview table grows a real column at a
    time (`dataset.frame.groupby(group_by.column, as_index=False).agg(
    **{slot.key: (option.column, option.func) for ...})` - real pandas
    named aggregation), computed fresh in `draw()` exactly like
    PipelineBuilderScene's own established "the scene calls real pandas,
    never pre-computed by the caller" discipline, wrapped in a real
    try/except so a wrong-but-somehow-reachable combination degrades to
    a visible, controlled message rather than an exception - defense in
    depth on top of MetricOption's own by-construction safety.

    `initial_group_by`/`initial_choices` seed a fresh instance with a
    prior pass's full picks (a revision is just constructing this scene
    again, pre-filled, never a bespoke partial-resume mechanism) - every
    step, including the group key, stays fully re-visitable via Back/
    Next either way.

    Never records a toggle/pick as its own AnalyticalAction or Evidence
    - the whole pipeline is recorded as ONE real action, keyed so a
    revision updates it in place, only once Finish is pressed (matches
    the "toggling/picking mechanics are never themselves Evidence"
    discipline established since L11's own DistributionExplorerScene)."""

    def __init__(
        self,
        app,
        title_key: str,
        dataset: Dataset,
        group_by_options: tuple[GroupByOption, ...],
        metric_slots: tuple[MetricSlot, ...],
        on_complete: Callable[[str, dict[str, str]], None],
        context: LessonContext,
        initial_group_by: str | None = None,
        initial_choices: dict[str, str] | None = None,
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.dataset = dataset
        self.group_by_options = group_by_options
        self.metric_slots = metric_slots
        self.on_complete = on_complete
        self.context = context
        self.guided = guided
        self.step_index = 0
        self.group_by_choice: str | None = initial_group_by
        self.choices: dict[str, str] = dict(initial_choices) if initial_choices else {}
        self._rebuild_buttons()

    def _total_steps(self) -> int:
        return 1 + len(self.metric_slots)

    def _is_group_by_step(self) -> bool:
        return self.step_index == 0

    def _current_slot(self) -> MetricSlot:
        return self.metric_slots[self.step_index - 1]

    def _is_last_step(self) -> bool:
        return self.step_index == self._total_steps() - 1

    def _current_options(self) -> tuple[GroupByOption, ...] | tuple[MetricOption, ...]:
        return self.group_by_options if self._is_group_by_step() else self._current_slot().options

    def _current_choice_key(self) -> str | None:
        return self.group_by_choice if self._is_group_by_step() else self.choices.get(self._current_slot().key)

    def _step_satisfied(self) -> bool:
        return self._current_choice_key() is not None

    def _selected_group_by(self) -> GroupByOption | None:
        if self.group_by_choice is None:
            return None
        return next(o for o in self.group_by_options if o.key == self.group_by_choice)

    def _selected_option(self, slot: MetricSlot) -> MetricOption | None:
        choice = self.choices.get(slot.key)
        if choice is None:
            return None
        return next(o for o in slot.options if o.key == choice)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        options = self._current_options()
        buttons: list[Button] = []
        for index, option in enumerate(options):
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
        self.next_button = Button(next_rect, next_label, self._next, enabled=self._step_satisfied())
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            if self._is_group_by_step():
                self.group_by_choice = option_key
            else:
                self.choices[self._current_slot().key] = option_key
            self._rebuild_buttons()

        return choose

    def _back(self) -> None:
        if self.step_index > 0:
            self.step_index -= 1
            self._rebuild_buttons()

    def _named_aggs(self) -> dict[str, tuple[str, str]]:
        named: dict[str, tuple[str, str]] = {}
        for slot in self.metric_slots:
            option = self._selected_option(slot)
            if option is not None:
                named[slot.key] = (option.column, option.func)
        return named

    def _finish(self) -> None:
        group_by = self._selected_group_by()
        named = self._named_aggs()
        lines = [f"orders.groupby('{group_by.column}', as_index=False).agg("]
        for slot_key, (column, func) in named.items():
            lines.append(f"    {slot_key}=('{column}', '{func}'),")
        lines.append(")")
        python_code = "\n".join(lines)
        self.context.record_action(label_key=self.title_key, python_code=python_code, key="store_summary_pipeline")
        self.on_complete(self.group_by_choice, dict(self.choices))

    def _next(self) -> None:
        if not self._step_satisfied():
            return
        if self._is_last_step():
            self._finish()
            return
        self.step_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def _compute_preview(self) -> tuple[pd.DataFrame | None, int, str | None]:
        """(preview_frame_or_None, real_total_group_count, error_or_None).
        Wrapped in a real try/except (guardrail: every reachable
        MetricOption is pre-vetted safe, so this should never actually
        trigger - but a wrong-but-somehow-reachable combination must
        degrade to a visible message, never an exception)."""
        group_by = self._selected_group_by()
        if group_by is None:
            return None, 0, None
        try:
            grouped = self.dataset.frame.groupby(group_by.column, as_index=False)
            named = self._named_aggs()
            frame = grouped.agg(**named) if named else grouped.size().rename(columns={"size": "count"})
            return frame, len(frame), None
        except Exception as exc:  # noqa: BLE001 - a deliberate, visible fallback, never a crash
            return None, 0, str(exc)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        progress = f"{self.step_index + 1} / {self._total_steps()}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 26, colors.TEXT)

        if self._is_group_by_step():
            prompt_key = "lesson.l12.builder.group_by_prompt"
        else:
            prompt_key = self._current_slot().label_key
        draw_centered_wrapped_text(surface, loc.t(prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)
        self._draw_preview(surface)

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        choice_key = self._current_choice_key()
        if choice_key is None:
            return
        options = self._current_options()
        index = next(i for i, option in enumerate(options) if option.key == choice_key)
        rect = self.buttons.buttons[index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_preview(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        group_by = self._selected_group_by()
        if group_by is None:
            draw_centered_text(surface, loc.t("lesson.l12.builder.pick_group_by_hint"), (CENTER_X, RESULT_TOP), 15, colors.BUTTON_TEXT_DISABLED)
            return

        frame, total, error = self._compute_preview()
        if error is not None or frame is None:
            draw_centered_text(surface, loc.t("lesson.l12.builder.cannot_compute"), (CENTER_X, RESULT_TOP), 15, colors.BUTTON_TEXT_DISABLED)
            return

        columns = list(frame.columns)
        header = "  |  ".join(columns)
        draw_centered_text(surface, header, (CENTER_X, RESULT_TOP), 14, colors.TEXT)

        preview_rows = frame.head(MAX_PREVIEW_ROWS)
        for row_index, row in enumerate(preview_rows.itertuples(index=False)):
            y = RESULT_TOP + HEADER_Y_GAP + row_index * ROW_HEIGHT
            line = "  |  ".join(_format_cell(value) for value in row)
            draw_centered_text(surface, line, (CENTER_X, y), 14, colors.BUTTON_TEXT_DISABLED)

        if total > MAX_PREVIEW_ROWS:
            note_y = RESULT_TOP + HEADER_Y_GAP + MAX_PREVIEW_ROWS * ROW_HEIGHT + 8
            note = loc.t("lesson.l12.builder.more_groups").format(shown=MAX_PREVIEW_ROWS, total=total)
            draw_centered_text(surface, note, (CENTER_X, note_y), 13, colors.BUTTON_TEXT_DISABLED)
        else:
            note_y = RESULT_TOP + HEADER_Y_GAP + total * ROW_HEIGHT + 8
            note = loc.t("lesson.l12.builder.group_count").format(total=total)
            draw_centered_text(surface, note, (CENTER_X, note_y), 13, colors.BUTTON_TEXT_DISABLED)

        if self.guided:
            hint_key = "lesson.l12.builder.group_by_hint" if self._is_group_by_step() else None
            if hint_key:
                draw_wrapped_text(surface, loc.t(hint_key), (CENTER_X - 300, HINT_Y), 600, 14, colors.BUTTON_TEXT_DISABLED)

from collections.abc import Callable

import pandas as pd
import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.lessons.framework.aggregation import AggregateOption, AggregationRequest, GroupByOption, PipelineChoices
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 90
PROMPT_SIZE = 20
PROMPT_MAX_WIDTH = 820
LEFT_COLUMN_X = 260
RIGHT_COLUMN_X = 700
COLUMN_LABEL_Y = 130
OPTION_SIZE = (220, 40)
FIRST_OPTION_Y = 160
OPTION_SPACING = 46
RESULT_RECT = pygame.Rect(230, 280, 500, 130)
MAX_PREVIEW_ROWS = 5
PREVIEW_ROW_HEIGHT = 22
HINT_Y = 450
NAV_BUTTON_Y = 495


def _format_group_key(value: object) -> str:
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _format_value(value: float) -> str:
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


class PipelineBuilderScene(Scene):
    """Build a group-by + aggregate pipeline for a stakeholder's request
    (spec §25 Lesson 12 'GroupBy Kitchen'): pick a group-by key and an
    aggregate function from two independent button groups, and a live
    result table - computed with real pandas, capped at MAX_PREVIEW_ROWS -
    updates as soon as both are chosen. Getting the pair right isn't
    enough to move on by accident: Next stays disabled until both choices
    are made, same as every other stage scene's completion gate.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split.

    Committing a complete (group-by, aggregate) pair also records it into
    `context` (workbench/context.py) as an AnalyticalAction with a real,
    obviously-correct pandas equivalent (e.g. "orders.groupby('store_id')
    ['revenue'].sum()") - unlike Lesson 29's FindingPickerScene proof,
    whose python_code calls a helper function rather than real pandas.
    `_commit_if_complete` fires on every click once both sides are chosen,
    including if the student changes their mind and re-picks a different
    pair for the *same* request - keyed by `request.key`, so that request's
    one slot in the Python Mirror updates to reflect the current choice
    instead of accumulating a line per click."""

    def __init__(
        self,
        app,
        title_key: str,
        dataset: Dataset,
        requests: tuple[AggregationRequest, ...],
        on_complete: Callable[[PipelineChoices], None],
        guided: bool = True,
        context: LessonContext | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.dataset = dataset
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.context = context if context is not None else LessonContext()
        self.request_index = 0
        self.choices: PipelineChoices = {}
        self._group_by_choice: str | None = None
        self._aggregate_choice: str | None = None
        self._load_pending_choice()
        self._rebuild_buttons()

    def _current_request(self) -> AggregationRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _load_pending_choice(self) -> None:
        # Only called when switching requests (init/back/next) - a lone
        # group-by or aggregate pick isn't committed to self.choices until
        # both sides are chosen, so rebuilding buttons after a single pick
        # must NOT reset that still-pending pick back to None.
        existing = self.choices.get(self._current_request().key)
        self._group_by_choice = existing[0] if existing else None
        self._aggregate_choice = existing[1] if existing else None

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()

        buttons = []
        for index, option in enumerate(request.group_by_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (LEFT_COLUMN_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_group_by(option.key)))
        for index, option in enumerate(request.aggregate_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (RIGHT_COLUMN_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose_aggregate(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.request_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_request() else loc.t("brief.next")
        both_chosen = self._group_by_choice is not None and self._aggregate_choice is not None
        self.next_button = Button(next_rect, next_label, self._next, enabled=both_chosen)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose_group_by(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._group_by_choice = option_key
            self._commit_if_complete()
            self._rebuild_buttons()

        return choose

    def _make_choose_aggregate(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._aggregate_choice = option_key
            self._commit_if_complete()
            self._rebuild_buttons()

        return choose

    def _commit_if_complete(self) -> None:
        if self._group_by_choice is not None and self._aggregate_choice is not None:
            request = self._current_request()
            self.choices[request.key] = (self._group_by_choice, self._aggregate_choice)
            group_by = self._selected_group_by(request)
            aggregate = self._selected_aggregate(request)
            python_code = f"{self.dataset.name}.groupby('{group_by.column}')['{request.value_column}'].{aggregate.func}()"
            # key=request.key: changing a pick and coming back to an
            # earlier one re-commits the *same* request - this updates
            # that request's one slot to the current choice instead of
            # accumulating a line per click.
            action = self.context.record_action(label_key=group_by.label_key, python_code=python_code, key=request.key)
            self.context.record_evidence(label_key=group_by.label_key, source_action=action, key=request.key)

    def _back(self) -> None:
        if self.request_index > 0:
            self.request_index -= 1
            self._load_pending_choice()
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_request().key not in self.choices:
            return
        if self._is_last_request():
            self.on_complete(dict(self.choices))
            return
        self.request_index += 1
        self._load_pending_choice()
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def _selected_group_by(self, request: AggregationRequest) -> GroupByOption | None:
        if self._group_by_choice is None:
            return None
        return next(option for option in request.group_by_options if option.key == self._group_by_choice)

    def _selected_aggregate(self, request: AggregationRequest) -> AggregateOption | None:
        if self._aggregate_choice is None:
            return None
        return next(option for option in request.aggregate_options if option.key == self._aggregate_choice)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        request = self._current_request()

        progress = f"{self.request_index + 1} / {len(self.requests)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)

        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        draw_centered_text(surface, loc.t("lesson.l12.group_by_label"), (LEFT_COLUMN_X, COLUMN_LABEL_Y), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t("lesson.l12.aggregate_label"), (RIGHT_COLUMN_X, COLUMN_LABEL_Y), 16, colors.BUTTON_TEXT_DISABLED)

        self.buttons.draw(surface)
        self._draw_selected_indicators(surface, request)
        self._draw_result_preview(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicators(self, surface: pygame.Surface, request: AggregationRequest) -> None:
        for option, choice_key in (
            (self._selected_group_by(request), self._group_by_choice),
            (self._selected_aggregate(request), self._aggregate_choice),
        ):
            if option is None:
                continue
            all_options = request.group_by_options if option in request.group_by_options else request.aggregate_options
            index = next(i for i, candidate in enumerate(all_options) if candidate.key == choice_key)
            button_index = index if all_options is request.group_by_options else len(request.group_by_options) + index
            rect = self.buttons.buttons[button_index].rect
            marker = pygame.Rect(rect.left, rect.top + 4, 4, rect.height - 8)
            pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_result_preview(self, surface: pygame.Surface, request: AggregationRequest) -> None:
        loc = self.app.localization
        group_by = self._selected_group_by(request)
        aggregate = self._selected_aggregate(request)
        if group_by is None or aggregate is None:
            draw_centered_text(surface, loc.t("lesson.l12.pick_both_hint"), (CENTER_X, RESULT_RECT.top + 20), 15, colors.BUTTON_TEXT_DISABLED)
            return

        grouped = self.dataset.frame.groupby(group_by.column)[request.value_column].agg(aggregate.func)
        rows = list(grouped.items())

        header = f"{group_by.column}  |  {request.value_column} ({aggregate.key})"
        draw_centered_text(surface, header, (CENTER_X, RESULT_RECT.top), 14, colors.TEXT)

        for index, (key, value) in enumerate(rows[:MAX_PREVIEW_ROWS]):
            y = RESULT_RECT.top + 26 + index * PREVIEW_ROW_HEIGHT
            line = f"{_format_group_key(key)}  |  {_format_value(value)}"
            draw_centered_text(surface, line, (CENTER_X, y), 14, colors.BUTTON_TEXT_DISABLED)

        if len(rows) > MAX_PREVIEW_ROWS:
            note_y = RESULT_RECT.top + 26 + MAX_PREVIEW_ROWS * PREVIEW_ROW_HEIGHT + 6
            draw_centered_text(surface, loc.t("workbench.data.more_rows"), (CENTER_X, note_y), 13, colors.BUTTON_TEXT_DISABLED)

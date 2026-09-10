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
OPTION_SIZE = (280, 40)
OPTION_SPACING = 300
SUMMARY_TOP = 220
SUMMARY_LINE_HEIGHT = 22
PREVIEW_TOP = 330
HEADER_Y_GAP = 18
ROW_HEIGHT = 20
MAX_PREVIEW_ROWS = 5
"""Real, deliberate: this lesson's own dataset scale (120 orders, 100
customers, 47 promotions) means an outer join can return up to 140 rows -
capped the same way AggregationBuilderScene's own preview already is, with
an explicit real count in the truncation note."""
NAV_BUTTON_Y = 500
HINT_Y = 470


@dataclass(frozen=True)
class JoinTypeOption:
    key: str
    label_key: str
    how: str  # a real pandas merge() how value: "inner" | "left" | "outer"


def _format_cell(value: object) -> str:
    if pd.isna(value):
        return "NaN"
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float):
        return f"{value:,.0f}" if value.is_integer() else f"{value:,.2f}"
    return str(value)


class JoinBuilderScene(Scene):
    """One real, live-computed join attempt - pick a join type, see the
    real `left_dataset.frame.merge(right_dataset.frame, on=join_column,
    how=..., indicator=True, validate=validate)` result: total row count,
    the real `_merge` breakdown (both/left_only/right_only), and a capped
    live preview table - never a node-per-row visualization (the retired
    JunctionScene's own approach, which cannot scale past a handful of
    rows without putting 100+ shapes on screen).

    When `validate` is set and the real merge raises
    `pandas.errors.MergeError`, that's caught and shown as its own
    distinct, real state (the actual exception's own message) instead of
    crashing or silently falling back - this is what makes `validate=`
    load-bearing rather than decorative: a real, controlled failure the
    student can see happen.

    `initial_choice` seeds a fresh instance with a prior pass's pick (a
    revision is just constructing this scene again, pre-filled, never a
    bespoke partial-resume mechanism - matching AggregationBuilderScene's
    own established pattern). `output_variable_name`/`mirror_action_key`
    mirror AggregationBuilderScene's own fix for the same class of bug:
    the recorded Python Mirror line must be a real, assignable statement
    a later action can reference by name, and a revision must update the
    same Mirror slot in place rather than appending a stale line.

    Never records a toggle/pick as its own AnalyticalAction or Evidence -
    the real join attempt is recorded as ONE action, only once a choice is
    confirmed via Continue (matches the "toggling/picking mechanics are
    never themselves Evidence" discipline established since L11's own
    DistributionExplorerScene)."""

    def __init__(
        self,
        app,
        title_key: str,
        left_dataset: Dataset,
        right_dataset: Dataset,
        join_column: str,
        join_type_options: tuple[JoinTypeOption, ...],
        on_complete: Callable[[str, bool], None],  # (chosen JoinTypeOption.key, real merge succeeded)
        context: LessonContext,
        validate: str | None = None,
        initial_choice: str | None = None,
        output_variable_name: str = "result",
        mirror_action_key: str = "join_pipeline",
        hint_key: str | None = None,
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.left_dataset = left_dataset
        self.right_dataset = right_dataset
        self.join_column = join_column
        self.join_type_options = join_type_options
        self.on_complete = on_complete
        self.context = context
        self.validate = validate
        self.output_variable_name = output_variable_name
        self.mirror_action_key = mirror_action_key
        self.hint_key = hint_key
        self.guided = guided
        self.choice: str | None = initial_choice
        self._rebuild_buttons()

    def _selected_option(self) -> JoinTypeOption | None:
        if self.choice is None:
            return None
        return next(o for o in self.join_type_options if o.key == self.choice)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []
        count = len(self.join_type_options)
        start_x = CENTER_X - (count - 1) * OPTION_SPACING // 2
        for index, option in enumerate(self.join_type_options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (start_x + index * OPTION_SPACING, FIRST_OPTION_Y)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        continue_rect = pygame.Rect(0, 0, 160, 44)
        continue_rect.center = (CENTER_X, NAV_BUTTON_Y)
        label = loc.t("brief.finish")
        self.continue_button = Button(continue_rect, label, self._finish, enabled=self.choice is not None)
        buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choice = option_key
            self._rebuild_buttons()

        return choose

    def _attempt_merge(self) -> tuple[pd.DataFrame | None, str | None]:
        """(merged_frame_or_None, merge_error_message_or_None) for
        whichever option is currently selected."""
        option = self._selected_option()
        if option is None:
            return None, None
        try:
            merged = self.left_dataset.frame.merge(
                self.right_dataset.frame, on=self.join_column, how=option.how, indicator=True, validate=self.validate
            )
            return merged, None
        except pd.errors.MergeError as exc:
            return None, str(exc)

    def _merge_call_code(self, option: JoinTypeOption) -> str:
        validate_kwarg = f", validate='{self.validate}'" if self.validate else ""
        return (
            f"{self.left_dataset.name}.merge({self.right_dataset.name}, on='{self.join_column}', "
            f"how='{option.how}', indicator=True{validate_kwarg})"
        )

    def _finish(self) -> None:
        option = self._selected_option()
        if option is None:
            return
        merged, error = self._attempt_merge()
        call_code = self._merge_call_code(option)
        if error is not None:
            python_code = f"import pandas as pd\ntry:\n    {call_code}\nexcept pd.errors.MergeError as exc:\n    str(exc)"
        else:
            python_code = f"{self.output_variable_name} = {call_code}"
        self.context.record_action(label_key=self.title_key, python_code=python_code, key=self.mirror_action_key)
        self.on_complete(self.choice, error is None)

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 26, colors.TEXT)
        draw_centered_wrapped_text(surface, loc.t("lesson.l13.builder.pick_join_type"), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)
        self._draw_result(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 300, HINT_Y), 600, 14, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        if self.choice is None:
            return
        index = next(i for i, option in enumerate(self.join_type_options) if option.key == self.choice)
        rect = self.buttons.buttons[index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_result(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        if self.choice is None:
            draw_centered_text(surface, loc.t("lesson.l13.builder.pick_hint"), (CENTER_X, SUMMARY_TOP), 15, colors.BUTTON_TEXT_DISABLED)
            return

        merged, error = self._attempt_merge()
        if error is not None:
            draw_centered_text(surface, loc.t("lesson.l13.builder.validation_failed_title"), (CENTER_X, SUMMARY_TOP), 16, colors.BUTTON_FOCUS_BORDER)
            # pandas' own MergeError message embeds real newlines/indentation
            # (e.g. "...not a many-to-one merge\n\nDuplicates in right:\n
            # customer_id\n   C004\n..."); pygame's font rendering doesn't
            # honor those - it renders the raw \n as a missing-glyph box
            # instead of wrapping, caught only by a real screenshot.
            # Collapsing all whitespace to single spaces lets
            # draw_centered_wrapped_text's own real word-wrap take over.
            flattened_error = " ".join(error.split())
            draw_centered_wrapped_text(surface, flattened_error, (CENTER_X, SUMMARY_TOP + 28), PROMPT_MAX_WIDTH, 13, colors.TEXT)
            return

        total = len(merged)
        counts = merged["_merge"].value_counts()
        both = int(counts.get("both", 0))
        left_only = int(counts.get("left_only", 0))
        right_only = int(counts.get("right_only", 0))

        summary = loc.t("lesson.l13.builder.result_summary").format(total=total, both=both, left_only=left_only, right_only=right_only)
        draw_centered_wrapped_text(surface, summary, (CENTER_X, SUMMARY_TOP), PROMPT_MAX_WIDTH, 15, colors.BUTTON_FOCUS_BORDER)

        preview_columns = [c for c in merged.columns if c != "_merge"]
        header = "  |  ".join(preview_columns)
        draw_centered_text(surface, header, (CENTER_X, PREVIEW_TOP), 13, colors.TEXT)

        preview_rows = merged[preview_columns].head(MAX_PREVIEW_ROWS)
        for row_index, row in enumerate(preview_rows.itertuples(index=False)):
            y = PREVIEW_TOP + HEADER_Y_GAP + row_index * ROW_HEIGHT
            line = "  |  ".join(_format_cell(value) for value in row)
            draw_centered_text(surface, line, (CENTER_X, y), 13, colors.BUTTON_TEXT_DISABLED)

        note_y = PREVIEW_TOP + HEADER_Y_GAP + min(total, MAX_PREVIEW_ROWS) * ROW_HEIGHT + 8
        if total > MAX_PREVIEW_ROWS:
            note = loc.t("lesson.l13.builder.more_rows").format(shown=MAX_PREVIEW_ROWS, total=total)
        else:
            note = loc.t("lesson.l13.builder.row_count").format(total=total)
        draw_centered_text(surface, note, (CENTER_X, note_y), 12, colors.BUTTON_TEXT_DISABLED)

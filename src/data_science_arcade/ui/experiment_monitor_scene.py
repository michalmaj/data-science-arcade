from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.brief import BriefOption
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.number_format import format_number, format_percent
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
WEEK_LABEL_Y = 78
TABLE_TOP = 116
ROW_HEIGHT = 56
LABEL_X = 60
VALUE_LINE_SIZE = 16
CI_LINE_SIZE = 15
RECOMMENDATION_GAP = 22
FIRST_OPTION_GAP = 30
OPTION_SIZE = (360, 38)
OPTION_SPACING = 42
CONTINUE_GAP = 26
CONTINUE_BUTTON_SIZE = (280, 44)


@dataclass(frozen=True)
class ExperimentMetricRow:
    """One real metric's own row at one real checkpoint - every value
    (rates/diff/CI) precomputed by the caller (data.py), never computed in
    this scene, matching AssignmentAuditScene's own division of labor.
    `threshold_cleared` is True when the ENTIRE interval clears this row's
    own pre-set policy threshold (whatever it is for this metric) -
    `warn`, separately, is True only for a real guardrail breach, so the
    scene can give that specific case a distinct visual treatment without
    knowing anything about "primary" vs "guardrail" semantics itself.
    `evidence_key`, when set, becomes a real EvidenceItem at Continue -
    left None for rows whose citable evidence role lives elsewhere (the
    primary's own week-7 role is carried by the mandatory contrast
    reveal, never duplicated here)."""

    label_key: str
    control_rate: float
    treatment_rate: float
    diff: float
    ci_lower: float
    ci_upper: float
    threshold_cleared: bool
    warn: bool
    status_label_key: str
    evidence_key: str | None = None


@dataclass(frozen=True)
class ExperimentCheckpoint:
    """One real point in the experiment's timeline. `recommendation_record_key`
    is None on the final (planned-end) checkpoint - the one where there's
    genuinely nothing left to recommend, only to decide."""

    week: int
    is_final: bool
    rows: tuple[ExperimentMetricRow, ...]
    mirror_action_label_key: str
    mirror_python_code: str
    record_key: str
    recommendation_record_key: str | None = None


class ExperimentMonitorScene(Scene):
    """Walks a fixed sequence of real checkpoints (week 1 -> week 3 ->
    week 7 for the main Quick Pay case) linearly - every student sees
    every checkpoint's real numbers regardless of what they pick along
    the way. At each non-final checkpoint, a real recommendation pulse-
    check is recorded as Python Mirror provenance only (`record_action`,
    never `record_evidence`) - a trajectory signal a later scorer MAY read
    for a positive recalibration observation, but which can never gate
    progression or cap the core dimensions: picking any option still just
    advances to the next checkpoint. The final checkpoint has no
    recommendation widget at all - only a single, always-enabled Continue.

    Built new rather than extending CheckpointMonitorScene, whose own
    Stop/Continue mechanic lets a student end monitoring early - the exact
    opposite of what every student needing to see the real week-7 result
    (and both guardrails) requires here. Retired alongside
    framework/monitoring.py, whose MonitoringCheckpoint/MetricRow this
    scene does not reuse (no CI, no LessonContext, no real recommendation
    capture - a real architectural extension, not a hack)."""

    def __init__(
        self,
        app,
        title_key: str,
        checkpoints: tuple[ExperimentCheckpoint, ...],
        total_planned_weeks: int,
        context: LessonContext,
        on_complete: Callable[[dict[int, str]], None],
        recommendation_prompt_key: str,
        recommendation_options: tuple[BriefOption, ...],
        recommendation_action_label_key: str,
        final_continue_label_key: str,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.checkpoints = checkpoints
        self.total_planned_weeks = total_planned_weeks
        self.context = context
        self.on_complete = on_complete
        self.recommendation_prompt_key = recommendation_prompt_key
        self.recommendation_options = recommendation_options
        self.recommendation_action_label_key = recommendation_action_label_key
        self.final_continue_label_key = final_continue_label_key
        self.checkpoint_index = 0
        self._recommendations: dict[int, str] = {}
        self._current_choice: str | None = None
        self._rebuild_buttons()

    def _current_checkpoint(self) -> ExperimentCheckpoint:
        return self.checkpoints[self.checkpoint_index]

    def _needs_recommendation(self) -> bool:
        return self._current_checkpoint().recommendation_record_key is not None

    def _rows_bottom(self) -> int:
        return TABLE_TOP + len(self._current_checkpoint().rows) * ROW_HEIGHT

    def _first_option_y(self) -> int:
        return self._rows_bottom() + RECOMMENDATION_GAP + FIRST_OPTION_GAP

    def _continue_y(self) -> int:
        if not self._needs_recommendation():
            return self._rows_bottom() + RECOMMENDATION_GAP + FIRST_OPTION_GAP
        options_bottom = self._first_option_y() + (len(self.recommendation_options) - 1) * OPTION_SPACING + OPTION_SIZE[1] // 2
        return options_bottom + CONTINUE_GAP

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []

        if self._needs_recommendation():
            first_y = self._first_option_y()
            for index, option in enumerate(self.recommendation_options):
                rect = pygame.Rect(0, 0, *OPTION_SIZE)
                rect.center = (CENTER_X, first_y + index * OPTION_SPACING)
                buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        continue_rect = pygame.Rect(0, 0, *CONTINUE_BUTTON_SIZE)
        continue_rect.center = (CENTER_X, self._continue_y())
        label_key = self.final_continue_label_key if self._current_checkpoint().is_final else "runtime.continue_button"
        enabled = (not self._needs_recommendation()) or self._current_choice is not None
        self.continue_button = Button(continue_rect, loc.t(label_key), self._continue, enabled=enabled)
        buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self._current_choice = option_key
            self._rebuild_buttons()

        return choose

    def _continue(self) -> None:
        if self._needs_recommendation() and self._current_choice is None:
            return
        checkpoint = self._current_checkpoint()
        action = self.context.record_action(
            label_key=checkpoint.mirror_action_label_key,
            python_code=checkpoint.mirror_python_code,
            key=checkpoint.record_key,
        )
        locale = self.app.localization.locale
        for row in checkpoint.rows:
            if row.evidence_key is not None:
                diff_pp = format_number(row.diff * 100, locale, signed=True)
                ci_lower_pp = format_number(row.ci_lower * 100, locale, signed=True)
                ci_upper_pp = format_number(row.ci_upper * 100, locale, signed=True)
                detail = f"{diff_pp}pp [{ci_lower_pp}pp, {ci_upper_pp}pp]"
                self.context.record_evidence(label_key=row.evidence_key, source_action=action, key=row.evidence_key, detail=detail)

        if checkpoint.recommendation_record_key is not None:
            assert self._current_choice is not None
            self.context.record_action(
                label_key=self.recommendation_action_label_key,
                python_code=f"week{checkpoint.week}_recommendation = '{self._current_choice}'",
                key=checkpoint.recommendation_record_key,
            )
            self._recommendations[checkpoint.week] = self._current_choice

        if checkpoint.is_final:
            self.on_complete(dict(self._recommendations))
            return
        self.checkpoint_index += 1
        self._current_choice = None
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        checkpoint = self._current_checkpoint()

        progress = f"{self.checkpoint_index + 1} / {len(self.checkpoints)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 26, colors.TEXT)

        week_text = f"{loc.t('lesson.l20.monitor.week_label')} {checkpoint.week} / {self.total_planned_weeks}"
        draw_centered_text(surface, week_text, (CENTER_X, WEEK_LABEL_Y), 16, colors.BUTTON_FOCUS_BORDER)

        for index, row in enumerate(checkpoint.rows):
            y = TABLE_TOP + index * ROW_HEIGHT
            value_color = colors.SEGMENT_SECONDARY if row.warn else colors.TEXT
            values_text = (
                f"{loc.t(row.label_key)}  -  "
                f"{loc.t('lesson.l20.monitor.control_label')} {format_percent(row.control_rate, loc.locale)}   "
                f"{loc.t('lesson.l20.monitor.treatment_label')} {format_percent(row.treatment_rate, loc.locale)}"
            )
            draw_wrapped_text(surface, values_text, (LABEL_X, y), 860, VALUE_LINE_SIZE, colors.TEXT)

            ci_color = colors.SEGMENT_SECONDARY if row.warn else (colors.BUTTON_FOCUS_BORDER if row.threshold_cleared else colors.BUTTON_TEXT_DISABLED)
            diff_pp = format_number(row.diff * 100, loc.locale, signed=True)
            ci_lower_pp = format_number(row.ci_lower * 100, loc.locale, signed=True)
            ci_upper_pp = format_number(row.ci_upper * 100, loc.locale, signed=True)
            ci_text = (
                f"{loc.t('lesson.l20.monitor.diff_label')} {diff_pp}pp   "
                f"{loc.t('lesson.l20.monitor.ci_label')} [{ci_lower_pp}pp, {ci_upper_pp}pp]   "
                f"{loc.t(row.status_label_key)}"
            )
            draw_wrapped_text(surface, ci_text, (LABEL_X, y + 22), 860, CI_LINE_SIZE, ci_color)

        if self._needs_recommendation():
            draw_centered_text(surface, loc.t(self.recommendation_prompt_key), (CENTER_X, self._rows_bottom() + RECOMMENDATION_GAP), 16, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        if self._current_choice is None or not self._needs_recommendation():
            return
        selected_index = next(i for i, option in enumerate(self.recommendation_options) if option.key == self._current_choice)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

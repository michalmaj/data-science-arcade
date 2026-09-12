from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text, wrap_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
CARD_RECT = pygame.Rect(40, 96, 880, 74)
TABLE_TOP = 190
TABLE_ROW_HEIGHT = 30
DIAGNOSTIC_COLUMN_X = 130
TREATMENT_COLUMN_X = 430
CONTROL_COLUMN_X = 610
GAP_COLUMN_X = 790
CONTINUE_BUTTON_SIZE = (200, 44)
CONTINUE_BUTTON_Y = 470


@dataclass(frozen=True)
class AuditRow:
    """One real diagnostic row - N split, platform share, or average
    tenure. Three different formatters (a plain count, a percentage, a
    day count) in the same table is exactly why SegmentSlicerScene's own
    value_format already had to stop taking a bare float - see its own
    docstring."""

    key: str
    label_key: str
    treatment_value: float
    control_value: float
    value_format: Callable[[float], str]
    gap_format: Callable[[float], str]


class AssignmentAuditScene(Scene):
    """Shows the real, already-executed consequence of ONE assignment
    design - never a candidate picker. The design itself is chosen
    entirely outside this scene (a plain BriefField, no numbers visible
    near it); this scene only ever renders what a real, committed
    execution produced. No interpret step - interpretation is the Final
    Randomization Brief's own job, not duplicated here.

    Built new rather than reusing SegmentSlicerScene (which lets a
    student freely re-pick and preview any candidate's own table before
    committing - exactly the "flip through and pick the prettiest
    realized balance" anti-pattern this lesson exists to dismantle, and
    which also has no LessonContext parameter at all) or
    ComparisonRevealScene (a flat single-value-per-line shape that can't
    hold a real 3-row x treatment/control/gap table with 3 different
    formatters in one table).

    `mechanism_evidence_key`/`balance_evidence_key` record the current
    truth of whichever design this instance renders, keyed so a second
    visit (after a real revision) updates those two roles in place
    rather than doubling them - matching every other lesson's "one real
    revision replaces, not appends" shape. Pass `contrast_evidence_key`
    instead (leaving the other two None) for the lesson's own mandatory,
    un-revisable mechanism-contrast beat, whose own single fact must
    never be overwritten by a later audit - see l18's own scenario.py."""

    def __init__(
        self,
        app,
        title_key: str,
        narrative_keys: tuple[str, ...],
        mechanism_label_key: str,
        mechanism_description_key: str,
        rows: tuple[AuditRow, ...],
        mirror_action_label_key: str,
        mirror_python_code: str,
        context: LessonContext,
        record_key: str,
        on_complete: Callable[[], None],
        mechanism_evidence_key: str | None = None,
        balance_evidence_key: str | None = None,
        contrast_evidence_key: str | None = None,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.narrative_keys = narrative_keys
        self.mechanism_label_key = mechanism_label_key
        self.mechanism_description_key = mechanism_description_key
        self.rows = rows
        self.mirror_action_label_key = mirror_action_label_key
        self.mirror_python_code = mirror_python_code
        self.context = context
        self.record_key = record_key
        self.on_complete = on_complete
        self.mechanism_evidence_key = mechanism_evidence_key
        self.balance_evidence_key = balance_evidence_key
        self.contrast_evidence_key = contrast_evidence_key

        loc = self.app.localization
        continue_rect = pygame.Rect(0, 0, *CONTINUE_BUTTON_SIZE)
        continue_rect.center = (CENTER_X, CONTINUE_BUTTON_Y)
        self.continue_button = Button(continue_rect, loc.t("runtime.continue_button"), self._continue)
        self.buttons = ButtonGroup([self.continue_button])

    def _continue(self) -> None:
        action = self.context.record_action(
            label_key=self.mirror_action_label_key,
            python_code=self.mirror_python_code,
            key=self.record_key,
        )
        if self.contrast_evidence_key is not None:
            self.context.record_evidence(label_key=self.contrast_evidence_key, source_action=action, key=self.contrast_evidence_key)
        else:
            self.context.record_evidence(label_key=self.mechanism_evidence_key, source_action=action, key=self.mechanism_evidence_key)
            self.context.record_evidence(label_key=self.balance_evidence_key, source_action=action, key=self.balance_evidence_key)
        self.on_complete()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 40), 26, colors.TEXT)

        y = 68
        narrative_font = get_font(14)
        for key in self.narrative_keys:
            text = loc.t(key)
            draw_wrapped_text(surface, text, (40, y), 880, 14, colors.BUTTON_TEXT_DISABLED)
            y += len(wrap_text(text, narrative_font, 880)) * 18

        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, CARD_RECT, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, CARD_RECT, width=1, border_radius=8)
        draw_single_line(surface, loc.t(self.mechanism_label_key), (CARD_RECT.left + 16, CARD_RECT.top + 10), CARD_RECT.width - 32, 16, colors.BUTTON_FOCUS_BORDER)
        draw_wrapped_text(
            surface, loc.t(self.mechanism_description_key), (CARD_RECT.left + 16, CARD_RECT.top + 34), CARD_RECT.width - 32, 13, colors.TEXT
        )

        self._draw_table(surface)
        self.buttons.draw(surface)

    def _draw_table(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        header_y = TABLE_TOP
        draw_single_line(surface, loc.t("lesson.l18.audit.column_diagnostic"), (DIAGNOSTIC_COLUMN_X - 110, header_y), 200, 14, colors.BUTTON_TEXT_DISABLED)
        draw_single_line(surface, loc.t("lesson.l18.audit.column_treatment"), (TREATMENT_COLUMN_X - 60, header_y), 140, 14, colors.BUTTON_TEXT_DISABLED)
        draw_single_line(surface, loc.t("lesson.l18.audit.column_control"), (CONTROL_COLUMN_X - 60, header_y), 140, 14, colors.BUTTON_TEXT_DISABLED)
        draw_single_line(surface, loc.t("lesson.l18.audit.column_gap"), (GAP_COLUMN_X - 60, header_y), 140, 14, colors.BUTTON_TEXT_DISABLED)

        for index, row in enumerate(self.rows):
            y = header_y + (index + 1) * TABLE_ROW_HEIGHT
            gap = row.treatment_value - row.control_value
            draw_single_line(surface, loc.t(row.label_key), (DIAGNOSTIC_COLUMN_X - 110, y), 220, 15, colors.TEXT)
            draw_single_line(surface, row.value_format(row.treatment_value), (TREATMENT_COLUMN_X - 60, y), 140, 15, colors.TEXT)
            draw_single_line(surface, row.value_format(row.control_value), (CONTROL_COLUMN_X - 60, y), 140, 15, colors.TEXT)
            draw_single_line(surface, row.gap_format(gap), (GAP_COLUMN_X - 60, y), 140, 15, colors.BUTTON_FOCUS_BORDER)

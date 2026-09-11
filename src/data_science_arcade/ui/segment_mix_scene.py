from collections.abc import Callable
from dataclasses import dataclass

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text
from data_science_arcade.workbench.context import LessonContext

CENTER_X = LOGICAL_SIZE[0] // 2
ASK_Y = 44
ASK_MAX_WIDTH = 860
PICKER_Y = 96
PICKER_SIZE = (200, 36)
PICKER_SPACING = 220
TABLE_TOP = 150
HEADER_Y = TABLE_TOP
ROW_HEIGHT = 30
SEGMENT_COLUMN_X = CENTER_X - 280
Q1_SHARE_COLUMN_X = CENTER_X - 100
Q1_RATE_COLUMN_X = CENTER_X + 40
Q2_SHARE_COLUMN_X = CENTER_X + 180
Q2_RATE_COLUMN_X = CENTER_X + 320
FIRST_FINISH_Y = 460
HINT_Y = 420


def _pct(value: float) -> str:
    return f"{value:.1f}%"


@dataclass(frozen=True)
class SegmentRow:
    key: str
    label_key: str
    q1_share: float
    q1_rate: float
    q2_share: float
    q2_rate: float


@dataclass(frozen=True)
class DimensionOption:
    """One real, complete dimension view - picking it renders its own 2
    real rows (`segment | Q1 share | Q1 rate | Q2 share | Q2 rate`), never
    a partial or reshaped table. `evidence_keys` are the real facts
    genuinely visible in this table (e.g. device: both rates declined,
    share shifted sharply; region: both rows track the aggregate,
    mix stays even) - recorded unconditionally by this scene itself once
    Finish confirms the dimension was actually inspected, decoupled from
    whatever a later reveal's own interpretation gets right or wrong
    (fact seen != correct first interpretation, the same discipline every
    ComparisonRevealScene reveal already follows)."""

    key: str
    label_key: str
    rows: tuple[SegmentRow, SegmentRow]
    mirror_code: str
    evidence_keys: tuple[str, ...] = ()


class SegmentMixScene(Scene):
    """Shows one real, live table for a chosen dimension - rate AND share
    together, for both periods, never split across separate screens. With
    more than one `dimension_options` entry, picking one is a free,
    un-punished toggle (matches this project's own "toggling/picking
    mechanics are never themselves Evidence" discipline) - Finish commits
    to "I've inspected this one." With exactly one entry, no picker
    renders at all - a "pinned" mode for a stage that already knows which
    dimension it needs shown (e.g. a mandatory device follow-up after a
    region-first path's own null finding).

    Deliberately not `SegmentSlicerScene` (`ui/segment_slicer_scene.py`):
    that scene's own data shape is one before/after rate pair per row,
    with no composition/share column at all, and no `LessonContext`
    integration in any of its 5 real current uses - reshaping it would
    mean hacking a scene 5 other lessons depend on, not fixing L15's own
    shape. This scene owns its own Evidence recording directly instead,
    the same way `ChartBuilderScene`/`JoinBuilderScene` do."""

    def __init__(
        self,
        app,
        title_key: str,
        ask_prompt_key: str,
        dimension_options: tuple[DimensionOption, ...],
        on_complete: Callable[[str], None],
        context: LessonContext,
        initial_choice: str | None = None,
        hint_key: str | None = None,
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.ask_prompt_key = ask_prompt_key
        self.dimension_options = dimension_options
        self.on_complete = on_complete
        self.context = context
        self.hint_key = hint_key
        self.guided = guided
        self.choice: str | None = initial_choice if initial_choice is not None else (
            dimension_options[0].key if len(dimension_options) == 1 else None
        )
        self._rebuild_buttons()

    def _selected_option(self) -> DimensionOption | None:
        if self.choice is None:
            return None
        return next(o for o in self.dimension_options if o.key == self.choice)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []

        if len(self.dimension_options) > 1:
            count = len(self.dimension_options)
            start_x = CENTER_X - (count - 1) * PICKER_SPACING // 2
            for index, option in enumerate(self.dimension_options):
                rect = pygame.Rect(0, 0, *PICKER_SIZE)
                rect.center = (start_x + index * PICKER_SPACING, PICKER_Y)
                buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        finish_rect = pygame.Rect(0, 0, 160, 44)
        finish_rect.center = (CENTER_X, FIRST_FINISH_Y)
        self.finish_button = Button(finish_rect, loc.t("brief.finish"), self._finish, enabled=self.choice is not None)
        buttons.append(self.finish_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choice = option_key
            self._rebuild_buttons()

        return choose

    def _finish(self) -> None:
        option = self._selected_option()
        if option is None:
            return
        # Keyed by the DIMENSION itself (never a fixed per-scene-instance
        # key) - a picker offering both region/device and a later pinned
        # re-show of one of them are still two real, independently
        # necessary Mirror definitions. A shared fixed key would let a
        # later dimension's own action silently overwrite an earlier
        # dimension's own real groupby line in place, breaking any
        # downstream reveal whose own recorded python_code still
        # references the now-deleted variable.
        action = self.context.record_action(label_key=self.title_key, python_code=option.mirror_code, key=f"segment_mix_{option.key}")
        for evidence_key in option.evidence_keys:
            self.context.record_evidence(label_key=evidence_key, source_action=action, key=evidence_key)
        self.on_complete(self.choice)

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 20), 22, colors.TEXT)
        draw_centered_wrapped_text(surface, loc.t(self.ask_prompt_key), (CENTER_X, ASK_Y), ASK_MAX_WIDTH, 16, colors.BUTTON_FOCUS_BORDER)

        self._draw_table(surface)
        self.buttons.draw(surface)
        self._draw_selected_indicator(surface)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 300, HINT_Y), 600, 14, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicator(self, surface: pygame.Surface) -> None:
        if self.choice is None or len(self.dimension_options) <= 1:
            return
        index = next(i for i, option in enumerate(self.dimension_options) if option.key == self.choice)
        rect = self.buttons.buttons[index].rect
        marker = pygame.Rect(rect.left, rect.top + 4, 4, rect.height - 8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

    def _draw_table(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        option = self._selected_option()
        if option is None:
            draw_centered_text(surface, loc.t("segment_mix.pick_hint"), (CENTER_X, TABLE_TOP + 30), 15, colors.BUTTON_TEXT_DISABLED)
            return

        draw_centered_text(surface, loc.t("segment_mix.segment_column"), (SEGMENT_COLUMN_X, HEADER_Y), 13, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t("segment_mix.q1_share_column"), (Q1_SHARE_COLUMN_X, HEADER_Y), 13, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t("segment_mix.q1_rate_column"), (Q1_RATE_COLUMN_X, HEADER_Y), 13, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t("segment_mix.q2_share_column"), (Q2_SHARE_COLUMN_X, HEADER_Y), 13, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t("segment_mix.q2_rate_column"), (Q2_RATE_COLUMN_X, HEADER_Y), 13, colors.BUTTON_TEXT_DISABLED)

        for index, row in enumerate(option.rows):
            y = HEADER_Y + (index + 1) * ROW_HEIGHT
            draw_centered_text(surface, loc.t(row.label_key), (SEGMENT_COLUMN_X, y), 15, colors.TEXT)
            draw_centered_text(surface, _pct(row.q1_share), (Q1_SHARE_COLUMN_X, y), 15, colors.TEXT)
            draw_centered_text(surface, _pct(row.q1_rate), (Q1_RATE_COLUMN_X, y), 15, colors.TEXT)
            draw_centered_text(surface, _pct(row.q2_share), (Q2_SHARE_COLUMN_X, y), 15, colors.TEXT)
            draw_centered_text(surface, _pct(row.q2_rate), (Q2_RATE_COLUMN_X, y), 15, colors.TEXT)

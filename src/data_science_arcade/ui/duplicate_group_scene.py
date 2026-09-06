from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.duplicate_group import DuplicateGroup, DuplicateGroupVerdicts, GroupVerdictOption
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 76
PROMPT_SIZE = 17
PROMPT_MAX_WIDTH = 820
TABLE_LEFT = 60
TABLE_TOP = 128
TABLE_WIDTH = LOGICAL_SIZE[0] - 2 * TABLE_LEFT
ROW_HEIGHT = 26
CELL_TEXT_SIZE = 13
VERDICT_OPTION_SIZE = (860, 40)
TABLE_VERDICT_GAP = 20
"""Vertical gap between the table's own real bottom (header + however
many rows the CURRENT group actually has - anywhere from 2 to 5 across
this lesson's real groups) and the first verdict button. A fixed
FIRST_VERDICT_Y sized for a 2-row group let a 5-row group's own last row
render underneath the button area - caught by a real screenshot, the
same failure mode this project's other content-driven-height scenes
(ComparisonRevealScene's box, WorkbenchScene's schema descriptions)
already guard against the same way: compute from the real content."""
VERDICT_SPACING = 46
HINT_Y = 440
NAV_BUTTON_Y = 490


class DuplicateGroupScene(Scene):
    """Steps through a fixed sequence of real, representative row groups
    (`groups`), one at a time - each group's own rows are shown as a
    plain table with `key_column` highlighted, and every OTHER column
    that actually disagrees across the group's own rows highlighted too,
    computed live from the real row data on every draw call. This is the
    deliberate one-line contrast with the retired RecordPairScene's own
    precomputed `matches: bool` per field: nothing here is authored,
    every highlight is a real fact about the rows currently on screen.

    Deliberately narrow in scope - not a general data-quality dashboard.
    A single shared `verdict_options` set is reused across every group
    (the scene itself carries no notion of which verdict is "correct"
    for a given group, mirroring SegmentSlicerScene's own no-evidence-
    awareness design); the calling lesson's own on_complete handler
    decides correctness and any evidence recording from its own
    group-key -> correct-verdict mapping, never this scene.

    guided=True also shows each group's own hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        groups: tuple[DuplicateGroup, ...],
        verdict_options: tuple[GroupVerdictOption, ...],
        on_complete: Callable[[DuplicateGroupVerdicts], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.groups = groups
        self.verdict_options = verdict_options
        self.on_complete = on_complete
        self.guided = guided
        self.group_index = 0
        self.verdicts: DuplicateGroupVerdicts = {}
        self._rebuild_buttons()

    def _current_group(self) -> DuplicateGroup:
        return self.groups[self.group_index]

    def _is_last_group(self) -> bool:
        return self.group_index == len(self.groups) - 1

    def _differing_columns(self, group: DuplicateGroup) -> set[str]:
        return {
            column
            for column in group.columns
            if column != group.key_column and len({row[column] for row in group.rows}) > 1
        }

    def _first_verdict_y(self, group: DuplicateGroup) -> int:
        table_bottom = TABLE_TOP + (len(group.rows) + 1) * ROW_HEIGHT
        return table_bottom + TABLE_VERDICT_GAP

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        group = self._current_group()
        first_verdict_y = self._first_verdict_y(group)
        buttons: list[Button] = []
        for index, option in enumerate(self.verdict_options):
            rect = pygame.Rect(0, 0, *VERDICT_OPTION_SIZE)
            rect.center = (CENTER_X, first_verdict_y + index * VERDICT_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.group_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_group() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=group.key in self.verdicts)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, verdict_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.verdicts[self._current_group().key] = verdict_key
            self._rebuild_buttons()

        return choose

    def _back(self) -> None:
        if self.group_index > 0:
            self.group_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_group().key not in self.verdicts:
            return
        if self._is_last_group():
            self.on_complete(dict(self.verdicts))
            return
        self.group_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every
        # stage in Pausable, which intercepts Escape before this scene
        # sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        group = self._current_group()

        progress = f"{self.group_index + 1} / {len(self.groups)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 26, colors.TEXT)
        draw_centered_wrapped_text(surface, loc.t(group.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        self._draw_table(surface, group)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, group)

        if self.guided and group.hint_key:
            draw_wrapped_text(surface, loc.t(group.hint_key), (CENTER_X - 300, HINT_Y), 600, 14, colors.BUTTON_TEXT_DISABLED)

    def _draw_table(self, surface: pygame.Surface, group: DuplicateGroup) -> None:
        differing = self._differing_columns(group)
        col_width = TABLE_WIDTH // len(group.columns)

        for col_index, column in enumerate(group.columns):
            x = TABLE_LEFT + col_index * col_width
            header_color = colors.BUTTON_FOCUS_BORDER if column == group.key_column else colors.BUTTON_TEXT_DISABLED
            draw_single_line(surface, column, (x, TABLE_TOP), col_width - 8, 13, header_color)

        row_top = TABLE_TOP + ROW_HEIGHT
        for row_index, row in enumerate(group.rows):
            y = row_top + row_index * ROW_HEIGHT
            for col_index, column in enumerate(group.columns):
                x = TABLE_LEFT + col_index * col_width
                is_highlighted = column == group.key_column or column in differing
                color = colors.BUTTON_FOCUS_BORDER if is_highlighted else colors.TEXT
                draw_single_line(surface, row[column], (x, y), col_width - 8, CELL_TEXT_SIZE, color)

    def _draw_selected_indicator(self, surface: pygame.Surface, group: DuplicateGroup) -> None:
        selected_key = self.verdicts.get(group.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(self.verdict_options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

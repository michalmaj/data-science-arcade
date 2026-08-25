from collections.abc import Callable
from enum import Enum

import pandas as pd
import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairResolution
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
TAB_BAR_Y = 42
TAB_SIZE = (148, 36)
TAB_SPACING = 156
CONTENT_RECT = pygame.Rect(30, 78, 900, 382)
CONTINUE_BUTTON_Y = 500
REPAIR_ROW_HEIGHT = 32
MAX_TABLE_ROWS = 8
PICKER_OPTION_SIZE = (420, 46)
PICKER_OPTION_SPACING = 54


class WorkbenchTab(Enum):
    MISSION = "workbench.tab.mission"
    DATA = "workbench.tab.data"
    PIPELINE = "workbench.tab.pipeline"
    EVIDENCE = "workbench.tab.evidence"
    DECISION = "workbench.tab.decision"
    PYTHON = "workbench.tab.python"


class DataView(Enum):
    TABLE = "table"
    SCHEMA = "schema"


def _format_cell(value: object) -> str:
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return str(value)


class WorkbenchScene(Scene):
    """The persistent analytical interface (spec §15.5/§16): a MISSION /
    DATA / PIPELINE / EVIDENCE / DECISION / PYTHON tab bar around one active
    Dataset. Used as a lesson stage (spec §25 Lesson 06 'Schema Repair
    Shop' is the first): `issues` flags specific DATA-tab columns as
    needing repair - every cell in an unresolved issue's column is
    clickable, opening a fix picker with several candidate transforms.
    Applying one calls Dataset.then() (so PIPELINE/PYTHON tabs immediately
    show the real change and its Python Mirror) and clears that column's
    flag, right or wrong - matching every other lesson's non-punitive
    "record the choice, reasoning happens at the decision stage" pattern.
    Continue enables once every issue has a resolution.

    guided=True also shows each issue's explanatory hint; guided=False
    hides it. EVIDENCE/DECISION stay placeholder tabs - no lesson needs
    them populated yet (spec §15.5: "not every tool must exist" from the
    start, capabilities unlock progressively)."""

    def __init__(
        self,
        app,
        dataset: Dataset,
        issues: tuple[RepairIssue, ...],
        on_complete: Callable[[RepairResolution], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.dataset = dataset
        self.issues = issues
        self.on_complete = on_complete
        self.guided = guided
        self.active_tab = WorkbenchTab.DATA
        self.data_view = DataView.TABLE
        self.resolution: RepairResolution = {}
        self.active_issue: RepairIssue | None = None
        self._rebuild_buttons()

    def _issue_for_column(self, column: str) -> RepairIssue | None:
        return next((issue for issue in self.issues if issue.column == column), None)

    def _all_resolved(self) -> bool:
        return len(self.resolution) == len(self.issues)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []
        for index, tab in enumerate(WorkbenchTab):
            rect = pygame.Rect(0, 0, *TAB_SIZE)
            first_center_x = CENTER_X - (len(WorkbenchTab) - 1) * TAB_SPACING // 2
            rect.center = (first_center_x + index * TAB_SPACING, TAB_BAR_Y)
            buttons.append(Button(rect, loc.t(tab.value), self._make_switch_tab(tab)))

        self.table_view_button = None
        self.schema_view_button = None
        self.picker_buttons: dict[str, Button] = {}
        if self.active_tab is WorkbenchTab.DATA:
            if self.active_issue is not None:
                buttons.extend(self._build_picker_buttons())
            else:
                table_rect = pygame.Rect(0, 0, 120, 30)
                table_rect.topleft = (CONTENT_RECT.left, CONTENT_RECT.top)
                schema_rect = pygame.Rect(0, 0, 120, 30)
                schema_rect.topleft = (CONTENT_RECT.left + 128, CONTENT_RECT.top)
                table_label = loc.t("workbench.data.view_table")
                schema_label = loc.t("workbench.data.view_schema")
                self.table_view_button = Button(table_rect, table_label, self._make_switch_view(DataView.TABLE))
                self.schema_view_button = Button(schema_rect, schema_label, self._make_switch_view(DataView.SCHEMA))
                buttons.append(self.table_view_button)
                buttons.append(self.schema_view_button)
                if self.data_view is DataView.TABLE:
                    buttons.extend(self._build_cell_buttons())

        continue_rect = pygame.Rect(0, 0, 200, 44)
        continue_rect.center = (CENTER_X, CONTINUE_BUTTON_Y)
        self.continue_button = Button(continue_rect, loc.t("workbench.continue"), self._continue, enabled=self._all_resolved())
        buttons.append(self.continue_button)

        self.buttons = ButtonGroup(buttons)
        # ButtonGroup defaults focus to the first button; keep it on the tab
        # that's actually showing instead of always snapping back to the
        # first tab whenever anything triggers a rebuild.
        self.buttons.focus_index = list(WorkbenchTab).index(self.active_tab)

    def _build_cell_buttons(self) -> list[Button]:
        table_top = CONTENT_RECT.top + 46
        frame = self.dataset.frame
        columns = list(frame.columns)
        left = CONTENT_RECT.left + 20
        width = CONTENT_RECT.width - 40
        col_width = width // len(columns) if columns else width
        row_top = table_top + REPAIR_ROW_HEIGHT
        shown_rows = frame.head(MAX_TABLE_ROWS)

        buttons: list[Button] = []
        for col_index, column in enumerate(columns):
            issue = self._issue_for_column(column)
            if issue is None or column in self.resolution:
                continue
            for row_index in range(len(shown_rows)):
                rect = pygame.Rect(left + col_index * col_width, row_top + row_index * REPAIR_ROW_HEIGHT, col_width - 8, REPAIR_ROW_HEIGHT - 6)
                text = _format_cell(shown_rows.iloc[row_index][column])
                button = Button(rect, text, self._make_open_issue(issue))
                buttons.append(button)
        return buttons

    def _build_picker_buttons(self) -> list[Button]:
        loc = self.app.localization
        issue = self.active_issue
        assert issue is not None
        buttons = []
        for index, option in enumerate(issue.options):
            rect = pygame.Rect(0, 0, *PICKER_OPTION_SIZE)
            rect.center = (CENTER_X, CONTENT_RECT.top + 120 + index * PICKER_OPTION_SPACING)
            button = Button(rect, loc.t(option.label_key), self._make_choose(issue, option.key))
            self.picker_buttons[option.key] = button
            buttons.append(button)
        return buttons

    def _make_switch_tab(self, tab: "WorkbenchTab"):
        def switch() -> None:
            self.active_tab = tab
            self._rebuild_buttons()

        return switch

    def _make_switch_view(self, view: "DataView"):
        def switch() -> None:
            self.data_view = view
            self._rebuild_buttons()

        return switch

    def _make_open_issue(self, issue: RepairIssue) -> Callable[[], None]:
        def open_issue() -> None:
            self.active_issue = issue
            self._rebuild_buttons()

        return open_issue

    def _make_choose(self, issue: RepairIssue, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            option = next(o for o in issue.options if o.key == option_key)
            self.dataset = self.dataset.then(
                f"{issue.column}_{option.key}",
                option.apply,
                schema=issue.schema_after,
                python_code=option.python_code,
            )
            self.resolution[issue.column] = option.key
            self.active_issue = None
            self._rebuild_buttons()

        return choose

    def _continue(self) -> None:
        if self._all_resolved():
            self.on_complete(dict(self.resolution))

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, CONTENT_RECT, border_radius=8)

        self.buttons.draw(surface)
        self._draw_active_data_view_indicator(surface)
        self._draw_active_tab_content(surface)

    def _draw_active_data_view_indicator(self, surface: pygame.Surface) -> None:
        if self.active_tab is not WorkbenchTab.DATA or self.active_issue is not None:
            return
        # The Table/Schema toggle is independent of keyboard focus (both
        # buttons can be un-focused at once), so its "which one is active"
        # signal is a separate underline, not the shared focus border.
        active_button = {
            DataView.TABLE: self.table_view_button,
            DataView.SCHEMA: self.schema_view_button,
        }.get(self.data_view)
        if active_button is None:
            return
        underline = pygame.Rect(0, 0, active_button.rect.width - 16, 2)
        underline.midtop = (active_button.rect.centerx, active_button.rect.bottom - 6)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, underline)

    def _draw_active_tab_content(self, surface: pygame.Surface) -> None:
        if self.active_tab is WorkbenchTab.DATA:
            self._draw_data_tab(surface)
        elif self.active_tab is WorkbenchTab.PIPELINE:
            self._draw_pipeline_tab(surface)
        elif self.active_tab is WorkbenchTab.PYTHON:
            self._draw_python_tab(surface)
        elif self.active_tab is WorkbenchTab.EVIDENCE:
            self._draw_placeholder(surface, "workbench.evidence.empty")
        elif self.active_tab is WorkbenchTab.MISSION:
            self._draw_mission_tab(surface)
        elif self.active_tab is WorkbenchTab.DECISION:
            self._draw_placeholder(surface, "workbench.decision.placeholder")

    def _draw_placeholder(self, surface: pygame.Surface, text_key: str) -> None:
        draw_wrapped_text(
            surface,
            self.app.localization.t(text_key),
            (CONTENT_RECT.left + 20, CONTENT_RECT.top + 60),
            CONTENT_RECT.width - 40,
            20,
            colors.BUTTON_TEXT_DISABLED,
        )

    def _draw_mission_tab(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        left = CONTENT_RECT.left + 20
        width = CONTENT_RECT.width - 40
        top = CONTENT_RECT.top + 20
        draw_wrapped_text(surface, loc.t("workbench.mission.objective"), (left, top), width, 18, colors.TEXT)

        row_top = top + 50
        for index, issue in enumerate(self.issues):
            y = row_top + index * 30
            resolved = issue.column in self.resolution
            status_key = "workbench.mission.resolved" if resolved else "workbench.mission.pending"
            color = colors.BUTTON_FOCUS_BORDER if resolved else colors.BUTTON_TEXT_DISABLED
            text = f"{issue.column} - {loc.t(status_key)}"
            draw_single_line(surface, text, (left, y), width, 16, color)

    def _draw_data_tab(self, surface: pygame.Surface) -> None:
        if self.active_issue is not None:
            self._draw_picker(surface)
        elif self.data_view is DataView.TABLE:
            self._draw_table(surface, CONTENT_RECT.top + 46)
        else:
            self._draw_schema(surface, CONTENT_RECT.top + 46)

    def _draw_picker(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        issue = self.active_issue
        assert issue is not None
        draw_centered_text(surface, loc.t(issue.prompt_key), (CENTER_X, CONTENT_RECT.top + 50), 20, colors.TEXT)
        if self.guided and issue.hint_key:
            draw_wrapped_text(
                surface, loc.t(issue.hint_key), (CENTER_X - 350, CONTENT_RECT.bottom - 60), 700, 15, colors.BUTTON_TEXT_DISABLED
            )

    def _draw_table(self, surface: pygame.Surface, top: int) -> None:
        loc = self.app.localization
        frame = self.dataset.frame
        columns = list(frame.columns)
        left = CONTENT_RECT.left + 20
        width = CONTENT_RECT.width - 40
        col_width = width // len(columns) if columns else width

        for index, column in enumerate(columns):
            flagged = self._issue_for_column(column) is not None and column not in self.resolution
            header_color = colors.BUTTON_FOCUS_BORDER if flagged else colors.TEXT
            draw_single_line(surface, column, (left + index * col_width, top), col_width - 8, 16, header_color)

        row_top = top + REPAIR_ROW_HEIGHT
        shown_rows = frame.head(MAX_TABLE_ROWS)
        for row_index, (_, row) in enumerate(shown_rows.iterrows()):
            y = row_top + row_index * REPAIR_ROW_HEIGHT
            for col_index, column in enumerate(columns):
                if self._issue_for_column(column) is not None and column not in self.resolution:
                    continue  # drawn as a clickable Button instead, see _build_cell_buttons
                draw_single_line(
                    surface,
                    _format_cell(row[column]),
                    (left + col_index * col_width, y + 5),
                    col_width - 8,
                    14,
                    colors.BUTTON_TEXT_DISABLED,
                )

        if len(frame) > MAX_TABLE_ROWS:
            note_y = row_top + MAX_TABLE_ROWS * REPAIR_ROW_HEIGHT + 8
            draw_wrapped_text(
                surface, loc.t("workbench.data.more_rows"), (left, note_y), width, 14, colors.BUTTON_TEXT_DISABLED
            )

        summary_y = CONTENT_RECT.bottom - 24
        summary = (
            f"{loc.t('workbench.data.rows_label')} {len(frame)}    "
            f"{loc.t('workbench.data.columns_label')} {len(columns)}"
        )
        draw_wrapped_text(surface, summary, (left, summary_y), width, 14, colors.BUTTON_TEXT_DISABLED)

    def _draw_schema(self, surface: pygame.Surface, top: int) -> None:
        left = CONTENT_RECT.left + 20
        width = CONTENT_RECT.width - 40
        line_height = 26
        for index, column in enumerate(self.dataset.schema.columns):
            y = top + index * line_height
            header = f"{column.name} ({column.dtype})" + ("" if not column.nullable else " - nullable")
            draw_single_line(surface, header, (left, y), width, 16, colors.TEXT)
            if column.description:
                draw_wrapped_text(surface, column.description, (left + 12, y + 18), width - 12, 13, colors.BUTTON_TEXT_DISABLED)

    def _draw_pipeline_tab(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        top = CONTENT_RECT.top + 30
        if not self.dataset.history:
            self._draw_placeholder(surface, "workbench.pipeline.empty")
            return
        draw_centered_text(surface, self.dataset.name, (CENTER_X, top), 18, colors.BUTTON_FOCUS_BORDER)
        for index, step in enumerate(self.dataset.history):
            draw_centered_text(surface, f"-> {step.name}", (CENTER_X, top + (index + 1) * 30), 16, colors.TEXT)

    def _draw_python_tab(self, surface: pygame.Surface) -> None:
        code = self.dataset.python_mirror()
        if not code:
            self._draw_placeholder(surface, "workbench.python.empty")
            return
        left = CONTENT_RECT.left + 20
        top = CONTENT_RECT.top + 20
        width = CONTENT_RECT.width - 40
        y = top
        for line in code.split("\n"):
            draw_wrapped_text(surface, line, (left, y), width, 15, colors.TEXT)
            y += 22

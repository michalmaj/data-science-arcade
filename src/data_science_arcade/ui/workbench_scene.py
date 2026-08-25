from enum import Enum

import pandas as pd
import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
TAB_BAR_Y = 42
TAB_SIZE = (148, 36)
TAB_SPACING = 156
CONTENT_RECT = pygame.Rect(30, 78, 900, 382)
BACK_BUTTON_Y = 500
ROW_HEIGHT = 22
MAX_TABLE_ROWS = 8


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
    Dataset. Only DATA and PIPELINE show real content this phase - the rest
    render a placeholder until there's an actual lesson driving them
    (Phase 7+)."""

    def __init__(self, app, dataset: Dataset) -> None:
        super().__init__(app)
        self.dataset = dataset
        self.active_tab = WorkbenchTab.DATA
        self.data_view = DataView.TABLE
        self._rebuild_buttons()

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons = []
        for index, tab in enumerate(WorkbenchTab):
            rect = pygame.Rect(0, 0, *TAB_SIZE)
            first_center_x = CENTER_X - (len(WorkbenchTab) - 1) * TAB_SPACING // 2
            rect.center = (first_center_x + index * TAB_SPACING, TAB_BAR_Y)
            buttons.append(Button(rect, loc.t(tab.value), self._make_switch_tab(tab)))

        self.table_view_button = None
        self.schema_view_button = None
        if self.active_tab is WorkbenchTab.DATA:
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

        back_rect = pygame.Rect(0, 0, 200, 44)
        back_rect.center = (CENTER_X, BACK_BUTTON_Y)
        buttons.append(Button(back_rect, loc.t("common.back"), self._back))

        self.buttons = ButtonGroup(buttons)
        # ButtonGroup defaults focus to the first button; keep it on the tab
        # that's actually showing instead of always snapping back to the
        # first tab whenever anything triggers a rebuild.
        self.buttons.focus_index = list(WorkbenchTab).index(self.active_tab)

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

    def _back(self) -> None:
        self.app.scenes.pop()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, CONTENT_RECT, border_radius=8)

        self.buttons.draw(surface)
        self._draw_active_data_view_indicator(surface)
        self._draw_active_tab_content(surface)

    def _draw_active_data_view_indicator(self, surface: pygame.Surface) -> None:
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
            self._draw_placeholder(surface, "workbench.mission.placeholder")
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

    def _draw_data_tab(self, surface: pygame.Surface) -> None:
        table_top = CONTENT_RECT.top + 46
        if self.data_view is DataView.TABLE:
            self._draw_table(surface, table_top)
        else:
            self._draw_schema(surface, table_top)

    def _draw_table(self, surface: pygame.Surface, top: int) -> None:
        loc = self.app.localization
        frame = self.dataset.frame
        columns = list(frame.columns)
        left = CONTENT_RECT.left + 20
        width = CONTENT_RECT.width - 40
        col_width = width // len(columns) if columns else width

        for index, column in enumerate(columns):
            draw_single_line(surface, column, (left + index * col_width, top), col_width - 8, 16, colors.TEXT)

        row_top = top + ROW_HEIGHT
        shown_rows = frame.head(MAX_TABLE_ROWS)
        for row_index, (_, row) in enumerate(shown_rows.iterrows()):
            y = row_top + row_index * ROW_HEIGHT
            for col_index, column in enumerate(columns):
                draw_single_line(
                    surface,
                    _format_cell(row[column]),
                    (left + col_index * col_width, y),
                    col_width - 8,
                    14,
                    colors.BUTTON_TEXT_DISABLED,
                )

        if len(frame) > MAX_TABLE_ROWS:
            note_y = row_top + MAX_TABLE_ROWS * ROW_HEIGHT + 8
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
        left = CONTENT_RECT.left + 20
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

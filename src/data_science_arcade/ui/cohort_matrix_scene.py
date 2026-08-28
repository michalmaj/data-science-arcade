from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.cohort import CohortChoices, CohortMatrix, CohortRequest, CohortRow
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 72
PROMPT_MAX_WIDTH = 820
COMPARISON_OPTION_SIZE = (380, 38)
COMPARISON_OPTION_Y = 112
GRID_LEFT = 50
ROW_LABEL_WIDTH = 90
COLUMN_WIDTH = 110
GRID_TOP = 158
ROW_HEIGHT = 30
HINT_Y = 385
NAV_BUTTON_Y = 460


class CohortMatrixScene(Scene):
    """A persistent cohort retention matrix (spec §25 Lesson 22 'Cohort
    Observatory'): rows are acquisition cohorts, columns are months since
    acquisition, cells are real retention rates - naturally triangular,
    since a cohort acquired more recently simply hasn't reached later
    months yet (drawn as a dash, not a zero). A fixed sequence of requests
    each poses a claim about the matrix; picking a comparison method
    (same months-since-acquisition vs. a mismatched one) highlights the
    two cells that comparison actually rests on, so a methodologically
    unsound comparison is visible as unsound - it's comparing cells from
    different columns - not just asserted to be wrong.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        matrix: CohortMatrix,
        requests: tuple[CohortRequest, ...],
        on_complete: Callable[[CohortChoices], None],
        guided: bool = True,
        month_header_key: str = "cohort.month_header",
        not_observed_key: str = "cohort.not_observed",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.matrix = matrix
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.month_header_key = month_header_key
        self.not_observed_key = not_observed_key
        self.request_index = 0
        self.choices: CohortChoices = {}
        self._rebuild_buttons()

    def _current_request(self) -> CohortRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _selected_option(self, request: CohortRequest):
        option_key = self.choices.get(request.key)
        if option_key is None:
            return None
        return next(option for option in request.options if option.key == option_key)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()
        buttons = []
        count = len(request.options)
        for index, option in enumerate(request.options):
            rect = pygame.Rect(0, 0, *COMPARISON_OPTION_SIZE)
            spacing = COMPARISON_OPTION_SIZE[0] + 20
            rect.center = (CENTER_X + (index - (count - 1) / 2) * spacing, COMPARISON_OPTION_Y)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.request_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_request() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=request.key in self.choices)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choices[self._current_request().key] = option_key
            self._rebuild_buttons()

        return choose

    def _back(self) -> None:
        if self.request_index > 0:
            self.request_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_request().key not in self.choices:
            return
        if self._is_last_request():
            self.on_complete(dict(self.choices))
            return
        self.request_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        request = self._current_request()

        progress = f"{self.request_index + 1} / {len(self.requests)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)
        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, 16, colors.TEXT)

        self._draw_matrix(surface, request)
        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _column_x(self, month: int) -> int:
        return GRID_LEFT + ROW_LABEL_WIDTH + month * COLUMN_WIDTH + COLUMN_WIDTH // 2

    def _row_y(self, row_index: int) -> int:
        return GRID_TOP + (row_index + 1) * ROW_HEIGHT

    def _cell_value(self, row: CohortRow, month: int) -> float | None:
        if month >= row.months_observed:
            return None
        return row.retention_by_month[month]

    def _draw_matrix(self, surface: pygame.Surface, request: CohortRequest) -> None:
        loc = self.app.localization
        header_y = GRID_TOP
        for month in range(self.matrix.month_count):
            header_text = f"{loc.t(self.month_header_key)} {month}"
            draw_centered_text(surface, header_text, (self._column_x(month), header_y), 13, colors.BUTTON_TEXT_DISABLED)

        highlighted = self._highlighted_cells(request)
        for row_index, row in enumerate(self.matrix.rows):
            y = self._row_y(row_index)
            draw_wrapped_text(surface, loc.t(row.label_key), (GRID_LEFT, y - 9), ROW_LABEL_WIDTH - 6, 14, colors.TEXT)
            for month in range(self.matrix.month_count):
                value = self._cell_value(row, month)
                x = self._column_x(month)
                is_highlighted = (row.key, month) in highlighted
                if is_highlighted:
                    cell_rect = pygame.Rect(0, 0, COLUMN_WIDTH - 10, ROW_HEIGHT - 6)
                    cell_rect.center = (x, y)
                    pygame.draw.rect(surface, colors.PANEL_BACKGROUND, cell_rect, border_radius=4)
                    pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, cell_rect, width=2, border_radius=4)
                text = f"{value:.0%}" if value is not None else loc.t(self.not_observed_key)
                color = colors.TEXT if value is not None else colors.BUTTON_TEXT_DISABLED
                draw_centered_text(surface, text, (x, y), 14, color)

    def _highlighted_cells(self, request: CohortRequest) -> set[tuple[str, int]]:
        option = self._selected_option(request)
        if option is None:
            return set()
        return {(option.cohort_a, option.month_a), (option.cohort_b, option.month_b)}

    def _draw_selected_indicator(self, surface: pygame.Surface, request: CohortRequest) -> None:
        selected_key = self.choices.get(request.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(request.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

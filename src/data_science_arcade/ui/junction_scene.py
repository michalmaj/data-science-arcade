from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.lessons.framework.join import JoinChoices, JoinRequest
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 82
PROMPT_SIZE = 18
PROMPT_MAX_WIDTH = 820
DIAGRAM_TOP = 122
NODE_SIZE = (150, 20)
NODE_SPACING = 24
LEFT_X = 170
RIGHT_X = 790
RESULT_Y = 350
OPTION_SIZE = (180, 40)
OPTION_Y = 392
OPTION_SPACING = 200
HINT_Y = 448
NAV_BUTTON_Y = 495


class JunctionScene(Scene):
    """The 'railway/junction' visualization (spec §25 Lesson 13 'Join
    Junction'): the left table's rows and the right table's rows are drawn
    as two node columns, connected by a line for every real key match -
    a fact of the data, independent of anything the player picks. A fixed
    sequence of requests each asks for one join type (inner/left/right);
    picking one dims whichever nodes that join type would drop and shows
    a live, really computed row count, instead of describing the effect
    in text alone.

    guided=True also shows each request's hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        left_dataset: Dataset,
        right_dataset: Dataset,
        join_column: str,
        requests: tuple[JoinRequest, ...],
        on_complete: Callable[[JoinChoices], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.left_dataset = left_dataset
        self.right_dataset = right_dataset
        self.join_column = join_column
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.request_index = 0
        self.choices: JoinChoices = {}
        self._matches = self._compute_matches()
        self._rebuild_buttons()

    def _compute_matches(self) -> list[tuple[int, int]]:
        """(left_row_index, right_row_index) pairs sharing a join_column
        value - computed once, since it doesn't depend on any choice."""
        left_frame = self.left_dataset.frame
        right_frame = self.right_dataset.frame
        matches: list[tuple[int, int]] = []
        for left_index, left_value in enumerate(left_frame[self.join_column]):
            for right_index, right_value in enumerate(right_frame[self.join_column]):
                if left_value == right_value:
                    matches.append((left_index, right_index))
        return matches

    def _current_request(self) -> JoinRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _current_how(self) -> str | None:
        option_key = self.choices.get(self._current_request().key)
        if option_key is None:
            return None
        request = self._current_request()
        return next(option.how for option in request.options if option.key == option_key)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()
        buttons = []
        for index, option in enumerate(request.options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X + (index - 1) * OPTION_SPACING, OPTION_Y)
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

    def _left_dropped(self, left_index: int, how: str | None) -> bool:
        if how is None:
            return False
        has_match = any(left_index == pair[0] for pair in self._matches)
        return not has_match and how in ("inner", "right")

    def _right_dropped(self, right_index: int, how: str | None) -> bool:
        if how is None:
            return False
        has_match = any(right_index == pair[1] for pair in self._matches)
        return not has_match and how in ("inner", "left")

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        request = self._current_request()

        progress = f"{self.request_index + 1} / {len(self.requests)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)

        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        self._draw_junction(surface)
        self._draw_result(surface)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, request)

        if self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_junction(self, surface: pygame.Surface) -> None:
        how = self._current_how()
        left_frame = self.left_dataset.frame
        right_frame = self.right_dataset.frame

        draw_centered_text(surface, self.left_dataset.name, (LEFT_X, DIAGRAM_TOP - 20), 15, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, self.right_dataset.name, (RIGHT_X, DIAGRAM_TOP - 20), 15, colors.BUTTON_TEXT_DISABLED)

        left_rects = [self._node_rect(LEFT_X, index) for index in range(len(left_frame))]
        right_rects = [self._node_rect(RIGHT_X, index) for index in range(len(right_frame))]

        for left_index, right_index in self._matches:
            start = left_rects[left_index].midright
            end = right_rects[right_index].midleft
            pygame.draw.line(surface, colors.BUTTON_FOCUS_BORDER, start, end, 1)

        for index, rect in enumerate(left_rects):
            dimmed = self._left_dropped(index, how)
            self._draw_node(surface, rect, self._row_label(left_frame, index), dimmed)
        for index, rect in enumerate(right_rects):
            dimmed = self._right_dropped(index, how)
            self._draw_node(surface, rect, self._row_label(right_frame, index), dimmed)

    def _node_rect(self, centerx: int, index: int) -> pygame.Rect:
        rect = pygame.Rect(0, 0, *NODE_SIZE)
        rect.center = (centerx, DIAGRAM_TOP + index * NODE_SPACING)
        return rect

    def _row_label(self, frame, index: int) -> str:
        row = frame.iloc[index]
        # The join column plus whichever other column identifies the row
        # to a human (a name for customers, an amount for orders) - never
        # every column, which would overflow a node this small.
        other_columns = [c for c in frame.columns if c != self.join_column]
        descriptive = other_columns[-1] if other_columns else self.join_column
        value = row[descriptive]
        if isinstance(value, float):
            value = f"${value:,.0f}" if value.is_integer() else f"${value:,.2f}"
        return f"{row[self.join_column]}  {value}"

    def _draw_node(self, surface: pygame.Surface, rect: pygame.Rect, label: str, dimmed: bool) -> None:
        fill = colors.PANEL_BACKGROUND if not dimmed else colors.BUTTON_DISABLED
        text_color = colors.TEXT if not dimmed else colors.BUTTON_TEXT_DISABLED
        pygame.draw.rect(surface, fill, rect, border_radius=4)
        draw_single_line(surface, label, (rect.left + 6, rect.top + 3), rect.width - 12, 13, text_color)

    def _draw_result(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        how = self._current_how()
        if how is None:
            draw_centered_text(surface, loc.t("lesson.l13.pick_a_join_hint"), (CENTER_X, RESULT_Y), 15, colors.BUTTON_TEXT_DISABLED)
            return
        merged = self.left_dataset.frame.merge(self.right_dataset.frame, on=self.join_column, how=how)
        text = f"{loc.t('lesson.l13.result_label')} {len(merged)}"
        draw_centered_text(surface, text, (CENTER_X, RESULT_Y), 18, colors.TEXT)

    def _draw_selected_indicator(self, surface: pygame.Surface, request: JoinRequest) -> None:
        selected_key = self.choices.get(request.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(request.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 4, 4, rect.height - 8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

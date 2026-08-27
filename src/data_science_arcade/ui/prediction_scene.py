from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.prediction import DIRECTIONS, HypothesisRequest, PredictionChoices
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
PROMPT_Y = 78
PROMPT_SIZE = 18
PROMPT_MAX_WIDTH = 820
DIRECTION_ROW_Y = 180
DIRECTION_BUTTON_SIZE = (200, 44)
DIRECTION_SPACING = 220
VERDICT_LINE1_Y = 230
VERDICT_LINE2_Y = 254
TABLE_METRIC_Y = 290
TABLE_HEADER_Y = 314
TABLE_VALUE_Y = 338
TABLE_COLUMN_OFFSET = 90
HINT_Y = 400
NAV_BUTTON_Y = 460


class PredictionScene(Scene):
    """A fixed sequence of requests, each asking the player to predict a
    metric's direction *before* any number is shown - the inverse of every
    other lesson-mechanic scene, which shows live data the moment an option
    is picked. Picking a direction only stages it; a separate Reveal click
    commits it and shows the real before/after values plus a correct/
    incorrect verdict against the actual computed direction (see
    lessons/framework/prediction.py:actual_direction) - once revealed, a
    request's direction buttons freeze, so a prediction can't be edited
    after seeing the truth.

    guided=True also shows each request's hint (while still predicting,
    never after reveal); guided=False hides it, matching every other stage
    scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        requests: tuple[HypothesisRequest, ...],
        on_complete: Callable[[PredictionChoices], None],
        guided: bool = True,
        before_label_key: str = "prediction.before_label",
        after_label_key: str = "prediction.after_label",
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.requests = requests
        self.on_complete = on_complete
        self.guided = guided
        self.before_label_key = before_label_key
        self.after_label_key = after_label_key
        self.request_index = 0
        self.choices: PredictionChoices = {}
        self._pending: str | None = None
        self._rebuild_buttons()

    def _current_request(self) -> HypothesisRequest:
        return self.requests[self.request_index]

    def _is_last_request(self) -> bool:
        return self.request_index == len(self.requests) - 1

    def _is_revealed(self) -> bool:
        return self._current_request().key in self.choices

    def _selected_direction(self, request: HypothesisRequest) -> str | None:
        return self.choices.get(request.key, self._pending)

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        request = self._current_request()
        revealed = self._is_revealed()
        buttons = []
        for index, direction in enumerate(DIRECTIONS):
            rect = pygame.Rect(0, 0, *DIRECTION_BUTTON_SIZE)
            rect.center = (CENTER_X + (index - 1) * DIRECTION_SPACING, DIRECTION_ROW_Y)
            label = loc.t(f"prediction.direction.{direction}")
            buttons.append(Button(rect, label, self._make_pick(direction), enabled=not revealed))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.request_index > 0)
        buttons.append(self.back_button)

        action_rect = pygame.Rect(0, 0, 140, 44)
        action_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        if revealed:
            next_label = loc.t("brief.finish") if self._is_last_request() else loc.t("brief.next")
            self.action_button = Button(action_rect, next_label, self._next)
        else:
            self.action_button = Button(action_rect, loc.t("prediction.reveal"), self._reveal, enabled=self._pending is not None)
        buttons.append(self.action_button)

        self.buttons = ButtonGroup(buttons)

    def _make_pick(self, direction: str) -> Callable[[], None]:
        def pick() -> None:
            if self._is_revealed():
                return
            self._pending = direction
            self._rebuild_buttons()

        return pick

    def _reveal(self) -> None:
        if self._pending is None:
            return
        self.choices[self._current_request().key] = self._pending
        self._rebuild_buttons()

    def _back(self) -> None:
        if self.request_index > 0:
            self.request_index -= 1
            self._pending = self.choices.get(self._current_request().key)
            self._rebuild_buttons()

    def _next(self) -> None:
        if not self._is_revealed():
            return
        if self._is_last_request():
            self.on_complete(dict(self.choices))
            return
        self.request_index += 1
        self._pending = self.choices.get(self._current_request().key)
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
        draw_centered_wrapped_text(surface, loc.t(request.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        if self._is_revealed():
            self._draw_reveal(surface, request)
        elif self.guided and request.hint_key:
            draw_wrapped_text(surface, loc.t(request.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, request)

    def _draw_reveal(self, surface: pygame.Surface, request: HypothesisRequest) -> None:
        loc = self.app.localization
        predicted = self.choices[request.key]
        correct = predicted == request.correct_direction
        verdict_key = "prediction.correct" if correct else "prediction.incorrect"
        verdict_color = colors.TEXT if correct else colors.BUTTON_FOCUS_BORDER

        prediction_line = f"{loc.t('prediction.your_prediction')} {loc.t(f'prediction.direction.{predicted}')}"
        draw_centered_text(surface, prediction_line, (CENTER_X, VERDICT_LINE1_Y), 16, colors.TEXT)
        draw_centered_text(surface, loc.t(verdict_key), (CENTER_X, VERDICT_LINE2_Y), 18, verdict_color)

        draw_centered_text(surface, loc.t(request.metric_label_key), (CENTER_X, TABLE_METRIC_Y), 16, colors.TEXT)
        before_x, after_x = CENTER_X - TABLE_COLUMN_OFFSET, CENTER_X + TABLE_COLUMN_OFFSET
        draw_centered_text(surface, loc.t(self.before_label_key), (before_x, TABLE_HEADER_Y), 14, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.after_label_key), (after_x, TABLE_HEADER_Y), 14, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, request.value_format(request.before_value), (before_x, TABLE_VALUE_Y), 16, colors.TEXT)
        draw_centered_text(surface, request.value_format(request.after_value), (after_x, TABLE_VALUE_Y), 16, colors.TEXT)

    def _draw_selected_indicator(self, surface: pygame.Surface, request: HypothesisRequest) -> None:
        selected = self._selected_direction(request)
        if selected is None:
            return
        index = DIRECTIONS.index(selected)
        rect = self.buttons.buttons[index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

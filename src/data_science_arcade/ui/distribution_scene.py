from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.fonts import get_font
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.distribution import DistributionLens, LensChoices, LensOption
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.histogram import draw_histogram, draw_value_marker
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text, draw_wrapped_text, wrap_text

CENTER_X = LOGICAL_SIZE[0] // 2
CHART_RECT = pygame.Rect(80, 68, 800, 150)
BIN_COUNT = 12
AXIS_LABEL_Y = CHART_RECT.bottom + 14
PROMPT_Y = AXIS_LABEL_Y + 32
PROMPT_SIZE = 20
PROMPT_MAX_WIDTH = 820
OPTION_SIZE = (420, 46)
FIRST_OPTION_Y = PROMPT_Y + 60
OPTION_SPACING = 50
HINT_Y = 460
NAV_BUTTON_Y = 500


class DistributionScene(Scene):
    """One real histogram of `values` (spec §25 Lesson 11 'Distribution
    Observatory': "manipulate distributions and compare summary
    statistics") stays visible for the whole stage, stepping through a
    fixed sequence of lenses - each asks which single number best answers
    some real question about the data. Picking an option overlays that
    option's marker_value as a vertical line on the same chart (or draws
    no line, for an option that denies there's anything to measure).

    guided=True also shows each lens's hint; guided=False hides it,
    matching every other stage scene's guided/independent split."""

    def __init__(
        self,
        app,
        title_key: str,
        values: list[float],
        lenses: tuple[DistributionLens, ...],
        on_complete: Callable[[LensChoices], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.values = values
        self.min_value = min(values)
        self.max_value = max(values)
        self.lenses = lenses
        self.on_complete = on_complete
        self.guided = guided
        self.lens_index = 0
        self.choices: LensChoices = {}
        self._rebuild_buttons()

    def _current_lens(self) -> DistributionLens:
        return self.lenses[self.lens_index]

    def _is_last_lens(self) -> bool:
        return self.lens_index == len(self.lenses) - 1

    def _prompt_line_count(self, lens: DistributionLens) -> int:
        loc = self.app.localization
        font = get_font(PROMPT_SIZE)
        return len(wrap_text(loc.t(lens.prompt_key), font, PROMPT_MAX_WIDTH))

    def _first_option_y(self, lens: DistributionLens) -> int:
        # Matches FlowBuilderScene's same fix: most prompts are one line
        # and this equals FIRST_OPTION_Y exactly; a prompt long enough to
        # wrap pushes the options down to stay clear of it.
        line_height = get_font(PROMPT_SIZE).get_linesize() + 4
        return FIRST_OPTION_Y + (self._prompt_line_count(lens) - 1) * line_height

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        lens = self._current_lens()
        first_option_y = self._first_option_y(lens)
        buttons = []
        for index, option in enumerate(lens.options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, first_option_y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.lens_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_lens() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=lens.key in self.choices)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choices[self._current_lens().key] = option_key
            self._rebuild_buttons()

        return choose

    def _back(self) -> None:
        if self.lens_index > 0:
            self.lens_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_lens().key not in self.choices:
            return
        if self._is_last_lens():
            self.on_complete(dict(self.choices))
            return
        self.lens_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def _selected_option(self, lens: DistributionLens) -> LensOption | None:
        selected_key = self.choices.get(lens.key)
        if selected_key is None:
            return None
        return next(option for option in lens.options if option.key == selected_key)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        lens = self._current_lens()

        progress = f"{self.lens_index + 1} / {len(self.lenses)}"
        draw_centered_text(surface, progress, (CENTER_X, 20), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 44), 28, colors.TEXT)

        draw_histogram(surface, CHART_RECT, self.values, self.min_value, self.max_value, BIN_COUNT, colors.TEXT)
        selected = self._selected_option(lens)
        if selected is not None and selected.marker_value is not None:
            draw_value_marker(surface, CHART_RECT, selected.marker_value, self.min_value, self.max_value, colors.BUTTON_FOCUS_BORDER)

        draw_centered_text(surface, f"${self.min_value:,.0f}", (CHART_RECT.left + 28, AXIS_LABEL_Y), 14, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, f"${self.max_value:,.0f}", (CHART_RECT.right - 28, AXIS_LABEL_Y), 14, colors.BUTTON_TEXT_DISABLED)

        draw_centered_wrapped_text(surface, loc.t(lens.prompt_key), (CENTER_X, PROMPT_Y), PROMPT_MAX_WIDTH, PROMPT_SIZE, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, lens)

        if self.guided and lens.hint_key:
            draw_wrapped_text(surface, loc.t(lens.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_selected_indicator(self, surface: pygame.Surface, lens: DistributionLens) -> None:
        selected_key = self.choices.get(lens.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(lens.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

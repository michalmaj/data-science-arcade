from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.flow import EventPlacement, FlowStep
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
STEP_BOX_SIZE = (150, 54)
STEP_SPACING = 172
DIAGRAM_Y = 105
PROMPT_Y = 170
OPTION_SIZE = (420, 46)
FIRST_OPTION_Y = 215
OPTION_SPACING = 54
HINT_Y = 390
NAV_BUTTON_Y = 470


class FlowBuilderScene(Scene):
    """Build an event instrumentation plan by placing an event at each step
    of a flow (spec §25 Lesson 04 'Event Log Factory'): every step in the
    flow diagram stays visible at once, filling in as you go, unlike the
    brief builder's plain '1/2' progress text - one step is active at a
    time, pick which of its candidate events actually belongs there, Back/
    Next between steps. on_complete fires once every step has a choice.

    guided=True also shows each step's explanatory hint text; guided=False
    hides it, matching the brief builder's and source board's guided mode."""

    def __init__(
        self,
        app,
        title_key: str,
        steps: tuple[FlowStep, ...],
        on_complete: Callable[[EventPlacement], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.steps = steps
        self.on_complete = on_complete
        self.guided = guided
        self.step_index = 0
        self.placement: EventPlacement = {}
        self._rebuild_buttons()

    def _current_step(self) -> FlowStep:
        return self.steps[self.step_index]

    def _first_box_x(self) -> int:
        return CENTER_X - (len(self.steps) - 1) * STEP_SPACING // 2

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        step = self._current_step()
        buttons = []
        for index, option in enumerate(step.options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.step_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_step() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=step.key in self.placement)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _is_last_step(self) -> bool:
        return self.step_index == len(self.steps) - 1

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.placement[self._current_step().key] = option_key
            self._rebuild_buttons()

        return choose

    def _back(self) -> None:
        if self.step_index > 0:
            self.step_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_step().key not in self.placement:
            return
        if self._is_last_step():
            self.on_complete(dict(self.placement))
            return
        self.step_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        step = self._current_step()

        progress = f"{self.step_index + 1} / {len(self.steps)}"
        draw_centered_text(surface, progress, (CENTER_X, 25), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 50), 28, colors.TEXT)

        self._draw_flow_diagram(surface)
        draw_centered_text(surface, loc.t(step.prompt_key), (CENTER_X, PROMPT_Y), 20, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, step)

        if self.guided and step.hint_key:
            draw_wrapped_text(surface, loc.t(step.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

    def _draw_flow_diagram(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        first_x = self._first_box_x()
        for index, step in enumerate(self.steps):
            rect = pygame.Rect(0, 0, *STEP_BOX_SIZE)
            rect.center = (first_x + index * STEP_SPACING, DIAGRAM_Y)
            pygame.draw.rect(surface, colors.PANEL_BACKGROUND, rect, border_radius=6)
            if index == self.step_index:
                pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, rect, width=2, border_radius=6)
            label_color = colors.TEXT if step.key in self.placement else colors.BUTTON_TEXT_DISABLED
            draw_single_line(surface, loc.t(step.short_label_key), (rect.left + 10, rect.top + 12), rect.width - 20, 14, label_color)
            # ASCII only: pygame's bundled default font (core/fonts.py) covers
            # Latin Extended-A, not general Unicode symbols like a checkmark -
            # a "✓" here silently rendered as a tofu box instead of crashing.
            marker = "OK" if step.key in self.placement else "?"
            draw_centered_text(surface, marker, (rect.centerx, rect.bottom - 16), 14, label_color)

    def _draw_selected_indicator(self, surface: pygame.Surface, step: FlowStep) -> None:
        selected_key = self.placement.get(step.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(step.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

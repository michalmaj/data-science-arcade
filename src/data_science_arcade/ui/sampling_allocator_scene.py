from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.sampling import SamplingAllocation, SamplingGroup
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_single_line, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
STEP_BUTTON_SIZE = (40, 40)
LABEL_X = 160
LABEL_WIDTH = 360
MINUS_X = 560
VALUE_X = 630
PLUS_X = 700
FIRST_ROW_Y = 150
ROW_SPACING = 62
REMAINING_Y = 400
HINT_Y = 430
CONFIRM_SIZE = (220, 44)
CONFIRM_Y = 480


class SamplingAllocatorScene(Scene):
    """Allocate a fixed contact budget across customer groups (spec §25
    Lesson 05 'Sampling Mission'): +/- steppers per group, a running
    'remaining budget' total, Confirm only enabled once every last contact
    is spent. guided=True also shows a hint about what an even split
    doesn't guarantee; guided=False hides it.

    diagnostic is an optional per-row status line (Lesson 19 'Power
    Plant' reuse): given a group and its current allocation, return
    (text, flagged) to draw beneath that row, or None to draw nothing -
    the default draws nothing, so Lesson 05 is unaffected. row_spacing
    is likewise overridable for callers whose diagnostic line needs more
    vertical room than Lesson 05's bare label-and-steppers row does."""

    def __init__(
        self,
        app,
        title_key: str,
        prompt_key: str,
        groups: tuple[SamplingGroup, ...],
        total_budget: int,
        step: int,
        on_complete: Callable[[SamplingAllocation], None],
        guided: bool = True,
        hint_key: str | None = None,
        diagnostic: Callable[[SamplingGroup, int], tuple[str, bool] | None] = lambda group, allocated: None,
        row_spacing: int = ROW_SPACING,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.prompt_key = prompt_key
        self.groups = groups
        self.total_budget = total_budget
        self.step = step
        self.on_complete = on_complete
        self.guided = guided
        self.hint_key = hint_key
        self.diagnostic = diagnostic
        self.row_spacing = row_spacing
        self.allocation: SamplingAllocation = {group.key: 0 for group in groups}
        self._rebuild_buttons()

    def _allocated_total(self) -> int:
        return sum(self.allocation.values())

    def _remaining(self) -> int:
        return self.total_budget - self._allocated_total()

    def _headroom(self, group: SamplingGroup) -> int:
        """How much more this one group can still absorb, independent of
        the total budget - unbounded (a large int) when group.available is
        None, matching every pre-existing caller's behavior exactly."""
        if group.available is None:
            return self.total_budget
        return group.available - self.allocation[group.key]

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        buttons: list[Button] = []
        self.minus_buttons: dict[str, Button] = {}
        self.plus_buttons: dict[str, Button] = {}
        remaining = self._remaining()

        for index, group in enumerate(self.groups):
            y = FIRST_ROW_Y + index * self.row_spacing
            minus_rect = pygame.Rect(0, 0, *STEP_BUTTON_SIZE)
            minus_rect.center = (MINUS_X, y)
            minus_button = Button(
                minus_rect, "-", self._make_decrement(group.key), enabled=self.allocation[group.key] > 0
            )
            self.minus_buttons[group.key] = minus_button
            buttons.append(minus_button)

            plus_rect = pygame.Rect(0, 0, *STEP_BUTTON_SIZE)
            plus_rect.center = (PLUS_X, y)
            plus_enabled = remaining >= self.step and self._headroom(group) >= self.step
            plus_button = Button(plus_rect, "+", self._make_increment(group), enabled=plus_enabled)
            self.plus_buttons[group.key] = plus_button
            buttons.append(plus_button)

        confirm_rect = pygame.Rect(0, 0, *CONFIRM_SIZE)
        confirm_rect.center = (CENTER_X, CONFIRM_Y)
        self.confirm_button = Button(confirm_rect, loc.t("source_board.confirm"), self._confirm, enabled=remaining == 0)
        buttons.append(self.confirm_button)

        self.buttons = ButtonGroup(buttons)

    def _make_increment(self, group: SamplingGroup) -> Callable[[], None]:
        def increment() -> None:
            # Re-checked here, not just via the button's own `enabled` flag -
            # matches this method's pre-existing _remaining() guard, and
            # matters for tests that call on_activate() directly, bypassing
            # `enabled` entirely.
            if self._remaining() >= self.step and self._headroom(group) >= self.step:
                self.allocation[group.key] += self.step
                self._rebuild_buttons()

        return increment

    def _make_decrement(self, key: str) -> Callable[[], None]:
        def decrement() -> None:
            if self.allocation[key] > 0:
                self.allocation[key] -= self.step
                self._rebuild_buttons()

        return decrement

    def _confirm(self) -> None:
        if self._remaining() == 0:
            self.on_complete(dict(self.allocation))

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special Escape handling needed: LessonRunner wraps every stage
        # in Pausable, which intercepts Escape before this scene sees it.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 50), 28, colors.TEXT)
        draw_centered_text(surface, loc.t(self.prompt_key), (CENTER_X, 90), 18, colors.TEXT)

        for index, group in enumerate(self.groups):
            y = FIRST_ROW_Y + index * self.row_spacing
            draw_single_line(surface, loc.t(group.label_key), (LABEL_X, y - 10), LABEL_WIDTH, 20, colors.TEXT)
            draw_centered_text(surface, str(self.allocation[group.key]), (VALUE_X, y), 20, colors.TEXT)

            diagnostic = self.diagnostic(group, self.allocation[group.key])
            if diagnostic is not None:
                text, flagged = diagnostic
                color = colors.BUTTON_FOCUS_BORDER if flagged else colors.BUTTON_TEXT_DISABLED
                draw_centered_text(surface, text, (CENTER_X, y + 24), 14, color)

        self.buttons.draw(surface)

        remaining_text = f"{loc.t('sampling.remaining_label')} {self._remaining()} / {self.total_budget}"
        draw_centered_text(surface, remaining_text, (CENTER_X, REMAINING_Y), 18, colors.BUTTON_FOCUS_BORDER)

        if self.guided and self.hint_key:
            draw_wrapped_text(surface, loc.t(self.hint_key), (CENTER_X - 300, HINT_Y), 600, 15, colors.BUTTON_TEXT_DISABLED)

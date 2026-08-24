from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.brief import AnalyticalBrief, BriefField
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
OPTION_SIZE = (420, 46)
FIRST_OPTION_Y = 190
OPTION_SPACING = 56
NAV_BUTTON_Y = 470


class BriefBuilderScene(Scene):
    """The step-by-step 'build a structured analytical brief' wizard (spec
    §25 Lesson 01's core mechanic, kept generic so any lesson can reuse it):
    one field per screen, pick an option (doesn't auto-advance - has to be
    confirmed with Next, same as picking the wrong option and changing your
    mind should be cheap), Back/Next between fields. on_complete fires once
    every field has a choice.

    guided=True also shows each field's explanatory hint text (spec Act 3
    'receive explanatory feedback'); guided=False hides it (Act 4 'less
    guidance')."""

    def __init__(
        self,
        app,
        title_key: str,
        fields: tuple[BriefField, ...],
        on_complete: Callable[[AnalyticalBrief], None],
        guided: bool = True,
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.fields = fields
        self.on_complete = on_complete
        self.guided = guided
        self.field_index = 0
        self.choices: AnalyticalBrief = {}
        self._rebuild_buttons()

    def _current_field(self) -> BriefField:
        return self.fields[self.field_index]

    def _rebuild_buttons(self) -> None:
        loc = self.app.localization
        field = self._current_field()
        buttons = []
        for index, option in enumerate(field.options):
            rect = pygame.Rect(0, 0, *OPTION_SIZE)
            rect.center = (CENTER_X, FIRST_OPTION_Y + index * OPTION_SPACING)
            buttons.append(Button(rect, loc.t(option.label_key), self._make_choose(option.key)))

        back_rect = pygame.Rect(0, 0, 140, 44)
        back_rect.center = (CENTER_X - 90, NAV_BUTTON_Y)
        self.back_button = Button(back_rect, loc.t("brief.back"), self._back, enabled=self.field_index > 0)
        buttons.append(self.back_button)

        next_rect = pygame.Rect(0, 0, 140, 44)
        next_rect.center = (CENTER_X + 90, NAV_BUTTON_Y)
        next_label = loc.t("brief.finish") if self._is_last_field() else loc.t("brief.next")
        self.next_button = Button(next_rect, next_label, self._next, enabled=field.key in self.choices)
        buttons.append(self.next_button)

        self.buttons = ButtonGroup(buttons)

    def _is_last_field(self) -> bool:
        return self.field_index == len(self.fields) - 1

    def _make_choose(self, option_key: str) -> Callable[[], None]:
        def choose() -> None:
            self.choices[self._current_field().key] = option_key
            self._rebuild_buttons()

        return choose

    def _back(self) -> None:
        if self.field_index > 0:
            self.field_index -= 1
            self._rebuild_buttons()

    def _next(self) -> None:
        if self._current_field().key not in self.choices:
            return
        if self._is_last_field():
            self.on_complete(dict(self.choices))
            return
        self.field_index += 1
        self._rebuild_buttons()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No Escape-to-quit here: an accidental Escape shouldn't abandon
        # mid-lesson progress the way it harmlessly backs out of a menu.
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        field = self._current_field()

        progress = f"{self.field_index + 1} / {len(self.fields)}"
        draw_centered_text(surface, progress, (CENTER_X, 60), 16, colors.BUTTON_TEXT_DISABLED)
        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 90), 28, colors.TEXT)
        draw_centered_text(surface, loc.t(field.prompt_key), (CENTER_X, 140), 20, colors.TEXT)

        self.buttons.draw(surface)
        self._draw_selected_indicator(surface, field)

        if self.guided and field.hint_key:
            draw_wrapped_text(
                surface,
                loc.t(field.hint_key),
                (CENTER_X - 300, 400),
                600,
                15,
                colors.BUTTON_TEXT_DISABLED,
            )

    def _draw_selected_indicator(self, surface: pygame.Surface, field: BriefField) -> None:
        selected_key = self.choices.get(field.key)
        if selected_key is None:
            return
        selected_index = next(i for i, option in enumerate(field.options) if option.key == selected_key)
        rect = self.buttons.buttons[selected_index].rect
        # A filled bar on the leading edge, not a border - keyboard focus
        # already uses a full border (Button.draw), and this option can be
        # both focused and selected at once, or neither; a second border
        # around the same or a different button reads as "two things are
        # focused," so "selected" needs a visually distinct treatment.
        marker = pygame.Rect(rect.left, rect.top + 6, 4, rect.height - 12)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

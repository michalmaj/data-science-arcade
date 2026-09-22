import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_centered_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2

CREDIT_LINE_KEYS = (
    "credits.author_line",
    "credits.built_with_line",
)


class CreditsScene(Scene):
    """A small, real credits screen - replaces the generic
    PlaceholderScene the main menu's Credits button used to open (which
    only ever said "Coming in a later phase.", with nothing left to add
    later once the course itself shipped)."""

    def __init__(self, app) -> None:
        super().__init__(app)
        back_rect = pygame.Rect(0, 0, 200, 48)
        back_rect.center = (CENTER_X, 420)
        self.buttons = ButtonGroup([Button(back_rect, app.localization.t("common.back"), self._back)])

    def _back(self) -> None:
        self.app.scenes.pop()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, loc.t("menu.credits"), (CENTER_X, 140), 36, colors.TEXT)
        draw_centered_text(surface, loc.t("app.title"), (CENTER_X, 200), 22, colors.BUTTON_FOCUS_BORDER)
        for index, key in enumerate(CREDIT_LINE_KEYS):
            draw_centered_wrapped_text(surface, loc.t(key), (CENTER_X, 250 + index * 40), 700, 16, colors.TEXT)
        self.buttons.draw(surface)

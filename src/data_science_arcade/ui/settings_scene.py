import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.localization.service import LOCALE_ENDONYMS
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text

CENTER_X = LOGICAL_SIZE[0] // 2


class SettingsScene(Scene):
    """Minimal settings screen. Only display mode and language exist this
    early; audio/accessibility options land with their own systems."""

    def __init__(self, app) -> None:
        super().__init__(app)
        fullscreen_rect = pygame.Rect(0, 0, 260, 48)
        fullscreen_rect.center = (CENTER_X, 230)
        language_rect = pygame.Rect(0, 0, 260, 48)
        language_rect.center = (CENTER_X, 290)
        back_rect = pygame.Rect(0, 0, 200, 48)
        back_rect.center = (CENTER_X, 360)
        self.fullscreen_button = Button(fullscreen_rect, "", self._toggle_fullscreen)
        self.language_button = Button(language_rect, "", self._toggle_language)
        self.back_button = Button(back_rect, "", self._back)
        self.buttons = ButtonGroup([self.fullscreen_button, self.language_button, self.back_button])
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        loc = self.app.localization
        state = loc.t("common.on") if self.app.fullscreen else loc.t("common.off")
        self.fullscreen_button.label = f"{loc.t('settings.fullscreen_label')} {state}"
        self.language_button.label = f"{loc.t('settings.language_label')} {LOCALE_ENDONYMS[loc.locale]}"
        self.back_button.label = loc.t("common.back")

    def _toggle_fullscreen(self) -> None:
        self.app.toggle_fullscreen()
        self._refresh_labels()

    def _toggle_language(self) -> None:
        next_locale = "pl" if self.app.localization.locale == "en" else "en"
        self.app.localization.set_locale(next_locale)
        self._refresh_labels()

    def _back(self) -> None:
        self.app.scenes.pop()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, self.app.localization.t("settings.title"), (CENTER_X, 160), 36, colors.TEXT)
        self.buttons.draw(surface)

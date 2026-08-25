from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.ui import colors
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2
BOX_RECT = pygame.Rect(40, 130, 880, 370)


class TwistRevealScene(Scene):
    """Shows the lesson's twist as real computed evidence, not a scripted
    number: an ordered list of labeled rates plus the Dataset's own
    python_mirror(), so the reveal is backed by an actual (if small,
    hand-crafted) Dataset rather than text pretending a computation
    happened. comparisons is (label_key, rate) pairs, shown in order -
    two for a before/after contrast, more for an N-way breakdown."""

    def __init__(
        self,
        app,
        title_key: str,
        narrative_keys: tuple[str, ...],
        dataset: Dataset,
        comparisons: tuple[tuple[str, float], ...],
        on_complete: Callable[[], None],
    ) -> None:
        super().__init__(app)
        self.title_key = title_key
        self.narrative_keys = narrative_keys
        self.dataset = dataset
        self.comparisons = comparisons
        self.on_complete = on_complete

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        ):
            self.on_complete()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.on_complete()

    def draw(self, surface: pygame.Surface) -> None:
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)

        draw_centered_text(surface, loc.t(self.title_key), (CENTER_X, 60), 28, colors.TEXT)

        pygame.draw.rect(surface, colors.PANEL_BACKGROUND, BOX_RECT, border_radius=8)
        pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, BOX_RECT, width=1, border_radius=8)

        left = BOX_RECT.left + 20
        width = BOX_RECT.width - 40
        y = BOX_RECT.top + 16
        for key in self.narrative_keys:
            draw_wrapped_text(surface, loc.t(key), (left, y), width, 17, colors.TEXT)
            y += 44

        y += 10
        for label_key, rate in self.comparisons:
            text = f"{loc.t(label_key)} {rate:.0%}"
            draw_wrapped_text(surface, text, (left, y), width, 20, colors.BUTTON_FOCUS_BORDER)
            y += 30

        y += 16
        for line in self.dataset.python_mirror().split("\n"):
            draw_wrapped_text(surface, line, (left, y), width, 14, colors.BUTTON_TEXT_DISABLED)
            y += 20

        draw_centered_text(
            surface,
            loc.t("dialogue.continue_hint"),
            (CENTER_X, BOX_RECT.bottom - 16),
            14,
            colors.BUTTON_TEXT_DISABLED,
        )

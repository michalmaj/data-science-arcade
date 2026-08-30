import pygame

from data_science_arcade.core.fonts import get_font
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_wrapped_text, wrap_text

HINT_BUTTON_SIZE = (100, 32)
HINT_TEXT_MAX_WIDTH = 600
HINT_TEXT_SIZE = 15
HINT_LINE_SPACING = 4


class HintController:
    """Direction -> Concept -> Procedure, revealed one tier at a time by
    the student clicking a "Hint" button - not `guided`'s single
    always-shown-or-hidden string. `revealed_tier` (0-3) is exactly
    "hints used" for whatever request this controller belongs to.

    Standalone and fully self-contained: draws its own button plus
    whatever tiers are already revealed at a given position. Not wired
    into any of the ~15 existing reused scenes (CorrelationScene,
    SegmentSlicerScene, etc.) yet - those still use today's single
    guided-bool hint_key unchanged. Real tiered hint *text* per request is
    a content decision belonging to each lesson's own content-deepening
    pass, not this foundation PR."""

    def __init__(self, app, hint_keys: tuple[str, ...], button_topleft: tuple[int, int]) -> None:
        if not 1 <= len(hint_keys) <= 3:
            raise ValueError(f"HintController supports 1-3 tiers, got {len(hint_keys)}")
        self.app = app
        self.hint_keys = hint_keys
        self.revealed_tier = 0
        rect = pygame.Rect(button_topleft, HINT_BUTTON_SIZE)
        self.button = Button(rect, app.localization.t("runtime.hint_button"), self.reveal_next)
        self.buttons = ButtonGroup([self.button])

    def reveal_next(self) -> None:
        if self.revealed_tier < len(self.hint_keys):
            self.revealed_tier += 1
            self.button.enabled = self.revealed_tier < len(self.hint_keys)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface, text_topleft: tuple[int, int]) -> None:
        self.buttons.draw(surface)
        loc = self.app.localization
        font = get_font(HINT_TEXT_SIZE)
        line_height = font.get_linesize() + HINT_LINE_SPACING
        x, y = text_topleft
        for index in range(self.revealed_tier):
            text = loc.t(self.hint_keys[index])
            draw_wrapped_text(surface, text, (x, y), HINT_TEXT_MAX_WIDTH, HINT_TEXT_SIZE, colors.BUTTON_TEXT_DISABLED, line_spacing=HINT_LINE_SPACING)
            y += len(wrap_text(text, font, HINT_TEXT_MAX_WIDTH)) * line_height + HINT_LINE_SPACING

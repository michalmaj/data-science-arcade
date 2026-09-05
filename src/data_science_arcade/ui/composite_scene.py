from collections.abc import Callable

import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.text import draw_centered_text, draw_wrapped_text

CENTER_X = LOGICAL_SIZE[0] // 2


class SequenceScene(Scene):
    """Shows `first`, then swaps to `build_second()` once `advance_to_second`
    is called - lets a single LessonRunner stage present two already-
    existing scenes back to back (e.g. inspect real data, then decide)
    without a bespoke composite mechanic per lesson. Matches the
    "runtime-conditional sub-scene can't be a second, sometimes-included
    stage" reasoning L05's own _DesignThenAllocateScene established,
    generalized to an unconditional two-step sequence rather than a
    conditional one - first built for L06's own mastery act (inspect the
    mastery export, then decide), reused as-is by L07."""

    def __init__(self, app, first: Scene, build_second: Callable[[], Scene]) -> None:
        super().__init__(app)
        self._build_second = build_second
        self._active = first

    def advance_to_second(self) -> None:
        self._active = self._build_second()

    def __getattr__(self, name: str):
        return getattr(self._active, name)

    def on_enter(self) -> None:
        self._active.on_enter()

    def on_exit(self) -> None:
        self._active.on_exit()

    def handle_event(self, event) -> None:
        self._active.handle_event(event)

    def draw(self, surface) -> None:
        self._active.draw(surface)


class OfferThenTaskScene(Scene):
    """Engage-or-skip gate for an optional mastery act whose task doesn't
    fit MasteryChallengeScene's own pick-a-metric-then-compare-two-values
    shape (e.g. a MultiChoiceField selection instead) - mirrors that
    scene's own OFFER phase so skipping still stays a real, zero-
    consequence choice like every other lesson's optional act. A single
    LessonRunner stage either way, matching SequenceScene's own reasoning
    for why a runtime-conditional sub-scene can't be a second,
    sometimes-included item in LessonRunner's own fixed stage list.
    First built for L06, reused as-is by L07 - `title_key`/`line_keys`
    are what let each lesson show its own real framing text without
    subclassing."""

    def __init__(
        self,
        app,
        build_task: Callable[[Callable[[dict], None]], Scene],
        on_complete: Callable[[bool, dict | None], None],
        title_key: str,
        line_keys: tuple[str, ...] = (),
    ) -> None:
        super().__init__(app)
        self._build_task = build_task
        self._on_complete = on_complete
        self._title_key = title_key
        self._line_keys = line_keys
        self._active: Scene | None = None
        self._rebuild_offer_buttons()

    def __getattr__(self, name: str):
        if self._active is not None:
            return getattr(self._active, name)
        raise AttributeError(name)

    def _rebuild_offer_buttons(self) -> None:
        loc = self.app.localization
        engage_rect = pygame.Rect(0, 0, 420, 46)
        engage_rect.center = (CENTER_X, 260)
        skip_rect = pygame.Rect(0, 0, 420, 46)
        skip_rect.center = (CENTER_X, 320)
        self.buttons = ButtonGroup(
            [
                Button(engage_rect, loc.t("mastery.engage"), self._engage),
                Button(skip_rect, loc.t("mastery.skip"), self._skip),
            ]
        )

    def _engage(self) -> None:
        self._active = self._build_task(lambda result: self._on_complete(True, result))

    def _skip(self) -> None:
        self._on_complete(False, None)

    def on_enter(self) -> None:
        if self._active is not None:
            self._active.on_enter()

    def on_exit(self) -> None:
        if self._active is not None:
            self._active.on_exit()

    def handle_event(self, event) -> None:
        if self._active is not None:
            self._active.handle_event(event)
        else:
            self.buttons.handle_event(event)

    def draw(self, surface) -> None:
        if self._active is not None:
            self._active.draw(surface)
            return
        loc = self.app.localization
        surface.fill(colors.BACKGROUND)
        draw_centered_text(surface, loc.t(self._title_key), (CENTER_X, 90), 28, colors.TEXT)
        for index, key in enumerate(self._line_keys):
            draw_wrapped_text(surface, loc.t(key), (CENTER_X - 400, 150 + index * 40), 800, 16, colors.TEXT)
        self.buttons.draw(surface)

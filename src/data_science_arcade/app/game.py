import pygame

from data_science_arcade.core import fonts
from data_science_arcade.core.display import (
    LOGICAL_SIZE,
    TARGET_FPS,
    compute_scaled_rect,
    window_to_logical,
)
from data_science_arcade.core.scenes import SceneManager
from data_science_arcade.localization.service import Localization
from data_science_arcade.progress.dev_mode import is_dev_mode
from data_science_arcade.progress.model import LessonState
from data_science_arcade.progress.store import ProgressStore
from data_science_arcade.ui import colors
from data_science_arcade.ui.main_menu_scene import MainMenuScene

WINDOW_TITLE = "Data Science Arcade"
MOUSE_POSITION_EVENTS = (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)


class App:
    """Owns the window, the scene stack, and the main loop.

    Gameplay always renders to a fixed 960x540 logical surface, which is then
    scaled (preserving aspect ratio, letterboxed/pillarboxed, never stretched)
    onto the real window - fixed-size when windowed, scaled-to-desktop in
    fullscreen. See spec §11.
    """

    def __init__(self, size: tuple[int, int] = LOGICAL_SIZE, fps: int = TARGET_FPS) -> None:
        self.size = size
        self.fps = fps
        self.logical_surface: pygame.Surface | None = None
        self.window_surface: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.running = False
        self.fullscreen = False
        self.scenes = SceneManager()
        self.localization = Localization()
        self.progress_store = ProgressStore()
        self.progress = self.progress_store.load()
        self.dev_mode = is_dev_mode()

    def init(self) -> None:
        pygame.init()
        fonts.clear_cache()
        self.logical_surface = pygame.Surface(self.size)
        self.fullscreen = self.progress.fullscreen
        try:
            self.localization.set_locale(self.progress.language)
        except ValueError:
            pass  # unrecognized locale in an old/corrupt save - keep the default
        self._apply_display_mode()
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.scenes.push(MainMenuScene(self))

    def save_progress(self) -> None:
        self.progress.fullscreen = self.fullscreen
        self.progress.language = self.localization.locale
        self.progress_store.save(self.progress)

    def effective_lesson_state(self, lesson_number: int) -> LessonState:
        """Real progress, except in dev mode a locked lesson displays as
        unlocked (for demoing the course map) without touching the save."""
        state = self.progress.state_of(lesson_number)
        if self.dev_mode and state == LessonState.LOCKED:
            return LessonState.UNLOCKED
        return state

    def _apply_display_mode(self) -> None:
        if self.fullscreen:
            self.window_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window_surface = pygame.display.set_mode(self.size)
        # Recreating the window can leave a stale mouse-down (the click that
        # triggered this) or an OS-generated refocus event sitting in the
        # queue against the old layout; drop it rather than risk it firing
        # against the new one. Mitigates a reported "first click after
        # switching fullscreen is swallowed" symptom - not a confirmed
        # root-caused fix, since real OS window-focus behavior isn't
        # reproducible headlessly.
        pygame.event.clear(MOUSE_POSITION_EVENTS)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self._apply_display_mode()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
        else:
            if event.type in MOUSE_POSITION_EVENTS:
                # Scenes draw onto the fixed logical canvas, so mouse hit
                # testing needs logical coordinates too - raw window
                # coordinates only line up 1:1 with it when unscaled
                # (windowed mode); fullscreen scales and letterboxes.
                event.pos = self._window_pos_to_logical(event.pos)
            self.scenes.handle_event(event)

    def _window_pos_to_logical(self, window_pos: tuple[int, int]) -> tuple[int, int]:
        x, y = window_to_logical(window_pos, self.size, self.window_surface.get_size())
        return (int(x), int(y))

    def update(self, dt: float) -> None:
        self.scenes.update(dt)

    def draw(self) -> None:
        self.logical_surface.fill(colors.BACKGROUND)
        self.scenes.draw(self.logical_surface)

        rect = compute_scaled_rect(self.size, self.window_surface.get_size())
        scaled = pygame.transform.scale(self.logical_surface, rect.size)
        self.window_surface.fill((0, 0, 0))
        self.window_surface.blit(scaled, rect.topleft)
        pygame.display.flip()

    def run(self) -> None:
        self.init()
        try:
            while self.running:
                dt = self.clock.tick(self.fps) / 1000
                for event in pygame.event.get():
                    self.handle_event(event)
                self.update(dt)
                self.draw()
        finally:
            pygame.quit()

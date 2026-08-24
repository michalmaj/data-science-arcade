import pygame

LOGICAL_SIZE = (960, 540)
TARGET_FPS = 60
WINDOW_TITLE = "Data Science Arcade"
BACKGROUND_COLOR = (12, 14, 22)


class App:
    """Owns the pygame window and the main loop for the fixed 960x540 logical canvas."""

    def __init__(self, size: tuple[int, int] = LOGICAL_SIZE, fps: int = TARGET_FPS) -> None:
        self.size = size
        self.fps = fps
        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.running = False

    def init(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)
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

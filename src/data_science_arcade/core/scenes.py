import pygame


class Scene:
    """Base class for a single game screen (menu, hub, workbench, ...)."""

    def __init__(self, app) -> None:
        self.app = app

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class SceneManager:
    """A simple scene stack: push/pop for navigation, replace to swap the top scene."""

    def __init__(self) -> None:
        self._stack: list[Scene] = []

    @property
    def current(self) -> Scene | None:
        return self._stack[-1] if self._stack else None

    def push(self, scene: Scene) -> None:
        if self.current is not None:
            self.current.on_exit()
        self._stack.append(scene)
        scene.on_enter()

    def pop(self) -> None:
        if not self._stack:
            return
        self._stack.pop().on_exit()
        if self.current is not None:
            self.current.on_enter()

    def replace(self, scene: Scene) -> None:
        if self._stack:
            self._stack.pop().on_exit()
        self._stack.append(scene)
        scene.on_enter()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current is not None:
            self.current.handle_event(event)

    def update(self, dt: float) -> None:
        if self.current is not None:
            self.current.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.current is not None:
            self.current.draw(surface)

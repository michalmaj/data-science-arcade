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


class Pausable(Scene):
    """Wraps another scene so Escape triggers on_escape instead of whatever
    the inner scene would otherwise do with it - e.g. a lesson stage that
    normally uses Escape to advance dialogue, wrapped so Escape opens a
    pause menu instead. Everything else (update/draw/other events) passes
    straight through to the inner scene, and its own on_enter/on_exit fire
    correctly even though SceneManager only ever sees this wrapper - it's
    the only thing actually on the stack."""

    def __init__(self, app, inner: Scene, on_escape) -> None:
        super().__init__(app)
        self.inner = inner
        self.on_escape = on_escape

    def __getattr__(self, name: str):
        # Anything not defined on Pausable itself (buttons, next_button,
        # dataset, ...) transparently reaches through to the inner scene,
        # so callers mostly don't need to know they're holding a wrapper.
        # isinstance()/type() checks still see Pausable, not the inner
        # scene's class - unwrap .inner explicitly for those.
        return getattr(self.inner, name)

    def on_enter(self) -> None:
        self.inner.on_enter()

    def on_exit(self) -> None:
        self.inner.on_exit()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_escape()
            return
        self.inner.handle_event(event)

    def update(self, dt: float) -> None:
        self.inner.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.inner.draw(surface)


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

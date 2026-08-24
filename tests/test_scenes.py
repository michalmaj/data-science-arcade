import pygame

from data_science_arcade.core.scenes import Pausable, Scene, SceneManager


class RecordingScene(Scene):
    def __init__(self, name: str) -> None:
        super().__init__(app=None)
        self.name = name
        self.events: list[str] = []

    def on_enter(self) -> None:
        self.events.append("enter")

    def on_exit(self) -> None:
        self.events.append("exit")

    def handle_event(self, event: pygame.event.Event) -> None:
        self.events.append(f"event:{pygame.event.event_name(event.type)}")

    def update(self, dt: float) -> None:
        self.events.append("update")

    def draw(self, surface) -> None:
        self.events.append("draw")


def test_push_enters_the_new_scene_and_becomes_current():
    manager = SceneManager()
    first = RecordingScene("first")

    manager.push(first)

    assert manager.current is first
    assert first.events == ["enter"]


def test_push_on_top_of_another_scene_exits_the_previous_one():
    manager = SceneManager()
    first, second = RecordingScene("first"), RecordingScene("second")
    manager.push(first)

    manager.push(second)

    assert manager.current is second
    assert first.events == ["enter", "exit"]
    assert second.events == ["enter"]


def test_pop_returns_to_the_previous_scene_and_re_enters_it():
    manager = SceneManager()
    first, second = RecordingScene("first"), RecordingScene("second")
    manager.push(first)
    manager.push(second)

    manager.pop()

    assert manager.current is first
    assert second.events == ["enter", "exit"]
    assert first.events == ["enter", "exit", "enter"]


def test_pop_on_an_empty_stack_is_a_no_op():
    manager = SceneManager()

    manager.pop()

    assert manager.current is None


def test_replace_swaps_the_top_scene_without_touching_the_rest_of_the_stack():
    manager = SceneManager()
    first, second, third = RecordingScene("first"), RecordingScene("second"), RecordingScene("third")
    manager.push(first)
    manager.push(second)

    manager.replace(third)

    assert manager.current is third
    assert second.events == ["enter", "exit"]
    assert third.events == ["enter"]
    manager.pop()
    assert manager.current is first


def test_pausable_forwards_on_enter_and_on_exit_to_the_inner_scene():
    manager = SceneManager()
    inner = RecordingScene("inner")
    wrapped = Pausable(app=None, inner=inner, on_escape=lambda: None)

    manager.push(wrapped)
    manager.pop()

    assert inner.events == ["enter", "exit"]


def test_pausable_forwards_update_and_draw_to_the_inner_scene():
    inner = RecordingScene("inner")
    wrapped = Pausable(app=None, inner=inner, on_escape=lambda: None)

    wrapped.update(0.1)
    wrapped.draw(surface=None)

    assert inner.events == ["update", "draw"]


def test_pausable_forwards_non_escape_events_to_the_inner_scene():
    inner = RecordingScene("inner")
    wrapped = Pausable(app=None, inner=inner, on_escape=lambda: None)

    wrapped.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))

    assert inner.events == ["event:MouseButtonDown"]


def test_pausable_intercepts_escape_instead_of_forwarding_it():
    calls = []
    inner = RecordingScene("inner")
    wrapped = Pausable(app=None, inner=inner, on_escape=lambda: calls.append("paused"))

    wrapped.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))

    assert calls == ["paused"]
    assert inner.events == []  # the inner scene never saw the Escape

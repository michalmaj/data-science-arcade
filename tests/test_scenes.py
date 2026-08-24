from data_science_arcade.core.scenes import Scene, SceneManager


class RecordingScene(Scene):
    def __init__(self, name: str) -> None:
        super().__init__(app=None)
        self.name = name
        self.events: list[str] = []

    def on_enter(self) -> None:
        self.events.append("enter")

    def on_exit(self) -> None:
        self.events.append("exit")


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

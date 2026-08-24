from collections.abc import Callable

from data_science_arcade.core.scenes import Scene

StageFactory = Callable[[Callable[[], None]], Scene]


class LessonRunner:
    """Drives a lesson through an ordered sequence of stage scenes.

    Each stage factory takes an `advance` callback and returns the Scene
    for that stage; the stage scene calls `advance` itself once the
    player finishes it (e.g. a DialogueScene's on_complete, or a brief
    builder's on_complete). Stages replace each other on the scene stack
    (constant depth) rather than pushing deeper each time. Finishing the
    last stage pops back to whatever opened the lesson (the course map).

    Not persisted: starting a lesson always begins at the first stage.
    Mid-lesson checkpoint/resume (spec §22) is deferred - see
    decisions/IMPLEMENTATION_STATE.md.
    """

    def __init__(self, app, stages: list[StageFactory], on_finished: Callable[[], None] | None = None) -> None:
        self.app = app
        self.stages = stages
        self.on_finished = on_finished
        self.index = 0

    def start(self) -> None:
        self.app.scenes.push(self._build_current_stage())

    def _build_current_stage(self) -> Scene:
        return self.stages[self.index](self._advance)

    def _advance(self) -> None:
        self.index += 1
        if self.index >= len(self.stages):
            self.app.scenes.pop()
            if self.on_finished:
                self.on_finished()
            return
        self.app.scenes.replace(self._build_current_stage())

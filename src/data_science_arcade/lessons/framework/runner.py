from collections.abc import Callable

from data_science_arcade.core.scenes import Pausable, Scene
from data_science_arcade.ui.pause_menu_scene import PauseMenuScene

StageFactory = Callable[[Callable[[], None]], Scene]


class LessonRunner:
    """Drives a lesson through an ordered sequence of stage scenes.

    Each stage factory takes an `advance` callback and returns the Scene
    for that stage; the stage scene calls `advance` itself once the
    player finishes it (e.g. a DialogueScene's on_complete, or a brief
    builder's on_complete). Stages replace each other on the scene stack
    (constant depth) rather than pushing deeper each time. Finishing the
    last stage pops back to whatever opened the lesson (the course map).

    Every stage is wrapped in Pausable, so Escape opens a pause menu
    (Resume, or Quit to abandon the lesson without finishing it) instead
    of whatever the stage would otherwise do with Escape - individual
    stage scenes never need to know about pausing at all.

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
        stage_scene = self.stages[self.index](self._advance)
        return Pausable(self.app, stage_scene, on_escape=self._open_pause_menu)

    def _open_pause_menu(self) -> None:
        background = self.app.scenes.current
        self.app.scenes.push(PauseMenuScene(self.app, background=background, on_quit=self.app.scenes.pop))

    def _advance(self) -> None:
        self.index += 1
        if self.index >= len(self.stages):
            self.app.scenes.pop()
            if self.on_finished:
                self.on_finished()
            return
        self.app.scenes.replace(self._build_current_stage())

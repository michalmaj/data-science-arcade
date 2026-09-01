from collections.abc import Callable

from data_science_arcade.core.scenes import Pausable, Scene
from data_science_arcade.lessons.framework.definition import LessonDefinition
from data_science_arcade.progress.model import LessonCheckpoint
from data_science_arcade.ui.mission_briefing_scene import MissionBriefingScene
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

    lesson_number/collected/definition are all optional and default to
    "no checkpointing, no briefing screen" - existing bare
    `LessonRunner(app, stages)` callers (mostly tests) are unaffected.
    When lesson_number is given, `collected` must be the *same dict
    object* the lesson's own stage closures write into (every one of the
    30 lessons' scenario.py files already builds one and writes into it
    before calling advance) - LessonRunner only ever mutates it in place
    on resume, never rebinds it, or the stage closures would keep writing
    into an orphaned copy while checkpoints silently stopped reflecting
    real progress. When `definition` is given, a MissionBriefingScene
    (real title/objectives/duration) is shown first, unless resuming from
    a mid-lesson checkpoint - you don't need to see "Start Mission" again
    to continue where you left off.

    `on_resume`, when given, is called once - after `collected` has been
    restored from the checkpoint but before the resumed stage is built -
    for any runtime state a lesson keeps *outside* `collected` itself and
    needs rebuilt from it. L01/L02 both thread a `LessonContext` through
    their stages via closures and stash its serialized form inside
    `collected["analytical_context"]`; restoring that dict alone doesn't
    repopulate the live `LessonContext` object the stage closures already
    hold a reference to. The previous approach - calling a lesson's own
    `_restore_context_if_present()` from inside its `briefing` stage
    factory - never actually ran on a real mid-lesson resume, since resume
    jumps straight to the saved `stage_index` and never re-enters stage 0:
    a real, silent bug (context always empty after resuming past the
    first stage, even though the checkpoint had genuinely saved it) that
    only a real second-App-instance resume test catches, not anything that
    exercises `collected` alone. Defaults to None (no-op) for every lesson
    that doesn't keep this kind of extra runtime state."""

    def __init__(
        self,
        app,
        stages: list[StageFactory],
        on_finished: Callable[[], None] | None = None,
        lesson_number: int | None = None,
        collected: dict | None = None,
        definition: LessonDefinition | None = None,
        on_resume: Callable[[], None] | None = None,
    ) -> None:
        self.app = app
        self.stages = stages
        self.on_finished = on_finished
        self.lesson_number = lesson_number
        self.collected = collected if collected is not None else {}
        self.definition = definition
        self.on_resume = on_resume
        self.index = 0
        self._stage_fingerprint = "|".join(stage.__name__ for stage in stages)

    def start(self) -> None:
        if self._resume_from_checkpoint():
            return
        if self.definition is not None:
            self.app.scenes.push(self._build_briefing_stage())
            return
        self.app.scenes.push(self._build_current_stage())

    def _resume_from_checkpoint(self) -> bool:
        if self.lesson_number is None:
            return False
        checkpoint = self.app.progress.checkpoint_for(self.lesson_number)
        if checkpoint is None:
            return False
        if checkpoint.stage_fingerprint != self._stage_fingerprint:
            return False  # a later change reshaped this lesson's stages - don't trust stale state
        if not (0 <= checkpoint.stage_index < len(self.stages)):
            return False
        self.index = checkpoint.stage_index
        self.collected.clear()
        self.collected.update(checkpoint.collected)  # mutate in place - never rebind self.collected
        if self.on_resume is not None:
            self.on_resume()
        self.app.scenes.push(self._build_current_stage())
        return True

    def _build_briefing_stage(self) -> Scene:
        scene = MissionBriefingScene(self.app, self.definition, on_start=self._start_first_stage)
        return Pausable(self.app, scene, on_escape=self._open_pause_menu)

    def _start_first_stage(self) -> None:
        self.app.scenes.replace(self._build_current_stage())

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
        self._save_checkpoint()
        self.app.scenes.replace(self._build_current_stage())

    def _save_checkpoint(self) -> None:
        if self.lesson_number is None:
            return
        checkpoint = LessonCheckpoint(
            stage_index=self.index,
            stage_fingerprint=self._stage_fingerprint,
            collected=dict(self.collected),
        )
        self.app.progress.save_checkpoint(self.lesson_number, checkpoint)
        self.app.save_progress()

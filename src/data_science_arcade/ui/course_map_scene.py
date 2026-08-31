import pygame

from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.core.scenes import Scene
from data_science_arcade.lessons.framework.evaluation import default_scorer
from data_science_arcade.lessons.registry import LESSON_RUNNERS
from data_science_arcade.progress.model import CHAPTER_COUNT, LESSONS_PER_CHAPTER, LessonState
from data_science_arcade.ui import colors
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.button_group import ButtonGroup
from data_science_arcade.ui.placeholder_scene import PlaceholderScene
from data_science_arcade.ui.resume_confirmation_scene import ResumeConfirmationScene
from data_science_arcade.ui.text import draw_centered_text

CENTER_X = LOGICAL_SIZE[0] // 2
CHAPTER_LABEL_X = 140
FIRST_LESSON_X = 260
FIRST_ROW_Y = 110
ROW_SPACING = 68
LESSON_COL_SPACING = 54
LESSON_SLOT_SIZE = (44, 40)
BACK_BUTTON_Y = 500
COMPLETED_MARKER_HEIGHT = 4


class CourseMapScene(Scene):
    """Six chapters x five lessons. A lesson slot is only clickable once
    unlocked; completed lessons stay clickable too, for replay."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._lesson_buttons: dict[int, Button] = {}
        buttons: list[Button] = []
        for chapter in range(1, CHAPTER_COUNT + 1):
            row_y = FIRST_ROW_Y + (chapter - 1) * ROW_SPACING
            for slot in range(LESSONS_PER_CHAPTER):
                lesson_number = (chapter - 1) * LESSONS_PER_CHAPTER + slot + 1
                rect = pygame.Rect(0, 0, *LESSON_SLOT_SIZE)
                rect.center = (FIRST_LESSON_X + slot * LESSON_COL_SPACING, row_y)
                button = Button(rect, "", self._make_open_lesson(lesson_number))
                self._lesson_buttons[lesson_number] = button
                buttons.append(button)

        back_rect = pygame.Rect(0, 0, 200, 44)
        back_rect.center = (CENTER_X, BACK_BUTTON_Y)
        self.back_button = Button(back_rect, "", self._back)
        buttons.append(self.back_button)

        self.buttons = ButtonGroup(buttons)
        self._refresh()

    def on_enter(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        loc = self.app.localization
        for lesson_number, button in self._lesson_buttons.items():
            button.label = f"{lesson_number:02d}"
            button.enabled = self.app.effective_lesson_state(lesson_number) is not LessonState.LOCKED
        self.back_button.label = loc.t("common.back")
        self.buttons.sync_focus()

    def _make_open_lesson(self, lesson_number: int):
        def open_lesson() -> None:
            self._open_lesson(lesson_number)

        return open_lesson

    def _open_lesson(self, lesson_number: int) -> None:
        if lesson_number in LESSON_RUNNERS:
            if self.app.progress.checkpoint_for(lesson_number) is not None:
                self.app.scenes.push(
                    ResumeConfirmationScene(
                        self.app,
                        on_resume=lambda: self._start_lesson(lesson_number),
                        on_start_over=lambda: self._start_lesson_fresh(lesson_number),
                    )
                )
                return
            self._start_lesson(lesson_number)
            return

        # No lesson runtime exists yet for lessons without a registry entry
        # (spec Phase 8+ adds more). In dev mode, treat a click as "play it"
        # and mark it complete so the unlock chain and completion marker can
        # actually be exercised; never happens for a normal student since
        # dev_mode defaults off.
        if self.app.dev_mode and self.app.progress.state_of(lesson_number) is not LessonState.COMPLETED:
            self.app.progress.complete(lesson_number)
            self.app.save_progress()
            self._refresh()

        loc = self.app.localization
        title = f"{loc.t('course_map.lesson_label')} {lesson_number:02d}"
        self.app.scenes.push(PlaceholderScene(self.app, title))

    def _start_lesson(self, lesson_number: int) -> None:
        def on_finished(result) -> None:
            hints_used = self.app.progress.hints_used.get(lesson_number, 0)
            scorer = runner.definition.scorer or default_scorer
            evaluation = scorer(result, runner.definition, hints_used)
            self.app.progress.record_evaluation(lesson_number, evaluation)
            self.app.progress.complete(lesson_number)
            self.app.save_progress()
            self._refresh()

        build_runner = LESSON_RUNNERS[lesson_number]
        runner, _ = build_runner(self.app, on_finished)
        runner.start()

    def _start_lesson_fresh(self, lesson_number: int) -> None:
        self.app.progress.checkpoints.pop(lesson_number, None)
        self._start_lesson(lesson_number)

    def _back(self) -> None:
        self.app.scenes.pop()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._back()
            return
        self.buttons.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BACKGROUND)
        loc = self.app.localization
        draw_centered_text(surface, loc.t("menu.course_map"), (CENTER_X, 50), 32, colors.TEXT)

        for chapter in range(1, CHAPTER_COUNT + 1):
            row_y = FIRST_ROW_Y + (chapter - 1) * ROW_SPACING
            label = f"{loc.t('course_map.chapter_label')} {chapter}"
            draw_centered_text(surface, label, (CHAPTER_LABEL_X, row_y), 18, colors.TEXT)

        self.buttons.draw(surface)

        for lesson_number, button in self._lesson_buttons.items():
            if self.app.effective_lesson_state(lesson_number) is LessonState.COMPLETED:
                marker = pygame.Rect(0, 0, button.rect.width - 12, COMPLETED_MARKER_HEIGHT)
                marker.midtop = (button.rect.centerx, button.rect.bottom - 8)
                pygame.draw.rect(surface, colors.BUTTON_FOCUS_BORDER, marker, border_radius=2)

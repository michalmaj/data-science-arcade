import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l01_question_first.scenario import BRIEF_FIELDS, DECISION_FIELDS
from data_science_arcade.lessons.l02_source_scout.scenario import DECISION_FIELDS as L02_DECISION_FIELDS
from data_science_arcade.lessons.l03_api_courier.scenario import DECISION_FIELDS as L03_DECISION_FIELDS
from data_science_arcade.lessons.l04_event_log_factory.scenario import CORRECT_EVENT_BY_STEP as L04_CORRECT_EVENT_BY_STEP
from data_science_arcade.lessons.l04_event_log_factory.scenario import DECISION_FIELDS as L04_DECISION_FIELDS
from data_science_arcade.lessons.l04_event_log_factory.scenario import FLOW_STEPS as L04_FLOW_STEPS
from data_science_arcade.lessons.l05_sampling_mission.scenario import CUSTOMER_GROUPS as L05_CUSTOMER_GROUPS
from data_science_arcade.lessons.l05_sampling_mission.scenario import DECISION_FIELDS as L05_DECISION_FIELDS
from data_science_arcade.lessons.l05_sampling_mission.scenario import STEP as L05_STEP
from data_science_arcade.lessons.l05_sampling_mission.scenario import TOTAL_BUDGET as L05_TOTAL_BUDGET
from data_science_arcade.progress.model import TOTAL_LESSONS, LessonState
from data_science_arcade.ui.api_console_scene import APIConsoleScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.course_map_scene import CourseMapScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene
from data_science_arcade.ui.placeholder_scene import PlaceholderScene
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene


def test_only_the_first_lesson_starts_enabled():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        assert course_map._lesson_buttons[1].enabled is True
        assert course_map._lesson_buttons[2].enabled is False
        assert course_map._lesson_buttons[TOTAL_LESSONS].enabled is False
    finally:
        pygame.quit()


def test_unlocking_a_lesson_in_progress_is_reflected_after_on_enter():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.progress.unlock(2)

        course_map.on_enter()

        assert course_map._lesson_buttons[2].enabled is True
    finally:
        pygame.quit()


def test_clicking_an_unlocked_lesson_with_no_runtime_yet_opens_a_placeholder():
    app = App()
    app.init()
    try:
        # Lesson 6 has no registry entry yet (only 1-5 do).
        app.progress.unlock(6)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(6)

        assert isinstance(app.scenes.current, PlaceholderScene)
        assert "06" in app.scenes.current.title
    finally:
        pygame.quit()


def test_clicking_lesson_one_starts_the_real_lesson_not_a_placeholder():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(1)

        # Every lesson stage is wrapped in Pausable (spec: Escape opens a
        # pause menu); .inner is the actual first-stage scene.
        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_two_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(2)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(2)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_three_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(3)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(3)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_four_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(4)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(4)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_five_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(5)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(5)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def _play_dialogue_to_the_end(scene: DialogueScene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


def _fill_out(scene: BriefBuilderScene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_one_marks_it_complete_and_unlocks_lesson_two():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(1)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _fill_out(app.scenes.current, BRIEF_FIELDS)  # guided work
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _fill_out(app.scenes.current, BRIEF_FIELDS)  # independent challenge
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(1) == LessonState.COMPLETED
        assert app.progress.state_of(2) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def test_finishing_lesson_two_marks_it_complete_and_unlocks_lesson_three():
    app = App()
    app.init()
    try:
        app.progress.unlock(2)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(2)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        source_scene = app.scenes.current
        source_scene.source_buttons[next(iter(source_scene.source_buttons))].on_activate()
        source_scene.confirm_button.on_activate()  # guided source board
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        source_scene = app.scenes.current
        source_scene.source_buttons[next(iter(source_scene.source_buttons))].on_activate()
        source_scene.confirm_button.on_activate()  # independent source board
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L02_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(2) == LessonState.COMPLETED
        assert app.progress.state_of(3) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _play_out_the_console(scene: APIConsoleScene) -> None:
    while not scene._all_sent():
        scene.action_button.on_activate()
    scene.action_button.on_activate()  # now showing Finish


def test_finishing_lesson_three_marks_it_complete_and_unlocks_lesson_four():
    app = App()
    app.init()
    try:
        app.progress.unlock(3)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(3)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _play_out_the_console(app.scenes.current)  # guided console
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _play_out_the_console(app.scenes.current)  # independent console
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L03_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(3) == LessonState.COMPLETED
        assert app.progress.state_of(4) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _place_every_flow_step_correctly(scene: FlowBuilderScene) -> None:
    for _ in L04_FLOW_STEPS:
        step = scene._current_step()
        correct_key = L04_CORRECT_EVENT_BY_STEP[step.key]
        index = next(i for i, option in enumerate(step.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_four_marks_it_complete_and_unlocks_lesson_five():
    app = App()
    app.init()
    try:
        app.progress.unlock(4)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(4)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _place_every_flow_step_correctly(app.scenes.current)  # guided flow
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _place_every_flow_step_correctly(app.scenes.current)  # independent flow
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L04_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(4) == LessonState.COMPLETED
        assert app.progress.state_of(5) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _spend_the_whole_l05_budget_evenly(scene: SamplingAllocatorScene) -> None:
    even_split = L05_TOTAL_BUDGET // len(L05_CUSTOMER_GROUPS)
    for group in L05_CUSTOMER_GROUPS:
        for _ in range(even_split // L05_STEP):
            scene.plus_buttons[group.key].on_activate()
    scene.confirm_button.on_activate()


def test_finishing_lesson_five_marks_it_complete_and_unlocks_lesson_six():
    app = App()
    app.init()
    try:
        app.progress.unlock(5)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(5)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _spend_the_whole_l05_budget_evenly(app.scenes.current)  # guided allocation
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _spend_the_whole_l05_budget_evenly(app.scenes.current)  # independent allocation
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L05_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(5) == LessonState.COMPLETED
        assert app.progress.state_of(6) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def test_dev_mode_shows_every_lesson_as_enabled_without_touching_the_save(monkeypatch):
    monkeypatch.setenv("DSA_DEV_MODE", "1")
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        assert course_map._lesson_buttons[TOTAL_LESSONS].enabled is True
        # the underlying save is untouched - only the *effective* state is unlocked
        assert app.progress.state_of(TOTAL_LESSONS) == LessonState.LOCKED
    finally:
        pygame.quit()


def test_dev_mode_click_marks_the_lesson_complete_and_unlocks_the_next(monkeypatch):
    monkeypatch.setenv("DSA_DEV_MODE", "1")
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        # Lesson 6 has no real runtime yet (only 1-5 are registered), so
        # this exercises the dev-mode shortcut - lessons 1-5 always launch
        # their real lesson now regardless of dev mode.
        course_map._open_lesson(6)

        assert app.progress.state_of(6) == LessonState.COMPLETED
        assert app.progress.state_of(7) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def test_completed_lesson_stays_enabled_for_replay():
    app = App()
    app.init()
    try:
        app.progress.complete(1)
        course_map = CourseMapScene(app)
        assert course_map._lesson_buttons[1].enabled is True
    finally:
        pygame.quit()


def test_escape_goes_back():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        previous = app.scenes._stack[-2]

        course_map.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        assert app.scenes.current is previous
    finally:
        pygame.quit()


def test_draw_does_not_crash_headless():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        course_map.draw(app.logical_surface)
    finally:
        pygame.quit()

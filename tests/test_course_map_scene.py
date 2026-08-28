import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.prediction import DIRECTIONS as L17_DIRECTIONS
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
from data_science_arcade.lessons.l06_schema_repair_shop.sales_export import REPAIR_ISSUES as L06_REPAIR_ISSUES
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import DECISION_FIELDS as L06_DECISION_FIELDS
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import DECISION_FIELDS as L07_DECISION_FIELDS
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import STRATEGIES as L07_STRATEGIES
from data_science_arcade.lessons.l08_duplicate_detective.candidate_pairs import CANDIDATE_PAIRS as L08_CANDIDATE_PAIRS
from data_science_arcade.lessons.l08_duplicate_detective.candidate_pairs import (
    CORRECT_DECISION_BY_PAIR as L08_CORRECT_DECISION_BY_PAIR,
)
from data_science_arcade.lessons.l08_duplicate_detective.scenario import DECISION_FIELDS as L08_DECISION_FIELDS
from data_science_arcade.lessons.l09_outlier_patrol.scenario import DECISION_FIELDS as L09_DECISION_FIELDS
from data_science_arcade.lessons.l09_outlier_patrol.transactions import CORRECT_ACTION_BY_CASE as L09_CORRECT_ACTION_BY_CASE
from data_science_arcade.lessons.l09_outlier_patrol.transactions import OUTLIER_CASES as L09_OUTLIER_CASES
from data_science_arcade.lessons.l10_validation_gate.checks import CORRECT_RULE_BY_CHECK as L10_CORRECT_RULE_BY_CHECK
from data_science_arcade.lessons.l10_validation_gate.checks import VALIDATION_CHECKS as L10_VALIDATION_CHECKS
from data_science_arcade.lessons.l10_validation_gate.scenario import DECISION_FIELDS as L10_DECISION_FIELDS
from data_science_arcade.lessons.l11_distribution_observatory.lenses import CORRECT_OPTION_BY_LENS as L11_CORRECT_OPTION_BY_LENS
from data_science_arcade.lessons.l11_distribution_observatory.scenario import DECISION_FIELDS as L11_DECISION_FIELDS
from data_science_arcade.lessons.l12_groupby_kitchen.requests import CORRECT_PIPELINE_BY_REQUEST as L12_CORRECT_PIPELINE_BY_REQUEST
from data_science_arcade.lessons.l12_groupby_kitchen.scenario import DECISION_FIELDS as L12_DECISION_FIELDS
from data_science_arcade.lessons.l13_join_junction.requests import CORRECT_HOW_BY_REQUEST as L13_CORRECT_HOW_BY_REQUEST
from data_science_arcade.lessons.l13_join_junction.scenario import DECISION_FIELDS as L13_DECISION_FIELDS
from data_science_arcade.lessons.l14_chart_designer.requests import CORRECT_OPTION_BY_REQUEST as L14_CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l14_chart_designer.scenario import DECISION_FIELDS as L14_DECISION_FIELDS
from data_science_arcade.lessons.l15_segment_detective.requests import CORRECT_OPTION_BY_REQUEST as L15_CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l15_segment_detective.scenario import DECISION_FIELDS as L15_DECISION_FIELDS
from data_science_arcade.lessons.l16_metric_forge.requests import CORRECT_OPTION_BY_REQUEST as L16_CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l16_metric_forge.scenario import DECISION_FIELDS as L16_DECISION_FIELDS
from data_science_arcade.lessons.l17_hypothesis_detective.requests import CORRECT_DIRECTION_BY_REQUEST as L17_CORRECT_DIRECTION_BY_REQUEST
from data_science_arcade.lessons.l17_hypothesis_detective.scenario import DECISION_FIELDS as L17_DECISION_FIELDS
from data_science_arcade.lessons.l18_randomization_control_room.requests import CORRECT_RULE_BY_REQUEST as L18_CORRECT_RULE_BY_REQUEST
from data_science_arcade.lessons.l18_randomization_control_room.scenario import DECISION_FIELDS as L18_DECISION_FIELDS
from data_science_arcade.lessons.l19_power_plant.experiments import SAMPLING_GROUPS as L19_SAMPLING_GROUPS
from data_science_arcade.lessons.l19_power_plant.experiments import STEP as L19_STEP
from data_science_arcade.lessons.l19_power_plant.experiments import TOTAL_WEEKS as L19_TOTAL_WEEKS
from data_science_arcade.lessons.l19_power_plant.scenario import DECISION_FIELDS as L19_DECISION_FIELDS
from data_science_arcade.lessons.l20_ab_test_commander.scenario import DECISION_FIELDS as L20_DECISION_FIELDS
from data_science_arcade.lessons.l21_funnel_factory.requests import CORRECT_DEFINITION_BY_REQUEST as L21_CORRECT_DEFINITION_BY_REQUEST
from data_science_arcade.lessons.l21_funnel_factory.scenario import DECISION_FIELDS as L21_DECISION_FIELDS
from data_science_arcade.lessons.l22_cohort_observatory.requests import CORRECT_OPTION_BY_REQUEST as L22_CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l22_cohort_observatory.scenario import DECISION_FIELDS as L22_DECISION_FIELDS
from data_science_arcade.progress.model import TOTAL_LESSONS, LessonState
from data_science_arcade.ui.api_console_scene import APIConsoleScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.checkpoint_monitor_scene import CheckpointMonitorScene
from data_science_arcade.ui.cohort_matrix_scene import CohortMatrixScene
from data_science_arcade.ui.course_map_scene import CourseMapScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.distribution_scene import DistributionScene
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene
from data_science_arcade.ui.funnel_builder_scene import FunnelBuilderScene
from data_science_arcade.ui.junction_scene import JunctionScene
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.placeholder_scene import PlaceholderScene
from data_science_arcade.ui.prediction_scene import PredictionScene
from data_science_arcade.ui.record_pair_scene import RecordPairScene
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene


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
        # Lesson 23 has no registry entry yet (only 1-22 do) - Chapter 5's
        # third lesson, once Lesson 22 ("Cohort Observatory") is complete.
        app.progress.unlock(23)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(23)

        assert isinstance(app.scenes.current, PlaceholderScene)
        assert "23" in app.scenes.current.title
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


def test_clicking_lesson_six_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(6)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(6)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_seven_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(7)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(7)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_eight_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(8)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(8)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_nine_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(9)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(9)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_ten_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(10)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(10)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_eleven_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(11)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(11)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twelve_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(12)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(12)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_thirteen_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(13)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(13)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_fourteen_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(14)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(14)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_fifteen_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(15)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(15)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_sixteen_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(16)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(16)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_seventeen_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(17)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(17)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_eighteen_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(18)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(18)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_nineteen_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(19)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(19)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(20)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(20)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_one_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(21)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(21)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_two_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(22)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(22)

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


def _first_flagged_cell_button(scene: WorkbenchScene) -> Button:
    chrome_labels = {
        scene.app.localization.t(key) for key in ("workbench.data.view_table", "workbench.data.view_schema", "workbench.continue")
    }
    tab_labels = {scene.app.localization.t(tab.value) for tab in type(scene.active_tab)}
    return next(b for b in scene.buttons.buttons if b.label not in chrome_labels and b.label not in tab_labels)


def _repair_every_l06_issue_correctly(scene: WorkbenchScene) -> None:
    for _ in L06_REPAIR_ISSUES:
        flagged_cell = _first_flagged_cell_button(scene)
        flagged_cell.on_activate()
        correct_key = scene.active_issue.options[0].key
        scene.picker_buttons[correct_key].on_activate()


def test_finishing_lesson_six_marks_it_complete_and_unlocks_lesson_seven():
    app = App()
    app.init()
    try:
        app.progress.unlock(6)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(6)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _repair_every_l06_issue_correctly(app.scenes.current)  # guided workbench
        app.scenes.current.continue_button.on_activate()
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _repair_every_l06_issue_correctly(app.scenes.current)  # independent workbench
        app.scenes.current.continue_button.on_activate()
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L06_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(6) == LessonState.COMPLETED
        assert app.progress.state_of(7) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_the_first_l07_strategy(scene) -> None:
    first_strategy_key = L07_STRATEGIES[0].key
    scene.source_buttons[first_strategy_key].on_activate()
    scene.confirm_button.on_activate()


def test_finishing_lesson_seven_marks_it_complete_and_unlocks_lesson_eight():
    app = App()
    app.init()
    try:
        app.progress.unlock(7)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(7)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_the_first_l07_strategy(app.scenes.current)  # guided comparison
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_the_first_l07_strategy(app.scenes.current)  # independent comparison
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L07_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(7) == LessonState.COMPLETED
        assert app.progress.state_of(8) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _decide_every_l08_pair_correctly(scene: RecordPairScene) -> None:
    for pair in L08_CANDIDATE_PAIRS:
        decision = L08_CORRECT_DECISION_BY_PAIR[pair.key]
        button = scene.merge_button if decision == "merge" else scene.keep_separate_button
        button.on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_eight_marks_it_complete_and_unlocks_lesson_nine():
    app = App()
    app.init()
    try:
        app.progress.unlock(8)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(8)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _decide_every_l08_pair_correctly(app.scenes.current)  # guided pairs
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _decide_every_l08_pair_correctly(app.scenes.current)  # independent pairs
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L08_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(8) == LessonState.COMPLETED
        assert app.progress.state_of(9) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _decide_every_l09_case_correctly(scene: FlowBuilderScene) -> None:
    for _ in L09_OUTLIER_CASES:
        step = scene._current_step()
        correct_key = L09_CORRECT_ACTION_BY_CASE[step.key]
        index = next(i for i, option in enumerate(step.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_nine_marks_it_complete_and_unlocks_lesson_ten():
    app = App()
    app.init()
    try:
        app.progress.unlock(9)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(9)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _decide_every_l09_case_correctly(app.scenes.current)  # guided cases
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _decide_every_l09_case_correctly(app.scenes.current)  # independent cases
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L09_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(9) == LessonState.COMPLETED
        assert app.progress.state_of(10) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _calibrate_every_l10_check_correctly(scene: FlowBuilderScene) -> None:
    for _ in L10_VALIDATION_CHECKS:
        step = scene._current_step()
        correct_key = L10_CORRECT_RULE_BY_CHECK[step.key]
        index = next(i for i, option in enumerate(step.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_ten_marks_it_complete_and_unlocks_lesson_eleven():
    app = App()
    app.init()
    try:
        app.progress.unlock(10)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(10)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _calibrate_every_l10_check_correctly(app.scenes.current)  # guided checks
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _calibrate_every_l10_check_correctly(app.scenes.current)  # independent checks
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L10_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(10) == LessonState.COMPLETED
        assert app.progress.state_of(11) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _calibrate_every_l11_lens_correctly(scene: DistributionScene) -> None:
    for _ in range(len(scene.lenses)):
        lens = scene._current_lens()
        correct_key = L11_CORRECT_OPTION_BY_LENS[lens.key]
        index = next(i for i, option in enumerate(lens.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_eleven_marks_it_complete_and_unlocks_lesson_twelve():
    app = App()
    app.init()
    try:
        app.progress.unlock(11)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(11)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _calibrate_every_l11_lens_correctly(app.scenes.current)  # guided lenses
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _calibrate_every_l11_lens_correctly(app.scenes.current)  # independent lenses
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L11_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(11) == LessonState.COMPLETED
        assert app.progress.state_of(12) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _build_every_l12_pipeline_correctly(scene: PipelineBuilderScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_group_by, correct_aggregate = L12_CORRECT_PIPELINE_BY_REQUEST[request.key]
        group_by_index = next(i for i, option in enumerate(request.group_by_options) if option.key == correct_group_by)
        aggregate_index = next(i for i, option in enumerate(request.aggregate_options) if option.key == correct_aggregate)
        scene.buttons.buttons[group_by_index].on_activate()
        aggregate_button_index = len(request.group_by_options) + aggregate_index
        scene.buttons.buttons[aggregate_button_index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twelve_marks_it_complete_and_unlocks_lesson_thirteen():
    app = App()
    app.init()
    try:
        app.progress.unlock(12)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(12)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _build_every_l12_pipeline_correctly(app.scenes.current)  # guided pipelines
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _build_every_l12_pipeline_correctly(app.scenes.current)  # independent pipelines
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L12_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(12) == LessonState.COMPLETED
        assert app.progress.state_of(13) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _choose_every_l13_join_correctly(scene: JunctionScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_how = L13_CORRECT_HOW_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.how == correct_how)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_thirteen_marks_it_complete_and_unlocks_lesson_fourteen():
    app = App()
    app.init()
    try:
        app.progress.unlock(13)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(13)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _choose_every_l13_join_correctly(app.scenes.current)  # guided junctions
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _choose_every_l13_join_correctly(app.scenes.current)  # independent junctions
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L13_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(13) == LessonState.COMPLETED
        assert app.progress.state_of(14) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l14_chart_correctly(scene: ChartDesignerScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L14_CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_fourteen_marks_it_complete_and_unlocks_lesson_fifteen():
    app = App()
    app.init()
    try:
        app.progress.unlock(14)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(14)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l14_chart_correctly(app.scenes.current)  # guided charts
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l14_chart_correctly(app.scenes.current)  # independent charts
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L14_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(14) == LessonState.COMPLETED
        assert app.progress.state_of(15) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l15_slice_correctly(scene: SegmentSlicerScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L15_CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_fifteen_marks_it_complete_and_unlocks_lesson_sixteen():
    app = App()
    app.init()
    try:
        app.progress.unlock(15)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(15)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l15_slice_correctly(app.scenes.current)  # guided slices
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l15_slice_correctly(app.scenes.current)  # independent slices
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L15_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(15) == LessonState.COMPLETED
        assert app.progress.state_of(16) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l16_metric_correctly(scene: SegmentSlicerScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L16_CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_sixteen_marks_it_complete_and_unlocks_lesson_seventeen():
    app = App()
    app.init()
    try:
        app.progress.unlock(16)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(16)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l16_metric_correctly(app.scenes.current)  # guided metrics
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l16_metric_correctly(app.scenes.current)  # independent metrics
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L16_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(16) == LessonState.COMPLETED
        assert app.progress.state_of(17) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _predict_every_l17_request_correctly(scene: PredictionScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_direction = L17_CORRECT_DIRECTION_BY_REQUEST[request.key]
        index = L17_DIRECTIONS.index(correct_direction)
        scene.buttons.buttons[index].on_activate()
        scene.action_button.on_activate()  # reveal
        scene.action_button.on_activate()  # next/finish


def test_finishing_lesson_seventeen_marks_it_complete_and_unlocks_lesson_eighteen():
    app = App()
    app.init()
    try:
        app.progress.unlock(17)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(17)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _predict_every_l17_request_correctly(app.scenes.current)  # guided predictions
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _predict_every_l17_request_correctly(app.scenes.current)  # independent predictions
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L17_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(17) == LessonState.COMPLETED
        assert app.progress.state_of(18) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l18_rule_correctly(scene: SegmentSlicerScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L18_CORRECT_RULE_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_eighteen_marks_it_complete_and_unlocks_lesson_nineteen():
    app = App()
    app.init()
    try:
        app.progress.unlock(18)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(18)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l18_rule_correctly(app.scenes.current)  # guided rules
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l18_rule_correctly(app.scenes.current)  # independent rules
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L18_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(18) == LessonState.COMPLETED
        assert app.progress.state_of(19) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _spend_the_whole_l19_budget_evenly(scene: SamplingAllocatorScene) -> None:
    even_split = L19_TOTAL_WEEKS // len(L19_SAMPLING_GROUPS)
    for group in L19_SAMPLING_GROUPS:
        for _ in range(even_split // L19_STEP):
            scene.plus_buttons[group.key].on_activate()
    scene.confirm_button.on_activate()


def test_finishing_lesson_nineteen_marks_it_complete_and_unlocks_lesson_twenty():
    app = App()
    app.init()
    try:
        app.progress.unlock(19)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(19)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _spend_the_whole_l19_budget_evenly(app.scenes.current)  # guided allocation
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _spend_the_whole_l19_budget_evenly(app.scenes.current)  # independent allocation
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L19_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(19) == LessonState.COMPLETED
        assert app.progress.state_of(20) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _keep_running_l20_to_the_end(scene: CheckpointMonitorScene) -> None:
    while not scene._is_last_checkpoint():
        scene.continue_button.on_activate()
    scene.stop_button.on_activate()  # relabeled "Finish" on the last checkpoint


def test_finishing_lesson_twenty_marks_it_complete_and_unlocks_lesson_twenty_one():
    app = App()
    app.init()
    try:
        app.progress.unlock(20)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(20)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _keep_running_l20_to_the_end(app.scenes.current)  # guided monitoring
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _keep_running_l20_to_the_end(app.scenes.current)  # independent monitoring
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L20_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(20) == LessonState.COMPLETED
        assert app.progress.state_of(21) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l21_definition_correctly(scene: FunnelBuilderScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L21_CORRECT_DEFINITION_BY_REQUEST[request.key]
        index = next(i for i, definition in enumerate(request.definitions) if definition.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twenty_one_marks_it_complete_and_unlocks_lesson_twenty_two():
    app = App()
    app.init()
    try:
        app.progress.unlock(21)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(21)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l21_definition_correctly(app.scenes.current)  # guided definitions
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l21_definition_correctly(app.scenes.current)  # independent definitions
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L21_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(21) == LessonState.COMPLETED
        assert app.progress.state_of(22) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l22_option_correctly(scene: CohortMatrixScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L22_CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twenty_two_marks_it_complete_and_unlocks_lesson_twenty_three():
    app = App()
    app.init()
    try:
        app.progress.unlock(22)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(22)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l22_option_correctly(app.scenes.current)  # guided comparisons
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l22_option_correctly(app.scenes.current)  # independent comparisons
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L22_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(22) == LessonState.COMPLETED
        assert app.progress.state_of(23) == LessonState.UNLOCKED
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

        # Lesson 23 has no real runtime yet (only 1-22 are registered) -
        # it's Chapter 5's third lesson - so this exercises the dev-mode
        # shortcut - lessons 1-22 always launch their real lesson now
        # regardless of dev mode.
        course_map._open_lesson(23)

        assert app.progress.state_of(23) == LessonState.COMPLETED
        assert app.progress.state_of(24) == LessonState.UNLOCKED
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

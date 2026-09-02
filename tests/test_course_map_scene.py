import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.prediction import DIRECTIONS as L17_DIRECTIONS
from data_science_arcade.lessons.l01_question_first.definition import LESSON_01
from data_science_arcade.lessons.l01_question_first.scenario import build_lesson_one_runner
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.mastery_challenge_scene import MasteryChallengeScene
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene
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
from data_science_arcade.lessons.l23_time_series_control_room.requests import CORRECT_OPTION_BY_REQUEST as L23_CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l23_time_series_control_room.scenario import DECISION_FIELDS as L23_DECISION_FIELDS
from data_science_arcade.lessons.l24_survey_bureau.requests import CORRECT_COMBO_BY_REQUEST as L24_CORRECT_COMBO_BY_REQUEST
from data_science_arcade.lessons.l24_survey_bureau.scenario import DECISION_FIELDS as L24_DECISION_FIELDS
from data_science_arcade.lessons.l25_kpi_emergency_room.requests import CORRECT_COMBO_BY_REQUEST as L25_CORRECT_COMBO_BY_REQUEST
from data_science_arcade.lessons.l25_kpi_emergency_room.scenario import DECISION_FIELDS as L25_DECISION_FIELDS
from data_science_arcade.lessons.l26_correlation_crime_scene.requests import CORRECT_OPTION_BY_REQUEST as L26_CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l26_correlation_crime_scene.scenario import DECISION_FIELDS as L26_DECISION_FIELDS
from data_science_arcade.lessons.l27_causality_courtroom.requests import CORRECT_OPTION_BY_REQUEST as L27_CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l27_causality_courtroom.scenario import DECISION_FIELDS as L27_DECISION_FIELDS
from data_science_arcade.lessons.l28_chart_crime_lab.requests import CORRECT_OPTION_BY_REQUEST as L28_CORRECT_OPTION_BY_REQUEST
from data_science_arcade.lessons.l28_chart_crime_lab.scenario import DECISION_FIELDS as L28_DECISION_FIELDS
from data_science_arcade.lessons.l29_the_executive_brief.findings import CORRECT_FINDING_KEYS as L29_CORRECT_FINDING_KEYS
from data_science_arcade.lessons.l29_the_executive_brief.scenario import DECISION_FIELDS as L29_DECISION_FIELDS
from data_science_arcade.lessons.l30_the_data_incident.scenario import DECISION_FIELDS as L30_DECISION_FIELDS
from data_science_arcade.progress.model import TOTAL_LESSONS, LessonCheckpoint, LessonState
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.ui.api_console_scene import APIConsoleScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.button import Button
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.checkpoint_monitor_scene import CheckpointMonitorScene
from data_science_arcade.ui.cohort_matrix_scene import CohortMatrixScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.course_map_scene import CourseMapScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.distribution_scene import DistributionScene
from data_science_arcade.ui.finding_picker_scene import FindingPickerScene
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene
from data_science_arcade.ui.funnel_builder_scene import FunnelBuilderScene
from data_science_arcade.ui.investigation_hub_scene import InvestigationHubScene
from data_science_arcade.ui.junction_scene import JunctionScene
from data_science_arcade.ui.mission_briefing_scene import MissionBriefingScene
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.placeholder_scene import PlaceholderScene
from data_science_arcade.ui.prediction_scene import PredictionScene
from data_science_arcade.ui.record_pair_scene import RecordPairScene
from data_science_arcade.ui.resume_confirmation_scene import ResumeConfirmationScene
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.survey_builder_scene import SurveyBuilderScene
from data_science_arcade.ui.timeseries_scene import TimeSeriesScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

from lesson_test_helpers import click_through_mission_briefing


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


# _open_lesson's "no registry entry yet" branch (and PlaceholderScene's use
# from it specifically - the class itself is still used elsewhere, e.g. the
# main menu) has no lesson number left to exercise it now that 1-30 all
# have real runtimes - see decisions/IMPLEMENTATION_STATE.md's technical
# debt note. There used to be a test here exercising that branch for
# whichever lesson hadn't shipped yet; it moved forward once per lesson
# from Lesson 3 onward and is retired for good now that Lesson 30 shipped.


def test_clicking_lesson_one_starts_the_real_lesson_not_a_placeholder():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(1)
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_three_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(23)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(23)
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_four_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(24)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(24)
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_five_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(25)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(25)
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_six_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(26)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(26)
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_seven_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(27)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(27)
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_eight_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(28)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(28)
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_twenty_nine_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(29)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(29)
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def test_clicking_lesson_thirty_starts_the_real_lesson_once_unlocked():
    app = App()
    app.init()
    try:
        app.progress.unlock(30)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(30)
        click_through_mission_briefing(app)

        assert isinstance(app.scenes.current.inner, DialogueScene)
        assert not isinstance(app.scenes.current.inner, PlaceholderScene)
    finally:
        pygame.quit()


def _play_dialogue_to_the_end(scene: DialogueScene) -> None:
    while scene.app.scenes.current is scene:
        scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))


L01_STAGE_FINGERPRINT = "|".join(
    (
        "briefing",
        "investigation",
        "meet_the_data",
        "grain_in_action",
        "guided_brief",
        "predict_window",
        "compute_window",
        "household_reveal",
        "revise_entity",
        "compute_entity",
        "coverage_reveal",
        "coverage_interpret",
        "the_twist",
        "evidence_review",
        "final_decision",
        "mastery_challenge",
        "feedback",
        "debrief",
    )
)
"""Must match the exact stage-factory function names/order in
lessons/l01_question_first/scenario.py::build_lesson_one_runner - a stale
copy here is exactly the kind of drift LessonRunner's own fingerprint
check exists to catch, so keep this list in sync by hand when that
function's stage list changes."""


def _fill_out(scene: BriefBuilderScene, fields) -> None:
    for _ in fields:
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()


def _click(surface_pos=(1, 1)) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=surface_pos, button=1)


def _play_lesson_one_to_completion(app) -> None:
    """The real 18-stage flow (decisions/IMPLEMENTATION_STATE.md has the
    full act-by-act rationale) - a from-scratch replacement for the old
    8-stage click sequence every prior version of this test used. Skips
    the optional mastery act via its own Skip button rather than playing
    it out, since it isn't required for a real playthrough to finish."""
    _play_dialogue_to_the_end(app.scenes.current)  # briefing
    _play_dialogue_to_the_end(app.scenes.current)  # investigation

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # meet_the_data
    workbench = app.scenes.current.inner
    first_inspection_option = next(iter(workbench.inspection_buttons.values()))
    first_inspection_option.on_activate()
    workbench.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, PipelineBuilderScene)  # grain_in_action
    pipeline = app.scenes.current.inner
    for _ in range(2):  # 2 GRAIN_REQUESTS, each with 2 group-by options + 1 aggregate option
        pipeline.buttons.buttons[0].on_activate()  # first group-by option
        pipeline.buttons.buttons[2].on_activate()  # the one aggregate option
        pipeline.next_button.on_activate()

    _fill_out(app.scenes.current.inner, range(6))  # guided_brief, 6 fields
    _fill_out(app.scenes.current.inner, range(2))  # predict_window, 2 fields

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # compute_window
    app.scenes.current.inner.buttons.buttons[0].on_activate()
    app.scenes.current.inner.continue_button.on_activate()

    _play_dialogue_to_the_end(app.scenes.current)  # household_reveal
    _fill_out(app.scenes.current.inner, range(1))  # revise_entity, 1 field

    assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # compute_entity
    app.scenes.current.inner.buttons.buttons[0].on_activate()
    app.scenes.current.inner.continue_button.on_activate()

    _play_dialogue_to_the_end(app.scenes.current)  # coverage_reveal
    _fill_out(app.scenes.current.inner, range(1))  # coverage_interpret, 1 field

    app.scenes.current.handle_event(_click())  # the_twist

    assert isinstance(app.scenes.current.inner, WorkbenchScene)  # evidence_review
    app.scenes.current.inner.continue_button.on_activate()

    assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision
    decision = app.scenes.current.inner
    decision.buttons.buttons[0].on_activate()  # claim
    decision.next_button.on_activate()
    evidence_ids = list(decision._evidence_toggle_buttons.keys())
    decision._evidence_toggle_buttons[evidence_ids[0]].on_activate()
    decision._evidence_toggle_buttons[evidence_ids[1]].on_activate()
    decision.next_button.on_activate()
    for _ in range(4):  # limitation, confidence, recommendation, follow_up
        decision.buttons.buttons[0].on_activate()
        decision.next_button.on_activate()

    assert isinstance(app.scenes.current.inner, MasteryChallengeScene)  # mastery_challenge - skipped
    app.scenes.current.inner.buttons.buttons[1].on_activate()

    assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
    app.scenes.current.inner.buttons.buttons[0].on_activate()

    _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes


def test_finishing_lesson_one_marks_it_complete_and_unlocks_lesson_two():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(1)
        click_through_mission_briefing(app)

        _play_lesson_one_to_completion(app)

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
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing

        source_scene = app.scenes.current
        source_scene.source_buttons[next(iter(source_scene.source_buttons))].on_activate()
        source_scene.confirm_button.on_activate()  # source_map

        assert isinstance(app.scenes.current.inner, WorkbenchScene)  # meet_billing
        workbench = app.scenes.current.inner
        next(iter(workbench.inspection_buttons.values())).on_activate()
        workbench.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, PipelineBuilderScene)  # compute_billing
        pipeline = app.scenes.current.inner
        pipeline.buttons.buttons[0].on_activate()  # first group-by option
        pipeline.buttons.buttons[2].on_activate()  # the one aggregate option
        pipeline.next_button.on_activate()

        assert isinstance(app.scenes.current.inner, WorkbenchScene)  # meet_app_log
        workbench = app.scenes.current.inner
        next(iter(workbench.inspection_buttons.values())).on_activate()
        workbench.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # comparison_1
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        app.scenes.current.inner.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, WorkbenchScene)  # meet_marketing
        workbench = app.scenes.current.inner
        next(iter(workbench.inspection_buttons.values())).on_activate()
        workbench.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # comparison_2
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        app.scenes.current.inner.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # gap_discovery
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        app.scenes.current.inner.continue_button.on_activate()

        _play_dialogue_to_the_end(app.scenes.current)  # finance_lead_confirms
        _fill_out(app.scenes.current, range(1))  # gut_check, 1 field

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # support_list
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        app.scenes.current.inner.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, WorkbenchScene)  # evidence_review
        app.scenes.current.inner.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision
        decision = app.scenes.current.inner
        decision.buttons.buttons[0].on_activate()  # answer_strategy
        decision.next_button.on_activate()
        evidence_ids = list(decision._evidence_toggle_buttons.keys())
        decision._evidence_toggle_buttons[evidence_ids[0]].on_activate()
        decision._evidence_toggle_buttons[evidence_ids[1]].on_activate()
        decision.next_button.on_activate()
        for _ in range(4):  # known_gap, safe_to_claim, not_safe_to_claim, recommendation
            decision.buttons.buttons[0].on_activate()
            decision.next_button.on_activate()

        assert isinstance(app.scenes.current.inner, MasteryChallengeScene)  # mastery_challenge - skipped
        app.scenes.current.inner.buttons.buttons[1].on_activate()

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
        app.scenes.current.inner.buttons.buttons[0].on_activate()

        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(2) == LessonState.COMPLETED
        assert app.progress.state_of(3) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _play_out_the_console(scene: APIConsoleScene, retry_choices: list | None = None) -> None:
    remaining = ["wait_and_retry"] if retry_choices is None else list(retry_choices)
    while not scene._base_exhausted():
        if scene._pending is not None:
            key = remaining.pop(0)
            option = next(o for o in scene._pending.retry_options if o.key == key)
            scene._make_choose_retry(option)()
        else:
            scene._send_request()
    scene.buttons.buttons[0].on_activate()  # now showing Finish


def test_finishing_lesson_three_marks_it_complete_and_unlocks_lesson_four():
    app = App()
    app.init()
    try:
        app.progress.unlock(3)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(3)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # framing
        _play_out_the_console(app.scenes.current.inner)  # acquisition

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # gut_check
        _fill_out(app.scenes.current, range(1))

        assert isinstance(app.scenes.current.inner, ComparisonRevealScene)  # completeness_reveal
        app.scenes.current.inner.buttons.buttons[0].on_activate()
        app.scenes.current.inner.continue_button.on_activate()

        _play_dialogue_to_the_end(app.scenes.current)  # root_cause_confirmed

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # revised_gut_check
        _fill_out(app.scenes.current, range(1))

        assert isinstance(app.scenes.current.inner, WorkbenchScene)  # evidence_review
        app.scenes.current.inner.continue_button.on_activate()

        assert isinstance(app.scenes.current.inner, DecisionBuilderScene)  # final_decision
        decision = app.scenes.current.inner
        decision.buttons.buttons[0].on_activate()  # acquisition_strategy
        decision.next_button.on_activate()
        evidence_ids = list(decision._evidence_toggle_buttons.keys())
        decision._evidence_toggle_buttons[evidence_ids[0]].on_activate()
        decision._evidence_toggle_buttons[evidence_ids[1]].on_activate()
        decision.next_button.on_activate()
        for _ in range(4):  # known_gap, safe_to_claim, not_safe_to_claim, recommendation
            decision.buttons.buttons[0].on_activate()
            decision.next_button.on_activate()

        assert isinstance(app.scenes.current.inner, MasteryChallengeScene)  # mastery_challenge - skipped
        app.scenes.current.inner.buttons.buttons[1].on_activate()

        assert isinstance(app.scenes.current.inner, LessonFeedbackScene)  # feedback
        app.scenes.current.inner.buttons.buttons[0].on_activate()

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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
        click_through_mission_briefing(app)

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


def _pick_every_l23_option_correctly(scene: TimeSeriesScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L23_CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twenty_three_marks_it_complete_and_unlocks_lesson_twenty_four():
    app = App()
    app.init()
    try:
        app.progress.unlock(23)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(23)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l23_option_correctly(app.scenes.current)  # guided lens picks
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l23_option_correctly(app.scenes.current)  # independent lens picks
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L23_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(23) == LessonState.COMPLETED
        assert app.progress.state_of(24) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l24_combo_correctly(scene: SurveyBuilderScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_wording, correct_channel = L24_CORRECT_COMBO_BY_REQUEST[request.key]
        wording_index = next(i for i, option in enumerate(request.wording_options) if option.key == correct_wording)
        channel_index = next(i for i, option in enumerate(request.channel_options) if option.key == correct_channel)
        scene.buttons.buttons[wording_index].on_activate()
        scene.buttons.buttons[len(request.wording_options) + channel_index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twenty_four_marks_it_complete_and_unlocks_lesson_twenty_five():
    app = App()
    app.init()
    try:
        app.progress.unlock(24)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(24)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l24_combo_correctly(app.scenes.current)  # guided survey designs
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l24_combo_correctly(app.scenes.current)  # independent survey designs
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L24_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(24) == LessonState.COMPLETED
        assert app.progress.state_of(25) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l25_combo_correctly(scene: AlertConfigScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_metric, correct_threshold = L25_CORRECT_COMBO_BY_REQUEST[request.key]
        metric_index = next(i for i, option in enumerate(request.metric_options) if option.key == correct_metric)
        threshold_index = next(i for i, option in enumerate(request.threshold_options) if option.key == correct_threshold)
        scene.buttons.buttons[metric_index].on_activate()
        scene.buttons.buttons[len(request.metric_options) + threshold_index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twenty_five_marks_it_complete_and_unlocks_lesson_twenty_six():
    app = App()
    app.init()
    try:
        app.progress.unlock(25)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(25)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l25_combo_correctly(app.scenes.current)  # guided monitor designs
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l25_combo_correctly(app.scenes.current)  # independent monitor designs
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L25_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(25) == LessonState.COMPLETED
        assert app.progress.state_of(26) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l26_option_correctly(scene: CorrelationScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L26_CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twenty_six_marks_it_complete_and_unlocks_lesson_twenty_seven():
    app = App()
    app.init()
    try:
        app.progress.unlock(26)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(26)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l26_option_correctly(app.scenes.current)  # guided verdicts
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l26_option_correctly(app.scenes.current)  # independent verdicts
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L26_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(26) == LessonState.COMPLETED
        assert app.progress.state_of(27) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l27_option_correctly(scene: CorrelationScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L27_CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twenty_seven_marks_it_complete_and_unlocks_lesson_twenty_eight():
    app = App()
    app.init()
    try:
        app.progress.unlock(27)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(27)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l27_option_correctly(app.scenes.current)  # guided verdicts
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l27_option_correctly(app.scenes.current)  # independent verdicts
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L27_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(27) == LessonState.COMPLETED
        assert app.progress.state_of(28) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l28_chart_correctly(scene: ChartDesignerScene) -> None:
    for _ in range(len(scene.requests)):
        request = scene._current_request()
        correct_key = L28_CORRECT_OPTION_BY_REQUEST[request.key]
        index = next(i for i, option in enumerate(request.options) if option.key == correct_key)
        scene.buttons.buttons[index].on_activate()
        scene.next_button.on_activate()


def test_finishing_lesson_twenty_eight_marks_it_complete_and_unlocks_lesson_twenty_nine():
    app = App()
    app.init()
    try:
        app.progress.unlock(28)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(28)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l28_chart_correctly(app.scenes.current)  # guided charts
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l28_chart_correctly(app.scenes.current)  # independent charts
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L28_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(28) == LessonState.COMPLETED
        assert app.progress.state_of(29) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _pick_every_l29_finding_correctly(scene: FindingPickerScene) -> None:
    # Unlike every other lesson's fixed-index-per-request helper, the pool
    # here shrinks after every pick - the correct finding's position has to
    # be looked up fresh each round rather than read off a stable mapping.
    for _ in range(scene.target_count):
        remaining = scene._remaining_findings()
        index = next(i for i, finding in enumerate(remaining) if finding.key in L29_CORRECT_FINDING_KEYS)
        scene.buttons.buttons[index].on_activate()


def test_finishing_lesson_twenty_nine_marks_it_complete_and_unlocks_lesson_thirty():
    app = App()
    app.init()
    try:
        app.progress.unlock(29)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(29)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation
        _pick_every_l29_finding_correctly(app.scenes.current)  # guided findings
        _play_dialogue_to_the_end(app.scenes.current)  # independent intro
        _pick_every_l29_finding_correctly(app.scenes.current)  # independent findings
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L29_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(29) == LessonState.COMPLETED
        assert app.progress.state_of(30) == LessonState.UNLOCKED
    finally:
        pygame.quit()


def _complete_l30_correlation_or_chart_lead(scene) -> None:
    scene.buttons.buttons[0].on_activate()
    scene.next_button.on_activate()


def _complete_l30_alert_lead(scene: AlertConfigScene) -> None:
    scene.buttons.buttons[0].on_activate()  # metric
    scene.buttons.buttons[len(scene._current_request().metric_options)].on_activate()  # threshold
    scene.next_button.on_activate()


def _investigate_every_l30_lead(app, hub: InvestigationHubScene) -> None:
    # Each of the 5 leads is a different reused scene type - unlike every
    # prior lesson's single-scene-type helper, this one has to know which
    # completion shape applies to whichever lead it just opened.
    for index in range(len(hub.leads)):
        hub.buttons.buttons[index].on_activate()
        lead_scene = app.scenes.current.inner
        if isinstance(lead_scene, AlertConfigScene):
            _complete_l30_alert_lead(lead_scene)
        else:
            _complete_l30_correlation_or_chart_lead(lead_scene)


def test_finishing_lesson_thirty_marks_it_complete():
    app = App()
    app.init()
    try:
        app.progress.unlock(30)
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(30)
        click_through_mission_briefing(app)

        _play_dialogue_to_the_end(app.scenes.current)  # briefing
        _play_dialogue_to_the_end(app.scenes.current)  # investigation intro
        hub = app.scenes.current.inner
        assert isinstance(hub, InvestigationHubScene)
        _investigate_every_l30_lead(app, hub)
        assert hub.conclude_button.enabled
        hub.conclude_button.on_activate()
        app.scenes.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(1, 1), button=1))  # twist
        _fill_out(app.scenes.current, L30_DECISION_FIELDS)  # decision
        _play_dialogue_to_the_end(app.scenes.current)  # debrief -> finishes

        assert app.scenes.current is course_map
        assert app.progress.state_of(30) == LessonState.COMPLETED
        # Lesson 30 is the course's last lesson - Progress.complete() only
        # unlocks lesson_number + 1 while lesson_number < TOTAL_LESSONS, so
        # there is no lesson 31 to check for, unlike every prior lesson's
        # finishing test.
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


# The dev-mode "click an unregistered lesson to auto-complete it via the
# placeholder shortcut" behavior (_open_lesson's fallback branch) has no
# lesson number left to exercise it now that lessons 1-30 are all
# registered - see decisions/IMPLEMENTATION_STATE.md's technical debt
# note. There used to be a test here for it, moved forward once per
# lesson from Lesson 3 onward; it's retired for good now that Lesson 30
# shipped, same as the placeholder-opens test above.


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


def test_finishing_a_lesson_records_a_real_evaluation_alongside_completion():
    app = App()
    app.init()
    try:
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(1)
        click_through_mission_briefing(app)

        _play_lesson_one_to_completion(app)

        evaluation = app.progress.evaluations[1]
        assert evaluation.completed_thoughtfully is True
        assert evaluation.hints_used == 0
        assert set(evaluation.dimension_scores) == set(LESSON_01.scoring_dimensions)
        assert all(score > 0 for score in evaluation.dimension_scores.values())
    finally:
        pygame.quit()


def test_opening_a_lesson_with_a_saved_checkpoint_shows_a_resume_prompt():
    app = App()
    app.init()
    try:
        _, l01_collected = build_lesson_one_runner(app, on_finished=lambda result: None)
        fingerprint = L01_STAGE_FINGERPRINT
        app.progress.save_checkpoint(1, LessonCheckpoint(stage_index=2, stage_fingerprint=fingerprint, collected=dict(l01_collected)))
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)

        course_map._open_lesson(1)

        assert isinstance(app.scenes.current, ResumeConfirmationScene)
    finally:
        pygame.quit()


def test_choosing_resume_continues_the_lesson_from_the_checkpoint():
    app = App()
    app.init()
    try:
        fingerprint = L01_STAGE_FINGERPRINT
        app.progress.save_checkpoint(1, LessonCheckpoint(stage_index=4, stage_fingerprint=fingerprint, collected={}))
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(1)

        app.scenes.current.buttons.buttons[0].on_activate()  # Resume

        assert isinstance(app.scenes.current.inner, BriefBuilderScene)  # guided_brief is stage index 4
        assert app.progress.checkpoint_for(1) is not None  # untouched by resuming
    finally:
        pygame.quit()


def test_choosing_start_over_clears_the_checkpoint_and_restarts_from_the_briefing():
    app = App()
    app.init()
    try:
        fingerprint = L01_STAGE_FINGERPRINT
        app.progress.save_checkpoint(1, LessonCheckpoint(stage_index=4, stage_fingerprint=fingerprint, collected={}))
        course_map = CourseMapScene(app)
        app.scenes.push(course_map)
        course_map._open_lesson(1)

        app.scenes.current.buttons.buttons[1].on_activate()  # Start Over

        assert isinstance(app.scenes.current.inner, MissionBriefingScene)
        assert app.progress.checkpoint_for(1) is None
    finally:
        pygame.quit()

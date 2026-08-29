from collections.abc import Callable

from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l01_question_first.scenario import build_lesson_one_runner
from data_science_arcade.lessons.l02_source_scout.scenario import build_lesson_two_runner
from data_science_arcade.lessons.l03_api_courier.scenario import build_lesson_three_runner
from data_science_arcade.lessons.l04_event_log_factory.scenario import build_lesson_four_runner
from data_science_arcade.lessons.l05_sampling_mission.scenario import build_lesson_five_runner
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import build_lesson_six_runner
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import build_lesson_seven_runner
from data_science_arcade.lessons.l08_duplicate_detective.scenario import build_lesson_eight_runner
from data_science_arcade.lessons.l09_outlier_patrol.scenario import build_lesson_nine_runner
from data_science_arcade.lessons.l10_validation_gate.scenario import build_lesson_ten_runner
from data_science_arcade.lessons.l11_distribution_observatory.scenario import build_lesson_eleven_runner
from data_science_arcade.lessons.l12_groupby_kitchen.scenario import build_lesson_twelve_runner
from data_science_arcade.lessons.l13_join_junction.scenario import build_lesson_thirteen_runner
from data_science_arcade.lessons.l14_chart_designer.scenario import build_lesson_fourteen_runner
from data_science_arcade.lessons.l15_segment_detective.scenario import build_lesson_fifteen_runner
from data_science_arcade.lessons.l16_metric_forge.scenario import build_lesson_sixteen_runner
from data_science_arcade.lessons.l17_hypothesis_detective.scenario import build_lesson_seventeen_runner
from data_science_arcade.lessons.l18_randomization_control_room.scenario import build_lesson_eighteen_runner
from data_science_arcade.lessons.l19_power_plant.scenario import build_lesson_nineteen_runner
from data_science_arcade.lessons.l20_ab_test_commander.scenario import build_lesson_twenty_runner
from data_science_arcade.lessons.l21_funnel_factory.scenario import build_lesson_twenty_one_runner
from data_science_arcade.lessons.l22_cohort_observatory.scenario import build_lesson_twenty_two_runner
from data_science_arcade.lessons.l23_time_series_control_room.scenario import build_lesson_twenty_three_runner

RunnerBuilder = Callable[..., tuple[LessonRunner, dict]]

LESSON_RUNNERS: dict[int, RunnerBuilder] = {
    1: build_lesson_one_runner,
    2: build_lesson_two_runner,
    3: build_lesson_three_runner,
    4: build_lesson_four_runner,
    5: build_lesson_five_runner,
    6: build_lesson_six_runner,
    7: build_lesson_seven_runner,
    8: build_lesson_eight_runner,
    9: build_lesson_nine_runner,
    10: build_lesson_ten_runner,
    11: build_lesson_eleven_runner,
    12: build_lesson_twelve_runner,
    13: build_lesson_thirteen_runner,
    14: build_lesson_fourteen_runner,
    15: build_lesson_fifteen_runner,
    16: build_lesson_sixteen_runner,
    17: build_lesson_seventeen_runner,
    18: build_lesson_eighteen_runner,
    19: build_lesson_nineteen_runner,
    20: build_lesson_twenty_runner,
    21: build_lesson_twenty_one_runner,
    22: build_lesson_twenty_two_runner,
    23: build_lesson_twenty_three_runner,
}
"""Lesson number -> its build_lesson_*_runner(app, on_finished) factory.
The single place CourseMapScene (or anything else that wants to launch a
lesson) needs to know about, instead of importing and special-casing each
lesson's scenario module individually. Lessons not listed here have no
runtime yet - spec Phase 8+ adds them."""

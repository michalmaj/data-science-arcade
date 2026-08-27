import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.core import fonts
from data_science_arcade.core.fonts import get_font
from data_science_arcade.lessons.l01_question_first.scenario import BRIEF_FIELDS as L01_BRIEF_FIELDS
from data_science_arcade.lessons.l01_question_first.scenario import DECISION_FIELDS as L01_DECISION_FIELDS
from data_science_arcade.lessons.l02_source_scout.scenario import DECISION_FIELDS as L02_DECISION_FIELDS
from data_science_arcade.lessons.l02_source_scout.scenario import SOURCES as L02_SOURCES
from data_science_arcade.lessons.l03_api_courier.scenario import DECISION_FIELDS as L03_DECISION_FIELDS
from data_science_arcade.lessons.l04_event_log_factory.scenario import DECISION_FIELDS as L04_DECISION_FIELDS
from data_science_arcade.lessons.l04_event_log_factory.scenario import FLOW_STEPS as L04_FLOW_STEPS
from data_science_arcade.lessons.l05_sampling_mission.scenario import DECISION_FIELDS as L05_DECISION_FIELDS
from data_science_arcade.lessons.l06_schema_repair_shop.sales_export import REPAIR_ISSUES as L06_REPAIR_ISSUES
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import DECISION_FIELDS as L06_DECISION_FIELDS
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import DECISION_FIELDS as L07_DECISION_FIELDS
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import STRATEGIES as L07_STRATEGIES
from data_science_arcade.lessons.l08_duplicate_detective.scenario import DECISION_FIELDS as L08_DECISION_FIELDS
from data_science_arcade.lessons.l09_outlier_patrol.scenario import DECISION_FIELDS as L09_DECISION_FIELDS
from data_science_arcade.lessons.l09_outlier_patrol.transactions import OUTLIER_CASES as L09_OUTLIER_CASES
from data_science_arcade.lessons.l10_validation_gate.checks import VALIDATION_CHECKS as L10_VALIDATION_CHECKS
from data_science_arcade.lessons.l10_validation_gate.scenario import DECISION_FIELDS as L10_DECISION_FIELDS
from data_science_arcade.lessons.l11_distribution_observatory.lenses import build_distribution_lenses
from data_science_arcade.lessons.l11_distribution_observatory.order_values import generate_order_values
from data_science_arcade.lessons.l11_distribution_observatory.scenario import DECISION_FIELDS as L11_DECISION_FIELDS
from data_science_arcade.lessons.l12_groupby_kitchen.requests import AGGREGATION_REQUESTS as L12_AGGREGATION_REQUESTS
from data_science_arcade.lessons.l12_groupby_kitchen.scenario import DECISION_FIELDS as L12_DECISION_FIELDS
from data_science_arcade.lessons.l13_join_junction.requests import JOIN_REQUESTS as L13_JOIN_REQUESTS
from data_science_arcade.lessons.l13_join_junction.scenario import DECISION_FIELDS as L13_DECISION_FIELDS
from data_science_arcade.lessons.l14_chart_designer.requests import CHART_REQUESTS as L14_CHART_REQUESTS
from data_science_arcade.lessons.l14_chart_designer.scenario import DECISION_FIELDS as L14_DECISION_FIELDS
from data_science_arcade.lessons.l15_segment_detective.requests import SEGMENT_REQUESTS as L15_SEGMENT_REQUESTS
from data_science_arcade.lessons.l15_segment_detective.scenario import DECISION_FIELDS as L15_DECISION_FIELDS
from data_science_arcade.localization.service import SUPPORTED_LOCALES, Localization
from data_science_arcade.ui.brief_builder_scene import OPTION_SIZE
from data_science_arcade.ui.button import BUTTON_TEXT_SIZE
from data_science_arcade.ui.chart_designer_scene import OPTION_SIZE as CHART_OPTION_SIZE
from data_science_arcade.ui.distribution_scene import OPTION_SIZE as DISTRIBUTION_OPTION_SIZE
from data_science_arcade.ui.flow_builder_scene import OPTION_SIZE as FLOW_OPTION_SIZE
from data_science_arcade.ui.junction_scene import OPTION_SIZE as JUNCTION_OPTION_SIZE
from data_science_arcade.ui.pipeline_builder_scene import OPTION_SIZE as PIPELINE_OPTION_SIZE
from data_science_arcade.ui.segment_slicer_scene import OPTION_SIZE as SEGMENT_OPTION_SIZE
from data_science_arcade.ui.source_board_scene import HEADER_SIZE, WIDE_HEADER_WIDTH
from data_science_arcade.ui.workbench_scene import PICKER_OPTION_SIZE

L11_LENSES = build_distribution_lenses(generate_order_values())

# Button.draw() centers text with no wrapping/truncation (unlike table cells
# or dialogue text), so any label wider than its button silently spills past
# its edges - this is what should have caught the Lesson 01 window_choice/
# limitation overflow that was originally found by hand via screenshots.
# Every lesson's BriefField options and SourceBoardScene source names get
# checked here, in both languages, rather than one test file per lesson.
BUTTON_PADDING = 40


def _collect_checks() -> list[tuple[str, str, int]]:
    checks: list[tuple[str, str, int]] = []

    option_button_width = OPTION_SIZE[0] - BUTTON_PADDING
    brief_fields = (
        *L01_BRIEF_FIELDS,
        *L01_DECISION_FIELDS,
        *L02_DECISION_FIELDS,
        *L03_DECISION_FIELDS,
        *L04_DECISION_FIELDS,
        *L05_DECISION_FIELDS,
        *L06_DECISION_FIELDS,
        *L07_DECISION_FIELDS,
        *L08_DECISION_FIELDS,
        *L09_DECISION_FIELDS,
        *L10_DECISION_FIELDS,
        *L11_DECISION_FIELDS,
        *L12_DECISION_FIELDS,
        *L13_DECISION_FIELDS,
        *L14_DECISION_FIELDS,
        *L15_DECISION_FIELDS,
    )
    for field in brief_fields:
        for option in field.options:
            checks.append((f"{field.key}.{option.key}", option.label_key, option_button_width))

    header_button_width = HEADER_SIZE[0] - BUTTON_PADDING
    for source in L02_SOURCES:
        checks.append((f"source.{source.key}", source.name_key, header_button_width))

    # L07 has 5 strategies (not L02's 3), so SourceBoardScene renders its
    # headers at the narrower WIDE_HEADER_WIDTH instead - see
    # source_board_scene.py's MANY_COLUMNS_THRESHOLD.
    wide_header_button_width = WIDE_HEADER_WIDTH - BUTTON_PADDING
    for strategy in L07_STRATEGIES:
        checks.append((f"strategy.{strategy.key}", strategy.name_key, wide_header_button_width))

    flow_option_button_width = FLOW_OPTION_SIZE[0] - BUTTON_PADDING
    for step in L04_FLOW_STEPS:
        for option in step.options:
            checks.append((f"{step.key}.{option.key}", option.label_key, flow_option_button_width))
    for case in L09_OUTLIER_CASES:
        for option in case.options:
            checks.append((f"{case.key}.{option.key}", option.label_key, flow_option_button_width))
    for check in L10_VALIDATION_CHECKS:
        for option in check.options:
            checks.append((f"{check.key}.{option.key}", option.label_key, flow_option_button_width))

    distribution_option_button_width = DISTRIBUTION_OPTION_SIZE[0] - BUTTON_PADDING
    for lens in L11_LENSES:
        for option in lens.options:
            checks.append((f"{lens.key}.{option.key}", option.label_key, distribution_option_button_width))

    pipeline_option_button_width = PIPELINE_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L12_AGGREGATION_REQUESTS:
        for option in request.group_by_options:
            checks.append((f"{request.key}.group_by.{option.key}", option.label_key, pipeline_option_button_width))
        for option in request.aggregate_options:
            checks.append((f"{request.key}.aggregate.{option.key}", option.label_key, pipeline_option_button_width))

    junction_option_button_width = JUNCTION_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L13_JOIN_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, junction_option_button_width))

    chart_option_button_width = CHART_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L14_CHART_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, chart_option_button_width))

    segment_option_button_width = SEGMENT_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L15_SEGMENT_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, segment_option_button_width))

    picker_option_button_width = PICKER_OPTION_SIZE[0] - BUTTON_PADDING
    for issue in L06_REPAIR_ISSUES:
        for option in issue.options:
            checks.append((f"{issue.column}.{option.key}", option.label_key, picker_option_button_width))

    return checks


ALL_CHECKS = _collect_checks()


@pytest.fixture(autouse=True)
def _pygame_session():
    pygame.init()
    fonts.clear_cache()
    yield
    pygame.quit()


@pytest.mark.parametrize("owner,label_key,max_width", ALL_CHECKS)
@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_button_label_fits_within_its_button(locale, owner, label_key, max_width):
    loc = Localization(locale=locale)
    text = loc.t(label_key)
    font = get_font(BUTTON_TEXT_SIZE)

    width, _height = font.size(text)

    assert width <= max_width, f"{locale}/{label_key} ({owner}) is {width}px wide, button only fits {max_width}px: {text!r}"

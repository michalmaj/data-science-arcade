import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.core import fonts
from data_science_arcade.core.fonts import get_font
from data_science_arcade.lessons.l01_question_first.scenario import (
    BRIEF_FIELDS as L01_BRIEF_FIELDS,
    CLAIM_FIELD as L01_CLAIM_FIELD,
    COVERAGE_INTERPRET_FIELD as L01_COVERAGE_INTERPRET_FIELD,
    DECISION_CONFIDENCE_FIELD as L01_DECISION_CONFIDENCE_FIELD,
    DECISION_FOLLOW_UP_FIELD as L01_DECISION_FOLLOW_UP_FIELD,
    DECISION_LIMITATION_FIELD as L01_DECISION_LIMITATION_FIELD,
    DECISION_RECOMMENDATION_FIELD as L01_DECISION_RECOMMENDATION_FIELD,
    ENTITY_INTERPRET_OPTIONS as L01_ENTITY_INTERPRET_OPTIONS,
    ENTITY_REVISION_FIELD as L01_ENTITY_REVISION_FIELD,
    GRAIN_REQUESTS as L01_GRAIN_REQUESTS,
    INSPECTION_PROMPT as L01_INSPECTION_PROMPT,
    MASTERY_INTERPRET_OPTIONS as L01_MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS as L01_MASTERY_METRIC_OPTIONS,
    WINDOW_CONFIDENCE_BEFORE_FIELD as L01_WINDOW_CONFIDENCE_BEFORE_FIELD,
    WINDOW_INTERPRET_OPTIONS as L01_WINDOW_INTERPRET_OPTIONS,
    WINDOW_PREDICTION_FIELD as L01_WINDOW_PREDICTION_FIELD,
)
from data_science_arcade.lessons.l02_source_scout.scenario import (
    ANSWER_STRATEGY_FIELD as L02_ANSWER_STRATEGY_FIELD,
    BILLING_INSPECTION as L02_BILLING_INSPECTION,
    APP_LOG_INSPECTION as L02_APP_LOG_INSPECTION,
    MARKETING_INSPECTION as L02_MARKETING_INSPECTION,
    BILLING_REQUESTS as L02_BILLING_REQUESTS,
    COMPARISON_1_INTERPRET_OPTIONS as L02_COMPARISON_1_INTERPRET_OPTIONS,
    COMPARISON_2_INTERPRET_OPTIONS as L02_COMPARISON_2_INTERPRET_OPTIONS,
    GAP_INTERPRET_OPTIONS as L02_GAP_INTERPRET_OPTIONS,
    KNOWN_GAP_FIELD as L02_KNOWN_GAP_FIELD,
    MASTERY_INTERPRET_OPTIONS as L02_MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS as L02_MASTERY_METRIC_OPTIONS,
    NOT_SAFE_TO_CLAIM_FIELD as L02_NOT_SAFE_TO_CLAIM_FIELD,
    RECOMMENDATION_FIELD as L02_RECOMMENDATION_FIELD,
    REVISION_FIELD as L02_REVISION_FIELD,
    SAFE_TO_CLAIM_FIELD as L02_SAFE_TO_CLAIM_FIELD,
    SOURCES as L02_SOURCES,
    SUPPORT_INTERPRET_OPTIONS as L02_SUPPORT_INTERPRET_OPTIONS,
)
from data_science_arcade.lessons.l03_api_courier.scenario import (
    ACQUISITION_STRATEGY_FIELD as L03_ACQUISITION_STRATEGY_FIELD,
    COMPLETENESS_INTERPRET_OPTIONS as L03_COMPLETENESS_INTERPRET_OPTIONS,
    INITIAL_GUT_CHECK_FIELD as L03_INITIAL_GUT_CHECK_FIELD,
    KNOWN_GAP_FIELD as L03_KNOWN_GAP_FIELD,
    MASTERY_INTERPRET_OPTIONS as L03_MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS as L03_MASTERY_METRIC_OPTIONS,
    NOT_SAFE_TO_CLAIM_FIELD as L03_NOT_SAFE_TO_CLAIM_FIELD,
    RECOMMENDATION_FIELD as L03_RECOMMENDATION_FIELD,
    REVISED_GUT_CHECK_FIELD as L03_REVISED_GUT_CHECK_FIELD,
    SAFE_TO_CLAIM_FIELD as L03_SAFE_TO_CLAIM_FIELD,
)
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
from data_science_arcade.lessons.l16_metric_forge.requests import METRIC_REQUESTS as L16_METRIC_REQUESTS
from data_science_arcade.lessons.l16_metric_forge.scenario import DECISION_FIELDS as L16_DECISION_FIELDS
from data_science_arcade.lessons.l17_hypothesis_detective.scenario import DECISION_FIELDS as L17_DECISION_FIELDS
from data_science_arcade.lessons.l18_randomization_control_room.requests import ASSIGNMENT_REQUESTS as L18_ASSIGNMENT_REQUESTS
from data_science_arcade.lessons.l18_randomization_control_room.scenario import DECISION_FIELDS as L18_DECISION_FIELDS
from data_science_arcade.lessons.l19_power_plant.scenario import DECISION_FIELDS as L19_DECISION_FIELDS
from data_science_arcade.lessons.l20_ab_test_commander.scenario import DECISION_FIELDS as L20_DECISION_FIELDS
from data_science_arcade.lessons.l21_funnel_factory.requests import FUNNEL_REQUESTS as L21_FUNNEL_REQUESTS
from data_science_arcade.lessons.l21_funnel_factory.scenario import DECISION_FIELDS as L21_DECISION_FIELDS
from data_science_arcade.lessons.l22_cohort_observatory.requests import COHORT_REQUESTS as L22_COHORT_REQUESTS
from data_science_arcade.lessons.l22_cohort_observatory.scenario import DECISION_FIELDS as L22_DECISION_FIELDS
from data_science_arcade.lessons.l23_time_series_control_room.requests import TIME_SERIES_REQUESTS as L23_TIME_SERIES_REQUESTS
from data_science_arcade.lessons.l23_time_series_control_room.scenario import DECISION_FIELDS as L23_DECISION_FIELDS
from data_science_arcade.lessons.l24_survey_bureau.requests import SURVEY_REQUESTS as L24_SURVEY_REQUESTS
from data_science_arcade.lessons.l24_survey_bureau.scenario import DECISION_FIELDS as L24_DECISION_FIELDS
from data_science_arcade.lessons.l25_kpi_emergency_room.requests import MONITORING_REQUESTS as L25_MONITORING_REQUESTS
from data_science_arcade.lessons.l25_kpi_emergency_room.scenario import DECISION_FIELDS as L25_DECISION_FIELDS
from data_science_arcade.lessons.l26_correlation_crime_scene.requests import CORRELATION_REQUESTS as L26_CORRELATION_REQUESTS
from data_science_arcade.lessons.l26_correlation_crime_scene.scenario import DECISION_FIELDS as L26_DECISION_FIELDS
from data_science_arcade.lessons.l27_causality_courtroom.requests import CORRELATION_REQUESTS as L27_CORRELATION_REQUESTS
from data_science_arcade.lessons.l27_causality_courtroom.scenario import DECISION_FIELDS as L27_DECISION_FIELDS
from data_science_arcade.lessons.l28_chart_crime_lab.requests import CHART_REQUESTS as L28_CHART_REQUESTS
from data_science_arcade.lessons.l28_chart_crime_lab.scenario import DECISION_FIELDS as L28_DECISION_FIELDS
from data_science_arcade.lessons.l29_the_executive_brief.findings import FINDINGS_POOL as L29_FINDINGS_POOL
from data_science_arcade.lessons.l29_the_executive_brief.scenario import DECISION_FIELDS as L29_DECISION_FIELDS
from data_science_arcade.lessons.l30_the_data_incident.leads import (
    DASHBOARD_CHART_REQUEST as L30_DASHBOARD_CHART_REQUEST,
    MONITORING_REQUEST as L30_MONITORING_REQUEST,
    PROMO_CORRELATION_REQUEST as L30_PROMO_CORRELATION_REQUEST,
    REDESIGN_CORRELATION_REQUEST as L30_REDESIGN_CORRELATION_REQUEST,
    REGIONAL_BREAKDOWN_REQUEST as L30_REGIONAL_BREAKDOWN_REQUEST,
)
from data_science_arcade.lessons.l30_the_data_incident.scenario import DECISION_FIELDS as L30_DECISION_FIELDS
from data_science_arcade.localization.service import SUPPORTED_LOCALES, Localization
from data_science_arcade.ui.alert_config_scene import OPTION_SIZE as ALERT_OPTION_SIZE
from data_science_arcade.ui.brief_builder_scene import OPTION_SIZE
from data_science_arcade.ui.correlation_scene import OPTION_SIZE as CORRELATION_OPTION_SIZE
from data_science_arcade.ui.button import BUTTON_TEXT_SIZE
from data_science_arcade.ui.chart_designer_scene import OPTION_SIZE as CHART_OPTION_SIZE
from data_science_arcade.ui.checkpoint_monitor_scene import NAV_BUTTON_SIZE as CHECKPOINT_NAV_BUTTON_SIZE
from data_science_arcade.ui.cohort_matrix_scene import COMPARISON_OPTION_SIZE as COHORT_COMPARISON_OPTION_SIZE
from data_science_arcade.ui.comparison_reveal_scene import OPTION_SIZE as COMPARISON_REVEAL_OPTION_SIZE
from data_science_arcade.ui.api_console_scene import CONTINUATION_OPTION_SIZE
from data_science_arcade.ui.mastery_challenge_scene import OPTION_SIZE as MASTERY_OPTION_SIZE
from data_science_arcade.ui.finding_picker_scene import OPTION_SIZE as FINDING_OPTION_SIZE
from data_science_arcade.ui.investigation_hub_scene import OPTION_SIZE as INVESTIGATION_OPTION_SIZE
from data_science_arcade.ui.survey_builder_scene import OPTION_SIZE as SURVEY_OPTION_SIZE
from data_science_arcade.ui.timeseries_scene import LENS_OPTION_SIZE as TIMESERIES_LENS_OPTION_SIZE
from data_science_arcade.ui.distribution_scene import OPTION_SIZE as DISTRIBUTION_OPTION_SIZE
from data_science_arcade.ui.flow_builder_scene import OPTION_SIZE as FLOW_OPTION_SIZE
from data_science_arcade.ui.funnel_builder_scene import DEFINITION_OPTION_SIZE as FUNNEL_DEFINITION_OPTION_SIZE
from data_science_arcade.ui.junction_scene import OPTION_SIZE as JUNCTION_OPTION_SIZE
from data_science_arcade.ui.pipeline_builder_scene import OPTION_SIZE as PIPELINE_OPTION_SIZE
from data_science_arcade.ui.prediction_scene import DIRECTION_BUTTON_SIZE
from data_science_arcade.ui.segment_slicer_scene import OPTION_SIZE as SEGMENT_OPTION_SIZE
from data_science_arcade.ui.source_board_scene import WIDE_HEADER_WIDTH
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
        L01_WINDOW_PREDICTION_FIELD,
        L01_WINDOW_CONFIDENCE_BEFORE_FIELD,
        L01_ENTITY_REVISION_FIELD,
        L01_COVERAGE_INTERPRET_FIELD,
        L01_CLAIM_FIELD,
        L01_DECISION_LIMITATION_FIELD,
        L01_DECISION_CONFIDENCE_FIELD,
        L01_DECISION_RECOMMENDATION_FIELD,
        L01_DECISION_FOLLOW_UP_FIELD,
        L02_ANSWER_STRATEGY_FIELD,
        L02_KNOWN_GAP_FIELD,
        L02_SAFE_TO_CLAIM_FIELD,
        L02_NOT_SAFE_TO_CLAIM_FIELD,
        L02_RECOMMENDATION_FIELD,
        L03_ACQUISITION_STRATEGY_FIELD,
        L03_INITIAL_GUT_CHECK_FIELD,
        L03_KNOWN_GAP_FIELD,
        L03_SAFE_TO_CLAIM_FIELD,
        L03_NOT_SAFE_TO_CLAIM_FIELD,
        L03_RECOMMENDATION_FIELD,
        L03_REVISED_GUT_CHECK_FIELD,
        L02_REVISION_FIELD,
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
        *L16_DECISION_FIELDS,
        *L17_DECISION_FIELDS,
        *L18_DECISION_FIELDS,
        *L19_DECISION_FIELDS,
        *L20_DECISION_FIELDS,
        *L21_DECISION_FIELDS,
        *L22_DECISION_FIELDS,
        *L23_DECISION_FIELDS,
        *L24_DECISION_FIELDS,
        *L25_DECISION_FIELDS,
        *L26_DECISION_FIELDS,
        *L27_DECISION_FIELDS,
        *L28_DECISION_FIELDS,
        *L29_DECISION_FIELDS,
        *L30_DECISION_FIELDS,
    )
    for field in brief_fields:
        for option in field.options:
            checks.append((f"{field.key}.{option.key}", option.label_key, option_button_width))

    # L02 now has 4 sources and L07 has 5 strategies - both exceed
    # SourceBoardScene's MANY_COLUMNS_THRESHOLD (3), so both render their
    # headers at the narrower WIDE_HEADER_WIDTH rather than HEADER_SIZE (no
    # lesson today uses SourceBoardScene with 3 or fewer sources).
    wide_header_button_width = WIDE_HEADER_WIDTH - BUTTON_PADDING
    for source in L02_SOURCES:
        checks.append((f"source.{source.key}", source.name_key, wide_header_button_width))
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
    for request in L01_GRAIN_REQUESTS:
        for option in request.group_by_options:
            checks.append((f"{request.key}.group_by.{option.key}", option.label_key, pipeline_option_button_width))
        for option in request.aggregate_options:
            checks.append((f"{request.key}.aggregate.{option.key}", option.label_key, pipeline_option_button_width))
    for request in L12_AGGREGATION_REQUESTS:
        for option in request.group_by_options:
            checks.append((f"{request.key}.group_by.{option.key}", option.label_key, pipeline_option_button_width))
        for option in request.aggregate_options:
            checks.append((f"{request.key}.aggregate.{option.key}", option.label_key, pipeline_option_button_width))
    for request in L02_BILLING_REQUESTS:
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
    for request in L28_CHART_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, chart_option_button_width))
    for option in L30_DASHBOARD_CHART_REQUEST.options:
        checks.append((f"{L30_DASHBOARD_CHART_REQUEST.key}.{option.key}", option.label_key, chart_option_button_width))

    segment_option_button_width = SEGMENT_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L15_SEGMENT_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, segment_option_button_width))
    for request in L16_METRIC_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, segment_option_button_width))
    for request in L18_ASSIGNMENT_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, segment_option_button_width))
    for option in L30_REGIONAL_BREAKDOWN_REQUEST.options:
        checks.append((f"{L30_REGIONAL_BREAKDOWN_REQUEST.key}.{option.key}", option.label_key, segment_option_button_width))

    # The three PredictionScene direction buttons (Lesson 17) are a fixed
    # shared response scale, not per-request content, so they're checked
    # once here rather than per-request like every other scene's options.
    direction_button_width = DIRECTION_BUTTON_SIZE[0] - BUTTON_PADDING
    for direction in ("increase", "decrease", "no_change"):
        checks.append((f"prediction.direction.{direction}", f"prediction.direction.{direction}", direction_button_width))

    # The two CheckpointMonitorScene nav buttons (Lesson 20) are fixed
    # scene chrome, not per-request content, so they're checked once here.
    checkpoint_nav_button_width = CHECKPOINT_NAV_BUTTON_SIZE[0] - BUTTON_PADDING
    for key in ("checkpoint.stop_button", "checkpoint.continue_button"):
        checks.append((key, key, checkpoint_nav_button_width))

    funnel_definition_button_width = FUNNEL_DEFINITION_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L21_FUNNEL_REQUESTS:
        for definition in request.definitions:
            checks.append((f"{request.key}.{definition.key}", definition.label_key, funnel_definition_button_width))

    cohort_comparison_button_width = COHORT_COMPARISON_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L22_COHORT_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, cohort_comparison_button_width))

    timeseries_lens_button_width = TIMESERIES_LENS_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L23_TIME_SERIES_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, timeseries_lens_button_width))

    survey_option_button_width = SURVEY_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L24_SURVEY_REQUESTS:
        for option in request.wording_options:
            checks.append((f"{request.key}.wording.{option.key}", option.label_key, survey_option_button_width))
        for option in request.channel_options:
            checks.append((f"{request.key}.channel.{option.key}", option.label_key, survey_option_button_width))

    alert_option_button_width = ALERT_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L25_MONITORING_REQUESTS:
        for option in request.metric_options:
            checks.append((f"{request.key}.metric.{option.key}", option.label_key, alert_option_button_width))
        for option in request.threshold_options:
            checks.append((f"{request.key}.threshold.{option.key}", option.label_key, alert_option_button_width))
    for option in L30_MONITORING_REQUEST.metric_options:
        checks.append((f"{L30_MONITORING_REQUEST.key}.metric.{option.key}", option.label_key, alert_option_button_width))
    for option in L30_MONITORING_REQUEST.threshold_options:
        checks.append((f"{L30_MONITORING_REQUEST.key}.threshold.{option.key}", option.label_key, alert_option_button_width))

    correlation_option_button_width = CORRELATION_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L26_CORRELATION_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, correlation_option_button_width))
    for request in L27_CORRELATION_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, correlation_option_button_width))
    for request in (L30_REDESIGN_CORRELATION_REQUEST, L30_PROMO_CORRELATION_REQUEST):
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, correlation_option_button_width))

    picker_option_button_width = PICKER_OPTION_SIZE[0] - BUTTON_PADDING
    for issue in L06_REPAIR_ISSUES:
        for option in issue.options:
            checks.append((f"{issue.column}.{option.key}", option.label_key, picker_option_button_width))
    for option in L01_INSPECTION_PROMPT.options:
        checks.append((f"inspection.{option.key}", option.label_key, picker_option_button_width))
    for prompt in (L02_BILLING_INSPECTION, L02_APP_LOG_INSPECTION, L02_MARKETING_INSPECTION):
        for option in prompt.options:
            checks.append((f"inspection.{option.key}", option.label_key, picker_option_button_width))

    comparison_reveal_option_button_width = COMPARISON_REVEAL_OPTION_SIZE[0] - BUTTON_PADDING
    for options in (
        L01_WINDOW_INTERPRET_OPTIONS,
        L01_ENTITY_INTERPRET_OPTIONS,
        L02_COMPARISON_1_INTERPRET_OPTIONS,
        L02_COMPARISON_2_INTERPRET_OPTIONS,
        L02_GAP_INTERPRET_OPTIONS,
        L02_SUPPORT_INTERPRET_OPTIONS,
        L03_COMPLETENESS_INTERPRET_OPTIONS,
    ):
        for option in options:
            checks.append((f"interpret.{option.key}", option.label_key, comparison_reveal_option_button_width))

    mastery_option_button_width = MASTERY_OPTION_SIZE[0] - BUTTON_PADDING
    for options in (
        L01_MASTERY_METRIC_OPTIONS,
        L01_MASTERY_INTERPRET_OPTIONS,
        L02_MASTERY_METRIC_OPTIONS,
        L02_MASTERY_INTERPRET_OPTIONS,
        L03_MASTERY_METRIC_OPTIONS,
        L03_MASTERY_INTERPRET_OPTIONS,
    ):
        for option in options:
            checks.append((f"mastery.{option.key}", option.label_key, mastery_option_button_width))

    continuation_option_button_width = CONTINUATION_OPTION_SIZE[0] - BUTTON_PADDING
    for retry_key in ("retry_immediately", "wait_and_retry", "skip"):
        checks.append((f"retry.{retry_key}", f"lesson.l03.retry.{retry_key}", continuation_option_button_width))
    for continuation_key in ("follow_cursor", "resend"):
        checks.append(
            (f"continuation.{continuation_key}", f"lesson.l03.continuation.{continuation_key}", continuation_option_button_width)
        )

    # FindingPickerScene (Lesson 29) has one flat shared pool rather than
    # per-request options, so there's no nested loop here like every other
    # scene above.
    finding_option_button_width = FINDING_OPTION_SIZE[0] - BUTTON_PADDING
    for finding in L29_FINDINGS_POOL:
        checks.append((f"finding.{finding.key}", finding.label_key, finding_option_button_width))

    return checks


ALL_CHECKS = _collect_checks()

# InvestigationHubScene (Lesson 30) appends " - <marker>" to a lead's own
# label once investigated, so the *longer*, post-investigation text is
# the real worst case to check - not just the bare label.
L30_LEAD_LABEL_KEYS = (
    "lesson.l30.lead_label.redesign_correlation",
    "lesson.l30.lead_label.regional_breakdown",
    "lesson.l30.lead_label.dashboard_chart",
    "lesson.l30.lead_label.promo_correlation",
    "lesson.l30.lead_label.monitoring_review",
)


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


@pytest.mark.parametrize("label_key", L30_LEAD_LABEL_KEYS)
@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_investigation_lead_label_fits_once_marked_investigated(locale, label_key):
    loc = Localization(locale=locale)
    text = f"{loc.t(label_key)} - {loc.t('investigation.investigated_marker')}"
    font = get_font(BUTTON_TEXT_SIZE)
    max_width = INVESTIGATION_OPTION_SIZE[0] - BUTTON_PADDING

    width, _height = font.size(text)

    assert width <= max_width, f"{locale}/{label_key} is {width}px wide once investigated, button only fits {max_width}px: {text!r}"

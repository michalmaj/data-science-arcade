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
from data_science_arcade.lessons.l04_event_log_factory.scenario import (
    DATA_MINIMIZATION_FIELD as L04_DATA_MINIMIZATION_FIELD,
    EVENT_A_INTERPRET_OPTIONS as L04_EVENT_A_INTERPRET_OPTIONS,
    INITIAL_GUT_CHECK_FIELD as L04_INITIAL_GUT_CHECK_FIELD,
    KNOWN_GAP_FIELD as L04_KNOWN_GAP_FIELD,
    MASTERY_INTERPRET_OPTIONS as L04_MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS as L04_MASTERY_METRIC_OPTIONS,
    NOT_COLLECTED_FIELD as L04_NOT_COLLECTED_FIELD,
    ORDER_A_IDENTIFIERS_FIELD as L04_ORDER_A_IDENTIFIERS_FIELD,
    ORDER_A_TRIGGER_FIELD as L04_ORDER_A_TRIGGER_FIELD,
    PAYMENT_B_IDENTIFIERS_FIELD as L04_PAYMENT_B_IDENTIFIERS_FIELD,
    PAYMENT_B_PROPERTIES_FIELD as L04_PAYMENT_B_PROPERTIES_FIELD,
    PAYMENT_B_TRIGGER_FIELD as L04_PAYMENT_B_TRIGGER_FIELD,
    QUESTIONS_ANSWERABLE_FIELD as L04_QUESTIONS_ANSWERABLE_FIELD,
    REQUIRED_CHANGE_FIELD as L04_REQUIRED_CHANGE_FIELD,
    SHIP_READINESS_FIELD as L04_SHIP_READINESS_FIELD,
)
from data_science_arcade.lessons.l05_sampling_mission.scenario import (
    DECISION_FIELDS as L05_DECISION_FIELDS,
    MASTERY_INTERPRET_OPTIONS as L05_MASTERY_INTERPRET_OPTIONS,
    MASTERY_METRIC_OPTIONS as L05_MASTERY_METRIC_OPTIONS,
    MECHANISM_INTERPRET_OPTIONS as L05_MECHANISM_INTERPRET_OPTIONS,
    VARIABILITY_INTERPRET_OPTIONS as L05_VARIABILITY_INTERPRET_OPTIONS,
)
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import DECISION_FIELDS as L06_DECISION_FIELDS
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import RAW_INSPECTION_PROMPT as L06_RAW_INSPECTION_PROMPT
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import REVEAL1_INTERPRET_OPTIONS as L06_REVEAL1_INTERPRET_OPTIONS
from data_science_arcade.lessons.l06_schema_repair_shop.scenario import REVEAL2_INTERPRET_OPTIONS as L06_REVEAL2_INTERPRET_OPTIONS
from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import ROUND1_ISSUES as L06_ROUND1_ISSUES
from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import ROUND2_ISSUES as L06_ROUND2_ISSUES
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import CONSEQUENCE_INTERPRET_OPTIONS as L07_CONSEQUENCE_INTERPRET_OPTIONS
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import DECISION_FIELDS as L07_DECISION_FIELDS
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import FIRST_ATTEMPT_INTERPRET_OPTIONS as L07_FIRST_ATTEMPT_INTERPRET_OPTIONS
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import RAW_INSPECTION_PROMPT as L07_RAW_INSPECTION_PROMPT
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import SENSITIVITY_INTERPRET_OPTIONS as L07_SENSITIVITY_INTERPRET_OPTIONS
from data_science_arcade.lessons.l07_missing_data_clinic.scenario import _build_investigation_requests as _l07_build_investigation_requests
from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import ROUND1_ISSUES as L07_ROUND1_ISSUES
from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import ROUND2_ISSUES as L07_ROUND2_ISSUES
from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import generate_orders as l07_generate_orders
from data_science_arcade.lessons.l08_duplicate_detective.scenario import DECISION_FIELDS as L08_DECISION_FIELDS
from data_science_arcade.lessons.l09_outlier_patrol.scenario import (
    ANOMALY_DIAGNOSIS_FIELD as L09_ANOMALY_DIAGNOSIS_FIELD,
    BULK_DIAGNOSIS_FIELD as L09_BULK_DIAGNOSIS_FIELD,
    CONSEQUENCE_INTERPRET_OPTIONS as L09_CONSEQUENCE_INTERPRET_OPTIONS,
    DECIMAL_DIAGNOSIS_FIELD as L09_DECIMAL_DIAGNOSIS_FIELD,
    DECISION_FIELDS as L09_DECISION_FIELDS,
    DETECTION_INTERPRET_OPTIONS as L09_DETECTION_INTERPRET_OPTIONS,
    MASTERY_MUST_NOT_REMOVE_FIELD as L09_MASTERY_MUST_NOT_REMOVE_FIELD,
    MASTERY_NEEDS_CORRECTION_FIELD as L09_MASTERY_NEEDS_CORRECTION_FIELD,
    PIPELINE_CHECK_INTERPRET_OPTIONS as L09_PIPELINE_CHECK_INTERPRET_OPTIONS,
    RAW_INSPECTION_PROMPT as L09_RAW_INSPECTION_PROMPT,
)
from data_science_arcade.lessons.l10_validation_gate.scenario import (
    BASELINE_INTERPRET_OPTIONS as L10_BASELINE_INTERPRET_OPTIONS,
    CONCENTRATION_INTERPRET_OPTIONS as L10_CONCENTRATION_INTERPRET_OPTIONS,
    CONSEQUENCE_INTERPRET_OPTIONS as L10_CONSEQUENCE_INTERPRET_OPTIONS,
    DECISION_FIELDS as L10_DECISION_FIELDS,
    GATE_RERUN_CLEAN_INTERPRET_OPTIONS as L10_GATE_RERUN_CLEAN_INTERPRET_OPTIONS,
    GATE_RERUN_INTERPRET_OPTIONS as L10_GATE_RERUN_INTERPRET_OPTIONS,
    GATE_RERUN_UNRESOLVED_INTERPRET_OPTIONS as L10_GATE_RERUN_UNRESOLVED_INTERPRET_OPTIONS,
    INVARIANT_SEVERITY_FIELD as L10_INVARIANT_SEVERITY_FIELD,
    INVARIANT_TOLERANCE_FIELD as L10_INVARIANT_TOLERANCE_FIELD,
    MASTERY_MISSING_RULE_FIELD as L10_MASTERY_MISSING_RULE_FIELD,
    MASTERY_PASS_MEANING_FIELD as L10_MASTERY_PASS_MEANING_FIELD,
    MASTERY_SEVERITY_FIELD as L10_MASTERY_SEVERITY_FIELD,
    OPTIONAL_FIELD_SEVERITY_FIELD as L10_OPTIONAL_FIELD_SEVERITY_FIELD,
    OPTIONAL_FIELD_THRESHOLD_FIELD as L10_OPTIONAL_FIELD_THRESHOLD_FIELD,
)
from data_science_arcade.lessons.l11_distribution_observatory.scenario import (
    BUSINESS_ASKS_FIELDS as L11_BUSINESS_ASKS_FIELDS,
    CAPACITY_CHECK_INTERPRET_OPTIONS as L11_CAPACITY_CHECK_INTERPRET_OPTIONS,
    DECISION_FIELDS as L11_DECISION_FIELDS,
    EXPLORE_INTERPRET_OPTIONS as L11_EXPLORE_INTERPRET_OPTIONS,
    MASTERY_INTERPRETATION_FIELD as L11_MASTERY_INTERPRETATION_FIELD,
    MASTERY_SUPPORTING_EVIDENCE_FIELD as L11_MASTERY_SUPPORTING_EVIDENCE_FIELD,
    SEGMENT_REVEAL_INTERPRET_OPTIONS as L11_SEGMENT_REVEAL_INTERPRET_OPTIONS,
    SHAPE_INTERPRET_OPTIONS as L11_SHAPE_INTERPRET_OPTIONS,
)
from data_science_arcade.lessons.l12_groupby_kitchen.scenario import (
    AOV_ROLLUP_INTERPRET_OPTIONS as L12_AOV_ROLLUP_INTERPRET_OPTIONS,
    CUSTOMER_COUNT_INTERPRET_OPTIONS as L12_CUSTOMER_COUNT_INTERPRET_OPTIONS,
    CUSTOMER_ROLLUP_INTERPRET_OPTIONS as L12_CUSTOMER_ROLLUP_INTERPRET_OPTIONS,
    DECISION_FIELDS as L12_DECISION_FIELDS,
    GRAIN_CHECK_INTERPRET_OPTIONS as L12_GRAIN_CHECK_INTERPRET_OPTIONS,
    GROUP_BY_OPTIONS as L12_GROUP_BY_OPTIONS,
    MASTERY_AVG_VALUE_METHOD_FIELD as L12_MASTERY_AVG_VALUE_METHOD_FIELD,
    MASTERY_PURCHASER_SUM_FIELD as L12_MASTERY_PURCHASER_SUM_FIELD,
    MASTERY_SUPPORTING_EVIDENCE_FIELD as L12_MASTERY_SUPPORTING_EVIDENCE_FIELD,
    METRIC_SLOTS as L12_METRIC_SLOTS,
)
from data_science_arcade.lessons.l13_join_junction.orders import (
    generate_active_promotions as l13_generate_active_promotions,
    generate_customers as l13_generate_customers,
)
from data_science_arcade.lessons.l13_join_junction.scenario import (
    DECISION_FIELDS as L13_DECISION_FIELDS,
    MASTERY_ROW_GROWTH_JUDGMENT_FIELD as L13_MASTERY_ROW_GROWTH_JUDGMENT_FIELD,
    MASTERY_SUPPORTING_EVIDENCE_FIELD as L13_MASTERY_SUPPORTING_EVIDENCE_FIELD,
    _deduped_promotions_dataset as l13_deduped_promotions_dataset,
    _join1_options as l13_join1_options,
    _promo_per_customer_dataset as l13_promo_per_customer_dataset,
    _raw_promo_options as l13_raw_promo_options,
    _repair_decision_options as l13_repair_decision_options,
)
from data_science_arcade.lessons.l14_chart_designer.scenario import (
    DATES_CONSEQUENCE_BAR_INTERPRET_OPTIONS as L14_DATES_CONSEQUENCE_BAR_INTERPRET_OPTIONS,
    DATES_CONSEQUENCE_LINE_INTERPRET_OPTIONS as L14_DATES_CONSEQUENCE_LINE_INTERPRET_OPTIONS,
    DATES_OPTIONS as L14_DATES_OPTIONS,
    DECISION_FIELDS as L14_DECISION_FIELDS,
    DISTRIBUTION_CONSEQUENCE_HISTOGRAM_INTERPRET_OPTIONS as L14_DISTRIBUTION_CONSEQUENCE_HISTOGRAM_INTERPRET_OPTIONS,
    DISTRIBUTION_CONSEQUENCE_POLYGON_INTERPRET_OPTIONS as L14_DISTRIBUTION_CONSEQUENCE_POLYGON_INTERPRET_OPTIONS,
    DISTRIBUTION_OPTIONS as L14_DISTRIBUTION_OPTIONS,
    STORE_CONSEQUENCE_BAR_INTERPRET_OPTIONS as L14_STORE_CONSEQUENCE_BAR_INTERPRET_OPTIONS,
    STORE_CONSEQUENCE_LINE_INTERPRET_OPTIONS as L14_STORE_CONSEQUENCE_LINE_INTERPRET_OPTIONS,
    STORE_OPTIONS as L14_STORE_OPTIONS,
)
from data_science_arcade.lessons.l15_segment_detective.scenario import (
    DECISION_FIELDS as L15_DECISION_FIELDS,
    DEVICE_OPTION as L15_DEVICE_OPTION,
    DEVICE_REVEAL_INTERPRET_OPTIONS as L15_DEVICE_REVEAL_INTERPRET_OPTIONS,
    HEADLINE_REVISION_FIELD as L15_HEADLINE_REVISION_FIELD,
    MASTERY_REVERSAL_JUDGMENT_FIELD as L15_MASTERY_REVERSAL_JUDGMENT_FIELD,
    MASTERY_SUPPORTING_EVIDENCE_FIELD as L15_MASTERY_SUPPORTING_EVIDENCE_FIELD,
    OVERALL_INTERPRET_OPTIONS as L15_OVERALL_INTERPRET_OPTIONS,
    REGION_NULL_INTERPRET_OPTIONS as L15_REGION_NULL_INTERPRET_OPTIONS,
    REGION_OPTION as L15_REGION_OPTION,
    STANDARDIZED_INTERPRET_OPTIONS as L15_STANDARDIZED_INTERPRET_OPTIONS,
    WEIGHTED_RECONSTRUCTION_INTERPRET_OPTIONS as L15_WEIGHTED_RECONSTRUCTION_INTERPRET_OPTIONS,
)
from data_science_arcade.lessons.l16_metric_forge.scenario import (
    DECISION_FIELDS as L16_DECISION_FIELDS,
    GUARDRAIL_FIELD as L16_GUARDRAIL_FIELD,
    MASTERY_EVIDENCE_FIELD as L16_MASTERY_EVIDENCE_FIELD,
    MASTERY_JUDGMENT_FIELD as L16_MASTERY_JUDGMENT_FIELD,
    PRIOR_VERDICT_FIELD as L16_PRIOR_VERDICT_FIELD,
    RERUN_INTERPRET_OPTIONS as L16_RERUN_INTERPRET_OPTIONS,
    STRESS_A_GUARDRAIL_INTERPRET_OPTIONS as L16_STRESS_A_GUARDRAIL_INTERPRET_OPTIONS,
    STRESS_A_PRIMARY_INTERPRET_OPTIONS as L16_STRESS_A_PRIMARY_INTERPRET_OPTIONS,
    STRESS_B_BACKLOG_INTERPRET_OPTIONS as L16_STRESS_B_BACKLOG_INTERPRET_OPTIONS,
    STRESS_B_DEFINITION_INTERPRET_OPTIONS as L16_STRESS_B_DEFINITION_INTERPRET_OPTIONS,
    _build_candidates as l16_build_candidates,
    EARLY as L16_EARLY,
    EARLY_AS_OF_EXPR as L16_EARLY_AS_OF_EXPR,
    HONEST as L16_HONEST,
)
from data_science_arcade.ui.metric_contract_scene import PICKER_SIZE as METRIC_CONTRACT_PICKER_SIZE
from data_science_arcade.lessons.l17_hypothesis_detective.scenario import (
    DECISION_FIELDS as L17_DECISION_FIELDS,
    DEVICE_PATTERN_INTERPRET_OPTIONS as L17_DEVICE_PATTERN_INTERPRET_OPTIONS,
    HYPOTHESIS_PLAN_FIELDS as L17_HYPOTHESIS_PLAN_FIELDS,
    MASTERY_EVIDENCE_FIELD as L17_MASTERY_EVIDENCE_FIELD,
    MASTERY_JUDGMENT_FIELD as L17_MASTERY_JUDGMENT_FIELD,
    MASTERY_URBAN_STATUS_FIELD as L17_MASTERY_URBAN_STATUS_FIELD,
    PRIMARY_INTERPRET_OPTIONS as L17_PRIMARY_INTERPRET_OPTIONS,
)
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
from data_science_arcade.ui.chart_builder_scene import OPTION_SIZE as CHART_BUILDER_OPTION_SIZE
from data_science_arcade.ui.chart_designer_scene import OPTION_SIZE as CHART_OPTION_SIZE
from data_science_arcade.ui.composite_scene import OFFER_BUTTON_SIZE
from data_science_arcade.ui.checkpoint_monitor_scene import NAV_BUTTON_SIZE as CHECKPOINT_NAV_BUTTON_SIZE
from data_science_arcade.ui.cohort_matrix_scene import COMPARISON_OPTION_SIZE as COHORT_COMPARISON_OPTION_SIZE
from data_science_arcade.ui.comparison_reveal_scene import OPTION_SIZE as COMPARISON_REVEAL_OPTION_SIZE
from data_science_arcade.ui.api_console_scene import CONTINUATION_OPTION_SIZE
from data_science_arcade.ui.mastery_challenge_scene import OPTION_SIZE as MASTERY_OPTION_SIZE
from data_science_arcade.ui.finding_picker_scene import OPTION_SIZE as FINDING_OPTION_SIZE
from data_science_arcade.ui.investigation_hub_scene import OPTION_SIZE as INVESTIGATION_OPTION_SIZE
from data_science_arcade.ui.survey_builder_scene import OPTION_SIZE as SURVEY_OPTION_SIZE
from data_science_arcade.ui.timeseries_scene import LENS_OPTION_SIZE as TIMESERIES_LENS_OPTION_SIZE
from data_science_arcade.ui.funnel_builder_scene import DEFINITION_OPTION_SIZE as FUNNEL_DEFINITION_OPTION_SIZE
from data_science_arcade.ui.join_builder_scene import OPTION_SIZE as JOIN_BUILDER_OPTION_SIZE
from data_science_arcade.ui.pipeline_builder_scene import OPTION_SIZE as PIPELINE_OPTION_SIZE
from data_science_arcade.ui.segment_mix_scene import PICKER_SIZE as SEGMENT_MIX_PICKER_SIZE
from data_science_arcade.ui.segment_slicer_scene import OPTION_SIZE as SEGMENT_OPTION_SIZE
from data_science_arcade.ui.source_board_scene import WIDE_HEADER_WIDTH
from data_science_arcade.ui.workbench_scene import PICKER_OPTION_SIZE

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
        L04_ORDER_A_TRIGGER_FIELD,
        L04_ORDER_A_IDENTIFIERS_FIELD,
        L04_PAYMENT_B_TRIGGER_FIELD,
        L04_PAYMENT_B_IDENTIFIERS_FIELD,
        L04_PAYMENT_B_PROPERTIES_FIELD,
        L04_DATA_MINIMIZATION_FIELD,
        L04_INITIAL_GUT_CHECK_FIELD,
        L04_SHIP_READINESS_FIELD,
        L04_QUESTIONS_ANSWERABLE_FIELD,
        L04_KNOWN_GAP_FIELD,
        L04_REQUIRED_CHANGE_FIELD,
        L04_NOT_COLLECTED_FIELD,
        *L05_DECISION_FIELDS,
        *L06_DECISION_FIELDS,
        *L07_DECISION_FIELDS,
        *L08_DECISION_FIELDS,
        *L09_DECISION_FIELDS,
        L09_DECIMAL_DIAGNOSIS_FIELD,
        L09_BULK_DIAGNOSIS_FIELD,
        L09_ANOMALY_DIAGNOSIS_FIELD,
        L09_MASTERY_MUST_NOT_REMOVE_FIELD,
        L09_MASTERY_NEEDS_CORRECTION_FIELD,
        *L10_DECISION_FIELDS,
        L10_OPTIONAL_FIELD_SEVERITY_FIELD,
        L10_OPTIONAL_FIELD_THRESHOLD_FIELD,
        L10_INVARIANT_TOLERANCE_FIELD,
        L10_INVARIANT_SEVERITY_FIELD,
        L10_MASTERY_MISSING_RULE_FIELD,
        L10_MASTERY_SEVERITY_FIELD,
        L10_MASTERY_PASS_MEANING_FIELD,
        *L11_BUSINESS_ASKS_FIELDS,
        *L11_DECISION_FIELDS,
        L11_MASTERY_SUPPORTING_EVIDENCE_FIELD,
        L11_MASTERY_INTERPRETATION_FIELD,
        *L12_DECISION_FIELDS,
        L12_MASTERY_SUPPORTING_EVIDENCE_FIELD,
        L12_MASTERY_PURCHASER_SUM_FIELD,
        L12_MASTERY_AVG_VALUE_METHOD_FIELD,
        *L13_DECISION_FIELDS,
        L13_MASTERY_SUPPORTING_EVIDENCE_FIELD,
        L13_MASTERY_ROW_GROWTH_JUDGMENT_FIELD,
        *L14_DECISION_FIELDS,
        *L15_DECISION_FIELDS,
        L15_HEADLINE_REVISION_FIELD,
        L15_MASTERY_SUPPORTING_EVIDENCE_FIELD,
        L15_MASTERY_REVERSAL_JUDGMENT_FIELD,
        *L16_DECISION_FIELDS,
        L16_GUARDRAIL_FIELD,
        L16_PRIOR_VERDICT_FIELD,
        L16_MASTERY_JUDGMENT_FIELD,
        L16_MASTERY_EVIDENCE_FIELD,
        *L17_HYPOTHESIS_PLAN_FIELDS,
        *L17_DECISION_FIELDS,
        L17_MASTERY_JUDGMENT_FIELD,
        L17_MASTERY_URBAN_STATUS_FIELD,
        L17_MASTERY_EVIDENCE_FIELD,
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

    # L02 now has 4 sources, which exceeds SourceBoardScene's
    # MANY_COLUMNS_THRESHOLD (3), so it renders its headers at the
    # narrower WIDE_HEADER_WIDTH rather than HEADER_SIZE.
    wide_header_button_width = WIDE_HEADER_WIDTH - BUTTON_PADDING
    for source in L02_SOURCES:
        checks.append((f"source.{source.key}", source.name_key, wide_header_button_width))

    pipeline_option_button_width = PIPELINE_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L01_GRAIN_REQUESTS:
        for option in request.group_by_options:
            checks.append((f"{request.key}.group_by.{option.key}", option.label_key, pipeline_option_button_width))
        for option in request.aggregate_options:
            checks.append((f"{request.key}.aggregate.{option.key}", option.label_key, pipeline_option_button_width))
    # AggregationBuilderScene's own OPTION_SIZE is (420, 40) - the same
    # 420 width as brief_builder_scene's, so L12's group-by/metric-slot
    # options share the same option_button_width group above rather than
    # needing a separate import for an identical number.
    for option in L12_GROUP_BY_OPTIONS:
        checks.append((f"group_by.{option.key}", option.label_key, option_button_width))
    for slot in L12_METRIC_SLOTS:
        for option in slot.options:
            checks.append((f"{slot.key}.{option.key}", option.label_key, option_button_width))
    for request in L02_BILLING_REQUESTS:
        for option in request.group_by_options:
            checks.append((f"{request.key}.group_by.{option.key}", option.label_key, pipeline_option_button_width))
        for option in request.aggregate_options:
            checks.append((f"{request.key}.aggregate.{option.key}", option.label_key, pipeline_option_button_width))

    join_builder_option_button_width = JOIN_BUILDER_OPTION_SIZE[0] - BUTTON_PADDING
    l13_customers = l13_generate_customers()
    l13_active_promotions = l13_generate_active_promotions()
    l13_promo_per_customer = l13_promo_per_customer_dataset(l13_active_promotions)
    l13_deduped_promotions = l13_deduped_promotions_dataset(l13_active_promotions)
    l13_options = (
        *l13_join1_options(l13_customers),
        *l13_raw_promo_options(l13_active_promotions),
        *l13_repair_decision_options(l13_active_promotions, l13_promo_per_customer, l13_deduped_promotions),
    )
    for option in l13_options:
        checks.append((f"join_builder.{option.key}", option.label_key, join_builder_option_button_width))

    chart_builder_option_button_width = CHART_BUILDER_OPTION_SIZE[0] - BUTTON_PADDING
    for option in (*L14_STORE_OPTIONS, *L14_DATES_OPTIONS, *L14_DISTRIBUTION_OPTIONS):
        checks.append((f"chart_builder.{option.key}", option.label_key, chart_builder_option_button_width))

    chart_option_button_width = CHART_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L28_CHART_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, chart_option_button_width))
    for option in L30_DASHBOARD_CHART_REQUEST.options:
        checks.append((f"{L30_DASHBOARD_CHART_REQUEST.key}.{option.key}", option.label_key, chart_option_button_width))

    segment_mix_picker_button_width = SEGMENT_MIX_PICKER_SIZE[0] - BUTTON_PADDING
    for option in (L15_REGION_OPTION, L15_DEVICE_OPTION):
        checks.append((f"segment_mix.dimension.{option.key}", option.label_key, segment_mix_picker_button_width))

    comparison_reveal_option_button_width_l15 = COMPARISON_REVEAL_OPTION_SIZE[0] - BUTTON_PADDING
    for options in (
        L15_OVERALL_INTERPRET_OPTIONS,
        L15_REGION_NULL_INTERPRET_OPTIONS,
        L15_DEVICE_REVEAL_INTERPRET_OPTIONS,
        L15_WEIGHTED_RECONSTRUCTION_INTERPRET_OPTIONS,
        L15_STANDARDIZED_INTERPRET_OPTIONS,
    ):
        for option in options:
            checks.append((f"interpret.{option.key}", option.label_key, comparison_reveal_option_button_width_l15))

    segment_option_button_width = SEGMENT_OPTION_SIZE[0] - BUTTON_PADDING
    for request in L18_ASSIGNMENT_REQUESTS:
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, segment_option_button_width))
    for option in L30_REGIONAL_BREAKDOWN_REQUEST.options:
        checks.append((f"{L30_REGIONAL_BREAKDOWN_REQUEST.key}.{option.key}", option.label_key, segment_option_button_width))
    for request in _l07_build_investigation_requests(l07_generate_orders()):
        for option in request.options:
            checks.append((f"{request.key}.{option.key}", option.label_key, segment_option_button_width))
    # L09's own by-zone segment request is built live inside its stage
    # closure (its Segment rows depend on the real dataset), not exported
    # as a module-level constant like L15/L18's own requests - only its
    # one static SliceOption label actually needs checking here.
    checks.append(("l09_segment.by_zone", "lesson.l09.segment.option.by_zone", segment_option_button_width))

    metric_contract_picker_button_width = METRIC_CONTRACT_PICKER_SIZE[0] - BUTTON_PADDING
    for option in l16_build_candidates(L16_HONEST, L16_EARLY, L16_EARLY_AS_OF_EXPR):
        checks.append((f"metric_contract.{option.key}", option.label_key, metric_contract_picker_button_width))

    comparison_reveal_option_button_width_l16 = COMPARISON_REVEAL_OPTION_SIZE[0] - BUTTON_PADDING
    for options in (
        L16_STRESS_A_PRIMARY_INTERPRET_OPTIONS,
        L16_STRESS_A_GUARDRAIL_INTERPRET_OPTIONS,
        L16_STRESS_B_DEFINITION_INTERPRET_OPTIONS,
        L16_STRESS_B_BACKLOG_INTERPRET_OPTIONS,
        L16_RERUN_INTERPRET_OPTIONS,
    ):
        for option in options:
            checks.append((f"interpret.{option.key}", option.label_key, comparison_reveal_option_button_width_l16))

    for options in (L17_PRIMARY_INTERPRET_OPTIONS, L17_DEVICE_PATTERN_INTERPRET_OPTIONS):
        for option in options:
            checks.append((f"interpret.{option.key}", option.label_key, comparison_reveal_option_button_width_l16))

    # The two CheckpointMonitorScene nav buttons (Lesson 20) are fixed
    # scene chrome, not per-request content, so they're checked once here.
    checkpoint_nav_button_width = CHECKPOINT_NAV_BUTTON_SIZE[0] - BUTTON_PADDING
    for key in ("checkpoint.stop_button", "checkpoint.continue_button"):
        checks.append((key, key, checkpoint_nav_button_width))

    # OfferThenTaskScene's own engage/skip buttons are fixed chrome, not
    # per-request content - the generic mastery.* pair every mastery-style
    # offer defaults to, plus every lesson's own override (currently only
    # L07's sensitivity revision offer, whose "reconsider a real Round 2
    # pick" framing doesn't fit the generic "bonus question" wording).
    offer_button_width = OFFER_BUTTON_SIZE[0] - BUTTON_PADDING
    for key in (
        "mastery.engage",
        "mastery.skip",
        "lesson.l07.sensitivity.revision_offer.engage",
        "lesson.l07.sensitivity.revision_offer.skip",
    ):
        checks.append((key, key, offer_button_width))

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
    for issue in (*L06_ROUND1_ISSUES, *L06_ROUND2_ISSUES, *L07_ROUND1_ISSUES, *L07_ROUND2_ISSUES):
        for option in issue.options:
            checks.append((f"{issue.column}.{option.key}", option.label_key, picker_option_button_width))
    for option in L01_INSPECTION_PROMPT.options:
        checks.append((f"inspection.{option.key}", option.label_key, picker_option_button_width))
    for prompt in (L02_BILLING_INSPECTION, L02_APP_LOG_INSPECTION, L02_MARKETING_INSPECTION):
        for option in prompt.options:
            checks.append((f"inspection.{option.key}", option.label_key, picker_option_button_width))
    for option in L06_RAW_INSPECTION_PROMPT.options:
        checks.append((f"l06_inspection.{option.key}", option.label_key, picker_option_button_width))
    for option in L07_RAW_INSPECTION_PROMPT.options:
        checks.append((f"l07_inspection.{option.key}", option.label_key, picker_option_button_width))
    for option in L09_RAW_INSPECTION_PROMPT.options:
        checks.append((f"l09_inspection.{option.key}", option.label_key, picker_option_button_width))

    comparison_reveal_option_button_width = COMPARISON_REVEAL_OPTION_SIZE[0] - BUTTON_PADDING
    # DistributionExplorerScene's own interpret OPTION_SIZE is (420, 40) -
    # the same 420 width as ComparisonRevealScene's, so L11's interpret
    # option lists (both its ComparisonRevealScene reveals and its own
    # DistributionExplorerScene reveals) share this same width group
    # rather than needing a separate import for an identical number.
    for options in (
        L01_WINDOW_INTERPRET_OPTIONS,
        L01_ENTITY_INTERPRET_OPTIONS,
        L02_COMPARISON_1_INTERPRET_OPTIONS,
        L02_COMPARISON_2_INTERPRET_OPTIONS,
        L02_GAP_INTERPRET_OPTIONS,
        L02_SUPPORT_INTERPRET_OPTIONS,
        L03_COMPLETENESS_INTERPRET_OPTIONS,
        L04_EVENT_A_INTERPRET_OPTIONS,
        L05_MECHANISM_INTERPRET_OPTIONS,
        L05_VARIABILITY_INTERPRET_OPTIONS,
        L06_REVEAL1_INTERPRET_OPTIONS,
        L06_REVEAL2_INTERPRET_OPTIONS,
        L07_FIRST_ATTEMPT_INTERPRET_OPTIONS,
        L07_SENSITIVITY_INTERPRET_OPTIONS,
        L07_CONSEQUENCE_INTERPRET_OPTIONS,
        L09_DETECTION_INTERPRET_OPTIONS,
        L09_CONSEQUENCE_INTERPRET_OPTIONS,
        L09_PIPELINE_CHECK_INTERPRET_OPTIONS,
        L10_BASELINE_INTERPRET_OPTIONS,
        L10_CONSEQUENCE_INTERPRET_OPTIONS,
        L10_GATE_RERUN_INTERPRET_OPTIONS,
        L10_CONCENTRATION_INTERPRET_OPTIONS,
        L10_GATE_RERUN_CLEAN_INTERPRET_OPTIONS,
        L10_GATE_RERUN_UNRESOLVED_INTERPRET_OPTIONS,
        L11_EXPLORE_INTERPRET_OPTIONS,
        L11_CAPACITY_CHECK_INTERPRET_OPTIONS,
        L11_SHAPE_INTERPRET_OPTIONS,
        L11_SEGMENT_REVEAL_INTERPRET_OPTIONS,
        L12_GRAIN_CHECK_INTERPRET_OPTIONS,
        L12_CUSTOMER_COUNT_INTERPRET_OPTIONS,
        L12_CUSTOMER_ROLLUP_INTERPRET_OPTIONS,
        L12_AOV_ROLLUP_INTERPRET_OPTIONS,
        L14_STORE_CONSEQUENCE_LINE_INTERPRET_OPTIONS,
        L14_STORE_CONSEQUENCE_BAR_INTERPRET_OPTIONS,
        L14_DATES_CONSEQUENCE_LINE_INTERPRET_OPTIONS,
        L14_DATES_CONSEQUENCE_BAR_INTERPRET_OPTIONS,
        L14_DISTRIBUTION_CONSEQUENCE_HISTOGRAM_INTERPRET_OPTIONS,
        L14_DISTRIBUTION_CONSEQUENCE_POLYGON_INTERPRET_OPTIONS,
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
        L04_MASTERY_METRIC_OPTIONS,
        L04_MASTERY_INTERPRET_OPTIONS,
        L05_MASTERY_METRIC_OPTIONS,
        L05_MASTERY_INTERPRET_OPTIONS,
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

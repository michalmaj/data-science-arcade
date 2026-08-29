from data_science_arcade.lessons.framework.correlation import CorrelationRequest, VerdictOption
from data_science_arcade.lessons.l26_correlation_crime_scene.correlation_data import (
    compute_correlation,
    compute_correlation_within,
    generate_dark_mode_data,
    generate_push_spend_data,
    generate_shipment_sales_data,
)

_push_spend = generate_push_spend_data()
_shipment_sales = generate_shipment_sales_data()
_dark_mode = generate_dark_mode_data()

PUSH_OPENS_CORRELATION = compute_correlation(_push_spend, "push_opens_per_week", "weekly_spend")
SHIPMENT_SALES_CORRELATION = compute_correlation(_shipment_sales, "shipment_received", "daily_sales")
DARK_MODE_CORRELATION = compute_correlation(_dark_mode, "dark_mode_enabled", "weekly_spend")
DARK_MODE_WITHIN_MODERN_CORRELATION = compute_correlation_within(_dark_mode, "device_group", "modern", "dark_mode_enabled", "weekly_spend")

# Three scenarios, each ruling out a different subset of explanations for
# a genuinely real correlation - hand-crafted, not random, and verified
# via script before any of this was written. The correct verdict's
# position varies across all three requests (0, 1, 2) so it can't be
# recognized by position alone.
PUSH_OPENS_CLAIM = CorrelationRequest(
    key="push_opens_claim",
    prompt_key="lesson.l26.request.push_opens_claim.prompt",
    hint_key="lesson.l26.request.push_opens_claim.hint",
    metric_a_label_key="lesson.l26.metric.push_opens",
    metric_b_label_key="lesson.l26.metric.weekly_spend",
    evidence_key="lesson.l26.evidence.push_opens_claim",
    correlation=PUSH_OPENS_CORRELATION,
    sample_size=len(_push_spend.frame),
    options=(
        VerdictOption("coincidence_ruled_out_only", "lesson.l26.option.push_opens_claim.coincidence_ruled_out_only", "lesson.l26.explanation.push_opens_claim.coincidence_ruled_out_only"),
        VerdictOption("proves_push_causes_spend", "lesson.l26.option.push_opens_claim.proves_push_causes_spend", "lesson.l26.explanation.push_opens_claim.proves_push_causes_spend"),
        VerdictOption("nothing_can_be_concluded", "lesson.l26.option.push_opens_claim.nothing_can_be_concluded", "lesson.l26.explanation.push_opens_claim.nothing_can_be_concluded"),
    ),
)

SHIPMENT_SALES_CLAIM = CorrelationRequest(
    key="shipment_sales_claim",
    prompt_key="lesson.l26.request.shipment_sales_claim.prompt",
    hint_key="lesson.l26.request.shipment_sales_claim.hint",
    metric_a_label_key="lesson.l26.metric.shipment_received",
    metric_b_label_key="lesson.l26.metric.daily_sales",
    evidence_key="lesson.l26.evidence.shipment_sales_claim",
    correlation=SHIPMENT_SALES_CORRELATION,
    sample_size=len(_shipment_sales.frame),
    options=(
        VerdictOption("reverse_causation_still_open", "lesson.l26.option.shipment_sales_claim.reverse_causation_still_open", "lesson.l26.explanation.shipment_sales_claim.reverse_causation_still_open"),
        VerdictOption("reverse_ruled_out_two_remain", "lesson.l26.option.shipment_sales_claim.reverse_ruled_out_two_remain", "lesson.l26.explanation.shipment_sales_claim.reverse_ruled_out_two_remain"),
        VerdictOption("must_be_the_shipment_then", "lesson.l26.option.shipment_sales_claim.must_be_the_shipment_then", "lesson.l26.explanation.shipment_sales_claim.must_be_the_shipment_then"),
    ),
)

DARK_MODE_CLAIM = CorrelationRequest(
    key="dark_mode_claim",
    prompt_key="lesson.l26.request.dark_mode_claim.prompt",
    hint_key="lesson.l26.request.dark_mode_claim.hint",
    metric_a_label_key="lesson.l26.metric.dark_mode_enabled",
    metric_b_label_key="lesson.l26.metric.weekly_spend",
    evidence_key="lesson.l26.evidence.dark_mode_claim",
    correlation=DARK_MODE_CORRELATION,
    sample_size=len(_dark_mode.frame),
    options=(
        VerdictOption("dark_mode_clearly_boosts_spend", "lesson.l26.option.dark_mode_claim.dark_mode_clearly_boosts_spend", "lesson.l26.explanation.dark_mode_claim.dark_mode_clearly_boosts_spend"),
        VerdictOption("device_group_rules_out_nothing", "lesson.l26.option.dark_mode_claim.device_group_rules_out_nothing", "lesson.l26.explanation.dark_mode_claim.device_group_rules_out_nothing"),
        VerdictOption("device_group_explains_it", "lesson.l26.option.dark_mode_claim.device_group_explains_it", "lesson.l26.explanation.dark_mode_claim.device_group_explains_it"),
    ),
)

CORRELATION_REQUESTS: tuple[CorrelationRequest, ...] = (PUSH_OPENS_CLAIM, SHIPMENT_SALES_CLAIM, DARK_MODE_CLAIM)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "push_opens_claim": "coincidence_ruled_out_only",
    "shipment_sales_claim": "reverse_ruled_out_two_remain",
    "dark_mode_claim": "device_group_explains_it",
}

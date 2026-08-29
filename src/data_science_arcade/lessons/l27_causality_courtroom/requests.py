from data_science_arcade.lessons.framework.correlation import CorrelationRequest, VerdictOption
from data_science_arcade.lessons.l27_causality_courtroom.case_data import (
    compute_correlation,
    generate_resolution_satisfaction_data,
    generate_tool_spend_data,
    generate_training_performance_data,
)

_tool_spend = generate_tool_spend_data()
_resolution_satisfaction = generate_resolution_satisfaction_data()
_training_performance = generate_training_performance_data()

TOOL_SPEND_CORRELATION = compute_correlation(_tool_spend, "tool_used", "impulse_spend")
RESOLUTION_SATISFACTION_CORRELATION = compute_correlation(_resolution_satisfaction, "resolved_under_1hr", "satisfaction_score")
TRAINING_PERFORMANCE_CORRELATION = compute_correlation(_training_performance, "completed_training", "performance_score")

# Three cases, each a real self-selection or selection-on-outcome trap -
# hand-crafted, not random, verified via script before any of this was
# written. Every case offers one option that reaches the *right verdict*
# for the *wrong reason* (a real, tempting mistake distinct from simply
# picking the opposite verdict), not just a correct option vs. an
# obviously-opposite one. The correct verdict's position varies across
# all three requests (0, 1, 2) so it can't be recognized by position alone.
TOOL_SPEND_CLAIM = CorrelationRequest(
    key="tool_spend_claim",
    prompt_key="lesson.l27.request.tool_spend_claim.prompt",
    hint_key="lesson.l27.request.tool_spend_claim.hint",
    metric_a_label_key="lesson.l27.metric.tool_used",
    metric_b_label_key="lesson.l27.metric.impulse_spend",
    evidence_key="lesson.l27.evidence.tool_spend_claim",
    correlation=TOOL_SPEND_CORRELATION,
    sample_size=len(_tool_spend.frame),
    options=(
        VerdictOption("sustain_self_selection", "lesson.l27.option.tool_spend_claim.sustain_self_selection", "lesson.l27.explanation.tool_spend_claim.sustain_self_selection"),
        VerdictOption("overrule_correlation_proves_it", "lesson.l27.option.tool_spend_claim.overrule_correlation_proves_it", "lesson.l27.explanation.tool_spend_claim.overrule_correlation_proves_it"),
        VerdictOption("sustain_wrong_reason_group_sizes", "lesson.l27.option.tool_spend_claim.sustain_wrong_reason_group_sizes", "lesson.l27.explanation.tool_spend_claim.sustain_wrong_reason_group_sizes"),
    ),
)

RESOLUTION_SATISFACTION_CLAIM = CorrelationRequest(
    key="resolution_satisfaction_claim",
    prompt_key="lesson.l27.request.resolution_satisfaction_claim.prompt",
    hint_key="lesson.l27.request.resolution_satisfaction_claim.hint",
    metric_a_label_key="lesson.l27.metric.resolved_under_1hr",
    metric_b_label_key="lesson.l27.metric.satisfaction_score",
    evidence_key="lesson.l27.evidence.resolution_satisfaction_claim",
    correlation=RESOLUTION_SATISFACTION_CORRELATION,
    sample_size=len(_resolution_satisfaction.frame),
    options=(
        VerdictOption("overrule_mandate_speed_everywhere", "lesson.l27.option.resolution_satisfaction_claim.overrule_mandate_speed_everywhere", "lesson.l27.explanation.resolution_satisfaction_claim.overrule_mandate_speed_everywhere"),
        VerdictOption("sustain_difficulty_not_speed", "lesson.l27.option.resolution_satisfaction_claim.sustain_difficulty_not_speed", "lesson.l27.explanation.resolution_satisfaction_claim.sustain_difficulty_not_speed"),
        VerdictOption("sustain_better_agents_handle_fast_tickets", "lesson.l27.option.resolution_satisfaction_claim.sustain_better_agents_handle_fast_tickets", "lesson.l27.explanation.resolution_satisfaction_claim.sustain_better_agents_handle_fast_tickets"),
    ),
)

TRAINING_PERFORMANCE_CLAIM = CorrelationRequest(
    key="training_performance_claim",
    prompt_key="lesson.l27.request.training_performance_claim.prompt",
    hint_key="lesson.l27.request.training_performance_claim.hint",
    metric_a_label_key="lesson.l27.metric.completed_training",
    metric_b_label_key="lesson.l27.metric.performance_score",
    evidence_key="lesson.l27.evidence.training_performance_claim",
    correlation=TRAINING_PERFORMANCE_CORRELATION,
    sample_size=len(_training_performance.frame),
    options=(
        VerdictOption("overrule_too_large_for_coincidence", "lesson.l27.option.training_performance_claim.overrule_too_large_for_coincidence", "lesson.l27.explanation.training_performance_claim.overrule_too_large_for_coincidence"),
        VerdictOption("sustain_reviews_are_always_biased", "lesson.l27.option.training_performance_claim.sustain_reviews_are_always_biased", "lesson.l27.explanation.training_performance_claim.sustain_reviews_are_always_biased"),
        VerdictOption("sustain_cant_separate_from_who_attended", "lesson.l27.option.training_performance_claim.sustain_cant_separate_from_who_attended", "lesson.l27.explanation.training_performance_claim.sustain_cant_separate_from_who_attended"),
    ),
)

CORRELATION_REQUESTS: tuple[CorrelationRequest, ...] = (TOOL_SPEND_CLAIM, RESOLUTION_SATISFACTION_CLAIM, TRAINING_PERFORMANCE_CLAIM)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "tool_spend_claim": "sustain_self_selection",
    "resolution_satisfaction_claim": "sustain_difficulty_not_speed",
    "training_performance_claim": "sustain_cant_separate_from_who_attended",
}

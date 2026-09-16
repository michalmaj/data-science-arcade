from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.alerting import MonitoringChoices
from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.l25_kpi_emergency_room.requests import CORRECT_METRIC_BY_REQUEST

_CORRECT_THRESHOLD_TRADEOFF_REASON = "flags_ordinary_variation_without_improving_detection_of_the_real_incidents"
_CORRECT_WRONG_METRIC_REASON = "did_not_align_with_either_incident_and_threshold_changes_only_shifted_which_days_alarmed"
_CORRECT_ALERT_LIMITS_REASON = "something_crossed_a_real_line_worth_investigating_not_why_it_happened"

_CALIBRATED_CLAIM = "checkout_and_delivery_alerts_flag_real_incidents_but_dont_explain_them_and_silence_elsewhere_isnt_proof_of_health"
_OVERCLAIM = "the_dashboard_now_proves_nothing_else_is_wrong"
_UNDERCLAIM = "alerts_dont_tell_us_anything_useful_without_a_root_cause"

# --- Evidence, claim-role-based over 7 real, unconditionally-recorded
# facts (never gated by which reveal interpretation a student picked) - 3
# roles, none a strict subset of another. Sized to what the new
# threshold-tradeoff / incident-coverage / wrong-metric-silence semantics
# actually require, not padded toward any earlier lesson's own role
# count. ---------------------------------------------------------------

PAGE_LOAD_TIME_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY = "lesson.l25.evidence.page_load_time_tight_false_alarm_count"
PAGE_LOAD_TIME_BALANCED_FALSE_ALARM_COUNT_EVIDENCE_KEY = "lesson.l25.evidence.page_load_time_balanced_false_alarm_count"
PAGE_LOAD_TIME_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY = "lesson.l25.evidence.page_load_time_real_incidents_caught"
CHECKOUT_ERROR_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY = "lesson.l25.evidence.checkout_error_rate_real_incidents_caught"
ON_TIME_DELIVERY_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY = "lesson.l25.evidence.on_time_delivery_rate_real_incidents_caught"
SOCIAL_MENTIONS_BALANCED_ALERT_COUNT_EVIDENCE_KEY = "lesson.l25.evidence.social_mentions_balanced_alert_count"
SOCIAL_MENTIONS_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY = "lesson.l25.evidence.social_mentions_tight_false_alarm_count"

THRESHOLD_TRADEOFF_KEYS: tuple[str, ...] = (
    PAGE_LOAD_TIME_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY,
    PAGE_LOAD_TIME_BALANCED_FALSE_ALARM_COUNT_EVIDENCE_KEY,
    PAGE_LOAD_TIME_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
)
"""Claim: tighter thresholds increased false-alarm cost here (2 vs. 0)
without improving detection of the real incidents (0 either way) - all
three facts are needed together, since the count alone doesn't defend
"cost without benefit" without the paired comparison."""

INCIDENT_COVERAGE_KEYS: tuple[str, ...] = (
    CHECKOUT_ERROR_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
    ON_TIME_DELIVERY_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
)
"""Claim: the compact two-metric set covers the two distinct observed
operational incidents - one metric catching one incident doesn't defend
"compact system," both are needed."""

WRONG_METRIC_SILENCE_KEYS: tuple[str, ...] = (
    SOCIAL_MENTIONS_BALANCED_ALERT_COUNT_EVIDENCE_KEY,
    SOCIAL_MENTIONS_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY,
)
"""Claim: silence on this metric never meant the business was healthy,
and merely tightening it didn't make it detect anything real - zero
alerts under balanced alone doesn't defend "no threshold helps" without
also showing tight's own 3 alerts never align with either real incident."""

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    *THRESHOLD_TRADEOFF_KEYS,
    *INCIDENT_COVERAGE_KEYS,
    *WRONG_METRIC_SILENCE_KEYS,
)

# --- Mastery: NovaMart Warehouse Ops alert-fatigue dataset (previously
# this lesson's own flat twist, promoted here unchanged - see
# twist_data.py). The mastery claim stays a calibrated association, never
# an unproven causal one: these rows show a real, strong pattern (46
# false alarms, 4-minute average response; the one real incident, a
# 360-minute response), not a measured dismissal mechanism. ------------

_CORRECT_MASTERY_WHAT_46_COST = "real_incident_response_was_90x_slower_consistent_with_alert_fatigue"
_CORRECT_MASTERY_CLAIM = "high_false_alarm_volume_has_a_real_cost_even_when_the_real_incident_is_eventually_caught"
_MASTERY_REQUIRED_EVIDENCE: tuple[str, ...] = ("false_alarm_avg_response_4_minutes", "real_incident_avg_response_360_minutes")


@dataclass(frozen=True)
class LessonTwentyFiveResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `initial_monitoring_choices` is the real, un-revised first pass -
    kept for transparency and for a real, non-scored recalibration
    observation. `monitoring_choices` is the FINAL, post-revision pass -
    both hold the FULL (metric_key, threshold_key) tuple per request, so
    the student's actual threshold pick is never lost from state even
    though METHOD reads only the metric component (see Conflict 1: tight
    and balanced are byte-identical for both real metrics in this
    dataset, so scoring threshold choice would mark an equivalent-
    outcome pick as wrong).

    `reveal_threshold_tradeoff_interpretation`/
    `reveal_incident_coverage_interpretation` are recorded for
    transparency only - never scored (zero InterpretOption.evidence_key
    anywhere: a student who picks the wrong interpretation of a reveal
    still saw the same real numbers and can cite them later)."""

    initial_monitoring_choices: MonitoringChoices
    monitoring_choices: MonitoringChoices
    reveal_threshold_tradeoff_interpretation: str | None
    reveal_incident_coverage_interpretation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return set(self.monitoring_choices) == set(CORRECT_METRIC_BY_REQUEST) and len(self.decision) > 0


def _all_metrics_correct(choices: MonitoringChoices) -> bool:
    return all(choices.get(key, ("", ""))[0] == correct_metric for key, correct_metric in CORRECT_METRIC_BY_REQUEST.items())


def _score_method(result: LessonTwentyFiveResult) -> tuple[float, FeedbackObservation | None]:
    """Two real, independent decisions - reads result.monitoring_choices
    only (the FINAL, post-revision pass), and only each request's own
    metric component (Conflict 1's resolution)."""
    hits = sum(
        result.monitoring_choices.get(key, ("", ""))[0] == correct_metric for key, correct_metric in CORRECT_METRIC_BY_REQUEST.items()
    )
    score = {2: 92.0, 1: 50.0, 0: 15.0}[hits]
    if hits < len(CORRECT_METRIC_BY_REQUEST):
        return score, FeedbackObservation("lesson.l25.feedback.metric_choice_not_defensible", ScoreDimension.METHOD)
    return score, None


def _reasoning_checks(result: LessonTwentyFiveResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("why_tight_threshold_creates_extra_false_alarms") == _CORRECT_THRESHOLD_TRADEOFF_REASON,
        dec.get("why_social_mentions_missed_both_observed_incidents") == _CORRECT_WRONG_METRIC_REASON,
        dec.get("what_an_alert_can_and_cant_tell_you") == _CORRECT_ALERT_LIMITS_REASON,
    )


def _score_reasoning(result: LessonTwentyFiveResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l25.feedback.why_tight_threshold_creates_extra_false_alarms_not_understood",
        "lesson.l25.feedback.why_social_mentions_missed_both_observed_incidents_not_understood",
        "lesson.l25.feedback.what_an_alert_can_and_cant_tell_you_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwentyFiveResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    threshold_tradeoff_role = all(key in present for key in THRESHOLD_TRADEOFF_KEYS)
    incident_coverage_role = all(key in present for key in INCIDENT_COVERAGE_KEYS)
    wrong_metric_silence_role = all(key in present for key in WRONG_METRIC_SILENCE_KEYS)
    roles_present = sum((threshold_tradeoff_role, incident_coverage_role, wrong_metric_silence_role))
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[roles_present]
    if roles_present < 3:
        return score, FeedbackObservation("lesson.l25.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_calibration(result: LessonTwentyFiveResult) -> tuple[float, FeedbackObservation | None]:
    """Reads `strongest_defensible_claim` only, matching every sibling's
    own precedent that this dimension doesn't require a before/after
    pair, only a single final-claim field."""
    claim = result.decision.get("strongest_defensible_claim")
    if claim == _CALIBRATED_CLAIM:
        return 92.0, None
    if claim == _OVERCLAIM:
        return 25.0, FeedbackObservation("lesson.l25.feedback.claim_overclaimed", ScoreDimension.OVERCONFIDENCE)
    if claim == _UNDERCLAIM:
        return 35.0, FeedbackObservation("lesson.l25.feedback.claim_underclaimed", ScoreDimension.OVERCONFIDENCE)
    return 15.0, FeedbackObservation("lesson.l25.feedback.claim_not_understood", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonTwentyFiveResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    first pass got at least one metric wrong but whose final (post-
    reveal, post-revision) pass is fully correct gets real recalibration
    credit - never a numeric bonus, just an additional observation."""
    initial_correct = _all_metrics_correct(result.initial_monitoring_choices)
    final_correct = _all_metrics_correct(result.monitoring_choices)
    if initial_correct or not final_correct:
        return None
    return FeedbackObservation("lesson.l25.feedback.metric_choice_recalibrated")


def _mastery_succeeded(result: LessonTwentyFiveResult) -> bool:
    what_correct = result.mastery_result.get("mastery_what_the_46_false_alarms_cost") == _CORRECT_MASTERY_WHAT_46_COST
    claim_correct = result.mastery_result.get("mastery_strongest_claim") == _CORRECT_MASTERY_CLAIM
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = all(key in supporting for key in _MASTERY_REQUIRED_EVIDENCE)
    return what_correct and claim_correct and both_facts_cited


def score_lesson_twenty_five(result: LessonTwentyFiveResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    calibration_score, calibration_observation = _score_calibration(result)

    dimension_scores = {
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.OVERCONFIDENCE: calibration_score,
    }

    observations = [
        observation
        for observation in (method_observation, reasoning_observation, evidence_observation, calibration_observation)
        if observation is not None
    ]
    recalibration = _recalibration_observation(result)
    if recalibration is not None:
        observations.append(recalibration)
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l25.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

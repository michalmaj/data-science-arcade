from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.correlation import CorrelationChoices
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.l26_correlation_crime_scene.requests import CORRECT_OPTION_BY_REQUEST

_CORRECT_WITHIN_MODERN_REASON = "isolates_whether_dark_mode_relates_to_spend_among_comparable_customers"
_CORRECT_ELIMINATION_REASON = "eliminating_one_explanation_narrows_the_space_it_doesnt_confirm_whats_left"
_CORRECT_ASSOCIATION_REASON = "establishes_a_strong_association_multiple_causal_stories_remain_compatible"
_CORRECT_NEXT_EVIDENCE = "a_randomized_test_or_ruling_out_alternatives"

_CALIBRATED_CLAIM = "a_real_pattern_not_a_proven_cause"
_OVERCLAIM = "direct_causation_confirmed_every_time"
_UNDERCLAIM = "correlation_this_strong_still_tells_us_nothing_useful"

# --- Evidence, claim-role-based over 5 real, unconditionally-recorded
# facts (never gated by which reveal interpretation a student picked) - 2
# roles, both fully required (no role needs partial-credit-within-role
# logic - each key plays a distinct, non-substitutable part of its own
# role's claim). ---------------------------------------------------------

PUSH_OPENS_CORRELATION_EVIDENCE_KEY = "lesson.l26.evidence.push_opens_correlation"
SHIPMENT_CORRELATION_EVIDENCE_KEY = "lesson.l26.evidence.shipment_correlation"
DARK_MODE_OVERALL_CORRELATION_EVIDENCE_KEY = "lesson.l26.evidence.dark_mode_overall_correlation"
DEVICE_GROUP_SPEND_CORRELATION_EVIDENCE_KEY = "lesson.l26.evidence.device_group_spend_correlation"
DARK_MODE_WITHIN_MODERN_CORRELATION_EVIDENCE_KEY = "lesson.l26.evidence.dark_mode_within_modern_correlation"

STRONG_ASSOCIATION_KEYS: tuple[str, ...] = (PUSH_OPENS_CORRELATION_EVIDENCE_KEY, SHIPMENT_CORRELATION_EVIDENCE_KEY)
"""Claim: the lesson contains genuine, quantitatively strong observed
associations - the causal ambiguity in this lesson is not caused by an
absence of association. Both facts are needed together: a single strong
correlation from one dataset doesn't defend a claim about the lesson's
observed associations generally, two independent ones do."""

CONFOUNDING_KEYS: tuple[str, ...] = (
    DARK_MODE_OVERALL_CORRELATION_EVIDENCE_KEY,
    DEVICE_GROUP_SPEND_CORRELATION_EVIDENCE_KEY,
    DARK_MODE_WITHIN_MODERN_CORRELATION_EVIDENCE_KEY,
)
"""Claim: the aggregate dark-mode/spend association is not stable within
the modern-device subgroup, and device_group is itself strongly
associated with spend - together that makes device_group an important
alternative explanation for the aggregate pattern, never a proven cause.
All three facts are needed together: the overall figure alone doesn't
show instability, the within-modern figure alone doesn't show device
group is a plausible rival, and device_group's own correlation alone
doesn't show the original pattern was affected by it at all."""

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (*STRONG_ASSOCIATION_KEYS, *CONFOUNDING_KEYS)


@dataclass(frozen=True)
class LessonTwentySixResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `initial_verdict_choices` is the real, un-revised first pass - kept
    for transparency and for a real, non-scored recalibration
    observation. `verdict_choices` is the FINAL, post-revision pass -
    METHOD reads this and only this: a student gets two real, mandatory
    reveals between the two passes and a real chance to act on them, so
    only what they finally commit to is graded.

    `reveal_strong_association_interpretation`/
    `reveal_confounding_interpretation` are recorded for transparency
    only - never scored (zero InterpretOption.evidence_key anywhere: a
    student who picks the wrong interpretation of a reveal still saw the
    same real numbers and can cite them later)."""

    initial_verdict_choices: CorrelationChoices
    verdict_choices: CorrelationChoices
    reveal_strong_association_interpretation: str | None
    reveal_confounding_interpretation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return set(self.verdict_choices) == set(CORRECT_OPTION_BY_REQUEST) and len(self.decision) > 0


def _all_verdicts_correct(choices: CorrelationChoices) -> bool:
    return all(choices.get(key) == correct for key, correct in CORRECT_OPTION_BY_REQUEST.items())


def _score_method(result: LessonTwentySixResult) -> tuple[float, FeedbackObservation | None]:
    """Three real, independent decisions - reads result.verdict_choices
    only (the FINAL, post-revision pass)."""
    hits = sum(result.verdict_choices.get(key) == correct for key, correct in CORRECT_OPTION_BY_REQUEST.items())
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[hits]
    if hits < len(CORRECT_OPTION_BY_REQUEST):
        return score, FeedbackObservation("lesson.l26.feedback.verdict_not_defensible", ScoreDimension.METHOD)
    return score, None


def _reasoning_checks(result: LessonTwentySixResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("why_the_within_modern_comparison_matters_more") == _CORRECT_WITHIN_MODERN_REASON,
        dec.get("why_ruling_out_reverse_causation_doesnt_prove_direct") == _CORRECT_ELIMINATION_REASON,
        dec.get("why_a_strong_observed_correlation_still_isnt_a_named_cause") == _CORRECT_ASSOCIATION_REASON,
        dec.get("next_evidence") == _CORRECT_NEXT_EVIDENCE,
    )


def _score_reasoning(result: LessonTwentySixResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {4: 95.0, 3: 76.0, 2: 55.0, 1: 32.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l26.feedback.why_the_within_modern_comparison_matters_more_not_understood",
        "lesson.l26.feedback.why_ruling_out_reverse_causation_doesnt_prove_direct_not_understood",
        "lesson.l26.feedback.why_a_strong_observed_correlation_still_isnt_a_named_cause_not_understood",
        "lesson.l26.feedback.next_evidence_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwentySixResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    strong_association_role = all(key in present for key in STRONG_ASSOCIATION_KEYS)
    confounding_role = all(key in present for key in CONFOUNDING_KEYS)
    roles_present = sum((strong_association_role, confounding_role))
    score = {2: 92.0, 1: 50.0, 0: 15.0}[roles_present]
    if roles_present < 2:
        return score, FeedbackObservation("lesson.l26.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_calibration(result: LessonTwentySixResult) -> tuple[float, FeedbackObservation | None]:
    """Reads `strongest_defensible_claim` only, matching every sibling's
    own precedent that this dimension doesn't require a before/after
    pair, only a single final-claim field."""
    claim = result.decision.get("strongest_defensible_claim")
    if claim == _CALIBRATED_CLAIM:
        return 92.0, None
    if claim == _OVERCLAIM:
        return 25.0, FeedbackObservation("lesson.l26.feedback.claim_overclaimed", ScoreDimension.OVERCONFIDENCE)
    if claim == _UNDERCLAIM:
        return 35.0, FeedbackObservation("lesson.l26.feedback.claim_underclaimed", ScoreDimension.OVERCONFIDENCE)
    return 15.0, FeedbackObservation("lesson.l26.feedback.claim_not_understood", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonTwentySixResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    first pass got at least one verdict wrong but whose final (post-
    reveal, post-revision) pass is fully correct gets real recalibration
    credit - never a numeric bonus, just an additional observation."""
    initial_correct = _all_verdicts_correct(result.initial_verdict_choices)
    final_correct = _all_verdicts_correct(result.verdict_choices)
    if initial_correct or not final_correct:
        return None
    return FeedbackObservation("lesson.l26.feedback.verdict_recalibrated")


def _mastery_succeeded(result: LessonTwentySixResult) -> bool:
    gap_correct = result.mastery_result.get("mastery_what_the_observational_gap_represents") == "overstates_what_the_experiment_attributes_to_the_program"
    claim_correct = result.mastery_result.get("mastery_strongest_claim") == "randomized_comparison_supports_a_much_smaller_positive_effect"
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = {"observational_gap_160_dollars", "randomized_estimate_15_dollars"} <= supporting
    return gap_correct and claim_correct and both_facts_cited


def score_lesson_twenty_six(result: LessonTwentySixResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l26.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

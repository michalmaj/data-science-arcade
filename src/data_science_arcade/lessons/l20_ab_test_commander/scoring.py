from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

# --- REASONING - 3 independent Final Decision Brief checks, all about the
# decision PROTOCOL, never about reading a single number. ----------------

_CORRECT_WHY_NOT_A_CLEAN_SHIP = "the_launch_rule_requires_every_guardrail_to_hold_too"
_CORRECT_WEEK3_STOPPING_JUDGMENT = "no_efficacy_stopping_rule_was_pre_specified"
_CORRECT_GENERAL_STOPPING_PRINCIPLE = "only_a_pre_specified_rule_efficacy_or_safety_justifies_acting_early"

# --- UNCERTAINTY - 2 independent checks about how the numbers moved -
# never a "true effect" claim (nobody observes a true effect; week 7 is a
# larger, more precise cumulative ESTIMATE, not revealed ground truth). --

_CORRECT_WEEK3_VS_WEEK7_EXPLANATION = "the_cumulative_estimate_moved_as_more_data_arrived_early_estimates_are_noisier"
_CORRECT_GUARDRAIL_VISIBILITY_EXPLANATION = (
    "the_support_harm_was_smaller_than_the_primary_lift_and_the_larger_sample_narrowed_its_interval_enough_to_clear_the_threshold"
)

# --- CALIBRATION (ScoreDimension.OVERCONFIDENCE - already displays as
# "Calibration"/"Kalibracja pewności" in both locales; no new enum member
# needed). Reads decision["final_verdict"] only. ------------------------

_CORRECT_FINAL_VERDICT = "hold_full_rollout_investigate_support_guardrail"
_PREMATURE_WEEK3_RECOMMENDATION = "ship_now"

# --- Evidence, role-based (never "any N of M"). The decision-protocol
# fact is recorded before any checkpoint data is shown (investigation
# stage); the week-3 tempting primary reading stays real, citable,
# genuinely OPTIONAL evidence - it does not substitute for the protocol
# role, exactly analogous to L17's "a result without timestamp/protocol
# provenance doesn't establish claim status." ----------------------------

DECISION_PROTOCOL_EVIDENCE_KEY = "lesson.l20.evidence.decision_protocol"
WEEK7_PRIMARY_PASS_EVIDENCE_KEY = "lesson.l20.evidence.week7_primary_pass"
SUPPORT_GUARDRAIL_BREACH_EVIDENCE_KEY = "lesson.l20.evidence.support_guardrail_breach"
REFUND_GUARDRAIL_CLEAN_EVIDENCE_KEY = "lesson.l20.evidence.refund_guardrail_clean"
WEEK3_PRIMARY_READING_EVIDENCE_KEY = "lesson.l20.evidence.week3_primary_reading"

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    DECISION_PROTOCOL_EVIDENCE_KEY,
    WEEK7_PRIMARY_PASS_EVIDENCE_KEY,
    SUPPORT_GUARDRAIL_BREACH_EVIDENCE_KEY,
    REFUND_GUARDRAIL_CLEAN_EVIDENCE_KEY,
)

# --- Mastery: NovaMart Logistics courier route-batching, a pre-specified
# SAFETY stopping rule genuinely met at its scheduled review. -----------

_CORRECT_MASTERY_STOPPING_JUDGMENT = "stop_now_pre_specified_safety_rule_is_met"
_CORRECT_MASTERY_CONTRAST = "a_safety_rule_was_pre_specified_here_efficacy_never_was_for_quickpay"
_MASTERY_REQUIRED_EVIDENCE = (
    "interim_ci_entirely_above_the_prespecified_1pp_threshold",
    "the_safety_rule_was_pre_specified_before_the_test_started",
)


@dataclass(frozen=True)
class LessonTwentyResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    No METHOD dimension: every student watches the identical, already-
    collected checkpoint data - there is no student-chosen execution act
    here the way L16's contract/L18's assignment/L19's weeks pick each
    were. `week1_recommendation`/`week3_recommendation` are the real
    trajectory a student leaned toward at each non-final checkpoint -
    kept for transparency and for CALIBRATION's own recalibration signal,
    but NEVER read by REASONING/EVIDENCE/UNCERTAINTY and never able to cap
    them: a patient student and a recalibrated one who both reach the
    correct final verdict score identically."""

    week1_recommendation: str | None
    week3_recommendation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return self.week3_recommendation is not None and len(self.decision) > 0


def _reasoning_checks(result: LessonTwentyResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("why_not_a_clean_ship") == _CORRECT_WHY_NOT_A_CLEAN_SHIP,
        dec.get("week3_stopping_rule_judgment") == _CORRECT_WEEK3_STOPPING_JUDGMENT,
        dec.get("general_stopping_principle") == _CORRECT_GENERAL_STOPPING_PRINCIPLE,
    )


def _score_reasoning(result: LessonTwentyResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {3: 95.0, 2: 70.0, 1: 45.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l20.feedback.why_not_a_clean_ship_not_understood",
        "lesson.l20.feedback.week3_stopping_rule_judgment_not_understood",
        "lesson.l20.feedback.general_stopping_principle_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _uncertainty_checks(result: LessonTwentyResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("what_explains_week3_vs_week7") == _CORRECT_WEEK3_VS_WEEK7_EXPLANATION,
        dec.get("why_guardrail_only_visible_at_week7") == _CORRECT_GUARDRAIL_VISIBILITY_EXPLANATION,
    )


def _score_uncertainty(result: LessonTwentyResult) -> tuple[float, FeedbackObservation | None]:
    checks = _uncertainty_checks(result)
    hits = sum(checks)
    score = {2: 92.0, 1: 50.0, 0: 15.0}[hits]
    if not checks[0]:
        return score, FeedbackObservation("lesson.l20.feedback.week3_vs_week7_explanation_not_understood", ScoreDimension.UNCERTAINTY)
    if not checks[1]:
        return score, FeedbackObservation("lesson.l20.feedback.guardrail_visibility_explanation_not_understood", ScoreDimension.UNCERTAINTY)
    return score, None


def _score_evidence(result: LessonTwentyResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(1 for key in CRITICAL_EVIDENCE_KEYS if key in present)
    score = {4: 95.0, 3: 74.0, 2: 50.0, 1: 25.0, 0: 10.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l20.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_calibration(result: LessonTwentyResult) -> tuple[float, FeedbackObservation | None]:
    """Reads decision['final_verdict'] only - structurally independent of
    week1_recommendation/week3_recommendation. A patient student and a
    recalibrated one (see _recalibration_observation) who both reach the
    correct verdict score identically here - patience is never scored
    lower than recalibration."""
    verdict = result.decision.get("final_verdict")
    if verdict == _CORRECT_FINAL_VERDICT:
        return 92.0, None
    if verdict == "ship_full_rollout_primary_passed":
        return 25.0, FeedbackObservation("lesson.l20.feedback.ignored_guardrail_breach", ScoreDimension.OVERCONFIDENCE)
    if verdict == "kill_the_feature_entirely":
        return 30.0, FeedbackObservation("lesson.l20.feedback.over_rejected_a_partial_result", ScoreDimension.OVERCONFIDENCE)
    return 35.0, FeedbackObservation("lesson.l20.feedback.treated_a_decided_result_as_inconclusive", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonTwentyResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    week-3 lean was premature ("ship now") but whose Final Decision
    Brief's own verdict correctly synthesizes the full week-7 picture gets
    real recalibration credit - never a numeric bonus (see
    _score_calibration's own docstring), just an additional observation."""
    if result.week3_recommendation != _PREMATURE_WEEK3_RECOMMENDATION:
        return None
    if result.decision.get("final_verdict") != _CORRECT_FINAL_VERDICT:
        return None
    return FeedbackObservation("lesson.l20.feedback.verdict_recalibrated")


def _mastery_succeeded(result: LessonTwentyResult) -> bool:
    """Transfer requires the correct stopping judgment (stop now - the
    pre-specified safety rule is genuinely met), the correct contrast with
    the main case (a safety rule was pre-specified here; an efficacy rule
    never was for Quick Pay - same underlying principle, opposite verdict),
    AND both real distinguishing facts cited as evidence."""
    judgment_correct = result.mastery_result.get("mastery_stopping_judgment") == _CORRECT_MASTERY_STOPPING_JUDGMENT
    contrast_correct = result.mastery_result.get("mastery_contrast_with_quickpay") == _CORRECT_MASTERY_CONTRAST
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = all(key in supporting for key in _MASTERY_REQUIRED_EVIDENCE)
    return judgment_correct and contrast_correct and both_facts_cited


def score_lesson_twenty(result: LessonTwentyResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    reasoning_score, reasoning_observation = _score_reasoning(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    evidence_score, evidence_observation = _score_evidence(result)
    calibration_score, calibration_observation = _score_calibration(result)

    dimension_scores = {
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.UNCERTAINTY: uncertainty_score,
        ScoreDimension.OVERCONFIDENCE: calibration_score,
    }

    observations = [
        observation
        for observation in (reasoning_observation, evidence_observation, uncertainty_observation, calibration_observation)
        if observation is not None
    ]
    recalibration = _recalibration_observation(result)
    if recalibration is not None:
        observations.append(recalibration)
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l20.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

# --- The 4 real, locked-plan fields METHOD scores - literal, hardcoded
# constants tied ONLY to the business ask, never derived from data.py's own
# computed rates (the exact class of hidden-coupling bug L16's own
# follow-up, PR #83, had to fix - the observed primary result also happens
# to be an increase, which must never be why "increase" counts as correct
# here). A dedicated regression test confirms this. -----------------------
_CORRECT_POPULATION = "all_eligible_returning_customers"
_CORRECT_OUTCOME = "repeat_purchase_14d"
_CORRECT_WINDOW = "fourteen_days"
_CORRECT_DIRECTION = "increase"

_CORRECT_DEVICE_STATUS = "exploratory_discovered_after_reveal"
_CORRECT_WHY_DIFFERS = "introduced_only_after_primary_result_visible"
_CORRECT_NEXT_STEP = "form_new_hypothesis_prespecify_test_on_new_data"

_CORRECT_PRIMARY_CLAIM = "observed_plus_one_pp_in_predicted_direction"
_CORRECT_DEVICE_CLAIM = "real_pattern_worth_a_new_pre_specified_test"

# Evidence, role-based (never "any N of M"). Every reveal's own
# InterpretOption tuple shares ONE evidence_key across all its options -
# "fact seen != correct interpretation" - except the provenance fact, which
# is a plain DialogueScene line (no interpretation to get right or wrong)
# and `plan_locked_before_results`, which the lock step itself records
# unconditionally, the same "a real fact recorded directly, not gated on an
# interpret pick" discipline `SegmentMixScene`/`MetricContractScene` use.
PLAN_LOCKED_EVIDENCE_KEY = "lesson.l17.evidence.plan_locked_before_results"
PRIMARY_RESULT_EVIDENCE_KEY = "lesson.l17.evidence.primary_observed_plus_one_pp"
DEVICE_PATTERN_EVIDENCE_KEY = "lesson.l17.evidence.device_pattern_diverges"
DEVICE_PROVENANCE_EVIDENCE_KEY = "lesson.l17.evidence.device_split_added_after_reveal"

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    PLAN_LOCKED_EVIDENCE_KEY,
    PRIMARY_RESULT_EVIDENCE_KEY,
    DEVICE_PATTERN_EVIDENCE_KEY,
    DEVICE_PROVENANCE_EVIDENCE_KEY,
)


@dataclass(frozen=True)
class LessonSeventeenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `hypothesis_plan` is the real FINAL LOCKED pre-data plan (after the one
    real, un-punished revision if the student took it) - METHOD scores
    this and only this, never the Final Hypothesis Brief's own later
    claims. This is the same METHOD-scores-execution/REASONING-scores-
    claims split every deepened lesson since L13's own follow-up has kept:
    a student can lock a perfect plan whose hypothesis the data then
    contradicts and still score METHOD high; a student whose eventual
    hypothesis happens to match the data while sitting on a badly
    specified (or silently rewritten) locked plan still scores METHOD low.
    Two dedicated regression tests confirm both directions explicitly."""

    hypothesis_plan: AnalyticalBrief
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return bool(self.hypothesis_plan) and len(self.decision) > 0


def _method_checks(result: LessonSeventeenResult) -> tuple[bool, ...]:
    plan = result.hypothesis_plan
    return (
        plan.get("target_population") == _CORRECT_POPULATION,
        plan.get("primary_outcome") == _CORRECT_OUTCOME,
        plan.get("observation_window") == _CORRECT_WINDOW,
        plan.get("predicted_direction") == _CORRECT_DIRECTION,
    )


def _score_method(result: LessonSeventeenResult) -> tuple[float, FeedbackObservation | None]:
    """4 real, independent checks against the LOCKED plan only - hit-
    banded, never binary. Structurally independent of any reveal outcome:
    this function never reads anything but `result.hypothesis_plan`."""
    checks = _method_checks(result)
    hits = sum(checks)
    score = {4: 95.0, 3: 78.0, 2: 58.0, 1: 36.0, 0: 15.0}[hits]
    if hits < 4:
        return score, FeedbackObservation("lesson.l17.feedback.plan_not_fully_specified", ScoreDimension.METHOD)
    return score, None


def _score_reasoning(result: LessonSeventeenResult) -> tuple[float, FeedbackObservation | None]:
    """3 independent Final Brief checks about the planned-vs-discovered
    distinction and what to do next - deliberately never re-checks the
    locked plan's own field values (that's METHOD's job, and Final Brief
    claims must never be able to retroactively fix or fake it)."""
    d = result.decision
    checks = (
        d.get("device_finding_status") == _CORRECT_DEVICE_STATUS,
        d.get("why_device_status_differs") == _CORRECT_WHY_DIFFERS,
        d.get("next_step") == _CORRECT_NEXT_STEP,
    )
    hits = sum(checks)
    score = {3: 95.0, 2: 70.0, 1: 42.0, 0: 12.0}[hits]
    if not checks[0]:
        return score, FeedbackObservation("lesson.l17.feedback.device_status_not_understood", ScoreDimension.REASONING)
    if not checks[1]:
        return score, FeedbackObservation("lesson.l17.feedback.why_differs_not_understood", ScoreDimension.REASONING)
    if not checks[2]:
        return score, FeedbackObservation("lesson.l17.feedback.next_step_not_understood", ScoreDimension.REASONING)
    return score, None


def _score_uncertainty(result: LessonSeventeenResult) -> tuple[float, FeedbackObservation | None]:
    """2 independent Final Brief checks, both about calibrated claim
    strength - does the student's own claim match what the evidence
    actually supports, never overclaiming and never dismissing it."""
    d = result.decision
    checks = (
        d.get("primary_result_claim") == _CORRECT_PRIMARY_CLAIM,
        d.get("strongest_defensible_device_claim") == _CORRECT_DEVICE_CLAIM,
    )
    hits = sum(checks)
    score = {2: 92.0, 1: 50.0, 0: 15.0}[hits]
    if not checks[0]:
        return score, FeedbackObservation("lesson.l17.feedback.primary_claim_not_calibrated", ScoreDimension.UNCERTAINTY)
    if not checks[1]:
        return score, FeedbackObservation("lesson.l17.feedback.device_claim_not_calibrated", ScoreDimension.UNCERTAINTY)
    return score, None


def _score_evidence(result: LessonSeventeenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(1 for key in CRITICAL_EVIDENCE_KEYS if key in present)
    score = {4: 95.0, 3: 74.0, 2: 50.0, 1: 25.0, 0: 10.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l17.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _mastery_succeeded(result: LessonSeventeenResult) -> bool:
    """Transfer requires BOTH the correct planned-result judgment (the
    pre-specified hypothesis was NOT borne out by the observed overall
    result) AND the real, distinguishing fact that the overall late rate
    itself increased - never accepting the tempting urban pattern alone as
    proof the hypothesis worked."""
    judgment_correct = result.mastery_result.get("mastery_route_judgment") == "not_borne_out_overall_late_rate_increased"
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    real_distinguishing_fact = "overall_late_rate_increased" in supporting
    return judgment_correct and real_distinguishing_fact


def score_lesson_seventeen(result: LessonSeventeenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    evidence_score, evidence_observation = _score_evidence(result)

    dimension_scores = {
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.UNCERTAINTY: uncertainty_score,
        ScoreDimension.EVIDENCE: evidence_score,
    }

    observations = [
        observation
        for observation in (method_observation, reasoning_observation, uncertainty_observation, evidence_observation)
        if observation is not None
    ]
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l17.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

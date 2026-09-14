from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.cohort import CohortChoices
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.l22_cohort_observatory.requests import CORRECT_OPTION_BY_REQUEST

_MAY_RETENTION_KEY = "may_retention_comparison"
_CORRECT_COMPARISON = CORRECT_OPTION_BY_REQUEST[_MAY_RETENTION_KEY]

_CORRECT_BUSINESS_QUESTION = "two_separate_questions_early_and_long_term"
_CORRECT_COMPARISON_BASIS = "same_month_across_cohorts"
_CORRECT_MAY_MONTH1_SUPPORT = "real_evidence_of_leading_early_retention_so_far"

_CORRECT_MONTH5_EVALUABLE = "no_data_doesnt_exist_yet"
_CORRECT_BLANK_CELL_MEANING = "cohort_hasnt_reached_that_month_yet"

_CALIBRATED_CLAIM = "strong_observed_month1_long_term_not_yet_observed"
_OVERCLAIM = "may_clearly_improved_retention_overall"
_UNDERCLAIM = "cant_say_anything_about_may_yet"

# --- Evidence, claim-role-based (never "any N of M", never interpretation-
# conditioned - a student who picks the WRONG interpretation of a reveal
# still saw the exact same real numbers and can cite them later; only
# METHOD/REASONING/CALIBRATION read the interpretation/decision fields
# themselves). 4 roles over 6 real, unconditionally-recorded facts - one
# key (JAN_MONTH1) legitimately double-duties across two roles, recorded
# once in the horizon reveal and re-affirmed under the same key in the
# reversal reveal (LessonContext.record_evidence's own update-by-key
# semantics - a no-op re-affirmation, not a duplicate pool entry). -------

MAY_MONTH1_EVIDENCE_KEY = "lesson.l22.evidence.may_month1"
JAN_MONTH1_EVIDENCE_KEY = "lesson.l22.evidence.jan_month1"
MAY_LATEST_OBSERVED_MONTH_EVIDENCE_KEY = "lesson.l22.evidence.may_latest_observed_month"
NOV_MONTH1_EVIDENCE_KEY = "lesson.l22.evidence.nov_month1"
NOV_MONTH5_EVIDENCE_KEY = "lesson.l22.evidence.nov_month5"
JAN_MONTH5_EVIDENCE_KEY = "lesson.l22.evidence.jan_month5"

EARLY_SAME_AGE_KEYS: tuple[str, ...] = (MAY_MONTH1_EVIDENCE_KEY, JAN_MONTH1_EVIDENCE_KEY)
HORIZON_AVAILABILITY_KEYS: tuple[str, ...] = (MAY_LATEST_OBSERVED_MONTH_EVIDENCE_KEY,)
RANKING_REVERSAL_KEYS: tuple[str, ...] = (
    NOV_MONTH1_EVIDENCE_KEY,
    JAN_MONTH1_EVIDENCE_KEY,
    NOV_MONTH5_EVIDENCE_KEY,
    JAN_MONTH5_EVIDENCE_KEY,
)
MISMATCHED_AGE_CONTRAST_KEYS: tuple[str, ...] = (MAY_MONTH1_EVIDENCE_KEY, JAN_MONTH5_EVIDENCE_KEY)

# Every individually-citable evidence key - used by scenario.py to detect
# which real facts a student selected. 6 entries, 4 scored roles.
CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    MAY_MONTH1_EVIDENCE_KEY,
    JAN_MONTH1_EVIDENCE_KEY,
    MAY_LATEST_OBSERVED_MONTH_EVIDENCE_KEY,
    NOV_MONTH1_EVIDENCE_KEY,
    NOV_MONTH5_EVIDENCE_KEY,
    JAN_MONTH5_EVIDENCE_KEY,
)

# --- Mastery: NovaMart Logistics courier week-1 activation, a different
# domain reproducing the same ranking-reversal + genuinely-unobserved-
# later shape with entirely different real numbers. ----------------------

_CORRECT_MASTERY_FAIR_COMPARISON = "compare_n_to_others_own_week1"
_CORRECT_MASTERY_CLAIM_STRENGTH = "n_strongest_observed_week1_week8_unknown"
_MASTERY_REQUIRED_EVIDENCE: tuple[str, ...] = ("n_week1_82_percent", "h_reversal_week1_78_vs_week8_44")


@dataclass(frozen=True)
class LessonTwentyTwoResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `initial_cohort_choices` is the real, un-revised first pass - kept for
    transparency and for a real, non-scored recalibration observation.
    `cohort_choices` is the FINAL, post-revision pass - METHOD reads this
    and only this: a student gets two real, mandatory reveals between the
    two passes and a real chance to act on them, so only what they
    finally commit to is graded.

    `reveal_horizon_interpretation`/`reveal_reversal_interpretation` are
    recorded for transparency only - never scored (see the module
    docstring above: the reveal's own real numbers stay citable as
    Evidence regardless of which interpretation a student first picks)."""

    initial_cohort_choices: CohortChoices
    cohort_choices: CohortChoices
    reveal_horizon_interpretation: str | None
    reveal_reversal_interpretation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return len(self.cohort_choices) == 1 and len(self.decision) > 0


def _score_method(result: LessonTwentyTwoResult) -> tuple[float, FeedbackObservation | None]:
    """One real decision, one right answer - reads result.cohort_choices
    only (the FINAL, post-revision pass), structurally independent of
    result.decision. Honestly binary: inventing a 3rd/4th option purely to
    manufacture a gradient would be the same false-gradient anti-pattern
    the local_bottleneck evidence fix (L21) already moved away from."""
    correct = result.cohort_choices.get(_MAY_RETENTION_KEY) == _CORRECT_COMPARISON
    if not correct:
        return 25.0, FeedbackObservation("lesson.l22.feedback.comparison_basis_not_defensible", ScoreDimension.METHOD)
    return 95.0, None


def _reasoning_checks(result: LessonTwentyTwoResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("business_question_horizon") == _CORRECT_BUSINESS_QUESTION,
        dec.get("correct_comparison_basis") == _CORRECT_COMPARISON_BASIS,
        dec.get("what_may_month1_supports") == _CORRECT_MAY_MONTH1_SUPPORT,
    )


def _score_reasoning(result: LessonTwentyTwoResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {3: 95.0, 2: 70.0, 1: 40.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l22.feedback.business_question_horizon_not_understood",
        "lesson.l22.feedback.correct_comparison_basis_not_understood",
        "lesson.l22.feedback.what_may_month1_supports_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _uncertainty_checks(result: LessonTwentyTwoResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("can_month5_be_evaluated") == _CORRECT_MONTH5_EVALUABLE,
        dec.get("blank_cell_meaning") == _CORRECT_BLANK_CELL_MEANING,
    )


def _score_uncertainty(result: LessonTwentyTwoResult) -> tuple[float, FeedbackObservation | None]:
    checks = _uncertainty_checks(result)
    hits = sum(checks)
    score = {2: 92.0, 1: 50.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l22.feedback.can_month5_be_evaluated_not_understood",
        "lesson.l22.feedback.blank_cell_meaning_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.UNCERTAINTY)
    return score, None


def _score_calibration(result: LessonTwentyTwoResult) -> tuple[float, FeedbackObservation | None]:
    """A genuinely separate failure mode from UNCERTAINTY: a student can
    correctly understand that month-5 isn't observed yet (UNCERTAINTY
    high) while still making an overclaim or underclaim about what May's
    real month-1 lead actually supports (CALIBRATION low) - reads
    `strongest_defensible_claim` only, never a before/after pair (neither
    L16's nor L20's own _score_overconfidence/_score_calibration require
    one either - both score a single final-claim field, with any
    before-pick powering only a separate, non-scoring recalibration
    observation, exactly like this lesson's own funnel_choices analog)."""
    claim = result.decision.get("strongest_defensible_claim")
    if claim == _CALIBRATED_CLAIM:
        return 92.0, None
    if claim == _OVERCLAIM:
        return 25.0, FeedbackObservation("lesson.l22.feedback.claim_overclaimed", ScoreDimension.OVERCONFIDENCE)
    if claim == _UNDERCLAIM:
        return 35.0, FeedbackObservation("lesson.l22.feedback.claim_underclaimed", ScoreDimension.OVERCONFIDENCE)
    return 15.0, FeedbackObservation("lesson.l22.feedback.claim_not_understood", ScoreDimension.OVERCONFIDENCE)


def _score_evidence(result: LessonTwentyTwoResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    early_same_age_role = all(key in present for key in EARLY_SAME_AGE_KEYS)
    horizon_availability_role = all(key in present for key in HORIZON_AVAILABILITY_KEYS)
    ranking_reversal_role = all(key in present for key in RANKING_REVERSAL_KEYS)
    mismatched_age_contrast_role = all(key in present for key in MISMATCHED_AGE_CONTRAST_KEYS)
    roles_present = sum((early_same_age_role, horizon_availability_role, ranking_reversal_role, mismatched_age_contrast_role))
    score = {4: 95.0, 3: 74.0, 2: 50.0, 1: 25.0, 0: 10.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l22.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _recalibration_observation(result: LessonTwentyTwoResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    first pass picked the mismatched comparison but whose final (post-
    reveal, post-revision) pass corrected it, gets real recalibration
    credit - never a numeric bonus, just an additional observation."""
    initial_correct = result.initial_cohort_choices.get(_MAY_RETENTION_KEY) == _CORRECT_COMPARISON
    final_correct = result.cohort_choices.get(_MAY_RETENTION_KEY) == _CORRECT_COMPARISON
    if initial_correct or not final_correct:
        return None
    return FeedbackObservation("lesson.l22.feedback.comparison_basis_recalibrated")


def _mastery_succeeded(result: LessonTwentyTwoResult) -> bool:
    fair_comparison_correct = result.mastery_result.get("mastery_fair_comparison") == _CORRECT_MASTERY_FAIR_COMPARISON
    claim_strength_correct = result.mastery_result.get("mastery_claim_strength") == _CORRECT_MASTERY_CLAIM_STRENGTH
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = all(key in supporting for key in _MASTERY_REQUIRED_EVIDENCE)
    return fair_comparison_correct and claim_strength_correct and both_facts_cited


def score_lesson_twenty_two(result: LessonTwentyTwoResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    calibration_score, calibration_observation = _score_calibration(result)

    dimension_scores = {
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.UNCERTAINTY: uncertainty_score,
        ScoreDimension.OVERCONFIDENCE: calibration_score,
    }

    observations = [
        observation
        for observation in (method_observation, reasoning_observation, evidence_observation, uncertainty_observation, calibration_observation)
        if observation is not None
    ]
    recalibration = _recalibration_observation(result)
    if recalibration is not None:
        observations.append(recalibration)
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l22.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

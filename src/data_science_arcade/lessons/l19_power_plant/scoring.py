from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.l19_power_plant import data as d

# --- METHOD - a real, literal 12-entry gradient over the FINAL EXECUTED
# plan only (result.final_weeks), never anything the Final Brief claims.
# A dict, not range/if-elif comparisons - eliminates tier-boundary
# off-by-one risk and is trivially exhaustively testable. 7 weeks is the
# first full week meeting the business's own +1.5pp sensitivity target
# and is never beaten by more weeks (the business ask is explicitly to
# find the SHORTEST adequate design, not just any adequate one); 8-12
# weeks are statistically adequate but cost more than needed - NEVER
# treated as a methodological error, just less efficient. --------------

METHOD_SCORE_BY_WEEKS = {
    1: 15.0,
    2: 15.0,
    3: 15.0,
    4: 35.0,
    5: 35.0,
    6: 55.0,
    7: 95.0,
    8: 80.0,
    9: 80.0,
    10: 80.0,
    11: 80.0,
    12: 80.0,
}

# --- REASONING - 4 independent Final Brief checks. Field #1's correct
# answer is a real per-playthrough value (whether result.final_weeks
# actually meets the sensitivity target), not a fixed constant. --------

_MEETS_TARGET_KEY = "meets_sensitivity_target"
_DOES_NOT_MEET_TARGET_KEY = "does_not_meet_sensitivity_target"
_CORRECT_SAMPLE_SIZE_EFFECT = "narrows_uncertainty_improves_sensitivity_not_effect_size"
_CORRECT_MDE_REPRESENTS = "design_stage_probability_not_post_hoc_cutoff"
_CORRECT_BUSINESS_VS_STATISTICAL = "answer_different_questions_not_interchangeable"

# --- UNCERTAINTY - 2 independent calibration-interpretation checks. ----

_CORRECT_UNDERPOWERED_INTERPRETATION = "inconclusive_neither_zero_nor_worthwhile_ruled_out"
_CORRECT_PRECISE_SMALL_EFFECT_INTERPRETATION = "precisely_estimated_small_effect_below_threshold"

# --- Evidence, role-based (never "any N of M"). The power-as-probability
# reveal's own two comparison values (4-week and 7-week detection rate)
# both become real, numbered EvidenceItems - only the 4-week one is a
# required role here (the "reference inadequate design" fact); the
# 7-week one stays real, citable, optional evidence. --------------------

FINAL_PLAN_SENSITIVITY_EVIDENCE_KEY = "lesson.l19.evidence.final_plan_sensitivity"
REFERENCE_INADEQUATE_DESIGN_EVIDENCE_KEY = "lesson.l19.evidence.reference_design_a_detection_rate"
UNDERPOWERED_CALIBRATION_EVIDENCE_KEY = "lesson.l19.evidence.underpowered_calibration_result"
PRECISE_TINY_EFFECT_EVIDENCE_KEY = "lesson.l19.evidence.precise_tiny_effect_calibration_result"

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    FINAL_PLAN_SENSITIVITY_EVIDENCE_KEY,
    REFERENCE_INADEQUATE_DESIGN_EVIDENCE_KEY,
    UNDERPOWERED_CALIBRATION_EVIDENCE_KEY,
    PRECISE_TINY_EFFECT_EVIDENCE_KEY,
)

# --- Mastery: NovaMart Logistics late-delivery reduction ---------------

_CORRECT_MASTERY_DESIGN_JUDGMENT = "inadequate_for_the_2pp_target"
_CORRECT_MASTERY_RESULT_INTERPRETATION = "inconclusive_neither_zero_nor_worthwhile_ruled_out"
_MASTERY_REQUIRED_EVIDENCE = ("design_inadequate_for_2pp_target", "wide_ci_crosses_zero_and_target")


@dataclass(frozen=True)
class LessonNineteenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `final_weeks` is the real FINAL value showing on the PowerPlannerScene
    at the moment Confirm was pressed (after the one real, un-punished
    revision if the student moved the stepper) - METHOD scores this and
    only this, never the Final Power Brief's own later claims.
    `cold_duration_pick` is kept for transparency (mirrors L18's own
    unused `initial_design`) but never read by scoring."""

    cold_duration_pick: int
    final_weeks: int
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return self.final_weeks > 0 and len(self.decision) > 0


def _score_method(result: LessonNineteenResult) -> tuple[float, FeedbackObservation | None]:
    """Reads result.final_weeks only - structurally independent of
    result.decision, the same METHOD-scores-execution invariant every
    deepened lesson since L13's own follow-up has kept. Weeks 8-12 get no
    corrective observation - they're genuinely adequate, never framed as
    a mistake, just less efficient than necessary."""
    score = METHOD_SCORE_BY_WEEKS[result.final_weeks]
    if not d.meets_sensitivity_target(result.final_weeks):
        return score, FeedbackObservation("lesson.l19.feedback.design_below_sensitivity_target", ScoreDimension.METHOD)
    return score, None


def _reasoning_checks(result: LessonNineteenResult) -> tuple[bool, ...]:
    dec = result.decision
    correct_classification = _MEETS_TARGET_KEY if d.meets_sensitivity_target(result.final_weeks) else _DOES_NOT_MEET_TARGET_KEY
    return (
        dec.get("final_design_meets_sensitivity_target") == correct_classification,
        dec.get("what_more_sample_size_changes") == _CORRECT_SAMPLE_SIZE_EFFECT,
        dec.get("what_mde_represents") == _CORRECT_MDE_REPRESENTS,
        dec.get("business_vs_statistical_detectability") == _CORRECT_BUSINESS_VS_STATISTICAL,
    )


def _score_reasoning(result: LessonNineteenResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {4: 95.0, 3: 78.0, 2: 55.0, 1: 30.0, 0: 12.0}[hits]
    feedback_keys = (
        "lesson.l19.feedback.final_design_classification_not_understood",
        "lesson.l19.feedback.sample_size_effect_not_understood",
        "lesson.l19.feedback.mde_meaning_not_understood",
        "lesson.l19.feedback.business_vs_statistical_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _uncertainty_checks(result: LessonNineteenResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("underpowered_result_interpretation") == _CORRECT_UNDERPOWERED_INTERPRETATION,
        dec.get("precise_small_effect_interpretation") == _CORRECT_PRECISE_SMALL_EFFECT_INTERPRETATION,
    )


def _score_uncertainty(result: LessonNineteenResult) -> tuple[float, FeedbackObservation | None]:
    checks = _uncertainty_checks(result)
    hits = sum(checks)
    score = {2: 92.0, 1: 50.0, 0: 15.0}[hits]
    if not checks[0]:
        return score, FeedbackObservation("lesson.l19.feedback.underpowered_interpretation_not_calibrated", ScoreDimension.UNCERTAINTY)
    if not checks[1]:
        return score, FeedbackObservation("lesson.l19.feedback.precise_small_effect_interpretation_not_calibrated", ScoreDimension.UNCERTAINTY)
    return score, None


def _score_evidence(result: LessonNineteenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(1 for key in CRITICAL_EVIDENCE_KEYS if key in present)
    score = {4: 95.0, 3: 74.0, 2: 50.0, 1: 25.0, 0: 10.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l19.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _mastery_succeeded(result: LessonNineteenResult) -> bool:
    """Transfer requires the correct design-adequacy judgment (the
    actually-used 4-week design was NOT adequately powered for the real
    2.0pp target), the correct treatment of the result's own uncertainty
    (inconclusive, not "no effect"), AND both real distinguishing facts
    cited as evidence - never accepting a correct judgment alone without
    the facts that actually ground it."""
    judgment_correct = result.mastery_result.get("mastery_design_judgment") == _CORRECT_MASTERY_DESIGN_JUDGMENT
    interpretation_correct = result.mastery_result.get("mastery_result_interpretation") == _CORRECT_MASTERY_RESULT_INTERPRETATION
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = all(key in supporting for key in _MASTERY_REQUIRED_EVIDENCE)
    return judgment_correct and interpretation_correct and both_facts_cited


def score_lesson_nineteen(result: LessonNineteenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l19.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

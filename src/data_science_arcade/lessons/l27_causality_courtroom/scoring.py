from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.correlation import CorrelationChoices
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.l27_causality_courtroom.requests import CORRECT_OPTION_BY_REQUEST

_CORRECT_WHY_NON_RANDOM = "people_or_processes_that_land_in_a_group_may_already_differ_before_anything_happens"
_OVERCLAIM_WHY_NON_RANDOM = "a_correlation_this_strong_can_only_be_the_treatment"
_DISTRACTOR_WHY_NON_RANDOM = "the_groups_use_different_outcome_scales"

_CORRECT_RIGHT_REASON = "misdiagnosing_the_mechanism_can_miss_the_real_problem_even_when_the_verdict_is_right"
_DISTRACTOR_RIGHT_REASON_A = "any_skepticism_works_as_long_as_the_final_call_is_right"
_DISTRACTOR_RIGHT_REASON_B = "the_reasoning_behind_a_sustained_objection_doesnt_need_recording"

_CORRECT_MISSING_EVIDENCE = "a_design_that_breaks_the_link_between_pre_existing_type_and_the_exposure_being_compared"
_DISTRACTOR_MISSING_EVIDENCE_A = "more_of_the_same_observational_data"
_DISTRACTOR_MISSING_EVIDENCE_B = "ask_the_self_selected_group"

_CORRECT_RANDOMIZATION_CHANGES = "breaks_the_link_between_pre_existing_type_and_assigned_condition_in_expectation"
_OVERCLAIM_RANDOMIZATION_CHANGES = "randomization_removes_all_bias_completely_and_forever"
_DENIAL_RANDOMIZATION_CHANGES = "randomization_doesnt_actually_change_the_comparison"

_CALIBRATED_VERDICT = "each_needs_a_proper_comparison_group"
_OVERCLAIM_VERDICT = "all_confirmed_effects_too_large_for_chance"
_UNDERCLAIM_VERDICT = "all_should_be_thrown_out"

# --- Evidence, claim-role-based over 5 real, unconditionally-recorded
# facts (never gated by which reveal interpretation a student picked) - 2
# roles, both fully required. -------------------------------------------

TOOL_SPEND_DIFFERENCE_EVIDENCE_KEY = "lesson.l27.evidence.tool_spend_difference"
RESOLUTION_SATISFACTION_DIFFERENCE_EVIDENCE_KEY = "lesson.l27.evidence.resolution_satisfaction_difference"
TRAINING_PERFORMANCE_DIFFERENCE_EVIDENCE_KEY = "lesson.l27.evidence.training_performance_difference"
CHECKOUT_BETA_OBSERVATIONAL_GAP_EVIDENCE_KEY = "lesson.l27.evidence.checkout_beta_observational_gap"
CHECKOUT_BETA_RANDOMIZED_GAP_EVIDENCE_KEY = "lesson.l27.evidence.checkout_beta_randomized_gap"

OBSERVED_DIFFERENCE_KEYS: tuple[str, ...] = (
    TOOL_SPEND_DIFFERENCE_EVIDENCE_KEY,
    RESOLUTION_SATISFACTION_DIFFERENCE_EVIDENCE_KEY,
    TRAINING_PERFORMANCE_DIFFERENCE_EVIDENCE_KEY,
)
"""Claim: each case has a real, business-interpretable observed
difference worth investigating - none of the three alone defends this
claim generally, all three genuinely distinct cases are needed together."""

RANDOMIZED_COMPARISON_KEYS: tuple[str, ...] = (
    CHECKOUT_BETA_OBSERVATIONAL_GAP_EVIDENCE_KEY,
    CHECKOUT_BETA_RANDOMIZED_GAP_EVIDENCE_KEY,
)
"""Claim: the observational comparison substantially overstated what the
randomized comparison estimates - the randomized number alone doesn't
defend this without the observational number to compare it against, and
vice versa."""

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (*OBSERVED_DIFFERENCE_KEYS, *RANDOMIZED_COMPARISON_KEYS)


@dataclass(frozen=True)
class LessonTwentySevenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `initial_verdict_choices` is the real, un-revised first pass, kept for
    transparency and a real, non-scored recalibration observation.
    `verdict_choices` is the FINAL, post-revision pass - METHOD reads this
    and only this.

    `reveal_observed_difference_interpretation`/
    `reveal_randomization_interpretation` are recorded for transparency
    only - never scored (zero InterpretOption.evidence_key anywhere)."""

    initial_verdict_choices: CorrelationChoices
    verdict_choices: CorrelationChoices
    reveal_observed_difference_interpretation: str | None
    reveal_randomization_interpretation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return set(self.verdict_choices) == set(CORRECT_OPTION_BY_REQUEST) and len(self.decision) > 0


def _all_verdicts_correct(choices: CorrelationChoices) -> bool:
    return all(choices.get(key) == correct for key, correct in CORRECT_OPTION_BY_REQUEST.items())


def _score_method(result: LessonTwentySevenResult) -> tuple[float, FeedbackObservation | None]:
    """Three real, independent decisions - reads result.verdict_choices
    only (the FINAL, post-revision pass)."""
    hits = sum(result.verdict_choices.get(key) == correct for key, correct in CORRECT_OPTION_BY_REQUEST.items())
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[hits]
    if hits < len(CORRECT_OPTION_BY_REQUEST):
        return score, FeedbackObservation("lesson.l27.feedback.verdict_not_defensible", ScoreDimension.METHOD)
    return score, None


def _reasoning_checks(result: LessonTwentySevenResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("why_non_random_group_formation_undermines_a_comparison") == _CORRECT_WHY_NON_RANDOM,
        dec.get("why_the_right_verdict_still_needs_the_right_reason") == _CORRECT_RIGHT_REASON,
        dec.get("missing_evidence") == _CORRECT_MISSING_EVIDENCE,
        dec.get("what_randomization_changes") == _CORRECT_RANDOMIZATION_CHANGES,
    )


def _score_reasoning(result: LessonTwentySevenResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {4: 95.0, 3: 76.0, 2: 55.0, 1: 32.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l27.feedback.why_non_random_group_formation_undermines_a_comparison_not_understood",
        "lesson.l27.feedback.why_the_right_verdict_still_needs_the_right_reason_not_understood",
        "lesson.l27.feedback.missing_evidence_not_understood",
        "lesson.l27.feedback.what_randomization_changes_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwentySevenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    observed_difference_role = all(key in present for key in OBSERVED_DIFFERENCE_KEYS)
    randomized_comparison_role = all(key in present for key in RANDOMIZED_COMPARISON_KEYS)
    roles_present = sum((observed_difference_role, randomized_comparison_role))
    score = {2: 92.0, 1: 50.0, 0: 15.0}[roles_present]
    if roles_present < 2:
        return score, FeedbackObservation("lesson.l27.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_calibration(result: LessonTwentySevenResult) -> tuple[float, FeedbackObservation | None]:
    """Reads `final_verdict` only, matching every sibling's own precedent
    that this dimension doesn't require a before/after pair, only a
    single final-claim field."""
    verdict = result.decision.get("final_verdict")
    if verdict == _CALIBRATED_VERDICT:
        return 92.0, None
    if verdict == _OVERCLAIM_VERDICT:
        return 25.0, FeedbackObservation("lesson.l27.feedback.verdict_overclaimed", ScoreDimension.OVERCONFIDENCE)
    if verdict == _UNDERCLAIM_VERDICT:
        return 35.0, FeedbackObservation("lesson.l27.feedback.verdict_underclaimed", ScoreDimension.OVERCONFIDENCE)
    return 15.0, FeedbackObservation("lesson.l27.feedback.verdict_not_understood", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonTwentySevenResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    first pass got at least one verdict wrong but whose final (post-
    reveal, post-revision) pass is fully correct gets real recalibration
    credit - never a numeric bonus, just an additional observation."""
    initial_correct = _all_verdicts_correct(result.initial_verdict_choices)
    final_correct = _all_verdicts_correct(result.verdict_choices)
    if initial_correct or not final_correct:
        return None
    return FeedbackObservation("lesson.l27.feedback.verdict_recalibrated")


def _mastery_succeeded(result: LessonTwentySevenResult) -> bool:
    naive_correct = (
        result.mastery_result.get("mastery_what_the_naive_comparison_shows")
        == "reflects_both_a_possible_effect_and_pre_existing_differences_between_who_opted_in_and_who_didnt"
    )
    claim_correct = (
        result.mastery_result.get("mastery_strongest_claim")
        == "the_randomized_test_estimates_a_much_smaller_effect_than_the_naive_comparison_suggested"
    )
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = {"naive_gap_37_points", "randomized_estimate_5_points"} <= supporting
    return naive_correct and claim_correct and both_facts_cited


def score_lesson_twenty_seven(result: LessonTwentySevenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l27.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

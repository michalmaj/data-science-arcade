from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.chart import ChartChoices
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.l28_chart_crime_lab.requests import CORRECT_OPTION_BY_REQUEST

_CORRECT_AXIS = "same_data_difference_occupies_more_visual_space_when_the_baseline_is_truncated"
_OVERCLAIM_AXIS = "any_non_zero_baseline_chart_is_automatically_dishonest"
_DISTRACTOR_AXIS = "the_underlying_numbers_must_have_been_altered"

_CORRECT_WINDOW = "a_short_window_can_omit_material_context_the_full_period_would_show"
_OVERCLAIM_WINDOW = "any_partial_window_is_invalid_only_full_history_is_honest"
_DISTRACTOR_WINDOW = "averaging_over_more_time_always_gives_the_one_true_number"

_CORRECT_DENOMINATOR = "the_denominator_must_match_the_population_the_question_implies"
_OVERCLAIM_DENOMINATOR = "any_rate_built_on_a_large_denominator_is_automatically_suspect"
_DISTRACTOR_DENOMINATOR = "percentages_are_inherently_less_trustworthy_than_raw_counts"

_CORRECT_DUAL_AXIS = "independent_axis_scaling_can_make_different_relative_changes_look_comparable"
_OVERCLAIM_DUAL_AXIS = "dual_axis_charts_are_never_a_legitimate_choice"
_DISTRACTOR_DUAL_AXIS = "as_long_as_both_lines_are_correctly_plotted_the_chart_is_honest"

_CALIBRATED_STANDARD = "check_both_the_real_numbers_and_the_real_presentation"
_OVERCLAIM_STANDARD = "any_chart_using_a_design_choice_like_axis_window_or_dual_axis_is_automatically_suspect"
_UNDERCLAIM_STANDARD = "if_the_underlying_numbers_are_accurate_the_chart_cannot_mislead"

# --- Evidence, claim-role-based over 9 real, unconditionally-recorded
# facts - 4 roles, one per real manipulation mechanism, all fully
# required within their own role. Never merged into one all-or-nothing
# role: axis truncation, cherry-picking, the wrong denominator, and
# dual-axis scaling are four genuinely separate claims, matching the
# Final Brief's own four separate REASONING fields. -----------------------

SATISFACTION_DATA_GAP_EVIDENCE_KEY = "lesson.l28.evidence.satisfaction_data_gap"
SATISFACTION_VISUAL_AMPLIFICATION_EVIDENCE_KEY = "lesson.l28.evidence.satisfaction_visual_amplification"
ACTIVE_USERS_FULL_PERIOD_CHANGE_EVIDENCE_KEY = "lesson.l28.evidence.active_users_full_period_change"
ACTIVE_USERS_LAST_TWO_MONTHS_CHANGE_EVIDENCE_KEY = "lesson.l28.evidence.active_users_last_two_months_change"
ACTIVE_USERS_FIRST_TWO_MONTHS_CHANGE_EVIDENCE_KEY = "lesson.l28.evidence.active_users_first_two_months_change"
RETURNS_FAIR_RATE_MINIMUM_QUARTER_EVIDENCE_KEY = "lesson.l28.evidence.returns_fair_rate_minimum_quarter"
RETURNS_FLAWED_RATE_MINIMUM_QUARTER_EVIDENCE_KEY = "lesson.l28.evidence.returns_flawed_rate_minimum_quarter"
MARKETING_SPEND_CHANGE_EVIDENCE_KEY = "lesson.l28.evidence.marketing_spend_change"
SIGNUPS_CHANGE_EVIDENCE_KEY = "lesson.l28.evidence.signups_change"

AXIS_SCALE_KEYS: tuple[str, ...] = (SATISFACTION_DATA_GAP_EVIDENCE_KEY, SATISFACTION_VISUAL_AMPLIFICATION_EVIDENCE_KEY)
"""Claim: the same real 3-point satisfaction gap occupies far more of the
chart's own vertical plotting space once the baseline is truncated. The
raw gap alone doesn't show the visual effect; the amplification ratio
alone doesn't show what real gap it's amplifying - both are needed."""

WINDOW_CONTEXT_KEYS: tuple[str, ...] = (
    ACTIVE_USERS_FULL_PERIOD_CHANGE_EVIDENCE_KEY,
    ACTIVE_USERS_LAST_TWO_MONTHS_CHANGE_EVIDENCE_KEY,
    ACTIVE_USERS_FIRST_TWO_MONTHS_CHANGE_EVIDENCE_KEY,
)
"""Claim: the same 12-month dataset supports very different-looking
endpoint stories depending on which window is chosen. No single window's
own number defends this - the claim is about the three genuinely
competing stories existing together."""

DENOMINATOR_KEYS: tuple[str, ...] = (RETURNS_FAIR_RATE_MINIMUM_QUARTER_EVIDENCE_KEY, RETURNS_FLAWED_RATE_MINIMUM_QUARTER_EVIDENCE_KEY)
"""Claim: changing the denominator doesn't just rescale the returns rate,
it changes which quarter looks best - the fair rate's own minimum (Q3)
and the flawed rate's own minimum (Q1) are needed together to show the
ranking itself changed, not just the numbers' size."""

DUAL_AXIS_KEYS: tuple[str, ...] = (MARKETING_SPEND_CHANGE_EVIDENCE_KEY, SIGNUPS_CHANGE_EVIDENCE_KEY)
"""Claim: the dual-axis chart's own visual similarity does not reflect
comparable real percent growth. Neither percent change alone defends
the mismatch - only the pair, side by side, does."""

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (*AXIS_SCALE_KEYS, *WINDOW_CONTEXT_KEYS, *DENOMINATOR_KEYS, *DUAL_AXIS_KEYS)


@dataclass(frozen=True)
class LessonTwentyEightResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `initial_verdict_choices` is the real, un-revised first pass, kept
    for transparency and a real, non-scored recalibration observation.
    `verdict_choices` is the FINAL, post-revision pass - METHOD reads
    this and only this.

    The four reveal interpretations are recorded for transparency only
    - never scored (zero InterpretOption.evidence_key anywhere). Four
    separate reveals, not one merged reveal per mechanism-pair: a single
    `ComparisonRevealScene` showing all 5 axis+window ComparisonValues
    together overflowed its own fixed layout (confirmed by direct
    measurement) - splitting one reveal per real mechanism fixed that and
    kept each reveal focused on one claim, at the cost of two extra
    stages (accounted for in `estimated_minutes`)."""

    initial_verdict_choices: ChartChoices
    verdict_choices: ChartChoices
    reveal_axis_interpretation: str | None
    reveal_window_interpretation: str | None
    reveal_denominator_interpretation: str | None
    reveal_dual_axis_interpretation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return set(self.verdict_choices) == set(CORRECT_OPTION_BY_REQUEST) and len(self.decision) > 0


def _all_verdicts_correct(choices: ChartChoices) -> bool:
    return all(choices.get(key) == correct for key, correct in CORRECT_OPTION_BY_REQUEST.items())


def _score_method(result: LessonTwentyEightResult) -> tuple[float, FeedbackObservation | None]:
    """Three real, independent decisions - reads result.verdict_choices
    only (the FINAL, post-revision pass)."""
    hits = sum(result.verdict_choices.get(key) == correct for key, correct in CORRECT_OPTION_BY_REQUEST.items())
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[hits]
    if hits < len(CORRECT_OPTION_BY_REQUEST):
        return score, FeedbackObservation("lesson.l28.feedback.pick_not_defensible", ScoreDimension.METHOD)
    return score, None


def _reasoning_checks(result: LessonTwentyEightResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("why_a_truncated_axis_misleads") == _CORRECT_AXIS,
        dec.get("why_cherry_picking_misleads") == _CORRECT_WINDOW,
        dec.get("why_the_wrong_denominator_misleads") == _CORRECT_DENOMINATOR,
        dec.get("why_a_truthful_chart_can_still_mislead") == _CORRECT_DUAL_AXIS,
    )


def _score_reasoning(result: LessonTwentyEightResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {4: 95.0, 3: 76.0, 2: 55.0, 1: 32.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l28.feedback.why_a_truncated_axis_misleads_not_understood",
        "lesson.l28.feedback.why_cherry_picking_misleads_not_understood",
        "lesson.l28.feedback.why_the_wrong_denominator_misleads_not_understood",
        "lesson.l28.feedback.why_a_truthful_chart_can_still_mislead_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwentyEightResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(
        all(key in present for key in role) for role in (AXIS_SCALE_KEYS, WINDOW_CONTEXT_KEYS, DENOMINATOR_KEYS, DUAL_AXIS_KEYS)
    )
    score = {4: 95.0, 3: 76.0, 2: 55.0, 1: 32.0, 0: 15.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l28.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_calibration(result: LessonTwentyEightResult) -> tuple[float, FeedbackObservation | None]:
    """Reads `chart_review_standard` only, matching every sibling's own
    precedent that this dimension doesn't require a before/after pair,
    only a single final-claim field."""
    standard = result.decision.get("chart_review_standard")
    if standard == _CALIBRATED_STANDARD:
        return 92.0, None
    if standard == _OVERCLAIM_STANDARD:
        return 25.0, FeedbackObservation("lesson.l28.feedback.standard_overclaimed", ScoreDimension.OVERCONFIDENCE)
    if standard == _UNDERCLAIM_STANDARD:
        return 35.0, FeedbackObservation("lesson.l28.feedback.standard_underclaimed", ScoreDimension.OVERCONFIDENCE)
    return 15.0, FeedbackObservation("lesson.l28.feedback.standard_not_understood", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonTwentyEightResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    first pass got at least one pick wrong but whose final (post-reveal,
    post-revision) pass is fully correct gets real recalibration credit -
    never a numeric bonus, just an additional observation."""
    initial_correct = _all_verdicts_correct(result.initial_verdict_choices)
    final_correct = _all_verdicts_correct(result.verdict_choices)
    if initial_correct or not final_correct:
        return None
    return FeedbackObservation("lesson.l28.feedback.pick_recalibrated")


def _mastery_succeeded(result: LessonTwentyEightResult) -> bool:
    flawed_correct = (
        result.mastery_result.get("mastery_what_the_flawed_rate_shows")
        == "a_mathematically_real_rate_but_not_the_right_denominator_for_the_question"
    )
    claim_correct = (
        result.mastery_result.get("mastery_strongest_claim")
        == "the_correctly_denominated_rate_is_the_relevant_rate_for_this_question"
    )
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = {"fair_rate_q3_low_point", "flawed_rate_q4_low_point"} <= supporting
    return flawed_correct and claim_correct and both_facts_cited


def score_lesson_twenty_eight(result: LessonTwentyEightResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l28.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

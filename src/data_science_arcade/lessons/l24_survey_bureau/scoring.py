from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.survey import SurveyChoices
from data_science_arcade.lessons.l24_survey_bureau.requests import CORRECT_COMBO_BY_REQUEST

_GENERAL_CHECK_KEY = "general_satisfaction_check"
_CORRECT_COMBO = CORRECT_COMBO_BY_REQUEST[_GENERAL_CHECK_KEY]

_CORRECT_IN_APP_POPUP_REASON = "excludes_customers_who_already_churned"
_CORRECT_POWER_USER_PANEL_REASON = "sampling_frame_excludes_critics_entirely"
_CORRECT_WORDING_REASON = "systematically_pushes_satisfaction_upward_never_fixes_reach_or_response"
_CORRECT_STILL_CANT_FIX_REASON = "who_actually_responds_can_still_be_uneven_even_with_full_reach_and_neutral_wording"

_CALIBRATED_CLAIM = "most_defensible_design_but_still_a_signal_not_proof_of_everyone"
_OVERCLAIM = "accurately_represents_all_customers"
_UNDERCLAIM = "tells_us_nothing_useful"

# --- Evidence, claim-role-based over 8 real, unconditionally-recorded
# facts (never gated by which reveal interpretation a student picked) - 3
# roles, none a strict subset of another. `coverage_bias_role` and
# `sampling_frame_role` are two genuinely different mechanisms - a channel
# that can never reach a group at all (coverage) is not the same failure
# as a channel whose own reachable population skews toward one segment
# (sampling frame) - so power_user_panel's own bias is never labeled or
# scored as "self-selection"/nonresponse; it has zero respondents from
# vocal_critic because the panel's own frame excludes them structurally,
# before response even enters the picture. `nonresponse_bias_role` is the
# third, separate mechanism: even a channel with NO reach restriction
# still sees wildly different response rates by segment. -----------------

BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY = "lesson.l24.evidence.broad_email_neutral_mean"
IN_APP_POPUP_NEUTRAL_MEAN_EVIDENCE_KEY = "lesson.l24.evidence.in_app_popup_neutral_mean"
IN_APP_POPUP_EXCLUDED_CHURNED_COUNT_EVIDENCE_KEY = "lesson.l24.evidence.in_app_popup_excluded_churned_count"
POWER_USER_PANEL_NEUTRAL_MEAN_EVIDENCE_KEY = "lesson.l24.evidence.power_user_panel_neutral_mean"
POWER_USER_PANEL_CRITIC_COUNT_EVIDENCE_KEY = "lesson.l24.evidence.power_user_panel_critic_count"
VOCAL_CRITIC_RESPONSE_RATE_EVIDENCE_KEY = "lesson.l24.evidence.vocal_critic_response_rate"
VOCAL_FAN_RESPONSE_RATE_EVIDENCE_KEY = "lesson.l24.evidence.vocal_fan_response_rate"
QUIET_MAJORITY_RESPONSE_RATE_EVIDENCE_KEY = "lesson.l24.evidence.quiet_majority_response_rate"

COVERAGE_BIAS_KEYS: tuple[str, ...] = (
    BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY,
    IN_APP_POPUP_NEUTRAL_MEAN_EVIDENCE_KEY,
    IN_APP_POPUP_EXCLUDED_CHURNED_COUNT_EVIDENCE_KEY,
)
SAMPLING_FRAME_KEYS: tuple[str, ...] = (
    BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY,
    POWER_USER_PANEL_NEUTRAL_MEAN_EVIDENCE_KEY,
    POWER_USER_PANEL_CRITIC_COUNT_EVIDENCE_KEY,
)
NONRESPONSE_BIAS_KEYS: tuple[str, ...] = (
    VOCAL_CRITIC_RESPONSE_RATE_EVIDENCE_KEY,
    VOCAL_FAN_RESPONSE_RATE_EVIDENCE_KEY,
    QUIET_MAJORITY_RESPONSE_RATE_EVIDENCE_KEY,
)

# Every individually-citable evidence key - used by scenario.py to detect
# which real facts a student selected. 8 entries, 3 scored roles.
CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY,
    IN_APP_POPUP_NEUTRAL_MEAN_EVIDENCE_KEY,
    IN_APP_POPUP_EXCLUDED_CHURNED_COUNT_EVIDENCE_KEY,
    POWER_USER_PANEL_NEUTRAL_MEAN_EVIDENCE_KEY,
    POWER_USER_PANEL_CRITIC_COUNT_EVIDENCE_KEY,
    VOCAL_CRITIC_RESPONSE_RATE_EVIDENCE_KEY,
    VOCAL_FAN_RESPONSE_RATE_EVIDENCE_KEY,
    QUIET_MAJORITY_RESPONSE_RATE_EVIDENCE_KEY,
)

# --- Mastery: NovaMart delivery-survey coverage exclusion, a different
# domain. Provenance stays explicit throughout: the 150 never-surveyed
# customers' own 20% figure is a SEPARATE support-ticket measure, never
# something they themselves answered in this survey. -----------------

_CORRECT_MASTERY_WHAT_88_REPRESENTS = "only_customers_whose_delivery_succeeded"
_CORRECT_MASTERY_WHY_BLENDED_IS_LOWER = "never_surveyed_group_has_a_separate_source_estimate"
_MASTERY_REQUIRED_EVIDENCE: tuple[str, ...] = (
    "delivery_succeeded_surveyed_88_percent",
    "delivery_failed_or_delayed_separate_source_20_percent",
)


@dataclass(frozen=True)
class LessonTwentyFourResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `initial_survey_choices` is the real, un-revised first pass - kept for
    transparency and for a real, non-scored recalibration observation.
    `survey_choices` is the FINAL, post-revision pass - METHOD reads this
    and only this: a student gets three real, mandatory reveals between
    the two passes and a real chance to act on them, so only what they
    finally commit to is graded.

    The three `reveal_*_interpretation` fields are recorded for
    transparency only - never scored (zero `InterpretOption.evidence_key`
    anywhere: a student who picks the wrong interpretation of a reveal
    still saw the same real numbers and can cite them later)."""

    initial_survey_choices: SurveyChoices
    survey_choices: SurveyChoices
    reveal_coverage_bias_interpretation: str | None
    reveal_sampling_frame_interpretation: str | None
    reveal_nonresponse_bias_interpretation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return len(self.survey_choices) == 1 and len(self.decision) > 0


def _score_method(result: LessonTwentyFourResult) -> tuple[float, FeedbackObservation | None]:
    """One real decision, one right answer - reads result.survey_choices
    only (the FINAL, post-revision pass), structurally independent of
    result.decision."""
    correct = result.survey_choices.get(_GENERAL_CHECK_KEY) == _CORRECT_COMBO
    if not correct:
        return 25.0, FeedbackObservation("lesson.l24.feedback.survey_combo_not_defensible", ScoreDimension.METHOD)
    return 95.0, None


def _reasoning_checks(result: LessonTwentyFourResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("why_in_app_popup_misleads") == _CORRECT_IN_APP_POPUP_REASON,
        dec.get("why_power_user_panel_misleads") == _CORRECT_POWER_USER_PANEL_REASON,
        dec.get("why_leading_wording_distorts") == _CORRECT_WORDING_REASON,
        dec.get("what_broad_email_neutral_still_cant_fix") == _CORRECT_STILL_CANT_FIX_REASON,
    )


def _score_reasoning(result: LessonTwentyFourResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {4: 95.0, 3: 76.0, 2: 55.0, 1: 32.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l24.feedback.why_in_app_popup_misleads_not_understood",
        "lesson.l24.feedback.why_power_user_panel_misleads_not_understood",
        "lesson.l24.feedback.why_leading_wording_distorts_not_understood",
        "lesson.l24.feedback.what_broad_email_neutral_still_cant_fix_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwentyFourResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    coverage_bias_role = all(key in present for key in COVERAGE_BIAS_KEYS)
    sampling_frame_role = all(key in present for key in SAMPLING_FRAME_KEYS)
    nonresponse_bias_role = all(key in present for key in NONRESPONSE_BIAS_KEYS)
    roles_present = sum((coverage_bias_role, sampling_frame_role, nonresponse_bias_role))
    score = {3: 95.0, 2: 70.0, 1: 40.0, 0: 15.0}[roles_present]
    if roles_present < 3:
        return score, FeedbackObservation("lesson.l24.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_calibration(result: LessonTwentyFourResult) -> tuple[float, FeedbackObservation | None]:
    """Reads `strongest_defensible_claim` only, never a before/after pair
    - matching every sibling lesson's own precedent that this dimension
    doesn't require one, only a single final-claim field."""
    claim = result.decision.get("strongest_defensible_claim")
    if claim == _CALIBRATED_CLAIM:
        return 92.0, None
    if claim == _OVERCLAIM:
        return 25.0, FeedbackObservation("lesson.l24.feedback.claim_overclaimed", ScoreDimension.OVERCONFIDENCE)
    if claim == _UNDERCLAIM:
        return 35.0, FeedbackObservation("lesson.l24.feedback.claim_underclaimed", ScoreDimension.OVERCONFIDENCE)
    return 15.0, FeedbackObservation("lesson.l24.feedback.claim_not_understood", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonTwentyFourResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    first pass picked a flawed combo but whose final (post-reveal,
    post-revision) pass corrected it, gets real recalibration credit -
    never a numeric bonus, just an additional observation."""
    initial_correct = result.initial_survey_choices.get(_GENERAL_CHECK_KEY) == _CORRECT_COMBO
    final_correct = result.survey_choices.get(_GENERAL_CHECK_KEY) == _CORRECT_COMBO
    if initial_correct or not final_correct:
        return None
    return FeedbackObservation("lesson.l24.feedback.survey_combo_recalibrated")


def _mastery_succeeded(result: LessonTwentyFourResult) -> bool:
    what_88_correct = result.mastery_result.get("mastery_what_88_percent_represents") == _CORRECT_MASTERY_WHAT_88_REPRESENTS
    why_blended_correct = result.mastery_result.get("mastery_why_blended_is_lower") == _CORRECT_MASTERY_WHY_BLENDED_IS_LOWER
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = all(key in supporting for key in _MASTERY_REQUIRED_EVIDENCE)
    return what_88_correct and why_blended_correct and both_facts_cited


def score_lesson_twenty_four(result: LessonTwentyFourResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l24.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

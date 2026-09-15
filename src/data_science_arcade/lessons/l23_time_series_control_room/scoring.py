from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.timeseries import TimeSeriesChoices
from data_science_arcade.lessons.l23_time_series_control_room.requests import CORRECT_OPTION_BY_REQUEST

_RELEASE_DIP_KEY = "release_dip_claim"
_CORRECT_LENS = CORRECT_OPTION_BY_REQUEST[_RELEASE_DIP_KEY]

_CORRECT_BASELINE_FOR_RELEASE_CLAIM = "weekday_aligned_reference_period"
_CORRECT_WEEKEND_SUPPORT = "matches_ordinary_recurring_pattern_no_extra_deviation"
_CORRECT_CAMPAIGN_SUPPORT = "real_observed_deviation_from_own_baseline"
_CORRECT_WHY_NEARBY_MISLEADING = "conflates_different_weekdays_own_different_baselines"

_CALIBRATED_CLAIM = "no_extra_release_deviation_campaign_real_not_causally_proven"
_OVERCLAIM = "release_and_campaign_both_definitely_caused_it"
_UNDERCLAIM = "everything_here_is_just_calendar_noise"

# --- Evidence, claim-role-based over 6 real, unconditionally-recorded
# facts (never gated by which reveal interpretation a student picked) - 3
# roles, none a strict subset of another: `weekday_baseline_structure`
# (all three weekday baselines, supporting "different weekdays have
# different normal baselines"), `release_window` (both weekend days,
# current+baseline each - one day alone doesn't defend a claim about the
# whole weekend), `campaign_deviation` (the campaign day's own current +
# baseline). Baseline facts legitimately double-duty across roles - the
# reference facts are recorded once (by the baseline reveal) and reused
# by both `weekday_baseline_structure` and `release_window`, the same
# double-duty pattern L22's own JAN_MONTH1_EVIDENCE_KEY established. -----

RELEASE_WEEKEND_SAT_CURRENT_EVIDENCE_KEY = "lesson.l23.evidence.release_weekend_sat_current"
RELEASE_WEEKEND_SAT_BASELINE_EVIDENCE_KEY = "lesson.l23.evidence.release_weekend_sat_baseline"
RELEASE_WEEKEND_SUN_CURRENT_EVIDENCE_KEY = "lesson.l23.evidence.release_weekend_sun_current"
RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY = "lesson.l23.evidence.release_weekend_sun_baseline"
CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY = "lesson.l23.evidence.campaign_monday_current"
CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY = "lesson.l23.evidence.campaign_monday_baseline"

WEEKDAY_BASELINE_STRUCTURE_KEYS: tuple[str, ...] = (
    CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY,
    RELEASE_WEEKEND_SAT_BASELINE_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY,
)
RELEASE_WINDOW_KEYS: tuple[str, ...] = (
    RELEASE_WEEKEND_SAT_CURRENT_EVIDENCE_KEY,
    RELEASE_WEEKEND_SAT_BASELINE_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_CURRENT_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY,
)
CAMPAIGN_DEVIATION_KEYS: tuple[str, ...] = (CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY, CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY)

# Every individually-citable evidence key - used by scenario.py to detect
# which real facts a student selected. 6 entries, 3 scored roles.
CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    RELEASE_WEEKEND_SAT_CURRENT_EVIDENCE_KEY,
    RELEASE_WEEKEND_SAT_BASELINE_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_CURRENT_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY,
    CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY,
    CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY,
)

# --- Mastery: NovaMart Logistics delivery-holiday alert, a different
# domain. The correct interpretation stays a non-causal recurring-pattern
# claim - two post-holiday observations support "this recurs," never
# "the holiday causes it" as a mechanism (that would need its own
# explicit, student-facing provenance fact, which this lesson doesn't
# give - see twist_data.py's own docstring, which stipulates the causal
# mechanism only for the dataset's own authoring, never as something
# handed to the student). -------------------------------------------------

_CORRECT_MASTERY_FAIR_REFERENCE = "compare_to_another_post_holiday_day"
_CORRECT_MASTERY_INCIDENT_INTERPRETATION = "recurring_post_holiday_pattern_not_a_one_off"
_MASTERY_REQUIRED_EVIDENCE: tuple[str, ...] = ("spring_alert_71_percent", "autumn_repeat_70_percent")


@dataclass(frozen=True)
class LessonTwentyThreeResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `initial_lens_choices` is the real, un-revised first pass - kept for
    transparency and for a real, non-scored recalibration observation.
    `lens_choices` is the FINAL, post-revision pass - METHOD reads this
    and only this: a student gets two real, mandatory reveals between the
    two passes and a real chance to act on them, so only what they
    finally commit to is graded.

    `reveal_weekday_baseline_interpretation`/`reveal_campaign_deviation_interpretation`
    are recorded for transparency only - never scored (zero
    InterpretOption.evidence_key anywhere: a student who picks the wrong
    interpretation of a reveal still saw the same real numbers and can
    cite them later)."""

    initial_lens_choices: TimeSeriesChoices
    lens_choices: TimeSeriesChoices
    reveal_weekday_baseline_interpretation: str | None
    reveal_campaign_deviation_interpretation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return len(self.lens_choices) == 1 and len(self.decision) > 0


def _score_method(result: LessonTwentyThreeResult) -> tuple[float, FeedbackObservation | None]:
    """One real decision, one right answer - reads result.lens_choices
    only (the FINAL, post-revision pass), structurally independent of
    result.decision."""
    correct = result.lens_choices.get(_RELEASE_DIP_KEY) == _CORRECT_LENS
    if not correct:
        return 25.0, FeedbackObservation("lesson.l23.feedback.lens_choice_not_defensible", ScoreDimension.METHOD)
    return 95.0, None


def _reasoning_checks(result: LessonTwentyThreeResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("baseline_for_release_claim") == _CORRECT_BASELINE_FOR_RELEASE_CLAIM,
        dec.get("what_post_release_weekend_supports") == _CORRECT_WEEKEND_SUPPORT,
        dec.get("what_campaign_monday_supports") == _CORRECT_CAMPAIGN_SUPPORT,
        dec.get("why_nearby_day_comparison_misleading") == _CORRECT_WHY_NEARBY_MISLEADING,
    )


def _score_reasoning(result: LessonTwentyThreeResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {4: 95.0, 3: 76.0, 2: 55.0, 1: 32.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l23.feedback.baseline_for_release_claim_not_understood",
        "lesson.l23.feedback.what_post_release_weekend_supports_not_understood",
        "lesson.l23.feedback.what_campaign_monday_supports_not_understood",
        "lesson.l23.feedback.why_nearby_day_comparison_misleading_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwentyThreeResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    weekday_baseline_structure_role = all(key in present for key in WEEKDAY_BASELINE_STRUCTURE_KEYS)
    release_window_role = all(key in present for key in RELEASE_WINDOW_KEYS)
    campaign_deviation_role = all(key in present for key in CAMPAIGN_DEVIATION_KEYS)
    roles_present = sum((weekday_baseline_structure_role, release_window_role, campaign_deviation_role))
    score = {3: 95.0, 2: 70.0, 1: 40.0, 0: 15.0}[roles_present]
    if roles_present < 3:
        return score, FeedbackObservation("lesson.l23.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_calibration(result: LessonTwentyThreeResult) -> tuple[float, FeedbackObservation | None]:
    """Reads `strongest_defensible_claim` only, never a before/after pair
    - matching L16's/L20's/L22's own precedent that this dimension doesn't
    require one to exist, only a single final-claim field."""
    claim = result.decision.get("strongest_defensible_claim")
    if claim == _CALIBRATED_CLAIM:
        return 92.0, None
    if claim == _OVERCLAIM:
        return 25.0, FeedbackObservation("lesson.l23.feedback.claim_overclaimed", ScoreDimension.OVERCONFIDENCE)
    if claim == _UNDERCLAIM:
        return 35.0, FeedbackObservation("lesson.l23.feedback.claim_underclaimed", ScoreDimension.OVERCONFIDENCE)
    return 15.0, FeedbackObservation("lesson.l23.feedback.claim_not_understood", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonTwentyThreeResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    first pass picked nearby_days_only but whose final (post-reveal,
    post-revision) pass corrected it, gets real recalibration credit -
    never a numeric bonus, just an additional observation."""
    initial_correct = result.initial_lens_choices.get(_RELEASE_DIP_KEY) == _CORRECT_LENS
    final_correct = result.lens_choices.get(_RELEASE_DIP_KEY) == _CORRECT_LENS
    if initial_correct or not final_correct:
        return None
    return FeedbackObservation("lesson.l23.feedback.lens_choice_recalibrated")


def _mastery_succeeded(result: LessonTwentyThreeResult) -> bool:
    fair_reference_correct = result.mastery_result.get("mastery_fair_reference") == _CORRECT_MASTERY_FAIR_REFERENCE
    incident_interpretation_correct = result.mastery_result.get("mastery_incident_interpretation") == _CORRECT_MASTERY_INCIDENT_INTERPRETATION
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    both_facts_cited = all(key in supporting for key in _MASTERY_REQUIRED_EVIDENCE)
    return fair_reference_correct and incident_interpretation_correct and both_facts_cited


def score_lesson_twenty_three(result: LessonTwentyThreeResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l23.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

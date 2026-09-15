from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.funnel import FunnelChoices
from data_science_arcade.lessons.l21_funnel_factory.requests import CORRECT_DEFINITION_BY_REQUEST

# --- REASONING - 4 independent Final Decision Brief checks. -------------

_CORRECT_INVESTIGATION_CONCLUSION = "blame_cart_to_checkout_step"
_CORRECT_WHY_LEGACY_UNDERCOUNTS = "tracking_pixel_missing_on_newer_app_builds"
_CORRECT_PERCENT_BASIS_ANSWER = "finds_the_step_thats_uniquely_bad_locally"
_CORRECT_GENERAL_LESSON = "justify_definition_independent_of_result"

# --- Evidence, claim-role-based (never "any N of M") - 4 real roles over
# 8 individually-citable facts, pair/2-of-3-aware where a role's own
# claim genuinely needs more than one number (matching L19's own
# power-probability-pair fix): a single add_to_cart reading doesn't prove
# "sensitivity to definition," and a lone checkout_started percentage
# doesn't prove "basis changes the story" - each of those roles requires
# a real contrast, not one citation. -------------------------------------

INSTRUMENTATION_GAP_EVIDENCE_KEY = "lesson.l21.evidence.instrumentation_gap"
DEFINITION_CHECK_LEGACY_EVIDENCE_KEY = "lesson.l21.evidence.definition_check_legacy"
DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY = "lesson.l21.evidence.definition_check_complete"
DEFINITION_CHECK_RAW_EVIDENCE_KEY = "lesson.l21.evidence.definition_check_raw"
BASIS_CHECK_TOP_EVIDENCE_KEY = "lesson.l21.evidence.basis_check_top"
BASIS_CHECK_PREVIOUS_EVIDENCE_KEY = "lesson.l21.evidence.basis_check_previous"
LOCAL_ADD_TO_CART_EVIDENCE_KEY = "lesson.l21.evidence.local_add_to_cart"
LOCAL_ORDER_CONFIRMED_EVIDENCE_KEY = "lesson.l21.evidence.local_order_confirmed"

DEFINITION_SENSITIVITY_KEYS: tuple[str, ...] = (
    DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
    DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY,
    DEFINITION_CHECK_RAW_EVIDENCE_KEY,
)
CONVERSION_BASIS_PAIR_KEYS: tuple[str, str] = (BASIS_CHECK_TOP_EVIDENCE_KEY, BASIS_CHECK_PREVIOUS_EVIDENCE_KEY)
LOCAL_NEIGHBOR_KEYS: tuple[str, ...] = (LOCAL_ADD_TO_CART_EVIDENCE_KEY, LOCAL_ORDER_CONFIRMED_EVIDENCE_KEY)

# Every individually-citable evidence key - used by scenario.py to detect
# which real facts a student selected. 8 entries, 4 scored roles.
CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    INSTRUMENTATION_GAP_EVIDENCE_KEY,
    *DEFINITION_SENSITIVITY_KEYS,
    *CONVERSION_BASIS_PAIR_KEYS,
    *LOCAL_NEIGHBOR_KEYS,
)


@dataclass(frozen=True)
class LessonTwentyOneResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `initial_funnel_choices` is the real, un-revised first pass - kept
    for transparency and for a real, non-scored recalibration observation
    (mirrors L19's unused `cold_duration_pick`/L20's `week1_recommendation`).
    `funnel_choices` is the FINAL, post-revision pass - METHOD reads this
    and only this, never the first pass's own picks: a student gets a
    real, mandatory reveal between the two passes and a real chance to
    act on it, so only what they finally commit to is graded."""

    initial_funnel_choices: FunnelChoices
    funnel_choices: FunnelChoices
    reveal_a_interpretation: str | None
    reveal_b_interpretation: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return len(self.funnel_choices) == 3 and len(self.decision) > 0


def _score_method(result: LessonTwentyOneResult) -> tuple[float, FeedbackObservation | None]:
    """Reads result.funnel_choices only (the FINAL, post-revision pass) -
    structurally independent of result.decision, the same METHOD-scores-
    execution invariant every deepened lesson keeps."""
    hits = sum(1 for key, correct in CORRECT_DEFINITION_BY_REQUEST.items() if result.funnel_choices.get(key) == correct)
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[hits]
    if hits < 3:
        return score, FeedbackObservation("lesson.l21.feedback.funnel_choices_not_fully_defensible", ScoreDimension.METHOD)
    return score, None


def _reasoning_checks(result: LessonTwentyOneResult) -> tuple[bool, ...]:
    dec = result.decision
    return (
        dec.get("checkout_investigation_conclusion") == _CORRECT_INVESTIGATION_CONCLUSION,
        dec.get("why_legacy_undercounts") == _CORRECT_WHY_LEGACY_UNDERCOUNTS,
        dec.get("percent_basis_question") == _CORRECT_PERCENT_BASIS_ANSWER,
        dec.get("general_lesson") == _CORRECT_GENERAL_LESSON,
    )


def _score_reasoning(result: LessonTwentyOneResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {4: 95.0, 3: 76.0, 2: 55.0, 1: 32.0, 0: 15.0}[hits]
    feedback_keys = (
        "lesson.l21.feedback.investigation_conclusion_not_understood",
        "lesson.l21.feedback.why_legacy_undercounts_not_understood",
        "lesson.l21.feedback.percent_basis_question_not_understood",
        "lesson.l21.feedback.general_lesson_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwentyOneResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    instrumentation_role = INSTRUMENTATION_GAP_EVIDENCE_KEY in present
    sensitivity_role = sum(1 for key in DEFINITION_SENSITIVITY_KEYS if key in present) >= 2
    basis_role = all(key in present for key in CONVERSION_BASIS_PAIR_KEYS)
    local_bottleneck_role = BASIS_CHECK_PREVIOUS_EVIDENCE_KEY in present and all(key in present for key in LOCAL_NEIGHBOR_KEYS)
    roles_present = sum((instrumentation_role, sensitivity_role, basis_role, local_bottleneck_role))
    score = {4: 95.0, 3: 74.0, 2: 50.0, 1: 25.0, 0: 10.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l21.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _recalibration_observation(result: LessonTwentyOneResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    first pass had at least one motivated-reasoning pick, but whose final
    (post-reveal, post-revision) pass corrected it into a fully defensible
    set of 3, gets real recalibration credit - never a numeric bonus (see
    _score_method's own docstring), just an additional observation."""
    initial_hits = sum(1 for key, correct in CORRECT_DEFINITION_BY_REQUEST.items() if result.initial_funnel_choices.get(key) == correct)
    final_hits = sum(1 for key, correct in CORRECT_DEFINITION_BY_REQUEST.items() if result.funnel_choices.get(key) == correct)
    if initial_hits >= len(CORRECT_DEFINITION_BY_REQUEST):
        return None
    if final_hits < len(CORRECT_DEFINITION_BY_REQUEST):
        return None
    return FeedbackObservation("lesson.l21.feedback.funnel_choices_recalibrated")


def _mastery_succeeded(result: LessonTwentyOneResult) -> bool:
    """Transfer requires the correct real-bottleneck judgment (profile
    completion, not signup), the correct explanation for why the team
    missed it (the flawed signup event masked a healthy step), AND both
    real distinguishing facts cited as evidence."""
    judgment_correct = result.mastery_result.get("mastery_real_bottleneck") == "profile_completed"
    why_correct = (
        result.mastery_result.get("mastery_why_missed") == "the_flawed_signup_event_made_a_healthy_step_look_broken_hiding_the_real_one"
    )
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    required = ("flawed_signup_rate_35_vs_correct_81_percent", "profile_completion_real_rate_42_percent")
    both_facts_cited = all(key in supporting for key in required)
    return judgment_correct and why_correct and both_facts_cited


def score_lesson_twenty_one(result: LessonTwentyOneResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)

    dimension_scores = {
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
    }

    observations = [
        observation for observation in (method_observation, reasoning_observation, evidence_observation) if observation is not None
    ]
    recalibration = _recalibration_observation(result)
    if recalibration is not None:
        observations.append(recalibration)
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l21.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

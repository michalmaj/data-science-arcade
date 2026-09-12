from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.l18_randomization_control_room.data import ID_PARITY, SIMPLE_RANDOM, STRATIFIED_RANDOM

# --- METHOD - a real 3-tier gradient over the FINAL EXECUTED design only,
# never anything the Final Brief claims. Stratified is best-aligned (a
# known pre-treatment covariate gets a guaranteed-balance design); simple
# random is valid and high, not a mistake; parity is low - deterministic,
# not a random mechanism at all. ---------------------------------------

_METHOD_SCORE_BY_DESIGN = {
    STRATIFIED_RANDOM: 95.0,
    SIMPLE_RANDOM: 78.0,
    ID_PARITY: 20.0,
}

# --- REASONING - 6 independent Final Brief checks. Field #1's correct
# answer is a real per-playthrough value (result.final_design), not a
# fixed constant like the other 5 - the one field in this lesson that
# can't follow a pure all-constants pattern. -----------------------------

_MECHANISM_CLASSIFICATION_BY_DESIGN = {
    ID_PARITY: "deterministic_not_randomized",
    SIMPLE_RANDOM: "valid_random_fixed_size",
    STRATIFIED_RANDOM: "valid_random_within_strata",
}
_CORRECT_WHAT_MAKES_RANDOMIZED = "decided_by_random_mechanism_before_outcome"
_CORRECT_EQUAL_GROUP_SIZES = "establishes_nothing_about_mechanism_alone"
_CORRECT_SMALL_IMBALANCE = "does_not_invalidate_valid_randomization"
_CORRECT_WHY_STRATIFY = "guarantees_balance_on_a_known_covariate_randomness_within_strata"
_CORRECT_WHAT_MUST_STAY_SEALED = "determined_without_outcomes_or_post_treatment_info"

# --- Evidence, role-based (never "any N of M"). Two roles track the
# CURRENT truth of the final executed design (keyed, updated in place on
# a real revision - see AssignmentAuditScene's own docstring); the third
# is the lesson's own mandatory, un-revisable mechanism-contrast fact,
# recorded exactly once and never overwritten - the one citable fact that
# directly proves "you cannot infer mechanism from balance alone." -------

ASSIGNMENT_MECHANISM_EVIDENCE_KEY = "lesson.l18.evidence.assignment_mechanism_final"
ASSIGNMENT_BALANCE_EVIDENCE_KEY = "lesson.l18.evidence.assignment_realized_balance_final"
MECHANISM_CONTRAST_EVIDENCE_KEY = "lesson.l18.evidence.mechanism_balance_contrast"

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    ASSIGNMENT_MECHANISM_EVIDENCE_KEY,
    ASSIGNMENT_BALANCE_EVIDENCE_KEY,
    MECHANISM_CONTRAST_EVIDENCE_KEY,
)

# --- Mastery: NovaMart Logistics packaging experiment -----------------

_CORRECT_MASTERY_MECHANISM_JUDGMENT = "genuinely_randomly_assigned_per_provenance"
_CORRECT_MASTERY_IMBALANCE_MEANING = "real_diagnostic_fact_not_invalidating"
_MASTERY_REQUIRED_EVIDENCE = "provenance_log_confirms_seeded_random_assignment"


@dataclass(frozen=True)
class LessonEighteenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `final_design` is the real FINAL EXECUTED design (after the one real,
    un-punished revision if the student took it) - METHOD scores this and
    only this, never the Final Randomization Brief's own later claims. A
    student can execute a perfectly valid stratified design and still
    write a Final Brief that overclaims what balance alone proves (high
    METHOD, lower REASONING); a student who leaves parity as the final
    executed design but correctly explains in the Brief why parity isn't
    randomized still scores METHOD low (decent REASONING). Two dedicated
    regression tests confirm both directions, plus a third confirming a
    genuinely well-executed AND well-reasoned playthrough scores high on
    both."""

    initial_design: str
    final_design: str
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return bool(self.final_design) and len(self.decision) > 0


def _score_method(result: LessonEighteenResult) -> tuple[float, FeedbackObservation | None]:
    """Reads result.final_design only - structurally independent of
    result.decision, the same METHOD-scores-execution invariant every
    deepened lesson since L13's own follow-up has kept. Simple random
    gets no corrective observation - it's a genuinely valid design, never
    framed as a lesser choice a student "should have" avoided."""
    score = _METHOD_SCORE_BY_DESIGN[result.final_design]
    if result.final_design == ID_PARITY:
        return score, FeedbackObservation("lesson.l18.feedback.parity_is_not_randomized", ScoreDimension.METHOD)
    return score, None


def _reasoning_checks(result: LessonEighteenResult) -> tuple[bool, ...]:
    d = result.decision
    return (
        d.get("mechanism_classification") == _MECHANISM_CLASSIFICATION_BY_DESIGN.get(result.final_design),
        d.get("what_makes_assignment_randomized") == _CORRECT_WHAT_MAKES_RANDOMIZED,
        d.get("what_equal_group_sizes_establish") == _CORRECT_EQUAL_GROUP_SIZES,
        d.get("how_to_interpret_small_realized_imbalance") == _CORRECT_SMALL_IMBALANCE,
        d.get("why_stratify_on_platform") == _CORRECT_WHY_STRATIFY,
        d.get("what_must_stay_sealed_during_assignment") == _CORRECT_WHAT_MUST_STAY_SEALED,
    )


def _score_reasoning(result: LessonEighteenResult) -> tuple[float, FeedbackObservation | None]:
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {6: 95.0, 5: 82.0, 4: 68.0, 3: 52.0, 2: 38.0, 1: 22.0, 0: 10.0}[hits]
    feedback_keys = (
        "lesson.l18.feedback.mechanism_classification_not_understood",
        "lesson.l18.feedback.what_makes_randomized_not_understood",
        "lesson.l18.feedback.equal_group_sizes_not_understood",
        "lesson.l18.feedback.small_imbalance_not_understood",
        "lesson.l18.feedback.why_stratify_not_understood",
        "lesson.l18.feedback.what_must_stay_sealed_not_understood",
    )
    for passed, key in zip(checks, feedback_keys):
        if not passed:
            return score, FeedbackObservation(key, ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonEighteenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(1 for key in CRITICAL_EVIDENCE_KEYS if key in present)
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 10.0}[roles_present]
    if roles_present < 3:
        return score, FeedbackObservation("lesson.l18.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _mastery_succeeded(result: LessonEighteenResult) -> bool:
    """Transfer requires the correct mechanism judgment (genuinely random,
    per its own recorded provenance), the correct treatment of the
    realized covariate imbalance (a real diagnostic fact, not proof the
    randomization failed), AND the real provenance-log evidence citation
    - never accepting a correct judgment alone without the fact that
    actually grounds it."""
    mechanism_correct = result.mastery_result.get("mastery_mechanism_judgment") == _CORRECT_MASTERY_MECHANISM_JUDGMENT
    imbalance_correct = result.mastery_result.get("mastery_imbalance_meaning") == _CORRECT_MASTERY_IMBALANCE_MEANING
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    real_distinguishing_fact = _MASTERY_REQUIRED_EVIDENCE in supporting
    return mechanism_correct and imbalance_correct and real_distinguishing_fact


def score_lesson_eighteen(result: LessonEighteenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l18.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

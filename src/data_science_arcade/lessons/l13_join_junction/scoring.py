from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

_CORRECT_JOIN1_TYPE = "left"
_CORRECT_JOIN1_ROW_COUNT = "120"

_CORRECT_PROMOTIONS_KEY_CARDINALITY = "many_to_one_from_promotions"
_CORRECT_REPAIR_CHOICE = "preaggregate_first"
_CORRECT_REPAIRED_ROW_COUNT = "120"
_CORRECT_VALIDATION_SUFFICIENCY = "no_needs_multiple_checks"

# Evidence, role-based (never "any N of M" - established L08-L12 discipline).
# Every ComparisonRevealScene reveal in this lesson sets
# comparisons_are_evidence=False; the only evidence recorded comes from
# each reveal's own interpret-click evidence_key (fixed facts, never
# revised) plus join1_consequence_role/repair_consequence_role, which are
# manually recorded and update-by-key so a revision never leaves two
# contradictory items describing the same attempt.
ORDERS_KEY_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.orders_key",)
JOIN1_CONSEQUENCE_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.join1_consequence",)
PROMOTIONS_KEY_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.promotions_key",)
FAN_OUT_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.fan_out",)
REPAIR_CONSEQUENCE_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.repair_consequence",)
MULTI_CHECK_VALIDATION_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.multi_check_validation",)

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    ORDERS_KEY_EVIDENCE_KEYS
    + JOIN1_CONSEQUENCE_EVIDENCE_KEYS
    + PROMOTIONS_KEY_EVIDENCE_KEYS
    + FAN_OUT_EVIDENCE_KEYS
    + REPAIR_CONSEQUENCE_EVIDENCE_KEYS
    + MULTI_CHECK_VALIDATION_EVIDENCE_KEYS
)


@dataclass(frozen=True)
class LessonThirteenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `join1_first_choice`/`join1_choice` and
    `promotions_repair_first_choice`/`promotions_repair_choice` are each a
    real cold-pick-then-revised-pick pair (an initial attempt, a real
    executed consequence, a revision offer) - kept genuinely separate from
    the Final Decision so trajectory feedback can fire only for a real
    wrong-then-corrected change AT the revision step itself, never
    inferred from "first pick differs from wherever Final Decision ended
    up" (the exact bug the L09/L10/L11 follow-ups each had to fix after
    the fact).

    METHOD is scored purely off these two FINAL EXECUTED states - not off
    `decision`'s own claims. A student who leaves a wrong pipeline in
    place but correctly states, in the Final Decision, what should have
    been done, scores low METHOD (the real pipeline stayed wrong) and can
    still score high REASONING (the normative understanding is real and
    separately credited) - Final Decision can never "rewrite history" and
    retroactively earn METHOD credit for a pipeline action that was never
    actually taken."""

    join1_first_choice: str | None
    join1_choice: str | None
    promotions_repair_first_choice: str | None
    promotions_repair_choice: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return bool(self.join1_choice) and bool(self.promotions_repair_choice) and len(self.decision) > 0


def _method_hits(result: LessonThirteenResult) -> list[tuple[bool, str]]:
    """(is_correct, feedback_key) pairs scored purely off the two real,
    FINAL EXECUTED pipeline states - never off the Final Decision's own
    claims about them (see LessonThirteenResult's own docstring)."""
    return [
        (result.join1_choice == _CORRECT_JOIN1_TYPE, "lesson.l13.feedback.join1_pipeline_wrong"),
        (result.promotions_repair_choice == _CORRECT_REPAIR_CHOICE, "lesson.l13.feedback.promotions_repair_pipeline_wrong"),
    ]


def _score_method(result: LessonThirteenResult) -> tuple[float, FeedbackObservation | None]:
    """Breadth: did the student's own FINAL, actually-executed pipeline
    (after both real revision opportunities) get Join 1 and the
    promotions repair right - never whether the Final Decision merely
    claims the right answer."""
    checks = _method_hits(result)
    hits = sum(1 for correct, _ in checks if correct)
    score = {2: 96.0, 1: 55.0, 0: 14.0}[hits]
    for correct, feedback_key in checks:
        if not correct:
            return score, FeedbackObservation(feedback_key, ScoreDimension.METHOD)
    return score, None


def _join1_normative_understanding(result: LessonThirteenResult) -> bool:
    """A pure comprehension check against the NORMATIVE join type/row
    count the requested table requires - not against whatever the
    student's own pipeline actually ended up as. A student stuck with a
    wrong (e.g. inner) pipeline can still honestly say what the join
    SHOULD have been, and REASONING credits that separately from
    METHOD's own pipeline-correctness score - mirrors L12's own
    `_grain_understood`."""
    d = result.decision
    return d.get("orders_join_type") == _CORRECT_JOIN1_TYPE and d.get("orders_join_row_count") == _CORRECT_JOIN1_ROW_COUNT


def _promotions_repair_normative_understanding(result: LessonThirteenResult) -> bool:
    """Same normative-comprehension split for the promotions repair: does
    the Final Decision correctly state that pre-aggregation is needed AND
    the real row count that produces, independent of whether the
    student's own pipeline actually got there."""
    d = result.decision
    return d.get("promotions_join_needs_preaggregation") == _CORRECT_REPAIR_CHOICE and d.get(
        "promotions_row_count_after_repair"
    ) == _CORRECT_REPAIRED_ROW_COUNT


def _validation_judgment_evidenced(result: LessonThirteenResult) -> bool:
    """A "row count alone isn't enough" claim is only really reasoned if
    the multi-check validation fact was actually cited - a claim with no
    supporting citation isn't reasoning, matching the evidence-hard-
    gating pattern first used in L09's own follow-up."""
    if result.decision.get("validation_sufficiency") != _CORRECT_VALIDATION_SUFFICIENCY:
        return True
    return any(key in result.critical_evidence_present for key in MULTI_CHECK_VALIDATION_EVIDENCE_KEYS)


def _score_reasoning(result: LessonThirteenResult) -> tuple[float, FeedbackObservation | None]:
    """Comprehension and coherence, not raw pipeline correctness - every
    check is about whether the student's own FINAL ARGUMENT is right and
    self-consistent, decoupled from whether the underlying pipeline
    itself was ever actually fixed (METHOD's own job)."""
    join1_understood = _join1_normative_understanding(result)
    promotions_key_understood = result.decision.get("promotions_key_cardinality") == _CORRECT_PROMOTIONS_KEY_CARDINALITY
    repair_understood = _promotions_repair_normative_understanding(result)
    validation_evidenced = _validation_judgment_evidenced(result)

    hits = int(join1_understood) + int(promotions_key_understood) + int(repair_understood) + int(validation_evidenced)
    score = {4: 95.0, 3: 74.0, 2: 52.0, 1: 30.0, 0: 12.0}[hits]
    if not join1_understood:
        return score, FeedbackObservation("lesson.l13.feedback.join1_not_understood", ScoreDimension.REASONING)
    if not promotions_key_understood:
        return score, FeedbackObservation("lesson.l13.feedback.promotions_key_cardinality_wrong", ScoreDimension.REASONING)
    if not repair_understood:
        return score, FeedbackObservation("lesson.l13.feedback.repair_not_understood", ScoreDimension.REASONING)
    if not validation_evidenced:
        return score, FeedbackObservation("lesson.l13.feedback.validation_claim_unevidenced", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonThirteenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(
        (
            bool(present & set(ORDERS_KEY_EVIDENCE_KEYS)),
            bool(present & set(JOIN1_CONSEQUENCE_EVIDENCE_KEYS)),
            bool(present & set(PROMOTIONS_KEY_EVIDENCE_KEYS)),
            bool(present & set(FAN_OUT_EVIDENCE_KEYS)),
            bool(present & set(REPAIR_CONSEQUENCE_EVIDENCE_KEYS)),
            bool(present & set(MULTI_CHECK_VALIDATION_EVIDENCE_KEYS)),
        )
    )
    score = {6: 97.0, 5: 85.0, 4: 70.0, 3: 52.0, 2: 34.0, 1: 18.0, 0: 6.0}[roles_present]
    if roles_present < 6:
        return score, FeedbackObservation("lesson.l13.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _trajectory_observations(result: LessonThirteenResult) -> list[FeedbackObservation]:
    """Fires only for a real wrong-then-corrected change AT the specific
    revision step itself - never inferred from "first pick differs from
    wherever Final Decision ended up," the exact bug the L09/L10/L11
    follow-ups each had to fix after the fact."""
    observations: list[FeedbackObservation] = []
    if result.join1_first_choice is not None and result.join1_first_choice != _CORRECT_JOIN1_TYPE and result.join1_choice == _CORRECT_JOIN1_TYPE:
        observations.append(FeedbackObservation("lesson.l13.feedback.orders_join_type_recovered_via_revision"))
    if (
        result.promotions_repair_first_choice is not None
        and result.promotions_repair_first_choice != _CORRECT_REPAIR_CHOICE
        and result.promotions_repair_choice == _CORRECT_REPAIR_CHOICE
    ):
        observations.append(FeedbackObservation("lesson.l13.feedback.promotions_repair_recovered_via_revision"))
    return observations


def _mastery_succeeded(result: LessonThirteenResult) -> bool:
    """The inverted-case transfer task requires BOTH the correct grain
    judgment (here, real row growth is expected and correct, not a
    trap) AND a real cited distinguishing fact (that each shipment
    genuinely passes through multiple real checkpoints by design - not
    "row count grew," which is exactly the naive heuristic being
    inverted). Applying the same evidence/claim pairing discipline the
    L12 follow-up just fixed for L12's own mastery task, so this design
    does not reintroduce that regression pattern from day one."""
    grain_correct = result.mastery_result.get("mastery_row_growth_judgment") == "expected_real_grain"
    evidence = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    real_distinguishing_fact = "shipment_has_multiple_real_checkpoints" in evidence
    return grain_correct and real_distinguishing_fact


def score_lesson_thirteen(result: LessonThirteenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
    observations.extend(_trajectory_observations(result))
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l13.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

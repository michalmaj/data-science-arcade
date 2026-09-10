from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

_CORRECT_JOIN1_TYPE = "left"
_CORRECT_JOIN1_ROW_COUNT = "120"
_JOIN1_ROW_COUNT_BY_TYPE: dict[str, str] = {"left": "120", "inner": "108", "outer": "140"}

_CORRECT_PROMOTIONS_KEY_CARDINALITY = "many_to_one_from_promotions"
_CORRECT_NEEDS_PREAGGREGATION = "preaggregate_first"
_CORRECT_REPAIRED_ROW_COUNT = "120"
_ROW_COUNT_BY_PREAGGREGATION_CLAIM: dict[str, str] = {"preaggregate_first": "120", "join_raw_directly": "147"}
_CORRECT_VALIDATION_SUFFICIENCY = "no_needs_multiple_checks"

# Evidence, role-based (never "any N of M" - established L08-L12 discipline).
# Every ComparisonRevealScene reveal in this lesson sets
# comparisons_are_evidence=False; the only evidence recorded comes from
# each reveal's own interpret-click evidence_key (fixed facts, never
# revised) plus join1_consequence_role, which is manually recorded and
# update-by-key so a stage-5 revision never leaves two contradictory
# items describing the same join attempt.
ORDERS_KEY_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.orders_key",)
JOIN1_CONSEQUENCE_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.join1_consequence",)
PROMOTIONS_KEY_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.promotions_key",)
FAN_OUT_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.fan_out",)
MULTI_CHECK_VALIDATION_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l13.evidence.multi_check_validation",)

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    ORDERS_KEY_EVIDENCE_KEYS
    + JOIN1_CONSEQUENCE_EVIDENCE_KEYS
    + PROMOTIONS_KEY_EVIDENCE_KEYS
    + FAN_OUT_EVIDENCE_KEYS
    + MULTI_CHECK_VALIDATION_EVIDENCE_KEYS
)


@dataclass(frozen=True)
class LessonThirteenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `join1_first_choice`/`join1_choice` are Join 1's own cold-pick-then-
    revised-pick pair (stage 3 -> stage 5's real revision offer) - kept
    genuinely separate so trajectory feedback can fire only for a real
    wrong-then-corrected change AT the revision step itself, never
    inferred from "first pick differs from wherever Final Decision ended
    up" (the exact bug the L09/L10/L11 follow-ups each had to fix after
    the fact). `decision`'s own `orders_join_type` field is the REAL
    scored METHOD fact - Join 1's own interactive pick drives the real,
    path-aware consequence reveal and evidence, but only the Final
    Decision's own committed answer is scored, mirroring how L12's
    `rollup_prior`/`rollup_revised_picks` drive practice and trajectory
    while `decision["network_customer_method"]` alone is the real scored
    fact."""

    join1_first_choice: str | None
    join1_choice: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return bool(self.join1_choice) and len(self.decision) > 0


def _method_hits(result: LessonThirteenResult) -> list[tuple[bool, str]]:
    """(is_correct, feedback_key) pairs in a fixed, checked-in-order
    sequence, scored purely off the Final Decision's own real fields -
    never off the earlier stage picks that drive practice/trajectory
    only (see LessonThirteenResult's own docstring)."""
    d = result.decision
    return [
        (d.get("orders_join_type") == _CORRECT_JOIN1_TYPE, "lesson.l13.feedback.orders_join_type_wrong"),
        (d.get("orders_join_row_count") == _CORRECT_JOIN1_ROW_COUNT, "lesson.l13.feedback.orders_join_row_count_wrong"),
        (d.get("promotions_key_cardinality") == _CORRECT_PROMOTIONS_KEY_CARDINALITY, "lesson.l13.feedback.promotions_key_cardinality_wrong"),
        (d.get("promotions_join_needs_preaggregation") == _CORRECT_NEEDS_PREAGGREGATION, "lesson.l13.feedback.needs_preaggregation_wrong"),
        (d.get("promotions_row_count_after_repair") == _CORRECT_REPAIRED_ROW_COUNT, "lesson.l13.feedback.repaired_row_count_wrong"),
    ]


def _score_method(result: LessonThirteenResult) -> tuple[float, FeedbackObservation | None]:
    """Breadth: how much of the real 5-fact pipeline (Join 1's own type
    and row count; the promotions key's real cardinality; whether it
    needs pre-aggregation; the repaired row count) is correct in the
    Final Decision's own committed answers."""
    checks = _method_hits(result)
    hits = sum(1 for correct, _ in checks if correct)
    score = {5: 96.0, 4: 80.0, 3: 62.0, 2: 44.0, 1: 26.0, 0: 10.0}[hits]
    for correct, feedback_key in checks:
        if not correct:
            return score, FeedbackObservation(feedback_key, ScoreDimension.METHOD)
    return score, None


def _join1_coherent(result: LessonThirteenResult) -> bool:
    """Does the stated row count actually match the pandas consequence of
    the stated join type, regardless of whether that join type is itself
    the objectively correct pick - a student claiming "left" while also
    claiming "108" would be self-contradictory."""
    join_type = result.decision.get("orders_join_type")
    expected = _JOIN1_ROW_COUNT_BY_TYPE.get(join_type)
    return expected is not None and result.decision.get("orders_join_row_count") == expected


def _promotions_repair_coherent(result: LessonThirteenResult) -> bool:
    """Does the stated repaired row count match the honest consequence of
    the student's own pre-aggregation claim - claiming pre-aggregation is
    needed while still reporting 147 (the raw-join number) would be
    incoherent, and so would claiming raw-join-is-fine while reporting
    120 (the number only pre-aggregation actually produces)."""
    claim = result.decision.get("promotions_join_needs_preaggregation")
    expected = _ROW_COUNT_BY_PREAGGREGATION_CLAIM.get(claim)
    return expected is not None and result.decision.get("promotions_row_count_after_repair") == expected


def _validation_judgment_evidenced(result: LessonThirteenResult) -> bool:
    """A "row count alone isn't enough" claim is only really reasoned if
    the multi-check validation fact was actually cited - a claim with no
    supporting citation isn't reasoning, matching the evidence-hard-
    gating pattern first used in L09's own follow-up."""
    if result.decision.get("validation_sufficiency") != _CORRECT_VALIDATION_SUFFICIENCY:
        return True
    return any(key in result.critical_evidence_present for key in MULTI_CHECK_VALIDATION_EVIDENCE_KEYS)


def _score_reasoning(result: LessonThirteenResult) -> tuple[float, FeedbackObservation | None]:
    """Coherence, not raw correctness - every check compares one part of
    the student's own final argument against another real fact about
    what they claimed, decoupled from whether the underlying pick itself
    was correct (METHOD's own job)."""
    join1_coherent = _join1_coherent(result)
    repair_coherent = _promotions_repair_coherent(result)
    validation_evidenced = _validation_judgment_evidenced(result)

    hits = int(join1_coherent) + int(repair_coherent) + int(validation_evidenced)
    score = {3: 93.0, 2: 63.0, 1: 34.0, 0: 12.0}[hits]
    if not join1_coherent:
        return score, FeedbackObservation("lesson.l13.feedback.join1_incoherent", ScoreDimension.REASONING)
    if not repair_coherent:
        return score, FeedbackObservation("lesson.l13.feedback.repair_incoherent", ScoreDimension.REASONING)
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
            bool(present & set(MULTI_CHECK_VALIDATION_EVIDENCE_KEYS)),
        )
    )
    score = {5: 97.0, 4: 82.0, 3: 60.0, 2: 40.0, 1: 20.0, 0: 8.0}[roles_present]
    if roles_present < 5:
        return score, FeedbackObservation("lesson.l13.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _trajectory_observations(result: LessonThirteenResult) -> list[FeedbackObservation]:
    """Fires only for a real wrong-then-corrected change AT the stage-5
    revision itself - never inferred from "first pick differs from
    wherever Final Decision ended up," the exact bug the L09/L10/L11
    follow-ups each had to fix after the fact."""
    observations: list[FeedbackObservation] = []
    if result.join1_first_choice is not None and result.join1_first_choice != _CORRECT_JOIN1_TYPE and result.join1_choice == _CORRECT_JOIN1_TYPE:
        observations.append(FeedbackObservation("lesson.l13.feedback.orders_join_type_recovered_via_revision"))
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

from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.repair import RepairResolution
from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import MASTERY_CORRECT, SAFE_COLUMNS_CORRECT

# The objectively correct declaration/resolution for each of the three
# real schema problems - fixed, not branched on student state, since (like
# L05, unlike L04) the hidden population never changes based on what the
# student did in an earlier stage; every KPI reveal is always computed
# from the same, always-correctly-repaired ground truth regardless of
# which repair options the student actually picked.
_CORRECT_CONTRACT = {
    "shipment_id_contract": "identifier",
    "delivered_at_contract": "timestamp",
    "duration_contract": "per_store_unit_drift",
}
_CORRECT_REPAIR = {
    "shipment_id": "cast_to_text",
    "delivered_at": "coerce_keep_nat",
    "duration_minutes": "fix_store_d_only",
}

# Which real facts matter most to cite - matched by substring on the
# picked item's real label_key, the same technique L04/L05's own
# CRITICAL_EVIDENCE_KEYS uses.
CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    "issue.shipment_id.evidence",
    "issue.delivered_at.evidence",
    "issue.duration_minutes.evidence",
    "reveal2.corrected_label",
)


@dataclass(frozen=True)
class LessonSixResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself."""

    safe_columns: frozenset[str]
    shipment_id_contract: str
    delivered_at_contract: str
    duration_contract: str
    round1_resolution: RepairResolution
    round2_resolution: RepairResolution
    malformed_count_reported: int
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_selection: frozenset[str] = frozenset()

    def completed_thoughtfully(self) -> bool:
        return bool(self.round1_resolution) and bool(self.round2_resolution) and len(self.decision) > 0


def _score_data_quality(result: LessonSixResult) -> tuple[float, FeedbackObservation | None]:
    """Four real declared judgments, not three - the safe-columns
    prediction is the same dtype-vs-semantic-type distinction the
    Contract Builder rounds test, just earlier and lighter-weight."""
    hits = (
        int(result.safe_columns == SAFE_COLUMNS_CORRECT)
        + int(result.shipment_id_contract == _CORRECT_CONTRACT["shipment_id_contract"])
        + int(result.delivered_at_contract == _CORRECT_CONTRACT["delivered_at_contract"])
        + int(result.duration_contract == _CORRECT_CONTRACT["duration_contract"])
    )
    score = 100.0 * hits / 4.0
    if result.duration_contract == "uniform_minutes":
        return score, FeedbackObservation(
            "lesson.l06.feedback.duration_declared_uniform_after_twist", ScoreDimension.DATA_QUALITY
        )
    if hits == 4:
        return score, FeedbackObservation("lesson.l06.feedback.contract_fully_correct", ScoreDimension.DATA_QUALITY)
    return score, None


def _score_reproducibility(result: LessonSixResult) -> tuple[float, FeedbackObservation | None]:
    """Whether the actually-executed transforms are the ones that
    genuinely generalize - a rule that "fixes" the majority but silently
    breaks the minority (or the reverse) is a real, different failure
    from simply not knowing the right concept (see Data Quality above);
    the two are scored independently on purpose - declaring the right
    semantic type doesn't mechanically force picking the matching correct
    transform, and vice versa."""
    resolution = {**result.round1_resolution, **result.round2_resolution}
    hits = sum(1 for column, correct_key in _CORRECT_REPAIR.items() if resolution.get(column) == correct_key)
    score = 100.0 * hits / 3.0
    if resolution.get("duration_minutes") == "fix_every_row":
        return score, FeedbackObservation(
            "lesson.l06.feedback.duration_overcorrected_every_row", ScoreDimension.REPRODUCIBILITY
        )
    if hits == 3:
        return score, FeedbackObservation("lesson.l06.feedback.all_repairs_generalize", ScoreDimension.REPRODUCIBILITY)
    return score, None


def _score_evidence(result: LessonSixResult) -> tuple[float, FeedbackObservation | None]:
    count = min(len(result.critical_evidence_present), 3)  # EvidenceField.max_count is 3
    score = {3: 95.0, 2: 70.0, 1: 40.0, 0: 15.0}[count]
    observation = (
        None if count >= 2 else FeedbackObservation("lesson.l06.feedback.evidence_missed_key_facts", ScoreDimension.EVIDENCE)
    )
    return score, observation


def _score_reasoning(result: LessonSixResult) -> tuple[float, FeedbackObservation | None]:
    kpi_correct = result.decision.get("kpi_result") == "corrected_12"
    readiness = result.decision.get("readiness")
    ambiguity = result.decision.get("remaining_ambiguity")
    safe_use = result.decision.get("safe_use")

    readiness_coherent = (readiness == "conditionally_ready") and (ambiguity != "nothing_remains")
    safe_use_coherent = safe_use == "this_month_sla"

    hits = int(kpi_correct) + int(readiness_coherent) + int(safe_use_coherent)
    score = {3: 92.0, 2: 60.0, 1: 32.0, 0: 12.0}[hits]
    if not kpi_correct and result.decision.get("kpi_result") in ("naive_29",):
        return score, FeedbackObservation("lesson.l06.feedback.reported_the_naive_number", ScoreDimension.REASONING)
    if readiness == "ready" and ambiguity != "nothing_remains":
        return score, FeedbackObservation("lesson.l06.feedback.readiness_contradicts_ambiguity", ScoreDimension.REASONING)
    if safe_use in ("cross_month_trend", "financial_reconciliation"):
        return score, FeedbackObservation("lesson.l06.feedback.safe_use_overreached", ScoreDimension.REASONING)
    return score, None


def _score_method(result: LessonSixResult) -> tuple[float, FeedbackObservation | None]:
    readiness_correct = result.decision.get("readiness") == "conditionally_ready"
    required_change_correct = result.decision.get("required_change") == "update_contract_and_validate"
    hits = int(readiness_correct) + int(required_change_correct)
    score = {2: 94.0, 1: 55.0, 0: 18.0}[hits]
    if result.decision.get("required_change") == "nothing_needed":
        return score, FeedbackObservation("lesson.l06.feedback.no_systemic_fix_proposed", ScoreDimension.METHOD)
    return score, None


def _mastery_succeeded(result: LessonSixResult) -> bool:
    return result.mastery_selection == MASTERY_CORRECT


def score_lesson_six(result: LessonSixResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    data_quality_score, data_quality_observation = _score_data_quality(result)
    reproducibility_score, reproducibility_observation = _score_reproducibility(result)
    evidence_score, evidence_observation = _score_evidence(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    method_score, method_observation = _score_method(result)

    dimension_scores = {
        ScoreDimension.DATA_QUALITY: data_quality_score,
        ScoreDimension.REPRODUCIBILITY: reproducibility_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.METHOD: method_score,
    }

    observations = [
        observation
        for observation in (
            data_quality_observation,
            reproducibility_observation,
            evidence_observation,
            reasoning_observation,
            method_observation,
        )
        if observation is not None
    ]
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l06.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

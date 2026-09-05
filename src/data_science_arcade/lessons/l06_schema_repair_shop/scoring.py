from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.repair import RepairResolution
from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import CORRECT_REPAIR, MASTERY_CORRECT, SAFE_COLUMNS_CORRECT

# The objectively correct declaration for each of the three real schema
# problems - fixed, not branched on student state, since (like L05, unlike
# L04) the hidden population never changes based on what the student did
# in an earlier stage. See twist_data.CORRECT_REPAIR for the *executed*-
# transform equivalent (shipment_id has two acceptable answers there,
# deliberately - see its own docstring).
_CORRECT_CONTRACT = {
    "shipment_id_contract": "identifier",
    "delivered_at_contract": "timestamp",
    "duration_contract": "per_store_unit_drift",
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
    reveal1_interpretation: str = ""
    reveal2_interpretation: str = ""

    def completed_thoughtfully(self) -> bool:
        return bool(self.round1_resolution) and bool(self.round2_resolution) and len(self.decision) > 0


def _score_data_quality(result: LessonSixResult) -> tuple[float, FeedbackObservation | None]:
    """Dominated by the three real Contract Builder declarations - the
    final understanding a student actually lands on. The safe-columns
    prediction is a *prior*, made before any real evidence exists, so it
    only ever adds a small bonus on top - never a drag that permanently
    caps a student who started with an incomplete read and then declared
    every real contract correctly afterward."""
    contract_hits = (
        int(result.shipment_id_contract == _CORRECT_CONTRACT["shipment_id_contract"])
        + int(result.delivered_at_contract == _CORRECT_CONTRACT["delivered_at_contract"])
        + int(result.duration_contract == _CORRECT_CONTRACT["duration_contract"])
    )
    predicted_safely = result.safe_columns == SAFE_COLUMNS_CORRECT
    score = min(100.0, 100.0 * contract_hits / 3.0 + (5.0 if predicted_safely else 0.0))
    if result.duration_contract == "uniform_minutes":
        return score, FeedbackObservation(
            "lesson.l06.feedback.duration_declared_uniform_after_twist", ScoreDimension.DATA_QUALITY
        )
    if contract_hits == 3 and not predicted_safely:
        return score, FeedbackObservation(
            "lesson.l06.feedback.contract_recovered_after_early_miss", ScoreDimension.DATA_QUALITY
        )
    if contract_hits == 3:
        return score, FeedbackObservation("lesson.l06.feedback.contract_fully_correct", ScoreDimension.DATA_QUALITY)
    return score, None


def _score_reproducibility(result: LessonSixResult) -> tuple[float, FeedbackObservation | None]:
    """Whether the actually-executed transforms are the ones that
    genuinely generalize - a rule that "fixes" the majority but silently
    breaks the minority (or the reverse) is a real, different failure
    from simply not knowing the right concept (see Data Quality above);
    the two are scored independently on purpose - declaring the right
    semantic type doesn't mechanically force picking the matching correct
    transform, and vice versa. This reads the student's own *final*
    resolution - Round 2 gives a real second chance at any Round 1 issue
    that wasn't resolved correctly the first time, once its own
    consequence was actually seen at Reveal 1, so a corrected final pick
    scores as correct, not as a permanently capped first mistake."""
    resolution = {**result.round1_resolution, **result.round2_resolution}
    hits = sum(1 for column, correct_keys in CORRECT_REPAIR.items() if resolution.get(column) in correct_keys)
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
    kpi_result = result.decision.get("kpi_result")
    kpi_correct = kpi_result == "corrected_12"
    readiness = result.decision.get("readiness")
    ambiguity = result.decision.get("remaining_ambiguity")
    safe_use = result.decision.get("safe_use")

    readiness_coherent = (readiness == "conditionally_ready") and (ambiguity != "nothing_remains")
    safe_use_coherent = safe_use == "this_month_sla"
    # A student can only honestly point at "whether the 2 bad timestamps
    # recur" as open if their own pipeline still shows them - a repair
    # that silently dropped every malformed row (malformed_count_reported
    # == 0) leaves nothing to have noticed a pattern in.
    ambiguity_coherent = not (ambiguity == "malformed_rows_pattern" and result.malformed_count_reported == 0)

    hits = int(kpi_correct) + int(readiness_coherent) + int(safe_use_coherent) + int(ambiguity_coherent)
    score = {4: 92.0, 3: 65.0, 2: 42.0, 1: 22.0, 0: 10.0}[hits]
    if kpi_result == "naive_29":
        return score, FeedbackObservation("lesson.l06.feedback.reported_the_naive_number", ScoreDimension.REASONING)
    if kpi_result == "corrected_12_all_month":
        return score, FeedbackObservation("lesson.l06.feedback.kpi_overclaimed_exactness", ScoreDimension.REASONING)
    if not ambiguity_coherent:
        return score, FeedbackObservation(
            "lesson.l06.feedback.ambiguity_contradicts_own_pipeline", ScoreDimension.REASONING
        )
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


def _interpretation_trajectory_observation(result: LessonSixResult) -> FeedbackObservation | None:
    """Reveal 1's interpretation is a real prediction made before the
    root-cause pivot even happens; Reveal 2's is a read of the actual
    mechanism right after seeing it. Trajectory only - this never touches
    a dimension score, just names what the sequence itself shows."""
    if result.reveal2_interpretation != "unit_drift":
        return None
    if result.reveal1_interpretation in ("ship_as_is", "assume_crash"):
        return FeedbackObservation("lesson.l06.feedback.recovered_the_read_by_reveal_two")
    return None


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
            _interpretation_trajectory_observation(result),
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

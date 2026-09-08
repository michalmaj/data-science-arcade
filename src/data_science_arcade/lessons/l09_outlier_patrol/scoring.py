from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.repair import RepairResolution
from data_science_arcade.lessons.l09_outlier_patrol.twist_data import (
    CORRECT_ANOMALY_KEY,
    CORRECT_BULK_KEY,
    CORRECT_DECIMAL_KEY,
    CORRECT_ROUND1_KEY,
    DIAGNOSIS_CORRECT_BY_FIELD,
    HIGH_REPRODUCIBILITY_ROUND1_KEYS,
    HIGH_REPRODUCIBILITY_ROUND2_KEYS,
    MASTERY_CORRECT_MUST_NOT_REMOVE,
    MASTERY_CORRECT_NEEDS_CORRECTION,
    MEDIUM_REPRODUCIBILITY_ROUND1_KEYS,
    MEDIUM_REPRODUCIBILITY_ROUND2_KEYS,
    apply_round2,
    total_exposure_state,
    typical_standard_order_state,
)

_CORRECT_PREVENTION = "entry_time_sanity_check"
_CORRECT_SEGMENT_TREATMENT = "interpret_in_context_no_auto_remove"
_CORRECT_SAFE_CLAIM = "both_numbers_scoped_honestly"
_CORRECT_CONFIRMED_DATA_ERRORS = "decimal_row_only"
_CORRECT_BULK_BASIS = "order_type_metadata"
_CORRECT_INCIDENT_TREATMENT = "keep_and_flag"

_REPORT_DEFENSIBLE = "report_defensible"
_REPORT_PROVISIONAL = "report_provisional"

# Evidence, split by the real role each fact plays in the final argument -
# not "any N of M." See _score_reasoning/_score_method below for the
# harder requirement: each of the 4 central claims below (errors, bulk,
# incident, segment) cannot be coherent without *its own* real evidence
# actually being cited, regardless of the EVIDENCE dimension's own
# separate score.
SEGMENT_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l09.evidence.segment_threshold_contrast",)
ERROR_PROVENANCE_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l09.issue.fulfillment_cost.evidence",)
BULK_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l09.issue.order_type.evidence",)
INCIDENT_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l09.issue.incident_reference.evidence",)

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    SEGMENT_EVIDENCE_KEYS + ERROR_PROVENANCE_EVIDENCE_KEYS + BULK_EVIDENCE_KEYS + INCIDENT_EVIDENCE_KEYS
)


@dataclass(frozen=True)
class LessonNineResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself."""

    round1_resolution: RepairResolution
    round2_resolution: RepairResolution
    diagnosis: dict
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_must_not_remove: frozenset[str] = frozenset()
    mastery_needs_correction: frozenset[str] = frozenset()
    initial_round1_resolution: RepairResolution = field(default_factory=dict)
    round1_revised: bool = False
    initial_round2_resolution: RepairResolution = field(default_factory=dict)
    round2_revised: bool = False

    def completed_thoughtfully(self) -> bool:
        return bool(self.round1_resolution) and bool(self.round2_resolution) and len(self.decision) > 0

    def final_typical_state(self) -> tuple[int, float]:
        dataset = apply_round2(self.round1_resolution, self.round2_resolution)
        return typical_standard_order_state(dataset)

    def final_total_state(self) -> tuple[int, float]:
        dataset = apply_round2(self.round1_resolution, self.round2_resolution)
        return total_exposure_state(dataset)

    def decimal_corrected(self) -> bool:
        return self.round2_resolution.get("fulfillment_cost") == CORRECT_DECIMAL_KEY

    def _round1_correct(self) -> bool:
        return self.round1_resolution.get("fulfillment_cost") == CORRECT_ROUND1_KEY

    def _incident_dropped(self) -> bool:
        return self.round2_resolution.get("incident_reference") == "drop_row"

    def _bulk_dropped(self) -> bool:
        return self.round2_resolution.get("order_type") == "drop_row"

    def typical_kpi_defensible(self) -> bool:
        """The typical-standard-order-cost metric's own real population
        (order_type == "standard") includes the decimal-error row and
        the documented-incident row, but never the bulk order (its own
        order_type keeps it out regardless of which Round 2 option was
        picked for it) - so this metric's defensibility depends on
        Round 1, the decimal correction, and the incident row surviving,
        but never on the bulk row's own treatment."""
        return self._round1_correct() and self.decimal_corrected() and not self._incident_dropped()

    def total_kpi_defensible(self) -> bool:
        """Total exposure needs every real order present and the decimal
        corrected - the bulk row's own treatment matters here, unlike
        for the typical metric, since total exposure has to include it."""
        return self.typical_kpi_defensible() and not self._bulk_dropped()


def _score_data_quality(result: LessonNineResult) -> tuple[float, FeedbackObservation | None]:
    """Final understanding, not the first guess: scored from the real
    executed treatment (Round 2's own picks), never from the Diagnosis
    Builder's own prior declaration - a student who diagnosed a row
    wrong but then, having actually looked at its own real provenance
    column, treats it correctly, gets full credit here. The diagnosis
    step is still real and still recorded (see
    _diagnosis_recovered_observations below), just never a scoring
    gate on its own."""
    decimal_correct = result.round2_resolution.get("fulfillment_cost") == CORRECT_DECIMAL_KEY
    bulk_correct = result.round2_resolution.get("order_type") == CORRECT_BULK_KEY
    anomaly_correct = result.round2_resolution.get("incident_reference") == CORRECT_ANOMALY_KEY
    hits = int(decimal_correct) + int(bulk_correct) + int(anomaly_correct)
    score = 100.0 * hits / 3
    if not decimal_correct:
        return score, FeedbackObservation("lesson.l09.feedback.decimal_row_mistreated", ScoreDimension.DATA_QUALITY)
    if not bulk_correct:
        return score, FeedbackObservation("lesson.l09.feedback.bulk_row_mistreated", ScoreDimension.DATA_QUALITY)
    if not anomaly_correct:
        return score, FeedbackObservation("lesson.l09.feedback.anomaly_row_mistreated", ScoreDimension.DATA_QUALITY)
    return score, FeedbackObservation("lesson.l09.feedback.every_row_correctly_treated", ScoreDimension.DATA_QUALITY)


def _segment_treatment_coherent(result: LessonNineResult, selected_evidence: set[str]) -> bool:
    """The segment-scope claim is only real and grounded if the segment
    contrast evidence was actually cited - naming the right conclusion
    without the fact that demonstrates it is a guess, not an argument."""
    if result.decision.get("segment_treatment") != _CORRECT_SEGMENT_TREATMENT:
        return False
    return bool(selected_evidence & set(SEGMENT_EVIDENCE_KEYS))


def _score_method(result: LessonNineResult) -> tuple[float, FeedbackObservation | None]:
    selected_evidence = set(result.critical_evidence_present)
    round1_correct = result.round1_resolution.get("fulfillment_cost") == CORRECT_ROUND1_KEY
    segment_correct = _segment_treatment_coherent(result, selected_evidence)
    prevention_correct = result.decision.get("prevention_action") == _CORRECT_PREVENTION
    hits = int(round1_correct) + int(segment_correct) + int(prevention_correct)
    score = {3: 94.0, 2: 68.0, 1: 40.0, 0: 15.0}[hits]
    if not round1_correct:
        return score, FeedbackObservation("lesson.l09.feedback.blanket_policy_applied", ScoreDimension.METHOD)
    if not segment_correct:
        return score, FeedbackObservation("lesson.l09.feedback.segment_scope_wrong", ScoreDimension.METHOD)
    if not prevention_correct:
        return score, FeedbackObservation("lesson.l09.feedback.no_prevention_recommended", ScoreDimension.METHOD)
    return score, None


def _reproducibility_tier(key: str | None, high: frozenset[str], medium: frozenset[str]) -> float:
    if key in high:
        return 1.0
    if key in medium:
        return 0.5
    return 0.0


def _score_reproducibility(result: LessonNineResult) -> tuple[float, FeedbackObservation | None]:
    """Whether the screening criterion and every real treatment are
    explicit, deterministic, and provenance-grounded - not whether
    they're also the objectively correct call (METHOD's own job), and
    not whether the Final Decision's own claims match the pipeline
    (REASONING's own job). A wrong-but-fully-specified blanket rule is
    still a real, restatable rule, so it earns real partial credit here,
    never a flat zero."""
    round1_tier = _reproducibility_tier(
        result.round1_resolution.get("fulfillment_cost"), HIGH_REPRODUCIBILITY_ROUND1_KEYS, MEDIUM_REPRODUCIBILITY_ROUND1_KEYS
    )
    decimal_tier = _reproducibility_tier(
        result.round2_resolution.get("fulfillment_cost"), HIGH_REPRODUCIBILITY_ROUND2_KEYS, MEDIUM_REPRODUCIBILITY_ROUND2_KEYS
    )
    bulk_tier = _reproducibility_tier(
        result.round2_resolution.get("order_type"), HIGH_REPRODUCIBILITY_ROUND2_KEYS, MEDIUM_REPRODUCIBILITY_ROUND2_KEYS
    )
    anomaly_tier = _reproducibility_tier(
        result.round2_resolution.get("incident_reference"), HIGH_REPRODUCIBILITY_ROUND2_KEYS, MEDIUM_REPRODUCIBILITY_ROUND2_KEYS
    )
    total_tier = round1_tier + decimal_tier + bulk_tier + anomaly_tier
    score = 20.0 + 20.0 * total_tier
    if total_tier < 4.0:
        return score, FeedbackObservation("lesson.l09.feedback.treatment_not_fully_grounded", ScoreDimension.REPRODUCIBILITY)
    return score, FeedbackObservation("lesson.l09.feedback.every_treatment_explicit_and_grounded", ScoreDimension.REPRODUCIBILITY)


def _bulk_basis_coherent(result: LessonNineResult, selected_evidence: set[str]) -> bool:
    """Excluding the bulk order from the typical-cost population is only
    a real, grounded claim if it's backed by the order's own real
    order_type evidence - never just because $950 looks far from the
    median. Requires the correct claim, the bulk evidence actually
    cited, and the row genuinely kept (not dropped) in the real
    pipeline."""
    if result.decision.get("bulk_order_population_basis") != _CORRECT_BULK_BASIS:
        return False
    if not (selected_evidence & set(BULK_EVIDENCE_KEYS)):
        return False
    return result.round2_resolution.get("order_type") == CORRECT_BULK_KEY


def _errors_coherent(result: LessonNineResult, selected_evidence: set[str]) -> bool:
    """Confirming the decimal row as the one real data error is only
    grounded if its own invoice-reference provenance was actually
    cited - not just because the correct option text was clicked."""
    if result.decision.get("confirmed_data_errors") != _CORRECT_CONFIRMED_DATA_ERRORS:
        return False
    if not (selected_evidence & set(ERROR_PROVENANCE_EVIDENCE_KEYS)):
        return False
    return result.round2_resolution.get("fulfillment_cost") == CORRECT_DECIMAL_KEY


def _incident_coherent(result: LessonNineResult, selected_evidence: set[str]) -> bool:
    """Claiming the anomaly row should be kept and flagged as a
    documented incident is only grounded if its own incident-reference
    evidence was actually cited."""
    if result.decision.get("incident_treatment") != _CORRECT_INCIDENT_TREATMENT:
        return False
    if not (selected_evidence & set(INCIDENT_EVIDENCE_KEYS)):
        return False
    return result.round2_resolution.get("incident_reference") == CORRECT_ANOMALY_KEY


def _kpi_defensibility_coherent(claimed_option: str | None, defensible: bool) -> bool:
    """A student who never fixed a real, nameable defect in their own
    pipeline can still be fully coherent here by correctly calling the
    result provisional - REASONING checks whether the claim matches
    reality, never whether the pipeline itself was good (DATA_QUALITY/
    METHOD's own job)."""
    expected = _REPORT_DEFENSIBLE if defensible else _REPORT_PROVISIONAL
    return claimed_option == expected


def _score_reasoning(result: LessonNineResult) -> tuple[float, FeedbackObservation | None]:
    """Coherence only - every check compares one part of the student's
    own final argument against another real fact about what they
    actually did or saw, decoupled from whether the underlying pick was
    itself correct (DATA_QUALITY's/METHOD's own job). Every reachable
    real pipeline state has an honest path here: the KPI claims are a
    defensible-vs-provisional judgment, never a guess at an exact dollar
    figure, so a student who never fixed a real defect can still be
    fully coherent by correctly calling their own result provisional."""
    selected_evidence = set(result.critical_evidence_present)

    errors_coherent = _errors_coherent(result, selected_evidence)
    bulk_coherent = _bulk_basis_coherent(result, selected_evidence)
    incident_coherent = _incident_coherent(result, selected_evidence)

    typical_kpi_coherent = _kpi_defensibility_coherent(
        result.decision.get("typical_kpi_defensibility"), result.typical_kpi_defensible()
    )
    total_kpi_coherent = _kpi_defensibility_coherent(
        result.decision.get("total_kpi_defensibility"), result.total_kpi_defensible()
    )

    safe_claim_coherent = (
        result.decision.get("safe_claim") == _CORRECT_SAFE_CLAIM and typical_kpi_coherent and total_kpi_coherent
    )

    hits = (
        int(errors_coherent)
        + int(bulk_coherent)
        + int(incident_coherent)
        + int(typical_kpi_coherent)
        + int(total_kpi_coherent)
        + int(safe_claim_coherent)
    )
    score = {6: 92.0, 5: 78.0, 4: 62.0, 3: 46.0, 2: 30.0, 1: 18.0, 0: 10.0}[hits]
    if not errors_coherent:
        return score, FeedbackObservation("lesson.l09.feedback.confirmed_errors_claim_incoherent", ScoreDimension.REASONING)
    if not bulk_coherent:
        return score, FeedbackObservation("lesson.l09.feedback.bulk_basis_not_grounded", ScoreDimension.REASONING)
    if not incident_coherent:
        return score, FeedbackObservation("lesson.l09.feedback.incident_claim_doesnt_match_execution", ScoreDimension.REASONING)
    if not typical_kpi_coherent:
        return score, FeedbackObservation("lesson.l09.feedback.typical_kpi_contradicts_own_pipeline", ScoreDimension.REASONING)
    if not total_kpi_coherent:
        return score, FeedbackObservation("lesson.l09.feedback.total_kpi_contradicts_own_pipeline", ScoreDimension.REASONING)
    if not safe_claim_coherent:
        return score, FeedbackObservation("lesson.l09.feedback.safe_claim_incoherent", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonNineResult) -> tuple[float, FeedbackObservation | None]:
    """Role-based, not "any N of M": scored from how many of the 4 real
    roles (segment, error provenance, bulk metadata, incident reference)
    are actually represented, not from a raw item count - citing two
    unrelated row facts instead of covering real breadth doesn't reach
    the top band."""
    present = set(result.critical_evidence_present)
    roles_present = sum(
        (
            bool(present & set(SEGMENT_EVIDENCE_KEYS)),
            bool(present & set(ERROR_PROVENANCE_EVIDENCE_KEYS)),
            bool(present & set(BULK_EVIDENCE_KEYS)),
            bool(present & set(INCIDENT_EVIDENCE_KEYS)),
        )
    )
    score = {4: 97.0, 3: 80.0, 2: 55.0, 1: 30.0, 0: 15.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l09.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _mastery_succeeded(result: LessonNineResult) -> bool:
    return (
        result.mastery_must_not_remove == MASTERY_CORRECT_MUST_NOT_REMOVE
        and result.mastery_needs_correction == MASTERY_CORRECT_NEEDS_CORRECTION
    )


def _diagnosis_recovered_observations(result: LessonNineResult) -> list[FeedbackObservation]:
    """The Diagnosis Builder's own prior declaration, checked only for a
    real productive-failure trajectory fact - never for scoring: a wrong
    initial diagnosis followed by the correct final treatment is a real
    recovery worth naming, not a permanent cap."""
    observations: list[FeedbackObservation] = []
    row_final_correct = {
        "decimal_row_diagnosis": result.round2_resolution.get("fulfillment_cost") == CORRECT_DECIMAL_KEY,
        "bulk_row_diagnosis": result.round2_resolution.get("order_type") == CORRECT_BULK_KEY,
        "anomaly_row_diagnosis": result.round2_resolution.get("incident_reference") == CORRECT_ANOMALY_KEY,
    }
    for field_key, correct_option in DIAGNOSIS_CORRECT_BY_FIELD.items():
        diagnosed_wrong = result.diagnosis.get(field_key) not in (None, correct_option)
        if diagnosed_wrong and row_final_correct.get(field_key):
            observations.append(FeedbackObservation("lesson.l09.feedback.diagnosis_recovered_via_treatment"))
    return observations


def _trajectory_observations(result: LessonNineResult) -> list[FeedbackObservation]:
    observations: list[FeedbackObservation] = []
    if (
        result.round1_revised
        and result.initial_round1_resolution.get("fulfillment_cost") not in (None, CORRECT_ROUND1_KEY)
        and result.round1_resolution.get("fulfillment_cost") == CORRECT_ROUND1_KEY
    ):
        observations.append(FeedbackObservation("lesson.l09.feedback.round1_recovered_via_revision"))
    if (
        result.round2_revised
        and result.initial_round2_resolution != result.round2_resolution
        and result.round2_resolution.get("fulfillment_cost") == CORRECT_DECIMAL_KEY
        and result.round2_resolution.get("order_type") == CORRECT_BULK_KEY
        and result.round2_resolution.get("incident_reference") == CORRECT_ANOMALY_KEY
    ):
        observations.append(FeedbackObservation("lesson.l09.feedback.round2_recovered_via_revision"))
    observations.extend(_diagnosis_recovered_observations(result))
    return observations


def score_lesson_nine(result: LessonNineResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    data_quality_score, data_quality_observation = _score_data_quality(result)
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    reproducibility_score, reproducibility_observation = _score_reproducibility(result)

    dimension_scores = {
        ScoreDimension.DATA_QUALITY: data_quality_score,
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.REPRODUCIBILITY: reproducibility_score,
    }

    observations = [
        observation
        for observation in (
            data_quality_observation,
            method_observation,
            reasoning_observation,
            evidence_observation,
            reproducibility_observation,
        )
        if observation is not None
    ]
    observations.extend(_trajectory_observations(result))
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l09.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

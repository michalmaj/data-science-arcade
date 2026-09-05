from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.repair import RepairResolution
from data_science_arcade.lessons.l07_missing_data_clinic.twist_data import CORRECT_TREATMENT, MASTERY_CORRECT

# The objectively correct declaration for each of the three real
# missingness cases - fixed, not branched on student state, since the
# hidden population never changes based on what the student did earlier.
# See twist_data.CORRECT_TREATMENT for the *executed*-treatment
# equivalent.
_CORRECT_MEANING = {
    "cold_pack_meaning": "structural_not_applicable",
    "promo_meaning": "explicit_category",
    "pick_minutes_meaning": "measurement_failure_legacy_peak",
}

# Which real facts matter most to cite - matched by substring on the
# picked item's real label_key, the same technique every deepened lesson
# since L04 uses.
CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    "issue.pick_minutes.evidence",
    "evidence.scanner_type_gap",
    "evidence.hour_bucket_gap",
    "sensitivity.lower_label",
)


@dataclass(frozen=True)
class LessonSevenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself."""

    cold_pack_meaning: str
    promo_meaning: str
    pick_minutes_meaning: str
    round1_resolution: RepairResolution
    round2_resolution: RepairResolution
    sensitivity_interpretation: str
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_selection: frozenset[str] = frozenset()

    def completed_thoughtfully(self) -> bool:
        return bool(self.round1_resolution) and bool(self.round2_resolution) and len(self.decision) > 0


def _score_data_quality(result: LessonSevenResult) -> tuple[float, FeedbackObservation | None]:
    hits = (
        int(result.cold_pack_meaning == _CORRECT_MEANING["cold_pack_meaning"])
        + int(result.promo_meaning == _CORRECT_MEANING["promo_meaning"])
        + int(result.pick_minutes_meaning == _CORRECT_MEANING["pick_minutes_meaning"])
    )
    score = 100.0 * hits / 3.0
    if result.pick_minutes_meaning == "random_noise":
        return score, FeedbackObservation(
            "lesson.l07.feedback.pick_minutes_called_random_noise", ScoreDimension.DATA_QUALITY
        )
    if hits == 3:
        return score, FeedbackObservation("lesson.l07.feedback.every_meaning_correct", ScoreDimension.DATA_QUALITY)
    return score, None


def _score_reproducibility(result: LessonSevenResult) -> tuple[float, FeedbackObservation | None]:
    """Whether the actually-executed treatments are the ones that
    genuinely match each column's own real meaning - a student can
    correctly declare a column's meaning (Data Quality above) and still
    pick a fabricating treatment for it, and vice versa; the two are
    scored independently on purpose, the same justification the L06
    follow-up already established for this project."""
    resolution = {**result.round1_resolution, **result.round2_resolution}
    hits = sum(1 for column, correct_keys in CORRECT_TREATMENT.items() if resolution.get(column) in correct_keys)
    score = 100.0 * hits / 3.0
    if resolution.get("pick_minutes") in ("fill_global_median", "fill_zero"):
        return score, FeedbackObservation(
            "lesson.l07.feedback.pick_minutes_naively_filled", ScoreDimension.REPRODUCIBILITY
        )
    if hits == 3:
        return score, FeedbackObservation("lesson.l07.feedback.every_treatment_matches", ScoreDimension.REPRODUCIBILITY)
    return score, None


def _score_evidence(result: LessonSevenResult) -> tuple[float, FeedbackObservation | None]:
    count = min(len(result.critical_evidence_present), 3)  # EvidenceField.max_count is 3
    score = {3: 95.0, 2: 70.0, 1: 40.0, 0: 15.0}[count]
    observation = (
        None if count >= 2 else FeedbackObservation("lesson.l07.feedback.evidence_missed_the_pattern", ScoreDimension.EVIDENCE)
    )
    return score, observation


def _score_reasoning(result: LessonSevenResult) -> tuple[float, FeedbackObservation | None]:
    """Coherence only - never "is this the objectively best answer in
    general," which is Uncertainty's and Method's own job. A range-real
    question genuinely has one right shape (does the student's own final
    argument actually match what their own pipeline produced), decoupled
    from whether that pipeline itself was the correct one to build."""
    treatment_claim = result.decision.get("treatment")
    treatment_coherent = treatment_claim == result.round2_resolution.get("pick_minutes")

    has_real_range = result.round2_resolution.get("pick_minutes") == "preserve_and_report"
    kpi_claims_range = result.decision.get("kpi_result") == "range_straddles"
    kpi_claim_coherent = kpi_claims_range == has_real_range

    diagnosis_correct = result.decision.get("missingness_diagnosis") == "legacy_peak_workflow"

    hits = int(treatment_coherent) + int(kpi_claim_coherent) + int(diagnosis_correct)
    score = {3: 92.0, 2: 60.0, 1: 32.0, 0: 12.0}[hits]
    if not treatment_coherent:
        return score, FeedbackObservation(
            "lesson.l07.feedback.claimed_treatment_doesnt_match_execution", ScoreDimension.REASONING
        )
    if not kpi_claim_coherent:
        return score, FeedbackObservation(
            "lesson.l07.feedback.kpi_claim_contradicts_own_pipeline", ScoreDimension.REASONING
        )
    if not diagnosis_correct:
        return score, FeedbackObservation("lesson.l07.feedback.diagnosis_denies_the_pattern", ScoreDimension.REASONING)
    return score, None


def _score_uncertainty(result: LessonSevenResult) -> tuple[float, FeedbackObservation | None]:
    """Process (the sensitivity reveal's own interpret click, mid-lesson)
    plus final (the Sensitivity/uncertainty Decision field's own
    conceptual-correctness) - deliberately not the kpi_result field too,
    since that field's own coherence is already Reasoning's job; scoring
    it again here under a different label would be the same click judged
    twice, not two independent signals."""
    has_real_range = result.round2_resolution.get("pick_minutes") == "preserve_and_report"
    correct_mid_choice = "range_real_undecided" if has_real_range else "range_collapsed_erased"
    mid_hit = result.sensitivity_interpretation == correct_mid_choice
    final_hit = result.decision.get("sensitivity") == "bounds_are_real_assumptions"

    hits = int(mid_hit) + int(final_hit)
    score = {2: 90.0, 1: 50.0, 0: 15.0}[hits]
    if not mid_hit and has_real_range:
        return score, FeedbackObservation(
            "lesson.l07.feedback.overclaimed_certainty_on_a_real_range", ScoreDimension.UNCERTAINTY
        )
    if not mid_hit and not has_real_range:
        return score, FeedbackObservation(
            "lesson.l07.feedback.missed_that_filling_erased_the_range", ScoreDimension.UNCERTAINTY
        )
    if result.decision.get("sensitivity") == "exact_truth_knowable":
        return score, FeedbackObservation("lesson.l07.feedback.claimed_the_exact_truth_is_knowable", ScoreDimension.UNCERTAINTY)
    return score, None


def _score_method(result: LessonSevenResult) -> tuple[float, FeedbackObservation | None]:
    treatment_correct = result.decision.get("treatment") == "preserve_and_report"
    required_action_correct = result.decision.get("required_action") == "fix_capture_path"
    hits = int(treatment_correct) + int(required_action_correct)
    score = {2: 94.0, 1: 55.0, 0: 18.0}[hits]
    if result.decision.get("required_action") == "nothing_needed":
        return score, FeedbackObservation("lesson.l07.feedback.no_systemic_fix_proposed", ScoreDimension.METHOD)
    return score, None


def _mastery_succeeded(result: LessonSevenResult) -> bool:
    return result.mastery_selection == MASTERY_CORRECT


def score_lesson_seven(result: LessonSevenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    data_quality_score, data_quality_observation = _score_data_quality(result)
    reproducibility_score, reproducibility_observation = _score_reproducibility(result)
    evidence_score, evidence_observation = _score_evidence(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    method_score, method_observation = _score_method(result)

    dimension_scores = {
        ScoreDimension.DATA_QUALITY: data_quality_score,
        ScoreDimension.REPRODUCIBILITY: reproducibility_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.UNCERTAINTY: uncertainty_score,
        ScoreDimension.METHOD: method_score,
    }

    observations = [
        observation
        for observation in (
            data_quality_observation,
            reproducibility_observation,
            evidence_observation,
            reasoning_observation,
            uncertainty_observation,
            method_observation,
        )
        if observation is not None
    ]
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l07.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

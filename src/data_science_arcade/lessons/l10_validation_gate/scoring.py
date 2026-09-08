from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.repair import RepairResolution
from data_science_arcade.lessons.l10_validation_gate.twist_data import CORRECT_BATCH_ACTION_KEY, CORRECT_ROUND1_KEY

_CORRECT_OPTIONAL_SEVERITY = "warn_at_threshold"
_CORRECT_OPTIONAL_THRESHOLD = "flag_over_2pct"
_CORRECT_INVARIANT_TOLERANCE = "small_tolerance_atol_1"
_CORRECT_INVARIANT_SEVERITY = "block"

_CORRECT_BASELINE_GATE_MEANING = "six_conditions_only"
_CORRECT_MISSING_COVERAGE = "cross_field_invariant_check"
_CORRECT_BATCH_SCOPE_DECISION = "block_whole_batch_replay"
_CORRECT_PASS_MEANING = "satisfies_written_checks_only"

_REPORT_DEFENSIBLE = "report_defensible"
_REPORT_PROVISIONAL = "report_provisional"

_OPT_OUT_GATE_VALUES = frozenset({"no_check", "no_action", "no_invariant_check"})

# Evidence, split by the real role each fact plays in the final argument -
# not "any N of M" (L08/L09 discipline). Every ComparisonRevealScene in
# this lesson sets comparisons_are_evidence=False (5 reveals x 2 values
# each would otherwise flood the Evidence step's own real layout ceiling,
# the exact bug the L09 follow-up hit and fixed) - the only evidence this
# lesson ever records comes from each reveal's own InterpretOption.
BASELINE_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l10.evidence.baseline_all_green",)
NAIVE_KPI_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l10.evidence.naive_total_published",)
INVARIANT_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l10.evidence.invariant_failure_rate",)
CONCENTRATION_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l10.evidence.concentration_by_source",)
CORRECTED_KPI_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l10.evidence.corrected_total",)

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    BASELINE_EVIDENCE_KEYS
    + NAIVE_KPI_EVIDENCE_KEYS
    + INVARIANT_EVIDENCE_KEYS
    + CONCENTRATION_EVIDENCE_KEYS
    + CORRECTED_KPI_EVIDENCE_KEYS
)


@dataclass(frozen=True)
class LessonTenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself."""

    round1_resolution: RepairResolution
    batch_action_resolution: RepairResolution
    gate_resolution: AnalyticalBrief
    decision: dict
    baseline_interpretation: str | None = None
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)
    initial_round1_resolution: RepairResolution = field(default_factory=dict)
    round1_revised: bool = False
    initial_batch_action_resolution: RepairResolution = field(default_factory=dict)
    batch_action_revised: bool = False

    def completed_thoughtfully(self) -> bool:
        return bool(self.round1_resolution) and bool(self.batch_action_resolution) and len(self.decision) > 0

    def replay_executed(self) -> bool:
        return self.batch_action_resolution.get("review_status") == CORRECT_BATCH_ACTION_KEY

    def published_total_defensible(self) -> bool:
        """A closed-form judgment over the student's own real pipeline
        state, never an enumerated dollar figure - the exact fix the L09
        follow-up made for the same class of problem (a student with an
        off-path-but-real pipeline state still needs an honest reporting
        path). The only way the final published total is genuinely
        defensible is a real block-and-replay: any other reachable state
        (approved-naive, quarantined, published-anyway, investigate-only-
        with-no-resolution) is provisional at best."""
        return self.replay_executed()

    def initially_overclaimed(self) -> bool:
        return self.initial_round1_resolution.get("review_status") == "approve_for_publication"


def _score_data_quality(result: LessonTenResult) -> tuple[float, FeedbackObservation | None]:
    severity_correct = result.gate_resolution.get("optional_field_severity") == _CORRECT_OPTIONAL_SEVERITY
    threshold_correct = result.gate_resolution.get("optional_field_threshold") == _CORRECT_OPTIONAL_THRESHOLD
    tolerance_correct = result.gate_resolution.get("invariant_tolerance") == _CORRECT_INVARIANT_TOLERANCE
    invariant_severity_correct = result.gate_resolution.get("invariant_severity") == _CORRECT_INVARIANT_SEVERITY
    hits = int(severity_correct) + int(threshold_correct) + int(tolerance_correct) + int(invariant_severity_correct)
    score = 100.0 * hits / 4
    if not tolerance_correct:
        return score, FeedbackObservation("lesson.l10.feedback.invariant_check_not_authored_well", ScoreDimension.DATA_QUALITY)
    if not invariant_severity_correct:
        return score, FeedbackObservation("lesson.l10.feedback.invariant_severity_too_low", ScoreDimension.DATA_QUALITY)
    if not severity_correct or not threshold_correct:
        return score, FeedbackObservation("lesson.l10.feedback.optional_check_miscalibrated", ScoreDimension.DATA_QUALITY)
    return score, FeedbackObservation("lesson.l10.feedback.every_check_well_calibrated", ScoreDimension.DATA_QUALITY)


def _score_method(result: LessonTenResult) -> tuple[float, FeedbackObservation | None]:
    round1_correct = result.round1_resolution.get("review_status") == CORRECT_ROUND1_KEY
    batch_action_correct = result.batch_action_resolution.get("review_status") == CORRECT_BATCH_ACTION_KEY
    severity_matches_stakes = result.gate_resolution.get("invariant_severity") == _CORRECT_INVARIANT_SEVERITY
    hits = int(round1_correct) + int(batch_action_correct) + int(severity_matches_stakes)
    score = {3: 94.0, 2: 68.0, 1: 40.0, 0: 15.0}[hits]
    if not round1_correct:
        return score, FeedbackObservation("lesson.l10.feedback.approved_naive_publication", ScoreDimension.METHOD)
    if not batch_action_correct:
        return score, FeedbackObservation("lesson.l10.feedback.batch_action_wrong", ScoreDimension.METHOD)
    if not severity_matches_stakes:
        return score, FeedbackObservation("lesson.l10.feedback.invariant_severity_doesnt_match_stakes", ScoreDimension.METHOD)
    return score, None


def _gate_field_explicit(value: str | None) -> float:
    if value is None or value in _OPT_OUT_GATE_VALUES:
        return 0.0
    return 1.0


def _score_reproducibility(result: LessonTenResult) -> tuple[float, FeedbackObservation | None]:
    """Whether the two authored checks are explicit, deterministic
    declarations at all - not whether they're also the objectively
    correct calibration (METHOD's own job). Opting out ("no check",
    "no action", "no invariant check") is a real, repeatable choice too,
    but it's the one choice that leaves nothing to reproduce."""
    total_tier = sum(
        (
            _gate_field_explicit(result.gate_resolution.get("optional_field_severity")),
            _gate_field_explicit(result.gate_resolution.get("optional_field_threshold")),
            _gate_field_explicit(result.gate_resolution.get("invariant_tolerance")),
            _gate_field_explicit(result.gate_resolution.get("invariant_severity")),
        )
    )
    score = 20.0 + 20.0 * total_tier
    if total_tier < 4.0:
        return score, FeedbackObservation("lesson.l10.feedback.checks_not_fully_specified", ScoreDimension.REPRODUCIBILITY)
    return score, FeedbackObservation("lesson.l10.feedback.every_check_explicit_and_specified", ScoreDimension.REPRODUCIBILITY)


def _baseline_coherent(result: LessonTenResult) -> bool:
    return (
        result.decision.get("baseline_gate_meaning") == _CORRECT_BASELINE_GATE_MEANING
        and result.baseline_interpretation == "six_conditions_held"
    )


def _missing_coverage_coherent(result: LessonTenResult) -> bool:
    if result.decision.get("missing_coverage") != _CORRECT_MISSING_COVERAGE:
        return False
    return result.gate_resolution.get("invariant_tolerance") != "no_invariant_check"


def _batch_scope_coherent(result: LessonTenResult) -> bool:
    if result.decision.get("batch_scope_decision") != _CORRECT_BATCH_SCOPE_DECISION:
        return False
    return result.batch_action_resolution.get("review_status") == CORRECT_BATCH_ACTION_KEY


def _pass_meaning_coherent(result: LessonTenResult) -> bool:
    return (
        result.decision.get("pass_meaning") == _CORRECT_PASS_MEANING
        and result.decision.get("baseline_gate_meaning") == _CORRECT_BASELINE_GATE_MEANING
    )


def _defensibility_coherent(result: LessonTenResult) -> bool:
    expected = _REPORT_DEFENSIBLE if result.published_total_defensible() else _REPORT_PROVISIONAL
    return result.decision.get("published_total_defensibility") == expected


def _score_reasoning(result: LessonTenResult) -> tuple[float, FeedbackObservation | None]:
    """Coherence only - every check compares one part of the student's
    own final argument against another real fact about what they
    actually did or saw, decoupled from whether the underlying pick was
    itself correct (DATA_QUALITY's/METHOD's own job)."""
    baseline_coherent = _baseline_coherent(result)
    coverage_coherent = _missing_coverage_coherent(result)
    scope_coherent = _batch_scope_coherent(result)
    pass_meaning_coherent = _pass_meaning_coherent(result)
    defensibility_coherent = _defensibility_coherent(result)

    hits = (
        int(baseline_coherent)
        + int(coverage_coherent)
        + int(scope_coherent)
        + int(pass_meaning_coherent)
        + int(defensibility_coherent)
    )
    score = {5: 92.0, 4: 74.0, 3: 56.0, 2: 38.0, 1: 22.0, 0: 10.0}[hits]
    if not baseline_coherent:
        return score, FeedbackObservation("lesson.l10.feedback.baseline_claim_incoherent", ScoreDimension.REASONING)
    if not coverage_coherent:
        return score, FeedbackObservation("lesson.l10.feedback.coverage_claim_incoherent", ScoreDimension.REASONING)
    if not scope_coherent:
        return score, FeedbackObservation("lesson.l10.feedback.batch_scope_claim_incoherent", ScoreDimension.REASONING)
    if not pass_meaning_coherent:
        return score, FeedbackObservation("lesson.l10.feedback.pass_meaning_incoherent", ScoreDimension.REASONING)
    if not defensibility_coherent:
        return score, FeedbackObservation("lesson.l10.feedback.defensibility_claim_incoherent", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(
        (
            bool(present & set(BASELINE_EVIDENCE_KEYS)),
            bool(present & set(NAIVE_KPI_EVIDENCE_KEYS)),
            bool(present & set(INVARIANT_EVIDENCE_KEYS)),
            bool(present & set(CONCENTRATION_EVIDENCE_KEYS)),
            bool(present & set(CORRECTED_KPI_EVIDENCE_KEYS)),
        )
    )
    score = {5: 97.0, 4: 82.0, 3: 62.0, 2: 42.0, 1: 24.0, 0: 12.0}[roles_present]
    if roles_present < 5:
        return score, FeedbackObservation("lesson.l10.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_overconfidence(result: LessonTenResult) -> tuple[float, FeedbackObservation | None]:
    """Before-signal: the Round 1 approve/hold pick - approving for
    publication under a green baseline gate IS the overclaiming act.
    After-signal: whether pass_meaning ends up correctly calibrated. A
    real recalibration (overclaimed at first, correctly calibrated by the
    end) earns a genuine bonus, mirroring L01's own before->after
    confidence shape - never a flat penalty just for having approved."""
    pass_meaning_correct = result.decision.get("pass_meaning") == _CORRECT_PASS_MEANING
    if pass_meaning_correct and result.initially_overclaimed():
        return 96.0, FeedbackObservation("lesson.l10.feedback.recalibrated_after_overclaiming", ScoreDimension.OVERCONFIDENCE)
    if pass_meaning_correct:
        return 82.0, None
    if result.initially_overclaimed():
        return 25.0, FeedbackObservation("lesson.l10.feedback.overclaimed_and_never_recalibrated", ScoreDimension.OVERCONFIDENCE)
    return 45.0, FeedbackObservation("lesson.l10.feedback.pass_meaning_overclaims", ScoreDimension.OVERCONFIDENCE)


def _trajectory_observations(result: LessonTenResult) -> list[FeedbackObservation]:
    observations: list[FeedbackObservation] = []
    if (
        result.round1_revised
        and result.initial_round1_resolution.get("review_status") not in (None, CORRECT_ROUND1_KEY)
        and result.round1_resolution.get("review_status") == CORRECT_ROUND1_KEY
    ):
        observations.append(FeedbackObservation("lesson.l10.feedback.round1_recovered_via_revision"))
    if (
        result.batch_action_revised
        and result.initial_batch_action_resolution.get("review_status") not in (None, CORRECT_BATCH_ACTION_KEY)
        and result.batch_action_resolution.get("review_status") == CORRECT_BATCH_ACTION_KEY
    ):
        observations.append(FeedbackObservation("lesson.l10.feedback.batch_action_recovered_via_revision"))
    return observations


def _mastery_succeeded(result: LessonTenResult) -> bool:
    return (
        result.mastery_result.get("mastery_missing_rule") == "cross_field_invariant_check"
        and result.mastery_result.get("mastery_severity") == "block"
        and result.mastery_result.get("mastery_pass_meaning") == "satisfies_written_checks_only"
    )


def score_lesson_ten(result: LessonTenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    data_quality_score, data_quality_observation = _score_data_quality(result)
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    reproducibility_score, reproducibility_observation = _score_reproducibility(result)
    overconfidence_score, overconfidence_observation = _score_overconfidence(result)

    dimension_scores = {
        ScoreDimension.DATA_QUALITY: data_quality_score,
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.REPRODUCIBILITY: reproducibility_score,
        ScoreDimension.OVERCONFIDENCE: overconfidence_score,
    }

    observations = [
        observation
        for observation in (
            data_quality_observation,
            method_observation,
            reasoning_observation,
            evidence_observation,
            reproducibility_observation,
            overconfidence_observation,
        )
        if observation is not None
    ]
    observations.extend(_trajectory_observations(result))
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l10.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

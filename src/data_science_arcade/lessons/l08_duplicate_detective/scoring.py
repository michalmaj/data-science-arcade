from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.repair import RepairResolution
from data_science_arcade.lessons.l08_duplicate_detective.twist_data import (
    CORRECT_CONFLICT_POLICY,
    CORRECT_DEDUPE_KEY,
    CORRECT_VERDICT_BY_GROUP,
    MASTERY_CORRECT_KEY,
    MASTERY_CORRECT_PRESERVE,
    apply_round2,
    captured_summary,
)

# The one, always-true correct answer for each Final Decision field with a
# single fixed correct option, regardless of path.
_CORRECT_OBSERVATION_UNIT = "paid_orders_with_captured_payment"
_CORRECT_DUPLICATE_DEFINITION = "shared_event_id"
_CORRECT_LEGITIMATE_REPEATS = frozenset({"multiple_lifecycle_events", "multiple_payment_attempts", "repeat_purchases"})
_CORRECT_PREVENTION = "idempotent_ingestion_and_uniqueness_validation"

# Real final (count, gmv) states this lesson's own real pipelines can
# land on, mapped to the one Final Decision option that honestly
# describes that state - an explicit mapping, never a boolean
# equivalence against a single option (the exact bug class the L07
# safety-and-coherence pass fixed: a wrong option must never pass just
# because another option also fails). Any real state not in this map
# (e.g. a keep_last-after-correct-round1 995/20) has no listed option
# that honestly describes it, so every kpi_result claim is incoherent
# there - correctly, since no real policy the game offers reaches it
# safely either.
_KPI_OPTION_BY_STATE: dict[tuple[int, float], str] = {
    (0, 0.0): "zero_orders_0",
    (19, 950.0): "nineteen_orders_950_one_excluded",
    (20, 1000.0): "twenty_orders_1000_no_caveats",
    (21, 1045.0): "twentyone_rows_1045",
}

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    "lesson.l08.evidence.event_id_duplicate_count",
    "lesson.l08.group.retry.evidence",
    "lesson.l08.group.decoy.evidence",
    "lesson.l08.group.conflict.evidence",
)


@dataclass(frozen=True)
class LessonEightResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself."""

    round1_resolution: RepairResolution
    round2_resolution: RepairResolution
    group_verdicts: dict[str, str]
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_key_choice: str = ""
    mastery_preserve_selection: frozenset[str] = frozenset()
    initial_round1_resolution: RepairResolution = field(default_factory=dict)
    round1_revised: bool = False

    def completed_thoughtfully(self) -> bool:
        return bool(self.round1_resolution) and bool(self.round2_resolution) and len(self.decision) > 0

    def final_captured_summary(self) -> tuple[int, float]:
        dataset = apply_round2(self.round1_resolution, self.round2_resolution)
        return captured_summary(dataset)


def _score_data_quality(result: LessonEightResult) -> tuple[float, FeedbackObservation | None]:
    hits = sum(
        1
        for group_key, correct_verdict in CORRECT_VERDICT_BY_GROUP.items()
        if result.group_verdicts.get(group_key) == correct_verdict
    )
    score = 100.0 * hits / len(CORRECT_VERDICT_BY_GROUP)
    if result.group_verdicts.get("replay_group") != CORRECT_VERDICT_BY_GROUP["replay_group"]:
        return score, FeedbackObservation(
            "lesson.l08.feedback.replay_group_misjudged", ScoreDimension.DATA_QUALITY
        )
    if result.group_verdicts.get("conflict_group") != CORRECT_VERDICT_BY_GROUP["conflict_group"]:
        return score, FeedbackObservation(
            "lesson.l08.feedback.conflict_group_misjudged", ScoreDimension.DATA_QUALITY
        )
    if hits == len(CORRECT_VERDICT_BY_GROUP):
        return score, FeedbackObservation("lesson.l08.feedback.every_group_correctly_judged", ScoreDimension.DATA_QUALITY)
    return score, None


def _score_method(result: LessonEightResult) -> tuple[float, FeedbackObservation | None]:
    dedupe_correct = result.round1_resolution.get("event_id") == CORRECT_DEDUPE_KEY
    conflict_correct = result.round2_resolution.get("amount") == CORRECT_CONFLICT_POLICY
    prevention_correct = result.decision.get("prevention_recommendation") == _CORRECT_PREVENTION
    hits = int(dedupe_correct) + int(conflict_correct) + int(prevention_correct)
    score = {3: 94.0, 2: 68.0, 1: 40.0, 0: 15.0}[hits]
    if result.decision.get("prevention_recommendation") == "nothing_needed":
        return score, FeedbackObservation("lesson.l08.feedback.no_prevention_recommended", ScoreDimension.METHOD)
    if not conflict_correct:
        return score, FeedbackObservation("lesson.l08.feedback.conflict_not_quarantined", ScoreDimension.METHOD)
    return score, None


def _score_reasoning(result: LessonEightResult) -> tuple[float, FeedbackObservation | None]:
    """Coherence only - every check here compares one part of the
    student's own final argument against another real fact about what
    they actually did, decoupled from whether what they did was itself
    the objectively correct choice (Method's/Data Quality's own job)."""
    observation_unit_correct = result.decision.get("observation_unit") == _CORRECT_OBSERVATION_UNIT
    dedupe_key_coherent = result.decision.get("dedupe_key") == result.round1_resolution.get("event_id")
    conflict_policy_coherent = result.decision.get("conflict_policy") == result.round2_resolution.get("amount")

    count, gmv = result.final_captured_summary()
    expected_kpi_option = _KPI_OPTION_BY_STATE.get((count, round(gmv, 2)))
    kpi_coherent = expected_kpi_option is not None and result.decision.get("kpi_result") == expected_kpi_option

    safe_claim_coherent = (
        result.decision.get("safe_claim") == "one_conflicting_payment_excluded_pending_reconciliation"
        and result.round2_resolution.get("amount") == CORRECT_CONFLICT_POLICY
    )

    hits = (
        int(observation_unit_correct)
        + int(dedupe_key_coherent)
        + int(conflict_policy_coherent)
        + int(kpi_coherent)
        + int(safe_claim_coherent)
    )
    score = {5: 92.0, 4: 75.0, 3: 55.0, 2: 38.0, 1: 22.0, 0: 10.0}[hits]
    if not observation_unit_correct:
        return score, FeedbackObservation("lesson.l08.feedback.observation_unit_wrong", ScoreDimension.REASONING)
    if not dedupe_key_coherent:
        return score, FeedbackObservation(
            "lesson.l08.feedback.dedupe_key_claim_doesnt_match_execution", ScoreDimension.REASONING
        )
    if not conflict_policy_coherent:
        return score, FeedbackObservation(
            "lesson.l08.feedback.conflict_policy_claim_doesnt_match_execution", ScoreDimension.REASONING
        )
    if not kpi_coherent:
        return score, FeedbackObservation("lesson.l08.feedback.kpi_claim_contradicts_own_pipeline", ScoreDimension.REASONING)
    if not safe_claim_coherent:
        return score, FeedbackObservation("lesson.l08.feedback.safe_claim_incoherent", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonEightResult) -> tuple[float, FeedbackObservation | None]:
    count = min(len(result.critical_evidence_present), 3)  # EvidenceField.max_count is 3
    score = {3: 95.0, 2: 70.0, 1: 40.0, 0: 15.0}[count]
    observation = (
        None if count >= 2 else FeedbackObservation("lesson.l08.feedback.evidence_missed_the_pattern", ScoreDimension.EVIDENCE)
    )
    return score, observation


def _score_reproducibility(result: LessonEightResult) -> tuple[float, FeedbackObservation | None]:
    """Whether the student picked a real, stated, deterministic rule -
    not whether they picked the single best one (Method's own job).
    Deliberately not identical to Method's own hit set: keep_higher_amount
    is a real, articulated rule (unlike keep-first/keep-last, bare
    tie-break defaults with no stated rationale), so it earns partial
    credit here while scoring zero on Method's stricter hit - a real,
    testable discrimination case."""
    dedupe_key_deterministic = result.round1_resolution.get("event_id") == CORRECT_DEDUPE_KEY
    conflict_policy_stated = result.round2_resolution.get("amount") in (CORRECT_CONFLICT_POLICY, "keep_higher_amount")
    hits = int(dedupe_key_deterministic) + int(conflict_policy_stated)
    score = {2: 90.0, 1: 50.0, 0: 15.0}[hits]
    if not conflict_policy_stated:
        return score, FeedbackObservation("lesson.l08.feedback.conflict_policy_not_a_real_rule", ScoreDimension.REPRODUCIBILITY)
    return score, None


def _mastery_succeeded(result: LessonEightResult) -> bool:
    return result.mastery_key_choice == MASTERY_CORRECT_KEY and result.mastery_preserve_selection == MASTERY_CORRECT_PRESERVE


def _trajectory_observations(result: LessonEightResult) -> list[FeedbackObservation]:
    observations: list[FeedbackObservation] = []
    if (
        result.round1_revised
        and result.initial_round1_resolution.get("event_id") not in (None, CORRECT_DEDUPE_KEY)
        and result.round1_resolution.get("event_id") == CORRECT_DEDUPE_KEY
    ):
        observations.append(FeedbackObservation("lesson.l08.feedback.dedupe_key_recovered_via_revision"))
    return observations


def score_lesson_eight(result: LessonEightResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l08.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.repair import RepairResolution
from data_science_arcade.lessons.l08_duplicate_detective.twist_data import (
    CORRECT_CONFLICT_POLICY,
    CORRECT_DEDUPE_KEY,
    CORRECT_VERDICT_BY_GROUP,
    HIGH_REPRODUCIBILITY_ROUND1_KEYS,
    HIGH_REPRODUCIBILITY_ROUND2_KEYS,
    MASTERY_CORRECT_KEY,
    MASTERY_CORRECT_PRESERVE,
    MEDIUM_REPRODUCIBILITY_ROUND1_KEYS,
    MEDIUM_REPRODUCIBILITY_ROUND2_KEYS,
    apply_round2,
    captured_state,
)

# The one, always-true correct answer for each Final Decision field with a
# single fixed correct option, regardless of path.
_CORRECT_OBSERVATION_UNIT = "paid_orders_with_captured_payment"
_CORRECT_IDENTITY_KEY = "shared_event_id"
_CORRECT_LEGITIMATE_REPEATS = frozenset({"multiple_lifecycle_events", "multiple_payment_attempts", "repeat_purchases"})
_CORRECT_PREVENTION = "idempotent_ingestion_and_uniqueness_validation"
_CORRECT_SAFE_CLAIM = "twenty_confirmed_range_disclosed"

# Real final (count, low, high) states this lesson's own real pipelines
# can land on, mapped to the one Final Decision option that honestly
# describes that state - an explicit mapping, never a boolean
# equivalence against a single option (the exact bug class the L07
# safety-and-coherence pass fixed: a wrong option must never pass just
# because another option also fails). low == high whenever a path leaves
# no genuinely disputed amount behind. Any real state not in this map
# (e.g. a keep_last-after-correct-round1 995/20, a single exact value)
# has no listed option that honestly describes it, so every kpi_result
# claim is incoherent there - correctly, since no real policy the game
# offers reaches it safely either.
_KPI_OPTION_BY_STATE: dict[tuple[int, float, float], str] = {
    (0, 0.0, 0.0): "zero_orders_0",
    (20, 995.0, 1000.0): "twenty_orders_range_995_to_1000",
    (20, 1000.0, 1000.0): "twenty_orders_1000_no_caveats",
    (21, 1045.0, 1045.0): "twentyone_rows_1045",
}

# Evidence, split by the real role each fact plays in the final argument
# - a role-based check, not "any 3 of N critical facts." A full Evidence
# score requires the conflict fact specifically (the central evidence
# once the final claim is about an unresolved amount) plus at least one
# real identity/legitimate-repeat fact, never an arbitrary combination.
IDENTITY_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l08.evidence.event_id_duplicate_count",)
LEGITIMATE_REPEAT_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l08.group.retry.evidence", "lesson.l08.group.decoy.evidence")
CONFLICT_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l08.group.conflict.evidence", "lesson.l08.issue.amount.evidence")
"""Two real citable facts describe the exact same conflict: the twist
group's own verdict-gated evidence, and Round 2's own issue.amount.evidence
(recorded unconditionally, regardless of which conflict-policy option
gets picked - RepairIssue.evidence_key always fires once an issue is
resolved). Citing either one counts: a student who first misjudged the
twist group (no group evidence recorded) but genuinely saw the conflict
via Round 2 and picked the correct reconciliation policy has real,
citable proof of the same fact - productive failure, not a dead end."""

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = IDENTITY_EVIDENCE_KEYS + LEGITIMATE_REPEAT_EVIDENCE_KEYS + CONFLICT_EVIDENCE_KEYS


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

    def final_captured_state(self) -> tuple[int, float, float]:
        dataset = apply_round2(self.round1_resolution, self.round2_resolution)
        return captured_state(dataset)


def _score_data_quality(result: LessonEightResult) -> tuple[float, FeedbackObservation | None]:
    group_hits = sum(
        1
        for group_key, correct_verdict in CORRECT_VERDICT_BY_GROUP.items()
        if result.group_verdicts.get(group_key) == correct_verdict
    )
    legitimate_repeats_correct = set(result.decision.get("legitimate_repeats", ())) == _CORRECT_LEGITIMATE_REPEATS
    hits = group_hits + int(legitimate_repeats_correct)
    total = len(CORRECT_VERDICT_BY_GROUP) + 1
    score = 100.0 * hits / total
    if result.group_verdicts.get("replay_group") != CORRECT_VERDICT_BY_GROUP["replay_group"]:
        return score, FeedbackObservation(
            "lesson.l08.feedback.replay_group_misjudged", ScoreDimension.DATA_QUALITY
        )
    if result.group_verdicts.get("conflict_group") != CORRECT_VERDICT_BY_GROUP["conflict_group"]:
        return score, FeedbackObservation(
            "lesson.l08.feedback.conflict_group_misjudged", ScoreDimension.DATA_QUALITY
        )
    if not legitimate_repeats_correct:
        return score, FeedbackObservation(
            "lesson.l08.feedback.legitimate_repeats_incorrect", ScoreDimension.DATA_QUALITY
        )
    if hits == total:
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


def _identity_key_coherent(result: LessonEightResult) -> bool:
    """Claiming "shared event ID" is only really grounded if the
    student's own group verdicts actually demonstrate it - the replay
    and conflict groups are the two real cases that share one; getting
    the definition right while still misjudging either of those isn't a
    real, evidenced claim, just a lucky guess."""
    if result.decision.get("identity_key") != _CORRECT_IDENTITY_KEY:
        return False
    return (
        result.group_verdicts.get("replay_group") == CORRECT_VERDICT_BY_GROUP["replay_group"]
        and result.group_verdicts.get("conflict_group") == CORRECT_VERDICT_BY_GROUP["conflict_group"]
    )


def _score_reasoning(result: LessonEightResult) -> tuple[float, FeedbackObservation | None]:
    """Coherence only - every check here compares one part of the
    student's own final argument against another real fact about what
    they actually did, decoupled from whether what they did was itself
    the objectively correct choice (Method's/Data Quality's own job)."""
    observation_unit_correct = result.decision.get("observation_unit") == _CORRECT_OBSERVATION_UNIT
    identity_key_coherent = _identity_key_coherent(result)
    removal_rule_coherent = result.decision.get("automatic_removal_rule") == result.round1_resolution.get("event_id")
    conflict_policy_coherent = result.decision.get("conflict_policy") == result.round2_resolution.get("amount")

    count, low, high = result.final_captured_state()
    expected_kpi_option = _KPI_OPTION_BY_STATE.get((count, round(low, 2), round(high, 2)))
    kpi_coherent = expected_kpi_option is not None and result.decision.get("kpi_result") == expected_kpi_option

    safe_claim_coherent = (
        result.decision.get("safe_claim") == _CORRECT_SAFE_CLAIM
        and result.round2_resolution.get("amount") == CORRECT_CONFLICT_POLICY
    )

    hits = (
        int(observation_unit_correct)
        + int(identity_key_coherent)
        + int(removal_rule_coherent)
        + int(conflict_policy_coherent)
        + int(kpi_coherent)
        + int(safe_claim_coherent)
    )
    score = {6: 92.0, 5: 78.0, 4: 62.0, 3: 46.0, 2: 30.0, 1: 18.0, 0: 10.0}[hits]
    if not observation_unit_correct:
        return score, FeedbackObservation("lesson.l08.feedback.observation_unit_wrong", ScoreDimension.REASONING)
    if not identity_key_coherent:
        return score, FeedbackObservation("lesson.l08.feedback.identity_key_not_grounded", ScoreDimension.REASONING)
    if not removal_rule_coherent:
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
    """Role-based, not "any 3 of N": the conflict fact is the central
    evidence for a final argument about an unresolved amount, so full
    credit requires it specifically, plus at least one real identity or
    legitimate-repeat fact - never an arbitrary combination that happens
    to skip the one fact the argument actually rests on."""
    present = set(result.critical_evidence_present)
    has_conflict = bool(present & set(CONFLICT_EVIDENCE_KEYS))
    has_identity_or_legitimate = bool(present & (set(IDENTITY_EVIDENCE_KEYS) | set(LEGITIMATE_REPEAT_EVIDENCE_KEYS)))
    if has_conflict and has_identity_or_legitimate:
        score = 95.0
    elif has_conflict or has_identity_or_legitimate:
        score = 55.0
    else:
        score = 15.0
    if not has_conflict:
        return score, FeedbackObservation("lesson.l08.feedback.evidence_missing_conflict_fact", ScoreDimension.EVIDENCE)
    if not has_identity_or_legitimate:
        return score, FeedbackObservation("lesson.l08.feedback.evidence_missed_the_pattern", ScoreDimension.EVIDENCE)
    return score, None


def _reproducibility_tier(key: str | None, high: frozenset[str], medium: frozenset[str]) -> float:
    if key in high:
        return 1.0
    if key in medium:
        return 0.5
    return 0.0


def _score_reproducibility(result: LessonEightResult) -> tuple[float, FeedbackObservation | None]:
    """Whether the key/criterion and the tie-break/reconciliation rule
    are both explicit and repeatable - not whether they're also the
    single best choice (Method's own job). A methodologically wrong but
    fully deterministic policy (dedupe_by_order_id) still scores real
    credit here; a real but row-order-dependent rule (keep_first/
    keep_last) scores partial credit, since its own real-world
    reproducibility depends on an unstated assumption about arrival
    order, not just on the rule being named."""
    round1_tier = _reproducibility_tier(
        result.round1_resolution.get("event_id"), HIGH_REPRODUCIBILITY_ROUND1_KEYS, MEDIUM_REPRODUCIBILITY_ROUND1_KEYS
    )
    round2_tier = _reproducibility_tier(
        result.round2_resolution.get("amount"), HIGH_REPRODUCIBILITY_ROUND2_KEYS, MEDIUM_REPRODUCIBILITY_ROUND2_KEYS
    )
    score = 20.0 + 40.0 * (round1_tier + round2_tier)
    if round1_tier < 1.0 or round2_tier < 1.0:
        return score, FeedbackObservation("lesson.l08.feedback.dedupe_relies_on_row_order", ScoreDimension.REPRODUCIBILITY)
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

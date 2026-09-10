from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

_CORRECT_GROUP_BY = "by_store"  # GroupByOption.key, not its own .column ("store_id")
_CORRECT_METRIC_OPTION: dict[str, str] = {
    "orders": "count_order_id",
    "revenue": "sum_revenue",
    "unique_customers": "nunique_customer_id",
    "aov": "mean_revenue",
}
_CORRECT_NETWORK_CUSTOMER_METHOD = "distinct_network_wide"
_CORRECT_NETWORK_AOV_METHOD = "order_level_or_weighted"
_CORRECT_RAW_OBSERVATION_UNIT = "order"
_CORRECT_REQUIRED_GRAIN = "store"
_SAFE_ROLLUP_METRICS = frozenset({"orders", "revenue"})

# Evidence, role-based (never "any N of M" - established L08-L11 discipline).
# Every ComparisonRevealScene reveal in this lesson sets
# comparisons_are_evidence=False; the only evidence recorded comes from
# each reveal's own interpret-click evidence_key, and every option at
# every one of these four reveals shares the same key - none of them has
# its own revision path, so gating Evidence behind the correct
# interpretation would repeat the exact bug L11's own follow-up (PR #72)
# had to fix after the fact. output_grain_role is also update-by-key: it
# starts describing whatever the student's FIRST group key actually
# produced, and is re-recorded (same key) if the store-summary revision
# changes the group key - never two contradictory items.
OUTPUT_GRAIN_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l12.evidence.output_grain",)
REPEAT_CUSTOMER_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l12.evidence.repeat_customer",)
CUSTOMER_ROLLUP_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l12.evidence.customer_rollup",)
AOV_ROLLUP_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l12.evidence.aov_rollup",)

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    OUTPUT_GRAIN_EVIDENCE_KEYS + REPEAT_CUSTOMER_EVIDENCE_KEYS + CUSTOMER_ROLLUP_EVIDENCE_KEYS + AOV_ROLLUP_EVIDENCE_KEYS
)

_METRIC_SLOT_ORDER: tuple[str, ...] = ("orders", "revenue", "unique_customers", "aov")


@dataclass(frozen=True)
class LessonTwelveResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `group_by`/`metric_choices` are the store-summary pipeline's own
    FINAL state - after the stage-5 revision opportunity, never the cold
    first pass (there is no separate prior-pass field for these; the
    revision itself already replaces them, matching how a fresh
    AggregationBuilderScene instance simply overwrites its own prior
    picks). `rollup_prior`/`rollup_revised_picks` are the two network
    roll-up method fields' own prior-then-revised pass, kept genuinely
    separate from `decision`'s own final network_customer_method/
    network_aov_method fields - Final Decision is not a substitute for
    the stage-10 revision, and the stage-10 revision is not silently
    discarded either; each has its own real, distinct role."""

    group_by: str | None
    metric_choices: dict[str, str]
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    rollup_prior: dict[str, str] = field(default_factory=dict)
    rollup_revised_picks: dict[str, str] | None = None
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return bool(self.group_by) and len(self.decision) > 0


def _method_hits(result: LessonTwelveResult) -> list[tuple[bool, str]]:
    """(is_correct, feedback_key) pairs in a fixed, checked-in-order
    sequence - group key first, then each metric slot in its own build
    order, then the two network roll-up methods."""
    hits = [(result.group_by == _CORRECT_GROUP_BY, "lesson.l12.feedback.group_by_wrong")]
    for slot_key in _METRIC_SLOT_ORDER:
        hits.append(
            (
                result.metric_choices.get(slot_key) == _CORRECT_METRIC_OPTION[slot_key],
                f"lesson.l12.feedback.{slot_key}_metric_wrong",
            )
        )
    hits.append((result.decision.get("network_customer_method") == _CORRECT_NETWORK_CUSTOMER_METHOD, "lesson.l12.feedback.network_customer_method_wrong"))
    hits.append((result.decision.get("network_aov_method") == _CORRECT_NETWORK_AOV_METHOD, "lesson.l12.feedback.network_aov_method_wrong"))
    return hits


def _score_method(result: LessonTwelveResult) -> tuple[float, FeedbackObservation | None]:
    """Breadth: how much of the real 7-fact pipeline (group key, 4
    metric-slot definitions, 2 network roll-up methods) is correct in
    its FINAL state. Scored on the pipeline's own post-revision state,
    never the cold first pass - the stage-5 revision offer exists
    precisely so an early miss on any of these 7 facts is never a
    permanent cap, matching every prior lesson's own productive-failure
    discipline."""
    checks = _method_hits(result)
    hits = sum(1 for correct, _ in checks if correct)
    score = {7: 96.0, 6: 84.0, 5: 71.0, 4: 58.0, 3: 45.0, 2: 32.0, 1: 19.0, 0: 8.0}[hits]
    for correct, feedback_key in checks:
        if not correct:
            return score, FeedbackObservation(feedback_key, ScoreDimension.METHOD)
    return score, None


def _grain_understood(result: LessonTwelveResult) -> bool:
    """A pure comprehension check against the NORMATIVE grain the
    requested table requires - not against whatever the student's own
    pipeline actually produced. A student stuck with a wrong (e.g.
    customer-level) pipeline can still honestly say what the table
    SHOULD have been, and REASONING credits that separately from
    METHOD's own pipeline-correctness score."""
    return (
        result.decision.get("raw_observation_unit") == _CORRECT_RAW_OBSERVATION_UNIT
        and result.decision.get("grouped_output_grain") == _CORRECT_REQUIRED_GRAIN
    )


def _safe_rollup_customers_coherent(result: LessonTwelveResult) -> bool:
    if result.decision.get("network_customer_method") != _CORRECT_NETWORK_CUSTOMER_METHOD:
        return True
    return "unique_customers" not in set(result.decision.get("safe_rollup_metrics", ()))


def _safe_rollup_aov_coherent(result: LessonTwelveResult) -> bool:
    if result.decision.get("network_aov_method") != _CORRECT_NETWORK_AOV_METHOD:
        return True
    return "aov" not in set(result.decision.get("safe_rollup_metrics", ()))


def _score_reasoning(result: LessonTwelveResult) -> tuple[float, FeedbackObservation | None]:
    """Grain/estimand coherence, not raw correctness - every check
    compares one part of the student's own final argument against
    another real fact about what they claimed, decoupled from whether
    the underlying pipeline itself was correct (METHOD's own job)."""
    grain_understood = _grain_understood(result)
    customers_coherent = _safe_rollup_customers_coherent(result)
    aov_coherent = _safe_rollup_aov_coherent(result)

    hits = int(grain_understood) + int(customers_coherent) + int(aov_coherent)
    score = {3: 93.0, 2: 63.0, 1: 34.0, 0: 12.0}[hits]
    if not grain_understood:
        return score, FeedbackObservation("lesson.l12.feedback.grain_not_understood", ScoreDimension.REASONING)
    if not customers_coherent:
        return score, FeedbackObservation("lesson.l12.feedback.safe_rollup_customers_incoherent", ScoreDimension.REASONING)
    if not aov_coherent:
        return score, FeedbackObservation("lesson.l12.feedback.safe_rollup_aov_incoherent", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwelveResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(
        (
            bool(present & set(OUTPUT_GRAIN_EVIDENCE_KEYS)),
            bool(present & set(REPEAT_CUSTOMER_EVIDENCE_KEYS)),
            bool(present & set(CUSTOMER_ROLLUP_EVIDENCE_KEYS)),
            bool(present & set(AOV_ROLLUP_EVIDENCE_KEYS)),
        )
    )
    score = {4: 97.0, 3: 80.0, 2: 55.0, 1: 30.0, 0: 12.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l12.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _trajectory_observations(result: LessonTwelveResult) -> list[FeedbackObservation]:
    """Fires only for a change that genuinely happened AT the stage-10
    revision itself (stage-7 prior wrong -> stage-10 revised correct) -
    never inferred from "prior differs from wherever Final Decision ends
    up," which would misattribute credit to a change the revision step
    itself never made (the exact bug the L11 follow-up found and fixed).
    Final Decision's own network_customer_method/network_aov_method
    fields are METHOD's own scored facts and are never used here."""
    observations: list[FeedbackObservation] = []
    revised = result.rollup_revised_picks
    if revised is None:
        return observations
    prior = result.rollup_prior
    if prior.get("network_customer_method") != _CORRECT_NETWORK_CUSTOMER_METHOD and revised.get("network_customer_method") == _CORRECT_NETWORK_CUSTOMER_METHOD:
        observations.append(FeedbackObservation("lesson.l12.feedback.customer_method_recovered_via_revision"))
    if prior.get("network_aov_method") != _CORRECT_NETWORK_AOV_METHOD and revised.get("network_aov_method") == _CORRECT_NETWORK_AOV_METHOD:
        observations.append(FeedbackObservation("lesson.l12.feedback.aov_method_recovered_via_revision"))
    return observations


def _mastery_succeeded(result: LessonTwelveResult) -> bool:
    """Two SEPARATE judgments, each requiring its own genuinely relevant
    supporting fact - not one combined judgment accepting either fact as
    interchangeable support. Customer overlap justifies why unique
    purchasers can't be summed across channels; it says nothing about
    whether the average value per conversion needs weighting, and vice
    versa for channel-volume differences. Treating them as interchangeable
    was exactly the "correct claim + unrelated true fact" regression
    pattern L03/L04/L11 all needed a guard for - this requires the
    correct evidence-to-claim PAIRING for both judgments, not just one
    real fact cited somewhere in the pile."""
    evidence = set(result.mastery_result.get("mastery_supporting_evidence", ()))

    purchaser_sum_correct = result.mastery_result.get("mastery_purchaser_sum") == "cant_sum_overlap"
    purchaser_sum_evidenced = "customers_overlap_channels" in evidence

    avg_value_correct = result.mastery_result.get("mastery_avg_value_method") == "raw_or_weighted"
    avg_value_evidenced = "channel_volumes_differ" in evidence

    return purchaser_sum_correct and purchaser_sum_evidenced and avg_value_correct and avg_value_evidenced


def score_lesson_twelve(result: LessonTwelveResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l12.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

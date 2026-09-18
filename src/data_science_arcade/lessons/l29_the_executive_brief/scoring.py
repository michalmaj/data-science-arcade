from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.findings import FindingChoices
from data_science_arcade.lessons.l29_the_executive_brief.findings import CORRECT_FINDING_KEYS, LEAD_FINDING_KEY, ON_TOPIC_FINDING_KEYS

_CORRECT_RECOMMENDATION = "keep_and_monitor_returns"
_OVERCLAIM_RECOMMENDATION = "expand_everywhere_no_monitoring"
_UNDERCLAIM_RECOMMENDATION = "revert_immediately"

_CORRECT_CAVEAT = "competitor_redesigned_too"

_CALIBRATED_CONFIDENCE = "high_sustained_with_consistent_evidence"
_OVERCLAIM_CONFIDENCE = "very_high_a_clear_triumph"
_UNDERCLAIM_CONFIDENCE = "low_could_be_noise"

CHART_FINDING_BY_OPTION: dict[str, str] = {
    "checkout_completion_over_time": "checkout_completion",
    "payment_step_abandonment_over_time": "payment_step_abandonment",
    "order_value_and_returns_steady_over_time": "order_value_and_returns_steady",
    "social_mentions_over_time": "social_mentions",
    "stock_price_over_time": "stock_price",
}
"""Which real finding each `supporting_chart` option is an exhibit for -
used to check chart/lead CONSISTENCY (does the student's own chart match
their own stated lead), never a fixed correct answer on its own."""


@dataclass(frozen=True)
class LessonTwentyNineResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `shortlist_choices` is Cut 1's real 5-of-8 pick (which findings bear
    on the stated decision at all). `cited_finding_keys` is Cut 2's real
    3-of-5 citation (the true headline set), resolved from `context.evidence`
    by the caller - see scenario.py's own `_cited_finding_keys` helper.
    No revision pass exists in this lesson (see scenario.py's own
    docstring for why), so there is no initial-vs-final distinction to
    keep here, unlike every sibling lesson's own Result dataclass."""

    shortlist_choices: FindingChoices
    cited_finding_keys: frozenset[str]
    decision: dict
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return len(self.shortlist_choices) > 0 and len(self.decision) > 0


def _score_reasoning(result: LessonTwentyNineResult) -> tuple[float, FeedbackObservation | None]:
    """Two real, independent checks: did the shortlist (Cut 1) correctly
    exclude every finding with no given connection to the stated
    decision, and does the final recommendation follow from the evidence
    actually cited."""
    shortlist_correct = set(result.shortlist_choices) == ON_TOPIC_FINDING_KEYS
    recommendation_correct = result.decision.get("recommendation") == _CORRECT_RECOMMENDATION
    hits = sum((shortlist_correct, recommendation_correct))
    score = {2: 92.0, 1: 50.0, 0: 15.0}[hits]
    if not shortlist_correct:
        return score, FeedbackObservation("lesson.l29.feedback.shortlist_not_decision_relevant", ScoreDimension.REASONING)
    if not recommendation_correct:
        return score, FeedbackObservation("lesson.l29.feedback.recommendation_not_supported", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonTwentyNineResult) -> tuple[float, FeedbackObservation | None]:
    """Cut 2's own real 3-of-5 citation, scored against the true
    3-finding headline set - reads `cited_finding_keys` only, the
    FINAL citation, independent of whether Cut 1's own shortlist was
    itself fully correct (see independence scenario D)."""
    hits = len(result.cited_finding_keys & CORRECT_FINDING_KEYS)
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[hits]
    if hits < len(CORRECT_FINDING_KEYS):
        return score, FeedbackObservation("lesson.l29.feedback.evidence_missing_a_headline_fact", ScoreDimension.EVIDENCE)
    return score, None


def _score_communication(result: LessonTwentyNineResult) -> tuple[float, FeedbackObservation | None]:
    """Three real, independent checks on the delivered artifact itself:
    is the right finding promoted to lead, does the cited chart actually
    support whichever lead the student chose (a consistency check, not a
    fixed answer - a student who picks the wrong lead but a chart that
    matches THAT lead still passes this one check), and is the caveat a
    real, specific limitation rather than a fabricated or non-epistemic
    one."""
    lead = result.decision.get("lead_finding")
    chart = result.decision.get("supporting_chart")
    lead_correct = lead == LEAD_FINDING_KEY
    chart_matches_own_lead = CHART_FINDING_BY_OPTION.get(chart) == lead
    caveat_correct = result.decision.get("caveats") == _CORRECT_CAVEAT
    hits = sum((lead_correct, chart_matches_own_lead, caveat_correct))
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[hits]
    if not lead_correct:
        return score, FeedbackObservation("lesson.l29.feedback.lead_finding_not_the_direct_outcome", ScoreDimension.COMMUNICATION)
    if not chart_matches_own_lead:
        return score, FeedbackObservation("lesson.l29.feedback.chart_doesnt_match_own_lead", ScoreDimension.COMMUNICATION)
    if not caveat_correct:
        return score, FeedbackObservation("lesson.l29.feedback.caveat_not_a_real_limitation", ScoreDimension.COMMUNICATION)
    return score, None


def _score_overconfidence(result: LessonTwentyNineResult) -> tuple[float, FeedbackObservation | None]:
    """Reads `confidence_level` only - confidence in the brief's own
    recommendation, matching every sibling's own single-field CALIBRATION
    read."""
    confidence = result.decision.get("confidence_level")
    if confidence == _CALIBRATED_CONFIDENCE:
        return 92.0, None
    if confidence == _OVERCLAIM_CONFIDENCE:
        return 25.0, FeedbackObservation("lesson.l29.feedback.confidence_overclaimed", ScoreDimension.OVERCONFIDENCE)
    if confidence == _UNDERCLAIM_CONFIDENCE:
        return 35.0, FeedbackObservation("lesson.l29.feedback.confidence_underclaimed", ScoreDimension.OVERCONFIDENCE)
    return 15.0, FeedbackObservation("lesson.l29.feedback.confidence_not_understood", ScoreDimension.OVERCONFIDENCE)


def _mastery_succeeded(result: LessonTwentyNineResult) -> bool:
    metric_correct = result.mastery_result.get("mastery_which_metric_actually_mattered") == "session_length_directly_relevant_to_engagement_question"
    claim_correct = result.mastery_result.get("mastery_strongest_claim") == "a_real_but_modest_engagement_gain"
    return metric_correct and claim_correct


def score_lesson_twenty_nine(result: LessonTwentyNineResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    communication_score, communication_observation = _score_communication(result)
    overconfidence_score, overconfidence_observation = _score_overconfidence(result)

    dimension_scores = {
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.COMMUNICATION: communication_score,
        ScoreDimension.OVERCONFIDENCE: overconfidence_score,
    }

    observations = [
        observation
        for observation in (reasoning_observation, evidence_observation, communication_observation, overconfidence_observation)
        if observation is not None
    ]
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l29.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

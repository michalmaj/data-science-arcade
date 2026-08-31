from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

INCOMPLETE_BASE_SCORE = 40.0
MINIMUM_SCORE = 20.0
MAXIMUM_SCORE = 100.0

DecisionChoices = dict[str, str | tuple[str, ...]]
"""Mirrors ui/decision_builder_scene.py's own DecisionChoices - inlined
rather than imported so this content/scoring module doesn't depend on a
ui/ scene, matching workbench/context.py's own zero-ui-dependency
precedent."""


def _clamp(score: float) -> float:
    return max(MINIMUM_SCORE, min(MAXIMUM_SCORE, score))


@dataclass(frozen=True)
class LessonOneResult:
    """Everything the student did, kept as plain recorded choices rather
    than a points rubric - score_lesson_one below is what turns this into
    real per-dimension scores. `evidence_families` is derived once, in
    scenario.py's own finished() closure (the one place LessonContext is
    still in scope), rather than requiring score_lesson_one to take a
    separate `context` param - keeping this scorer's signature identical
    to default_scorer's (result, definition, hints_used), which is what
    lets course_map_scene.py call either one interchangeably via
    LessonDefinition.scorer."""

    guided_brief: AnalyticalBrief
    entity_revision: str
    window_prediction: str
    window_confidence_before: str
    window_interpretation: str
    entity_interpretation: str
    coverage_interpretation: str
    decision: DecisionChoices
    evidence_families: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False

    def completed_thoughtfully(self) -> bool:
        """A choice was made for every required step - the six guided-
        brief fields, both sensitivity rounds' predictions/interpretations,
        the coverage interpretation, and every step of the final decision
        (evidence held to its own real min_count, not just non-empty).
        Mastery is deliberately excluded - it's optional by design."""
        decision_single_selects = ("claim", "limitation", "confidence", "recommendation", "follow_up")
        return (
            len(self.guided_brief) >= 6
            and bool(self.entity_revision)
            and bool(self.window_prediction)
            and bool(self.window_confidence_before)
            and bool(self.window_interpretation)
            and bool(self.entity_interpretation)
            and bool(self.coverage_interpretation)
            and all(self.decision.get(key) for key in decision_single_selects)
            and len(self.decision.get("evidence", ())) >= 2
        )


def _score_reasoning(result: LessonOneResult) -> tuple[float, FeedbackObservation | None]:
    """Adequacy of the final Claim's scope to what was actually gathered -
    not whether entity_revision differs from the original guided pick.
    Keeping the original entity choice with a real, acknowledged
    limitation is exactly as sound a piece of reasoning as revising it;
    what's actually being checked is whether the Claim overreaches what
    the Evidence + Limitation the student themselves chose can support."""
    claim = result.decision.get("claim")
    limitation = result.decision.get("limitation")
    well_scoped_claim = claim in ("well_scoped", "either_view")
    real_limitation = limitation in ("definition_sensitive", "coverage_gap")

    if well_scoped_claim and real_limitation:
        return 90.0, FeedbackObservation("lesson.l01.feedback.claim_matches_evidence", ScoreDimension.REASONING)
    if claim == "overreaching" or limitation == "no_real_limitation":
        return 30.0, FeedbackObservation("lesson.l01.feedback.claim_overreaches", ScoreDimension.REASONING)
    if claim == "cannot_say":
        return 45.0, None  # honest about the limits, but doesn't actually reason to a position
    return 60.0, None  # a mixed case: one half of the argument coheres, the other doesn't


def _score_evidence(result: LessonOneResult) -> tuple[float, FeedbackObservation | None]:
    """Real breadth, not just a count that clears min_count. Spanning more
    than one family (window-sensitivity, entity-sensitivity, the coverage
    finding) means the final Claim is actually grounded in the whole
    investigation, not just whichever number was seen first."""
    evidence_count = len(result.decision.get("evidence", ()))
    family_count = len(result.evidence_families)
    if evidence_count >= 2 and family_count >= 2:
        return 90.0, FeedbackObservation("lesson.l01.feedback.evidence_spans_investigation", ScoreDimension.EVIDENCE)
    if evidence_count >= 2:
        return 60.0, None
    return 30.0, None


def _score_uncertainty(result: LessonOneResult) -> tuple[float, FeedbackObservation | None]:
    """Whether the stated Limitation is one of this investigation's own
    real, checkable gaps (definition-sensitivity, the coverage gap) rather
    than a generic caveat or an outright denial that any limitation
    exists."""
    limitation = result.decision.get("limitation")
    if limitation in ("definition_sensitive", "coverage_gap"):
        return 85.0, FeedbackObservation("lesson.l01.feedback.limitation_matches_claim", ScoreDimension.UNCERTAINTY)
    if limitation == "no_seasonality":
        return 50.0, None  # a real kind of limitation in general, just not this dataset's actual gap
    return 25.0, None  # "no_real_limitation"


def _score_overconfidence(result: LessonOneResult) -> tuple[float, FeedbackObservation | None]:
    """Calibration between stated Confidence and the real hedged-ness of
    the Claim - not a rule that confidence must fall after the twist.
    High confidence is a real overconfidence signal only when the Claim
    itself overreaches or refuses to commit; paired with a well-scoped
    Claim, high confidence is a milder miscalibration (the Limitation was
    named but not really taken to heart), not the worst case. A real
    before->after drop (window_confidence_before was "high", the final
    Confidence isn't) earns a small bonus - the one place this lesson
    directly rewards revising in light of new evidence, not just holding
    a coherent position throughout."""
    claim = result.decision.get("claim")
    after = result.decision.get("confidence")
    well_scoped_claim = claim in ("well_scoped", "either_view")

    if well_scoped_claim and after != "high":
        recalibrated = result.window_confidence_before == "high"
        score = 90.0 if recalibrated else 80.0
        return score, FeedbackObservation("lesson.l01.feedback.confidence_well_calibrated", ScoreDimension.OVERCONFIDENCE)
    if not well_scoped_claim and after == "high":
        return 25.0, None
    if well_scoped_claim and after == "high":
        return 55.0, None
    return 50.0, None


def score_lesson_one(result: LessonOneResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    """Lesson 01's own scorer, wired in via LessonDefinition.scorer -
    course_map_scene.py calls this instead of evaluation.py's generic
    default_scorer for this lesson only. hints_used is tracked and
    surfaced as its own observation, never subtracted from a dimension
    score directly - a student who takes a hint and then reasons well
    afterward scores exactly as well on Reasoning as one who didn't need
    it (see the four _score_* functions above, none of which reference
    hints_used at all)."""
    if not result.completed_thoughtfully():
        return LessonEvaluation(
            dimension_scores={dimension: INCOMPLETE_BASE_SCORE for dimension in definition.scoring_dimensions},
            observations=(FeedbackObservation("lesson.feedback.incomplete"),),
            hints_used=hints_used,
            completed_thoughtfully=False,
        )

    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    overconfidence_score, overconfidence_observation = _score_overconfidence(result)

    dimension_scores = {
        ScoreDimension.REASONING: _clamp(reasoning_score),
        ScoreDimension.EVIDENCE: _clamp(evidence_score),
        ScoreDimension.UNCERTAINTY: _clamp(uncertainty_score),
        ScoreDimension.OVERCONFIDENCE: _clamp(overconfidence_score),
    }

    observations = [FeedbackObservation("lesson.feedback.completed")]
    for observation in (reasoning_observation, evidence_observation, uncertainty_observation, overconfidence_observation):
        if observation is not None:
            observations.append(observation)
    if result.mastery_engaged:
        observations.append(FeedbackObservation("lesson.l01.feedback.mastery_completed"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=True,
    )

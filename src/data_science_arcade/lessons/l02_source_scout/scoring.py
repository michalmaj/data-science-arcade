from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

INCOMPLETE_BASE_SCORE = 40.0
MINIMUM_SCORE = 20.0
MAXIMUM_SCORE = 100.0

DecisionChoices = dict[str, str | tuple[str, ...]]
"""Mirrors ui/decision_builder_scene.py's own DecisionChoices - inlined
rather than imported so this content/scoring module doesn't depend on a
ui/ scene, matching l01_question_first/scoring.py's own precedent."""

CRITICAL_EVIDENCE_KEYS = ("billing_active", "legacy_missing", "legacy_status_unresolved")
"""The three facts an argument about this lesson's question actually
needs, per explicit review feedback - not "2+ sources," which rewards
diversity that isn't itself evidence of a good argument. Derived once in
scenario.py's own result-builder closure (while context is still in
scope), mirroring exactly how l01_question_first/scoring.py pre-derives
evidence_families."""

COHERENT_NOT_SAFE_ANSWERS = ("single_exact_total", "individual_customer_decision")
"""Both are genuinely unsafe things to claim from this data - a student
can coherently name either one alongside a well-scoped Safe-to-claim
pick; there isn't one single "correct" choice here the way there is for
Answer Strategy."""


def _clamp(score: float) -> float:
    return max(MINIMUM_SCORE, min(MAXIMUM_SCORE, score))


@dataclass(frozen=True)
class LessonTwoResult:
    """Everything the student did, kept as plain recorded choices rather
    than a points rubric - score_lesson_two below is what turns this into
    real per-dimension scores. `critical_evidence_present` is derived once
    in scenario.py's own finished() closure (the one place LessonContext
    is still in scope), keeping this scorer's signature identical to
    default_scorer's (result, definition, hints_used)."""

    initial_inspect_pick: str
    comparison_1_interpretation: str
    comparison_2_interpretation: str
    gap_interpretation: str
    revision_choice: str
    decision: DecisionChoices
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False

    def completed_thoughtfully(self) -> bool:
        """A choice was made for every required step - both comparison
        interpretations, the gap interpretation, the revision gut-check,
        and every step of the final decision (evidence held to its own
        real min_count, not just non-empty). Mastery is deliberately
        excluded - it's optional by design. The Source Map's initial pick
        is required too (it's the productive-failure entry point, always
        answerable), but never scored on its own content."""
        single_selects = ("answer_strategy", "known_gap", "safe_to_claim", "not_safe_to_claim", "recommendation")
        return (
            bool(self.initial_inspect_pick)
            and bool(self.comparison_1_interpretation)
            and bool(self.comparison_2_interpretation)
            and bool(self.gap_interpretation)
            and bool(self.revision_choice)
            and all(self.decision.get(key) for key in single_selects)
            and len(self.decision.get("evidence", ())) >= 2
        )


def _score_data_quality(result: LessonTwoResult) -> tuple[float, FeedbackObservation | None]:
    """Answer Strategy's own quality - not "which source(s) to trust,"
    since the strong answer isn't a source choice at all, it's an honest
    floor-plus-range. False precision (adding the unresolved 30 to
    Billing's 100 as if resolved) is scored as harshly as dropping them
    entirely - both treat an unresolved population incorrectly, just in
    opposite directions."""
    strategy = result.decision.get("answer_strategy")
    if strategy == "floor_and_range":
        return 90.0, FeedbackObservation("lesson.l02.feedback.honest_floor_and_range", ScoreDimension.DATA_QUALITY)
    if strategy in ("false_precision", "naive_exclusion"):
        return 30.0, FeedbackObservation("lesson.l02.feedback.answer_mishandles_the_unresolved_population", ScoreDimension.DATA_QUALITY)
    if strategy == "cannot_determine":
        return 45.0, None  # under-claims what the data actually supports
    return 55.0, None


def _score_evidence(result: LessonTwoResult) -> tuple[float, FeedbackObservation | None]:
    """Role, not source-diversity: an argument is only as strong as
    whether it actually cites the three facts that make it true - Billing
    confirms 100, 30 real accounts are missing from Billing, and no
    source resolves those 30's status. Any other real evidence (App log,
    Support) is legitimate but additional, never a substitute for these
    three."""
    critical_count = len(result.critical_evidence_present)
    evidence_count = len(result.decision.get("evidence", ()))
    if critical_count == 3:
        return 90.0, FeedbackObservation("lesson.l02.feedback.evidence_covers_the_real_argument", ScoreDimension.EVIDENCE)
    if critical_count == 2:
        return 60.0, None
    if evidence_count >= 2:
        return 40.0, None
    return 25.0, None


def _score_uncertainty(result: LessonTwoResult) -> tuple[float, FeedbackObservation | None]:
    """Whether Known Gap names the real, specific mechanism (systematic
    legacypay exclusion) rather than a generic caveat, a denial, or a
    confidently-stated but unsupported alternative (the tracking-bug
    decoy) - scored as a real negative signal, not just "not the best
    answer," since it asserts something nothing in the investigation
    actually supports."""
    gap = result.decision.get("known_gap")
    if gap == "legacy_exclusion":
        return 85.0, FeedbackObservation("lesson.l02.feedback.gap_named_precisely", ScoreDimension.UNCERTAINTY)
    if gap == "tracking_bug_decoy":
        return 25.0, None
    if gap == "generic_caveat":
        return 45.0, None
    return 20.0, None  # "no_real_gap" - denies a gap the student's own evidence establishes


def _score_reasoning(result: LessonTwoResult) -> tuple[float, FeedbackObservation | None]:
    """Internal coherence between Safe-to-claim and Not-safe-to-claim, not
    which specific pair was picked - either "a single exact total" or
    "precise enough for the individual-customer sunset decision" is a
    genuinely correct thing to name as unsafe alongside a well-scoped
    Safe-to-claim pick. What's actually wrong is a pair that contradicts
    itself (claiming the range is both safe and also unsafe), or a
    Safe-to-claim pick that already overreaches or under-claims before
    coherence with the next step is even relevant."""
    safe = result.decision.get("safe_to_claim")
    not_safe = result.decision.get("not_safe_to_claim")
    if safe == "floor_and_range" and not_safe in COHERENT_NOT_SAFE_ANSWERS:
        return 90.0, FeedbackObservation("lesson.l02.feedback.scope_is_coherent", ScoreDimension.REASONING)
    if safe == "floor_and_range" and not_safe == "range_itself":
        return 30.0, FeedbackObservation("lesson.l02.feedback.scope_contradicts_itself", ScoreDimension.REASONING)
    if safe in ("exact_precision", "nothing_usable"):
        return 40.0, None
    return 55.0, None


def score_lesson_two(result: LessonTwoResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    """Lesson 02's own scorer, wired in via LessonDefinition.scorer.
    hints_used is tracked and surfaced as its own observation, never
    subtracted from a dimension score directly - same non-punitive
    discipline as score_lesson_one."""
    if not result.completed_thoughtfully():
        return LessonEvaluation(
            dimension_scores={dimension: INCOMPLETE_BASE_SCORE for dimension in definition.scoring_dimensions},
            observations=(FeedbackObservation("lesson.feedback.incomplete"),),
            hints_used=hints_used,
            completed_thoughtfully=False,
        )

    data_quality_score, data_quality_observation = _score_data_quality(result)
    evidence_score, evidence_observation = _score_evidence(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)

    dimension_scores = {
        ScoreDimension.DATA_QUALITY: _clamp(data_quality_score),
        ScoreDimension.EVIDENCE: _clamp(evidence_score),
        ScoreDimension.UNCERTAINTY: _clamp(uncertainty_score),
        ScoreDimension.REASONING: _clamp(reasoning_score),
    }

    observations = [FeedbackObservation("lesson.feedback.completed")]
    for observation in (data_quality_observation, evidence_observation, uncertainty_observation, reasoning_observation):
        if observation is not None:
            observations.append(observation)
    if result.mastery_engaged:
        observations.append(FeedbackObservation("lesson.l02.feedback.mastery_completed"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=True,
    )

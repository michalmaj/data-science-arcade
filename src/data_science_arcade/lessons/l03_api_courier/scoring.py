from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

INCOMPLETE_BASE_SCORE = 40.0
MINIMUM_SCORE = 20.0
MAXIMUM_SCORE = 100.0

DecisionChoices = dict[str, str | tuple[str, ...]]
"""Mirrors ui/decision_builder_scene.py's own DecisionChoices - inlined
rather than imported so this content/scoring module doesn't depend on a
ui/ scene, matching l01/l02's own precedent."""

CRITICAL_EVIDENCE_KEYS = ("running_total", "total_count", "page3_shortfall")
"""The three facts every real argument about this lesson's question
needs, regardless of which path a student took through the rate-limit
branch (see scenario.py) - the confirmed floor, the API's own declared
total, and the specific, named mechanism behind the gap between them. A
student who skipped page 5 instead of backing off also has a fourth,
real fact available (the skipped-page gap) but it's additional, not
required - the argument is already complete without it, the same "role,
not source-count" principle l02_source_scout/scoring.py's own
CRITICAL_EVIDENCE_KEYS established."""


def _clamp(score: float) -> float:
    return max(MINIMUM_SCORE, min(MAXIMUM_SCORE, score))


@dataclass(frozen=True)
class LessonThreeResult:
    """Everything the student did, kept as plain recorded choices rather
    than a points rubric - score_lesson_three below is what turns this
    into real per-dimension scores. `critical_evidence_present` and
    `page5_recovered` are both derived once in scenario.py's own
    finished() closure (the one place LessonContext/the console's own
    final total are still in scope), keeping this scorer's signature
    identical to default_scorer's (result, definition, hints_used)."""

    initial_gut_check: str
    interpret_choice: str
    revised_gut_check: str
    decision: DecisionChoices
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    page5_recovered: bool = True
    mastery_engaged: bool = False

    def completed_thoughtfully(self) -> bool:
        """A choice was made for every required step - the interpret pick,
        both gut-checks, and every step of the final decision (evidence
        held to its own real min_count, not just non-empty). Mastery is
        deliberately excluded - it's optional by design."""
        single_selects = ("acquisition_strategy", "known_gap", "safe_to_claim", "not_safe_to_claim", "recommendation")
        return (
            bool(self.initial_gut_check)
            and bool(self.interpret_choice)
            and bool(self.revised_gut_check)
            and all(self.decision.get(key) for key in single_selects)
            and len(self.decision.get("evidence", ())) >= 2
        )


def _score_data_quality(result: LessonThreeResult) -> tuple[float, FeedbackObservation | None]:
    """Acquisition Strategy's own quality, not which specific number the
    student's own session happened to produce - the well-scoped answer
    (a confirmed floor, a named shortfall, a range that flags the
    threshold) is the same right shape under either real path through the
    rate-limit branch."""
    strategy = result.decision.get("acquisition_strategy")
    if strategy == "floor_and_range":
        return 90.0, FeedbackObservation("lesson.l03.feedback.floor_and_range", ScoreDimension.DATA_QUALITY)
    if strategy in ("raw_no_caveat", "discard_and_restart"):
        return 30.0, None
    if strategy == "refuse_until_repull":
        return 45.0, None  # under-claims what's already achievable
    return 55.0, None


def _score_method(result: LessonThreeResult) -> tuple[float, FeedbackObservation | None]:
    """Did the rate-limited page actually get recovered, or left skipped -
    the one real procedural signal this lesson has that L01/L02 never
    needed a dimension for. Not about which button was clicked first
    (retrying immediately once before backing off is a completely normal,
    real path to a full recovery) - only about where page 5 actually
    ended up."""
    if result.page5_recovered:
        return 85.0, FeedbackObservation("lesson.l03.feedback.recovered_via_backoff", ScoreDimension.METHOD)
    return 40.0, None


def _score_evidence(result: LessonThreeResult) -> tuple[float, FeedbackObservation | None]:
    """Role, not source-count: an argument is only as strong as whether it
    actually cites the three facts that make it true - the confirmed
    floor, the declared total, and the specific named mechanism. The
    skip-path's own fourth fact (page 5 unrecovered) is real and worth
    citing but never required - the argument is already complete at 3."""
    critical_count = len(result.critical_evidence_present)
    evidence_count = len(result.decision.get("evidence", ()))
    if critical_count == 3:
        return 90.0, FeedbackObservation("lesson.l03.feedback.evidence_covers_the_argument", ScoreDimension.EVIDENCE)
    if critical_count == 2:
        return 60.0, None
    if evidence_count >= 2:
        return 40.0, None
    return 25.0, None


def _score_uncertainty(result: LessonThreeResult) -> tuple[float, FeedbackObservation | None]:
    """Whether Known Gap names the real, specific mechanism (a page
    silently short despite a success status) rather than conflating it
    with the separately-resolved rate limit, denying any gap remains, or
    an unsupported claim nothing in the investigation backs."""
    gap = result.decision.get("known_gap")
    if gap == "page_shortfall":
        return 85.0, FeedbackObservation("lesson.l03.feedback.gap_named_precisely", ScoreDimension.UNCERTAINTY)
    if gap in ("rate_limit_alone", "pagination_broken"):
        return 25.0, None
    return 20.0, None  # "nothing_missing" - denies a gap the student's own evidence establishes


def _score_reasoning(result: LessonThreeResult) -> tuple[float, FeedbackObservation | None]:
    """Internal coherence between Safe-to-claim and Not-safe-to-claim -
    unlike l02_source_scout's own version of this check, L03's
    Not-safe-to-claim has exactly one correct answer (a single exact
    total), not a set of equally-valid ones, so this compares against one
    value rather than a coherence set. What's actually wrong is a
    Safe-to-claim pick that already overreaches or under-claims, or a
    pair that contradicts itself (also calling the floor+range unsafe)."""
    safe = result.decision.get("safe_to_claim")
    not_safe = result.decision.get("not_safe_to_claim")
    if safe == "floor_and_threshold_flag" and not_safe == "single_exact_total":
        return 90.0, FeedbackObservation("lesson.l03.feedback.scope_is_coherent", ScoreDimension.REASONING)
    if safe == "floor_and_threshold_flag" and not_safe == "range_itself_untrustworthy":
        return 30.0, FeedbackObservation("lesson.l03.feedback.scope_contradicts_itself", ScoreDimension.REASONING)
    if safe in ("exact_precision", "nothing_usable"):
        return 40.0, None
    return 55.0, None


def _score_trajectory(result: LessonThreeResult) -> FeedbackObservation | None:
    """Unscored (no ScoreDimension attached) - a real signal about the
    student's own initial-belief-to-revision arc, the same kind of signal
    l02_source_scout/scoring.py's own _score_trajectory tracks for its own
    (differently-shaped) productive-failure moment. The one case worth
    calling out: assuming the pull was complete right after the console
    closed, then correctly flagging it once the completeness reveal made
    the real gap visible."""
    if result.initial_gut_check == "yes_complete" and result.revised_gut_check == "no_would_flag_it":
        return FeedbackObservation("lesson.l03.feedback.revised_after_the_reveal")
    return None


def score_lesson_three(result: LessonThreeResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    """Lesson 03's own scorer, wired in via LessonDefinition.scorer.
    hints_used is tracked and surfaced as its own observation, never
    subtracted from a dimension score directly - same non-punitive
    discipline as score_lesson_one/score_lesson_two."""
    if not result.completed_thoughtfully():
        return LessonEvaluation(
            dimension_scores={dimension: INCOMPLETE_BASE_SCORE for dimension in definition.scoring_dimensions},
            observations=(FeedbackObservation("lesson.feedback.incomplete"),),
            hints_used=hints_used,
            completed_thoughtfully=False,
        )

    data_quality_score, data_quality_observation = _score_data_quality(result)
    method_score, method_observation = _score_method(result)
    evidence_score, evidence_observation = _score_evidence(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)

    dimension_scores = {
        ScoreDimension.DATA_QUALITY: _clamp(data_quality_score),
        ScoreDimension.METHOD: _clamp(method_score),
        ScoreDimension.EVIDENCE: _clamp(evidence_score),
        ScoreDimension.UNCERTAINTY: _clamp(uncertainty_score),
        ScoreDimension.REASONING: _clamp(reasoning_score),
    }

    observations = [FeedbackObservation("lesson.feedback.completed")]
    for observation in (data_quality_observation, method_observation, evidence_observation, uncertainty_observation, reasoning_observation):
        if observation is not None:
            observations.append(observation)
    trajectory_observation = _score_trajectory(result)
    if trajectory_observation is not None:
        observations.append(trajectory_observation)
    if result.mastery_engaged:
        observations.append(FeedbackObservation("lesson.l03.feedback.mastery_completed"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=True,
    )

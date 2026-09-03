from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

INCOMPLETE_BASE_SCORE = 40.0
MINIMUM_SCORE = 20.0
MAXIMUM_SCORE = 100.0

DecisionChoices = dict[str, str | tuple[str, ...]]
"""Mirrors ui/decision_builder_scene.py's own DecisionChoices - inlined
rather than imported so this content/scoring module doesn't depend on a
ui/ scene, matching l01/l02/l03's own precedent."""

CRITICAL_EVIDENCE_KEYS = ("distinct", "event_a_gap", "event_b_outcome")
"""Substrings matched against each evidence item's own label_key, the
same technique l03_api_courier/scoring.py's own CRITICAL_EVIDENCE_KEYS
uses. "distinct" and "event_b_outcome" are always real and citable
(ComparisonRevealScene auto-records both reveal values unconditionally,
and the Combined Workbench visit always records one real Event B
fact - captured or missing, either way something real). "event_a_gap"
only ever gets recorded when Event A actually has a real problem (see
scenario.py's root-cause stage) - on the event_a_clean path nothing
records it, exactly like l03's own `page_skipped` "just never matches
anything" on the path where it isn't true."""


def _clamp(score: float) -> float:
    return max(MINIMUM_SCORE, min(MAXIMUM_SCORE, score))


@dataclass(frozen=True)
class LessonFourResult:
    """Everything the student did, kept as plain recorded choices rather
    than a points rubric - score_lesson_four below is what turns this
    into real per-dimension scores. `critical_evidence_present`,
    `event_a_clean`, `outcome_captured`, and `spec_quality_hits` are all
    derived once in scenario.py's own finished() closure (the one place
    LessonContext and the student's own raw spec choices are still in
    scope), keeping this scorer's signature identical to
    default_scorer's (result, definition, hints_used)."""

    initial_gut_check: str
    decision: DecisionChoices
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    event_a_clean: bool = True
    outcome_captured: bool = True
    spec_quality_hits: int = 0
    """0-6: how many of the spec builder's six real fields (Event A
    trigger, Event A identifiers, Event B trigger, Event B identifiers,
    Event B properties [outcome present AND no raw-card-number], the
    top-level minimization field) the student got right - DATA_QUALITY's
    own signal, independent of how well the student later reasons about
    the consequences."""
    mastery_engaged: bool = False
    mastery_metric: str = ""
    mastery_interpretation: str = ""

    def completed_thoughtfully(self) -> bool:
        """A choice was made for every required step - the gut-check and
        every step of the final decision (evidence held to its own real
        min_count, not just non-empty). Mastery is deliberately excluded -
        it's optional by design."""
        single_selects = ("ship_readiness", "questions_answerable", "known_gap", "required_change", "not_collected")
        return (
            bool(self.initial_gut_check)
            and all(self.decision.get(key) for key in single_selects)
            and len(self.decision.get("evidence", ())) >= 2
        )


def _score_data_quality(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    """The spec builder's own six choices, not how well the student later
    argues about their consequences - a clean signal source independent
    of the final decision, matching the plan's own explicit split."""
    if result.spec_quality_hits == 6:
        return 90.0, FeedbackObservation("lesson.l04.feedback.spec_fully_correct", ScoreDimension.DATA_QUALITY)
    if result.spec_quality_hits >= 4:
        return 60.0, None
    if result.spec_quality_hits >= 2:
        return 40.0, None
    return 25.0, None


def _score_reproducibility(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    """Ship-readiness and Required-change both have to match the real
    event_a_clean state - an ambiguous/imprecise trigger definition is
    exactly what reproducibility means for instrumentation, and this is
    where that judgment actually gets exercised. Correct-on-the-clean-path
    ("nothing to fix") is graded exactly as seriously as correct-on-the-
    dirty-path ("fix the trigger and identifiers") - neither is the
    "default" right answer."""
    ship = result.decision.get("ship_readiness")
    required_change = result.decision.get("required_change")
    expected_ship = "ship_clean" if result.event_a_clean else "ship_with_fix"
    expected_change = "nothing_needed" if result.event_a_clean else "fix_trigger_and_identifiers"
    if ship == expected_ship and required_change == expected_change:
        return 90.0, FeedbackObservation("lesson.l04.feedback.reproducibility_matches_real_state", ScoreDimension.REPRODUCIBILITY)
    if ship == expected_ship or required_change == expected_change:
        return 55.0, None
    return 25.0, None


def _expected_critical_count(result: LessonFourResult) -> int:
    """A clean-path argument is complete at 2 real facts (the distinct
    count, the Event B outcome fact) - there's no Event A mechanism to
    cite. A not-clean-path argument has a real third fact and isn't
    complete without it."""
    return 2 if result.event_a_clean else 3


def _score_evidence(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    expected = _expected_critical_count(result)
    critical_count = len(result.critical_evidence_present)
    evidence_count = len(result.decision.get("evidence", ()))
    if critical_count >= expected:
        return 90.0, FeedbackObservation("lesson.l04.feedback.evidence_covers_the_argument", ScoreDimension.EVIDENCE)
    if critical_count == expected - 1:
        return 60.0, None
    if evidence_count >= 2:
        return 40.0, None
    return 25.0, None


def _score_uncertainty(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    """Known Gap branches on outcome_captured only - Event A's state is
    already fully actionable via Ship-readiness, leaving no *open* unknown
    about it either way (see the plan's own reasoning for why Known Gap
    doesn't also branch on event_a_clean)."""
    gap = result.decision.get("known_gap")
    if not result.outcome_captured and gap == "decline_reason_unknown":
        return 85.0, FeedbackObservation("lesson.l04.feedback.gap_named_precisely", ScoreDimension.UNCERTAINTY)
    if result.outcome_captured and gap == "no_remaining_gap":
        return 85.0, FeedbackObservation("lesson.l04.feedback.gap_named_precisely", ScoreDimension.UNCERTAINTY)
    if gap in ("never_know_failures", "duplication_means_untrustworthy"):
        return 25.0, None
    return 20.0, None


_STEP3_IMPLIES_OUTCOME_CAPTURED = {
    "all_three_clean": True,
    "all_three_once_fixed": True,
    "pm_support_once_fixed": False,
    "pm_support_clean_growth_no": False,
}
_STEP4_IMPLIES_OUTCOME_CAPTURED = {
    "no_remaining_gap": True,
    "decline_reason_unknown": False,
}


def _score_reasoning(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    """Internal coherence between Which-questions-answerable and Known
    Gap, both read on the one dimension they share (outcome_captured) -
    the two steps have to agree on the real state, not just each look
    individually defensible. The "duplication means none of this can be
    trusted" decoy is graded low unconditionally - it's not that it
    disagrees on outcome_captured specifically, it's that it directly
    contradicts having called any question answerable at all in step 3."""
    answerable = result.decision.get("questions_answerable")
    gap = result.decision.get("known_gap")
    if gap == "duplication_means_untrustworthy":
        return 20.0, None
    step3_implies = _STEP3_IMPLIES_OUTCOME_CAPTURED.get(answerable)
    step4_implies = _STEP4_IMPLIES_OUTCOME_CAPTURED.get(gap)
    if step3_implies is None or step4_implies is None:
        return 45.0, None
    if step3_implies == step4_implies:
        return 90.0, FeedbackObservation("lesson.l04.feedback.scope_is_coherent", ScoreDimension.REASONING)
    return 30.0, FeedbackObservation("lesson.l04.feedback.scope_contradicts_itself", ScoreDimension.REASONING)


def score_lesson_four(result: LessonFourResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    """Lesson 04's own scorer, wired in via LessonDefinition.scorer.
    hints_used is tracked and surfaced as its own observation, never
    subtracted from a dimension score directly - same non-punitive
    discipline as every prior lesson's own calibrated scorer."""
    if not result.completed_thoughtfully():
        return LessonEvaluation(
            dimension_scores={dimension: INCOMPLETE_BASE_SCORE for dimension in definition.scoring_dimensions},
            observations=(FeedbackObservation("lesson.feedback.incomplete"),),
            hints_used=hints_used,
            completed_thoughtfully=False,
        )

    data_quality_score, data_quality_observation = _score_data_quality(result)
    reproducibility_score, reproducibility_observation = _score_reproducibility(result)
    evidence_score, evidence_observation = _score_evidence(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)

    dimension_scores = {
        ScoreDimension.DATA_QUALITY: _clamp(data_quality_score),
        ScoreDimension.REPRODUCIBILITY: _clamp(reproducibility_score),
        ScoreDimension.EVIDENCE: _clamp(evidence_score),
        ScoreDimension.UNCERTAINTY: _clamp(uncertainty_score),
        ScoreDimension.REASONING: _clamp(reasoning_score),
    }

    observations = [FeedbackObservation("lesson.feedback.completed")]
    for observation in (
        data_quality_observation,
        reproducibility_observation,
        evidence_observation,
        uncertainty_observation,
        reasoning_observation,
    ):
        if observation is not None:
            observations.append(observation)
    if result.mastery_engaged:
        # Same discipline as l03's own mastery fix: "engaged" alone would
        # credit a lucky-guess interpretation the same as one actually
        # reached through the correct metric - both have to be right
        # together.
        if result.mastery_metric == "distinct_user_id_count" and result.mastery_interpretation == "some_signups_double_counted":
            observations.append(FeedbackObservation("lesson.l04.feedback.mastery_solved"))
        else:
            observations.append(FeedbackObservation("lesson.l04.feedback.mastery_attempted"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=True,
    )

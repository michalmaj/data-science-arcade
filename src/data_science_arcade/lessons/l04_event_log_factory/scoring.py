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
scenario.py's root-cause stage) - on the clean path nothing records it,
exactly like l03's own `page_skipped` "just never matches anything" on
the path where it isn't true. A student on the "both" real state gets
two real facts under this same category (event_a_gap_duplicate AND
event_a_gap_identifiers, both containing "event_a_gap") - the category
count still only needs one of them cited, see _expected_critical_count."""


def _clamp(score: float) -> float:
    return max(MINIMUM_SCORE, min(MAXIMUM_SCORE, score))


@dataclass(frozen=True)
class LessonFourResult:
    """Everything the student did, kept as plain recorded choices rather
    than a points rubric - score_lesson_four below is what turns this
    into real per-dimension scores. Every field below `decision` is
    derived once in scenario.py's own _build_result() (the one place
    LessonContext and the student's own raw spec choices are still in
    scope), keeping this scorer's signature identical to
    default_scorer's (result, definition, hints_used)."""

    initial_gut_check: str
    decision: DecisionChoices
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    event_a_state: str = "clean"
    """"clean" | "trigger" | "identifiers" | "both" - the 4 real,
    independent Event A states (see twist_data.event_a_state). Ship-
    readiness and Required-change both branch on this directly, not on
    a single collapsed flag - a student who broke both trigger and
    identifiers needs both mechanisms named and both fixes required,
    not whichever single-problem state a priority order happened to
    check first."""
    event_a_clean: bool = True
    """Derived from event_a_state (`== "clean"`) - kept as its own field
    only because EVIDENCE's expected-category-count is coarser than
    Ship-readiness/Required-change: 2 categories on the clean path, 3
    otherwise, regardless of which specific problem (or both) is real."""
    outcome_captured: bool = True
    decline_reason_captured: bool = False
    """Whether decline_reason_detail was one of the properties picked -
    none of the three stated business questions need it (Growth's own
    question only needs outcome), but it's the one property that would
    actually close the specific "why declined" gap Known Gap asks
    about, so it gets its own signal distinct from outcome_captured."""
    privacy_violation: bool = False
    """Whether raw_card_number was picked in the spec - a real, distinct
    launch blocker (compliance, not data quality), and the one Not-
    collected has to catch a student contradicting if they claim "we
    don't collect this" while their own spec actually does."""
    spec_quality_hits: float = 0.0
    """0.0-6.0: the spec builder's six real fields (Event A trigger,
    Event A identifiers, Event B trigger, Event B identifiers, Event B
    properties, the top-level minimization field) - five score a plain
    0/1, and Properties itself is graduated (see scenario.py's own
    _properties_quality) since picking outcome alone is a real, fully
    sufficient, deliberately minimal answer that shouldn't score any
    lower than picking outcome plus reasonable extras, and picking
    extras shouldn't score identically to the deliberate minimum either.
    DATA_QUALITY's own signal, independent of how well the student
    later reasons about the consequences."""
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
    of the final decision. >=5.5 (every boolean field right, Properties
    at least "outcome plus one real extra") still reads as a strong
    spec, just not the single best one (exactly outcome alone, or every
    field perfect) - a real, if modest, distinction, not a cliff."""
    if result.spec_quality_hits >= 6.0:
        return 90.0, FeedbackObservation("lesson.l04.feedback.spec_fully_correct", ScoreDimension.DATA_QUALITY)
    if result.spec_quality_hits >= 5.5:
        return 80.0, None
    if result.spec_quality_hits >= 4:
        return 60.0, None
    if result.spec_quality_hits >= 2:
        return 40.0, None
    return 25.0, None


def _expected_ship_readiness(result: LessonFourResult) -> str:
    """A live Event A data-integrity problem (duplicates, or an
    unverifiable order count) is treated as more urgent than a missing
    or sensitive Event B property - it's actively producing wrong
    numbers right now, not just a missing capability - so it takes
    priority whenever both are real. Ship-readiness itself doesn't need
    to distinguish an outcome-gap from a privacy violation - both are
    real "the properties side needs work" blockers, matching the
    content's own block_for_properties_too option, which was already in
    the field before this needed a scorer that actually used it."""
    if result.event_a_state != "clean":
        return "ship_with_fix"
    if result.privacy_violation or not result.outcome_captured:
        return "block_for_properties_too"
    return "ship_clean"


def _expected_required_change(result: LessonFourResult) -> str:
    """Mirrors _expected_ship_readiness's own priority, but names the
    specific Event A mechanism (trigger/identifiers/both) instead of a
    generic "fix it" - a student diagnoses the mechanism, not "fix
    everything just in case." fix_properties covers either a missing
    outcome or a privacy violation - Not-collected is where the privacy
    case specifically gets its own named, distinct check (see
    _score_not_collected_coherence)."""
    if result.event_a_state != "clean":
        return {"trigger": "fix_trigger", "identifiers": "fix_identifiers", "both": "fix_both"}[result.event_a_state]
    if result.privacy_violation or not result.outcome_captured:
        return "fix_properties"
    return "nothing_needed"


def _score_reproducibility(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    """Ship-readiness and Required-change both have to match the real,
    full state - an ambiguous/imprecise trigger definition is exactly
    what reproducibility means for instrumentation, and this is where
    that judgment actually gets exercised. Correct-on-the-clean-state
    ("nothing to fix") is graded exactly as seriously as correct on any
    of the three real not-clean states - none of them is the "default"
    right answer."""
    ship = result.decision.get("ship_readiness")
    required_change = result.decision.get("required_change")
    expected_ship = _expected_ship_readiness(result)
    expected_change = _expected_required_change(result)
    if ship == expected_ship and required_change == expected_change:
        return 90.0, FeedbackObservation("lesson.l04.feedback.reproducibility_matches_real_state", ScoreDimension.REPRODUCIBILITY)
    if ship == expected_ship or required_change == expected_change:
        return 55.0, None
    return 25.0, None


def _expected_critical_count(result: LessonFourResult) -> int:
    """A clean-path argument is complete at 2 real facts (the distinct
    count, the Event B outcome fact) - there's no Event A mechanism to
    cite. A not-clean-path argument (trigger, identifiers, or both) has
    a real third fact and isn't complete without it - "both" happens to
    have two real event_a_gap facts available, but citing either one
    still satisfies this same category-level count."""
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


def _expected_known_gap(result: LessonFourResult) -> str:
    """Three real states, not two: without outcome we can't even tell
    approved from declined from error (a more severe gap than "we know
    it declined, just not why"); with outcome but no decline_reason_detail
    we know THAT it declined but not WHY; with both, the gap is closed."""
    if not result.outcome_captured:
        return "cannot_distinguish_outcomes"
    if not result.decline_reason_captured:
        return "decline_reason_unknown"
    return "no_remaining_gap"


def _score_uncertainty(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    gap = result.decision.get("known_gap")
    if gap == _expected_known_gap(result):
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
_KNOWN_GAP_IMPLIES_OUTCOME_CAPTURED = {
    "no_remaining_gap": True,
    "decline_reason_unknown": True,
    "cannot_distinguish_outcomes": False,
}


def _score_questions_vs_gap_coherence(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
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
    step4_implies = _KNOWN_GAP_IMPLIES_OUTCOME_CAPTURED.get(gap)
    if step3_implies is None or step4_implies is None:
        return 45.0, None
    if step3_implies == step4_implies:
        return 90.0, FeedbackObservation("lesson.l04.feedback.scope_is_coherent", ScoreDimension.REASONING)
    return 30.0, FeedbackObservation("lesson.l04.feedback.scope_contradicts_itself", ScoreDimension.REASONING)


def _score_not_collected_coherence(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    """Whether Not-collected agrees with what the spec actually did. A
    student whose own spec included raw_card_number and who still picks
    "we don't collect this" is making a false, self-contradictory claim
    about their own design - a different, and more serious, error than
    just missing a decoy. Productive failure still applies: a student
    who made that spec-time mistake can recognize it here and score
    well anyway by naming it honestly instead of denying it."""
    not_collected = result.decision.get("not_collected")
    if result.privacy_violation:
        if not_collected == "raw_card_number_needs_removal":
            return 90.0, FeedbackObservation("lesson.l04.feedback.privacy_mistake_acknowledged", ScoreDimension.REASONING)
        if not_collected == "raw_card_numbers":
            return 20.0, FeedbackObservation("lesson.l04.feedback.privacy_contradiction", ScoreDimension.REASONING)
        return 40.0, None
    if not_collected == "raw_card_numbers":
        return 90.0, None
    return 45.0, None


_REASONING_DOMINATES_BELOW = 30.0
"""Below this, a sub-check's score reflects a real, direct disagreement
or contradiction - not just an incomplete or suboptimal pick - and
should set the overall REASONING score outright rather than being
averaged (and so diluted) against an unrelated good answer from the
other check. 40/45 (a wrong-but-not-contradictory pick) still average
normally; 20/30 (an actual contradiction, or two claims that can't both
be true) do not."""


def _score_reasoning(result: LessonFourResult) -> tuple[float, FeedbackObservation | None]:
    """Two real, independent coherence checks this lesson has - Which-
    questions-answerable vs. Known Gap, and Not-collected vs. the actual
    spec. A severe, direct self-contradiction in *either* one dominates
    the combined score rather than being diluted by averaging against an
    unrelated good answer - reasoning is only as strong as its most
    self-contradictory claim."""
    coherence_score, coherence_observation = _score_questions_vs_gap_coherence(result)
    privacy_score, privacy_observation = _score_not_collected_coherence(result)
    if coherence_score <= _REASONING_DOMINATES_BELOW or privacy_score <= _REASONING_DOMINATES_BELOW:
        if coherence_score <= privacy_score:
            return coherence_score, coherence_observation
        return privacy_score, privacy_observation
    combined = (coherence_score + privacy_score) / 2
    observation = privacy_observation or coherence_observation
    return combined, observation


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

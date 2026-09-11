from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

_CORRECT_OVERALL_RESULT = "rose_28_4_to_33_2"
_CORRECT_WITHIN_DEVICE_RESULT = "both_declined"
_CORRECT_STATEMENTS_RELATIONSHIP = "both_true_different_comparisons"
_CORRECT_EXPLANATION = "mix_shifted_toward_higher_converting_group"
_CORRECT_STANDARDIZED_INTERPRETATION = "no_within_device_gain_at_fixed_mix"
_CORRECT_CLAIM = "names_both_facts_respects_causal_boundary"
_CORRECT_REVISED_HEADLINE = "need_to_check_composition_first"
_PREMATURE_HEADLINES: frozenset[str] = frozenset({"conversion_improved", "conversion_worsened"})

# Evidence, role-based (never "any N of M" - established L08-L14 discipline).
# 4 real central roles - `overall_change`/`standardized_comparison` come
# from their own ComparisonRevealScene's shared evidence_key (decoupled
# from first-interpretation correctness); `device_rates`/`device_share`
# come from SegmentMixScene's own unconditional Finish recording (see its
# own docstring) - never from manual scenario-level record_evidence calls.
# `region_null`/`weighted_reconstruction` are real, path-dependent bonus
# facts, present in the pool but never required for full EVIDENCE credit
# (region doesn't explain the reversal; the reconstruction identity
# supports the claim but isn't itself one of the 4 things a defensible
# claim must cite).
OVERALL_CHANGE_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l15.evidence.overall_change",)
DEVICE_RATES_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l15.evidence.device_rates",)
DEVICE_SHARE_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l15.evidence.device_share",)
STANDARDIZED_COMPARISON_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l15.evidence.standardized_comparison",)
REGION_NULL_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l15.evidence.region_null",)
WEIGHTED_RECONSTRUCTION_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l15.evidence.weighted_reconstruction",)

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    OVERALL_CHANGE_EVIDENCE_KEYS + DEVICE_RATES_EVIDENCE_KEYS + DEVICE_SHARE_EVIDENCE_KEYS + STANDARDIZED_COMPARISON_EVIDENCE_KEYS
)
BONUS_EVIDENCE_KEYS: tuple[str, ...] = REGION_NULL_EVIDENCE_KEYS + WEIGHTED_RECONSTRUCTION_EVIDENCE_KEYS


@dataclass(frozen=True)
class LessonFifteenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `first_dimension` (region/device) is recorded for the Python Mirror's
    own sake only - the user's own explicit instruction is that the first
    dimension inspected is never scored and never even surfaces as
    trajectory flavor text, since either real path is an equally sound
    way to start a real investigation.

    `prior_headline`/`revised_headline` are a real, separate cold-pick-
    then-revised-pick pair (mirroring `chart_choice_*_first`/
    `chart_choice_*` in L14) - kept genuinely distinct from the Final
    Brief's own `strongest_defensible_claim` field so a real recalibration
    bonus can fire only for an actual wrong-then-corrected change at the
    dedicated revision stage, never inferred from "first pick differs from
    wherever the Final Brief ended up" (the exact bug class the L09/L10/
    L11/L13/L14 follow-ups each had to fix after the fact)."""

    prior_headline: str | None
    first_dimension: str | None
    region_inspected: bool
    revised_headline: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return bool(self.revised_headline) and len(self.decision) > 0


def _overall_and_within_understood(result: LessonFifteenResult) -> bool:
    d = result.decision
    return d.get("observed_overall_result") == _CORRECT_OVERALL_RESULT and d.get("within_device_result") == _CORRECT_WITHIN_DEVICE_RESULT


def _statements_relationship_understood(result: LessonFifteenResult) -> bool:
    return result.decision.get("statements_relationship") == _CORRECT_STATEMENTS_RELATIONSHIP


def _explanation_understood(result: LessonFifteenResult) -> bool:
    return result.decision.get("what_explains_the_reversal") == _CORRECT_EXPLANATION


def _standardized_understood(result: LessonFifteenResult) -> bool:
    return result.decision.get("standardized_interpretation") == _CORRECT_STANDARDIZED_INTERPRETATION


def _score_reasoning(result: LessonFifteenResult) -> tuple[float, FeedbackObservation | None]:
    """4 real, independent comprehension checks - never binary, hit-
    banded, mirroring L12's own `_grain_understood`/L14's own normative-
    understanding pattern."""
    checks = (
        _overall_and_within_understood(result),
        _statements_relationship_understood(result),
        _explanation_understood(result),
        _standardized_understood(result),
    )
    hits = sum(checks)
    score = {4: 95.0, 3: 72.0, 2: 48.0, 1: 26.0, 0: 10.0}[hits]
    if not checks[0]:
        return score, FeedbackObservation("lesson.l15.feedback.overall_and_within_not_understood", ScoreDimension.REASONING)
    if not checks[1]:
        return score, FeedbackObservation("lesson.l15.feedback.statements_relationship_not_understood", ScoreDimension.REASONING)
    if not checks[2]:
        return score, FeedbackObservation("lesson.l15.feedback.explanation_not_understood", ScoreDimension.REASONING)
    if not checks[3]:
        return score, FeedbackObservation("lesson.l15.feedback.standardized_not_understood", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonFifteenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(
        (
            bool(present & set(OVERALL_CHANGE_EVIDENCE_KEYS)),
            bool(present & set(DEVICE_RATES_EVIDENCE_KEYS)),
            bool(present & set(DEVICE_SHARE_EVIDENCE_KEYS)),
            bool(present & set(STANDARDIZED_COMPARISON_EVIDENCE_KEYS)),
        )
    )
    score = {4: 95.0, 3: 65.0, 2: 40.0, 1: 20.0, 0: 10.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l15.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_overconfidence(result: LessonFifteenResult) -> tuple[float, FeedbackObservation | None]:
    """The after-signal: does the Final Brief's own `strongest_defensible_
    claim` respect the real causal boundary (names both real facts,
    never overclaims causally, never dismisses the aggregate as fake)."""
    if result.decision.get("strongest_defensible_claim") == _CORRECT_CLAIM:
        return 92.0, None
    return 30.0, FeedbackObservation("lesson.l15.feedback.claim_not_defensible", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonFifteenResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal - never punished, only
    credited: a student whose prior headline was premature (called it
    improved or worsened before ever looking) but who both revised that
    headline correctly AND landed a real, defensible final claim gets
    real recalibration credit, extending L10's own two-point before/after
    bonus to a real three-point structure (prior headline -> revision ->
    final claim) since a dedicated revision stage exists here."""
    if result.prior_headline not in _PREMATURE_HEADLINES:
        return None
    if result.revised_headline != _CORRECT_REVISED_HEADLINE:
        return None
    if result.decision.get("strongest_defensible_claim") != _CORRECT_CLAIM:
        return None
    return FeedbackObservation("lesson.l15.feedback.headline_recalibrated")


def _mastery_succeeded(result: LessonFifteenResult) -> bool:
    """The fulfillment non-reversal transfer requires BOTH the correct
    judgment (no reversal - the aggregate's own real improvement is
    genuine, the mix shift only shrinks its size) AND a real
    distinguishing fact cited (that both real segments improved, not
    just that the mix shifted) - the same evidence/claim pairing
    discipline established since the L12 follow-up, applied from day one
    rather than needing a follow-up to catch a missing pairing."""
    judgment_correct = result.mastery_result.get("mastery_reversal_judgment") == "no_reversal_real_improvement"
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    real_distinguishing_fact = "both_carriers_improved" in supporting
    return judgment_correct and real_distinguishing_fact


def score_lesson_fifteen(result: LessonFifteenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    overconfidence_score, overconfidence_observation = _score_overconfidence(result)

    dimension_scores = {
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.OVERCONFIDENCE: overconfidence_score,
    }

    observations = [
        observation for observation in (reasoning_observation, evidence_observation, overconfidence_observation) if observation is not None
    ]
    recalibration = _recalibration_observation(result)
    if recalibration is not None:
        observations.append(recalibration)
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l15.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

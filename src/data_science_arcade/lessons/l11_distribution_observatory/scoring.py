from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

_CORRECT_FINANCE = "mean"
_CORRECT_OPS = "p90"
_CORRECT_PRODUCT_PRIOR = "median"
_CORRECT_PRODUCT_FINAL = "median_with_limitation"
_PRODUCT_FINAL_SUMMARY_BY_OPTION: dict[str, str] = {
    "median_with_limitation": "median",
    "median_denies_mixture": "median",
    "mean_as_typical": "mean",
}
_CORRECT_SHAPE = "two_separate_populations"
_CORRECT_COMMUNICATION = "differentiated_summaries_per_audience"

# Evidence, split by the real role each fact plays in the final argument -
# never "any N of M" (established L08/L09/L10 discipline). Every reveal
# in this lesson that shows real comparison values sets
# comparisons_are_evidence=False (or, for DistributionExplorerScene,
# never records a toggle as evidence at all) - the only evidence this
# lesson ever records comes from a real interpret choice.
CENTER_LOCATION_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l11.evidence.center_location",)
UPPER_TAIL_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l11.evidence.upper_tail_p90",)
SHAPE_MIXTURE_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l11.evidence.shape_mixture",)
SEGMENT_EXPLAINS_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l11.evidence.segment_explains_mixture",)

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    CENTER_LOCATION_EVIDENCE_KEYS + UPPER_TAIL_EVIDENCE_KEYS + SHAPE_MIXTURE_EVIDENCE_KEYS + SEGMENT_EXPLAINS_EVIDENCE_KEYS
)


@dataclass(frozen=True)
class LessonElevenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself."""

    business_asks_prior: dict[str, str]
    decision: dict
    segment_interpretation_seen: str | None = None
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)
    business_asks_revised_picks: dict[str, str] | None = None
    """The real picks made on the revision_offer screen, keyed exactly
    like business_asks_prior - None means the offer was skipped. Never
    the Final Decision's own fields (a different, more nuanced option
    space for product_typical_order_claim) and never a bare
    engaged=True flag - see _trajectory_observations for why comparing
    prior directly against these real revised picks (not against
    whatever the Final Decision ends up being) is what keeps "recovered
    via revision" honest about which step actually produced the fix."""

    def completed_thoughtfully(self) -> bool:
        return bool(self.business_asks_prior) and len(self.decision) > 0

    def _product_final_summary(self) -> str | None:
        return _PRODUCT_FINAL_SUMMARY_BY_OPTION.get(self.decision.get("product_typical_order_claim"))


def _score_method(result: LessonElevenResult) -> tuple[float, FeedbackObservation | None]:
    """Core METHOD scores only the FINAL (post-revision) picks - the
    prior business_asks pass lives entirely in an unscored trajectory
    observation (see _trajectory_observations), matching L09's own
    "prior pick is never a scored dimension on its own" precedent, not
    L10's own OVERCONFIDENCE shape (there is no claim-of-certainty act
    here to overclaim - just an untrained first guess)."""
    finance_correct = result.decision.get("finance_summary_choice") == _CORRECT_FINANCE
    product_correct = result.decision.get("product_typical_order_claim") == _CORRECT_PRODUCT_FINAL
    ops_correct = result.decision.get("ops_capacity_summary") == _CORRECT_OPS
    hits = int(finance_correct) + int(product_correct) + int(ops_correct)
    score = {3: 94.0, 2: 60.0, 1: 30.0, 0: 10.0}[hits]
    if not finance_correct:
        return score, FeedbackObservation("lesson.l11.feedback.finance_summary_wrong", ScoreDimension.METHOD)
    if not product_correct:
        return score, FeedbackObservation("lesson.l11.feedback.product_summary_wrong", ScoreDimension.METHOD)
    if not ops_correct:
        return score, FeedbackObservation("lesson.l11.feedback.ops_summary_wrong", ScoreDimension.METHOD)
    return score, None


def _shape_claim_coherent(result: LessonElevenResult) -> bool:
    return result.decision.get("shape_interpretation") == _CORRECT_SHAPE


def _product_shape_coherent(result: LessonElevenResult) -> bool:
    """Claiming the real limitation (product_typical_order_claim's own
    correct option, which asserts the median doesn't describe business
    orders) without ever citing the one fact that actually explains WHY
    - the segment-explains-mixture evidence role - would be a real
    self-contradiction. Checked entirely against the FINAL Decision's
    own fields (the product claim, and the real evidence the student
    chose to cite), never against the un-revisable segment_reveal
    trajectory pick itself: that stage has no revision path, so an
    earlier version of this check gated REASONING on
    segment_interpretation_seen directly, which permanently punished a
    fully correct final argument after nothing more than a wrong first
    read there - the same productive-failure bug the evidence-gating
    fix already closed everywhere else in this lesson (see the L11
    follow-up). Only checked when the product claim is itself correct;
    a wrong product claim is METHOD's own failure, not a REASONING one.
    Genuinely independent of EVIDENCE's own role-completeness score -
    this asks whether the specific segment role backs up this specific
    claim, not how many of the 4 roles were gathered overall."""
    if result.decision.get("product_typical_order_claim") != _CORRECT_PRODUCT_FINAL:
        return True
    present = set(result.critical_evidence_present)
    return bool(present & set(SEGMENT_EXPLAINS_EVIDENCE_KEYS))


def _real_differentiation(result: LessonElevenResult) -> bool:
    picks = {
        result.decision.get("finance_summary_choice"),
        result.decision.get("ops_capacity_summary"),
        result._product_final_summary(),
    }
    return len(picks - {None}) > 1


def _communication_claim_coherent(result: LessonElevenResult) -> bool:
    if result.decision.get("communication_recommendation") != _CORRECT_COMMUNICATION:
        return True
    return _real_differentiation(result)


def _score_reasoning(result: LessonElevenResult) -> tuple[float, FeedbackObservation | None]:
    """Coherence only - every check compares one part of the student's
    own final argument against another real fact about what they
    actually did or saw, decoupled from whether the underlying pick was
    itself correct (METHOD's own job)."""
    shape_coherent = _shape_claim_coherent(result)
    product_coherent = _product_shape_coherent(result)
    communication_coherent = _communication_claim_coherent(result)

    hits = int(shape_coherent) + int(product_coherent) + int(communication_coherent)
    score = {3: 92.0, 2: 62.0, 1: 34.0, 0: 12.0}[hits]
    if not shape_coherent:
        return score, FeedbackObservation("lesson.l11.feedback.shape_claim_incoherent", ScoreDimension.REASONING)
    if not product_coherent:
        return score, FeedbackObservation("lesson.l11.feedback.product_claim_self_contradicted", ScoreDimension.REASONING)
    if not communication_coherent:
        return score, FeedbackObservation("lesson.l11.feedback.communication_claim_incoherent", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonElevenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(
        (
            bool(present & set(CENTER_LOCATION_EVIDENCE_KEYS)),
            bool(present & set(UPPER_TAIL_EVIDENCE_KEYS)),
            bool(present & set(SHAPE_MIXTURE_EVIDENCE_KEYS)),
            bool(present & set(SEGMENT_EXPLAINS_EVIDENCE_KEYS)),
        )
    )
    score = {4: 97.0, 3: 80.0, 2: 55.0, 1: 30.0, 0: 12.0}[roles_present]
    if roles_present < 4:
        return score, FeedbackObservation("lesson.l11.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_communication(result: LessonElevenResult) -> tuple[float, FeedbackObservation | None]:
    """Distinct from REASONING: REASONING asks whether the student's own
    interpretation of mean/median/p90/mixture is internally coherent;
    COMMUNICATION asks whether the final report itself avoids collapsing
    a real bimodal mix into one misleading headline number - a student
    can have fully correct REASONING and still score low here by
    recommending one global number, or by the underlying finance/product/
    ops picks not actually being differentiated in practice."""
    recommendation_correct = result.decision.get("communication_recommendation") == _CORRECT_COMMUNICATION
    differentiated = _real_differentiation(result)
    hits = int(recommendation_correct) + int(differentiated)
    score = {2: 96.0, 1: 55.0, 0: 15.0}[hits]
    if not recommendation_correct:
        return score, FeedbackObservation("lesson.l11.feedback.communication_recommendation_wrong", ScoreDimension.COMMUNICATION)
    if not differentiated:
        return score, FeedbackObservation("lesson.l11.feedback.reporting_not_actually_differentiated", ScoreDimension.COMMUNICATION)
    return score, None


def _trajectory_observations(result: LessonElevenResult) -> list[FeedbackObservation]:
    """Fires only for a change that genuinely happened AT the revision
    step itself (prior wrong -> revised correct on that same screen) -
    never inferred from "prior differs from whatever the Final Decision
    ends up being," which could just as easily reflect a second, later
    change with nothing to do with the revision offer at all."""
    observations: list[FeedbackObservation] = []
    revised = result.business_asks_revised_picks
    if revised is None:
        return observations
    prior = result.business_asks_prior
    if prior.get("finance_prior_pick") != _CORRECT_FINANCE and revised.get("finance_prior_pick") == _CORRECT_FINANCE:
        observations.append(FeedbackObservation("lesson.l11.feedback.finance_recovered_via_revision"))
    if prior.get("product_prior_pick") != _CORRECT_PRODUCT_PRIOR and revised.get("product_prior_pick") == _CORRECT_PRODUCT_PRIOR:
        observations.append(FeedbackObservation("lesson.l11.feedback.product_recovered_via_revision"))
    if prior.get("ops_prior_pick") != _CORRECT_OPS and revised.get("ops_prior_pick") == _CORRECT_OPS:
        observations.append(FeedbackObservation("lesson.l11.feedback.ops_recovered_via_revision"))
    return observations


def _mastery_succeeded(result: LessonElevenResult) -> bool:
    """Success requires the real PAIR of a correct interpretation AND a
    genuinely distinguishing supporting fact - a known regression pattern
    in this codebase (L03/L04 both once scored a correct-sounding final
    interpretation alone, ignoring which check actually grounded it).
    Citing only "same mean" (true, but insufficient alone) never counts;
    a real spread/shape fact must be among what was cited."""
    interpretation_correct = result.mastery_result.get("mastery_interpretation") == "no_practically_different"
    evidence = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    real_distinguishing_fact = bool(evidence & {"different_spread_or_std", "different_shape_right_skew"})
    return interpretation_correct and real_distinguishing_fact


def score_lesson_eleven(result: LessonElevenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    communication_score, communication_observation = _score_communication(result)

    dimension_scores = {
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.COMMUNICATION: communication_score,
    }

    observations = [
        observation
        for observation in (method_observation, reasoning_observation, evidence_observation, communication_observation)
        if observation is not None
    ]
    observations.extend(_trajectory_observations(result))
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l11.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

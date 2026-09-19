from dataclasses import dataclass

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.framework.investigation import InvestigationResult
from data_science_arcade.lessons.l30_the_data_incident.leads import (
    CORRECT_BASELINE_CHECK,
    CORRECT_CHART_OPTION,
    CORRECT_CHECKOUT_HEALTH_OPTION,
    CORRECT_DEDUP_CHOICE,
    CORRECT_REGIONAL_CUT,
    MINIMUM_LEADS_REQUIRED,
    monitoring_choice_is_sound,
)
from data_science_arcade.workbench.context import EvidenceItem

# --- Evidence roles - see leads.py's own on_complete wrappers for exactly
# which lead records which key. `regional_cut`/`baseline_check`/
# `checkout_health` are STABLE per-lead slot keys (reopening the same
# lead with a different choice replaces that one slot in place, rather
# than leaving both an old and a new fact separately citable - see
# LessonContext.record_evidence's own keyed-replace behavior and the
# regression this fixed). Because the key alone doesn't say whether the
# slot's CURRENT content is the correct/informative variant or the
# decoy, correctness is looked up from the matching raw `*_choice` field
# on LessonThirtyResult instead - `_slot_is_correct` below is the only
# place that needs to know the mapping. `promo_context` and
# `redesign_weak_correlation` have no "wrong variant" (visiting either
# lead always produces the same qualitative fact regardless of which
# verdict/dedup choice was made), so they're checked by presence alone. ---

_SLOT_CORRECT_CHOICE: dict[str, tuple[str, str]] = {
    "regional_cut": ("regional_cut_choice", CORRECT_REGIONAL_CUT),
    "baseline_check": ("baseline_check_choice", CORRECT_BASELINE_CHECK),
    "checkout_health": ("checkout_health_choice", CORRECT_CHECKOUT_HEALTH_OPTION),
}

_BASELINE_REVERSION_ROLE = frozenset({"regional_cut", "baseline_check"})
_PROMO_CONTEXT_ROLE = frozenset({"promo_context"})
_REDESIGN_COUNTEREVIDENCE_ROLE = frozenset({"redesign_weak_correlation", "checkout_health"})


def _slot_is_correct(result: "LessonThirtyResult", slot_key: str) -> bool:
    if slot_key not in _SLOT_CORRECT_CHOICE:
        return True  # promo_context / redesign_weak_correlation: no wrong variant
    field_name, correct_value = _SLOT_CORRECT_CHOICE[slot_key]
    return getattr(result, field_name) == correct_value


def _correctly_gathered_role_keys(result: "LessonThirtyResult") -> frozenset[str]:
    """Which role-bearing evidence keys are present AND, for the slots
    that have a wrong variant, currently reflect the correct choice -
    used for licensing/uncertainty logic, which cares about the real
    current state of the investigation, not what's cited in the report."""
    return frozenset(
        item.key for item in result.gathered_evidence if item.key is not None and _slot_is_correct(result, item.key)
    )

_CORRECT_WHAT_HAPPENED = "east_promo_reverted"
_INSUFFICIENT_WHAT_HAPPENED = "insufficient_evidence_investigate_further"

_COHERENT_ACTION = {
    _CORRECT_WHAT_HAPPENED: "do_not_revert_measure_separately",
    "redesign_broke_checkout": "revert_redesign",
    _INSUFFICIENT_WHAT_HAPPENED: "investigate_before_deciding",
}
_COHERENT_IMPACT = {
    _CORRECT_WHAT_HAPPENED: "no_ongoing_loss_reversion",
    "redesign_broke_checkout": "severe_ongoing_loss",
    _INSUFFICIENT_WHAT_HAPPENED: "unclear_insufficient_investigation",
}
_COHERENT_FOLLOW_UP = "design_promo_incrementality_check"  # always coherent: the permanent uncertainty this answers is present on every path


@dataclass(frozen=True)
class LessonThirtyResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    Every `*_choice` field is None when that lead was never investigated
    - scoring below only ever grades the choices that exist, never
    rewards or penalizes on how many leads were opened (see
    `_score_method`'s own docstring)."""

    leads_investigated: InvestigationResult
    gathered_evidence: tuple[EvidenceItem, ...]
    regional_cut_choice: str | None
    baseline_check_choice: str | None
    checkout_health_choice: str | None
    dedup_choice: str | None
    promo_verdict_choice: str | None
    redesign_verdict_choice: str | None
    monitoring_choice: tuple[str, float] | None
    dashboard_choice: str | None
    decision: AnalyticalBrief

    def completed_thoughtfully(self) -> bool:
        return len(self.leads_investigated) >= MINIMUM_LEADS_REQUIRED and len(self.decision) > 0

    def evidence_by_id(self) -> dict[str, EvidenceItem]:
        return {item.id: item for item in self.gathered_evidence}


def _licensed_conclusion(result: "LessonThirtyResult") -> str:
    """What the real evidence in THIS playthrough actually supports -
    never authorial truth. Requires both a baseline/reversion fact and
    the promo-context fact, and only counts a baseline/reversion slot
    when its CURRENT choice is the correct one (a student who reopened
    regional_breakdown and left it on `by_device` hasn't actually
    established concentration, even though a `regional_cut` evidence
    item still exists). The redesign-counterevidence role isn't required
    to license this claim (a student can defensibly conclude "promo
    reversion" from those two alone) - it instead gates whether
    `redesign_not_fully_checked` belongs in the honest uncertainty list
    (see `_expected_uncertainties`)."""
    correct_keys = _correctly_gathered_role_keys(result)
    has_baseline = bool(correct_keys & _BASELINE_REVERSION_ROLE)
    has_promo = bool(correct_keys & _PROMO_CONTEXT_ROLE)
    if has_baseline and has_promo:
        return "promo_reversion_supported"
    return "insufficient_evidence"


def _redesign_ruled_out(result: "LessonThirtyResult") -> bool:
    return bool(_correctly_gathered_role_keys(result) & _REDESIGN_COUNTEREVIDENCE_ROLE)


def _score_method(result: LessonThirtyResult) -> tuple[float, FeedbackObservation | None]:
    """Grades the QUALITY of choices actually made, never the number of
    leads opened (a flat lead count would reward "open all 6", exactly
    the fake-choice failure mode this lesson is built to avoid). A
    threshold is only graded against another when the data actually
    discriminates between them - `monitoring_choice_is_sound` recomputes
    the real outcome for the student's own combo rather than reading a
    fixed answer key, so east_revenue's three equally-good thresholds are
    never treated as two wrong answers and one right one."""
    checks: list[bool] = []
    if result.regional_cut_choice is not None:
        checks.append(result.regional_cut_choice == CORRECT_REGIONAL_CUT)
    if result.baseline_check_choice is not None:
        checks.append(result.baseline_check_choice == CORRECT_BASELINE_CHECK)
    if result.checkout_health_choice is not None:
        checks.append(result.checkout_health_choice == CORRECT_CHECKOUT_HEALTH_OPTION)
    if result.dedup_choice is not None:
        checks.append(result.dedup_choice == CORRECT_DEDUP_CHOICE)
    if result.dashboard_choice is not None:
        checks.append(result.dashboard_choice == CORRECT_CHART_OPTION)
    if result.monitoring_choice is not None:
        metric_key, multiplier = result.monitoring_choice
        checks.append(monitoring_choice_is_sound(metric_key, multiplier))

    if not checks:
        return 15.0, FeedbackObservation("lesson.l30.feedback.method_no_real_checks", ScoreDimension.METHOD)

    ratio = sum(checks) / len(checks)
    if ratio >= 0.75:
        return 92.0, None
    if ratio >= 0.5:
        return 60.0, FeedbackObservation("lesson.l30.feedback.method_mixed_execution", ScoreDimension.METHOD)
    return 30.0, FeedbackObservation("lesson.l30.feedback.method_weak_execution", ScoreDimension.METHOD)


def _score_reasoning(result: LessonThirtyResult) -> tuple[float, FeedbackObservation | None]:
    """Is `what_happened` the conclusion THIS playthrough's own real
    evidence actually licenses - never whether it matches the authorial
    truth regardless of what was gathered. A student who skipped the
    critical leads and still asserts the strong claim is scored as an
    overclaim, not a lucky correct guess; a student who gathered enough
    but still hedges is scored as too cautious, not simply "wrong"."""
    licensed = _licensed_conclusion(result)
    claim = result.decision.get("what_happened")
    expected = _CORRECT_WHAT_HAPPENED if licensed == "promo_reversion_supported" else _INSUFFICIENT_WHAT_HAPPENED
    if claim == expected:
        return 92.0, None
    if licensed == "insufficient_evidence" and claim == _CORRECT_WHAT_HAPPENED:
        return 20.0, FeedbackObservation("lesson.l30.feedback.claim_outruns_evidence", ScoreDimension.REASONING)
    if licensed == "promo_reversion_supported" and claim == _INSUFFICIENT_WHAT_HAPPENED:
        return 45.0, FeedbackObservation("lesson.l30.feedback.claim_too_cautious_for_evidence", ScoreDimension.REASONING)
    return 15.0, FeedbackObservation("lesson.l30.feedback.what_happened_not_supported", ScoreDimension.REASONING)


def _score_evidence(result: LessonThirtyResult) -> tuple[float, FeedbackObservation | None]:
    """Does the final report cite a real, sufficient set of THIS
    playthrough's own gathered facts - independent of whether the claim
    itself (scored under REASONING) is correct. A student honestly
    admitting insufficient evidence isn't required to cite a full 3-role
    set to score well here; a student asserting the strong claim is."""
    cited_ids = result.decision.get("supporting_evidence", ())
    evidence_by_id = result.evidence_by_id()
    # A cited slot only counts toward a role if its CURRENT content (the
    # final choice made in that lead) is actually the correct/informative
    # one - citing the `regional_cut` slot while it's still left on
    # `by_device` doesn't defend the concentration claim, even though the
    # slot itself was "gathered".
    cited_keys = frozenset(
        evidence_by_id[evidence_id].key
        for evidence_id in cited_ids
        if evidence_id in evidence_by_id and evidence_by_id[evidence_id].key and _slot_is_correct(result, evidence_by_id[evidence_id].key)
    )

    if result.decision.get("what_happened") == _INSUFFICIENT_WHAT_HAPPENED:
        if cited_ids:
            return 80.0, None
        return 30.0, FeedbackObservation("lesson.l30.feedback.no_evidence_cited", ScoreDimension.EVIDENCE)

    roles_hit = sum(
        (
            bool(cited_keys & _BASELINE_REVERSION_ROLE),
            bool(cited_keys & _PROMO_CONTEXT_ROLE),
            bool(cited_keys & _REDESIGN_COUNTEREVIDENCE_ROLE),
        )
    )
    score = {3: 95.0, 2: 65.0, 1: 35.0, 0: 15.0}[roles_hit]
    if roles_hit < 3:
        return score, FeedbackObservation("lesson.l30.feedback.evidence_missing_a_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_communication(result: LessonThirtyResult) -> tuple[float, FeedbackObservation | None]:
    """Internal coherence of the report, never a second correctness
    check on `what_happened` itself - a student can reach the wrong
    conclusion and still write a report whose recommendation, business
    impact, and follow-up genuinely follow from THEIR OWN stated claim,
    and should score well here even while REASONING scores low."""
    claim = result.decision.get("what_happened")
    action_coherent = _COHERENT_ACTION.get(claim) == result.decision.get("recommended_action")
    impact_coherent = _COHERENT_IMPACT.get(claim) == result.decision.get("business_impact")
    follow_up_coherent = result.decision.get("follow_up_measurement") == _COHERENT_FOLLOW_UP

    hits = sum((action_coherent, impact_coherent, follow_up_coherent))
    score = {3: 92.0, 2: 60.0, 1: 35.0, 0: 15.0}[hits]
    if not action_coherent:
        return score, FeedbackObservation("lesson.l30.feedback.recommendation_not_coherent", ScoreDimension.COMMUNICATION)
    if not impact_coherent:
        return score, FeedbackObservation("lesson.l30.feedback.business_impact_not_coherent", ScoreDimension.COMMUNICATION)
    if not follow_up_coherent:
        return score, FeedbackObservation("lesson.l30.feedback.follow_up_not_coherent", ScoreDimension.COMMUNICATION)
    return score, None


def _expected_uncertainties(result: "LessonThirtyResult") -> frozenset[str]:
    expected = {"promo_causal_lift_unknown"}
    if not _redesign_ruled_out(result):
        expected.add("redesign_not_fully_checked")
    return frozenset(expected)


def _score_uncertainty(result: LessonThirtyResult) -> tuple[float, FeedbackObservation | None]:
    """What remains genuinely unresolved GIVEN this playthrough's own
    coverage - `promo_causal_lift_unknown` is permanent (this incident
    data can never identify it, no matter how thoroughly investigated);
    `redesign_not_fully_checked` is conditional on whether either
    redesign-counterevidence lead was actually done."""
    selected = frozenset(result.decision.get("remaining_uncertainties", ()))
    if "nothing_left_uncertain" in selected:
        return 15.0, FeedbackObservation("lesson.l30.feedback.uncertainty_overclaimed", ScoreDimension.UNCERTAINTY)

    expected = _expected_uncertainties(result)
    if selected == expected:
        return 92.0, None
    if expected <= selected:
        return 60.0, FeedbackObservation("lesson.l30.feedback.uncertainty_partially_right", ScoreDimension.UNCERTAINTY)
    return 30.0, FeedbackObservation("lesson.l30.feedback.uncertainty_missed_expected", ScoreDimension.UNCERTAINTY)


def _score_overconfidence(result: LessonThirtyResult) -> tuple[float, FeedbackObservation | None]:
    """Reads `root_cause_confidence` only: does its STRENGTH match this
    playthrough's own real evidence coverage - independent of whether
    `remaining_uncertainties` correctly names WHAT is still unknown
    (that's UNCERTAINTY's own job). `certain_promo_caused_exact_uplift`
    is wrong on every path: the exact causal lift of the promo is never
    identified by this observational incident data, no matter how much
    was investigated."""
    confidence = result.decision.get("root_cause_confidence")
    if confidence == "certain_promo_caused_exact_uplift":
        return 20.0, FeedbackObservation("lesson.l30.feedback.confidence_overclaimed", ScoreDimension.OVERCONFIDENCE)

    licensed = _licensed_conclusion(result)
    expected = "high_but_bounded" if licensed == "promo_reversion_supported" else "low_too_early"
    if confidence == expected:
        return 92.0, None
    return 40.0, FeedbackObservation("lesson.l30.feedback.confidence_miscalibrated", ScoreDimension.OVERCONFIDENCE)


def score_lesson_thirty(result: LessonThirtyResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    communication_score, communication_observation = _score_communication(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    overconfidence_score, overconfidence_observation = _score_overconfidence(result)

    dimension_scores = {
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.COMMUNICATION: communication_score,
        ScoreDimension.UNCERTAINTY: uncertainty_score,
        ScoreDimension.OVERCONFIDENCE: overconfidence_score,
    }

    observations = [
        observation
        for observation in (
            method_observation,
            reasoning_observation,
            evidence_observation,
            communication_observation,
            uncertainty_observation,
            overconfidence_observation,
        )
        if observation is not None
    ]
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

_CORRECT_BUSINESS_OUTCOME = "durable_not_a_single_number"
_CORRECT_DENOMINATOR_RATIONALE = "cant_shrink_by_leaving_open"
_CORRECT_MATURITY_REASONING = "immature_hasnt_had_its_window"
_CORRECT_NUMERATOR_LOOPHOLE = "closing_without_finishing"
_CORRECT_DENOMINATOR_LOOPHOLE = "closed_only_denominator_hides_backlog"
_CORRECT_GUARDRAIL_BREACH_ACTION = "gate_on_guardrails"
_PREMATURE_PRIOR_VERDICT = "ship_it_success"

# Evidence, role-based (never "any N of M"). Every reveal's own
# InterpretOption tuple shares ONE evidence_key across all its options -
# "fact seen != correct interpretation," the same discipline every
# ComparisonRevealScene reveal in this codebase already follows. Split
# across 5 real, separately-citable central facts - Stress Test A and
# Stress Test B each split into two real, sequential reveals (a single
# ComparisonRevealScene reveal can only ever yield one evidence_key per
# completion) rather than gluing two independent facts into one item.
HEADLINE_IMPROVED_EVIDENCE_KEY = "lesson.l16.evidence.headline_improved"
GUARDRAIL_DETERIORATED_EVIDENCE_KEY = "lesson.l16.evidence.guardrail_deteriorated"
DEFINITION_STRESS_RESULT_EVIDENCE_KEY = "lesson.l16.evidence.definition_stress_result"
AGED_BACKLOG_EVIDENCE_KEY = "lesson.l16.evidence.aged_backlog"
REVISED_CONTRACT_RESISTS_EVIDENCE_KEY = "lesson.l16.evidence.revised_contract_resists"

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    HEADLINE_IMPROVED_EVIDENCE_KEY,
    GUARDRAIL_DETERIORATED_EVIDENCE_KEY,
    DEFINITION_STRESS_RESULT_EVIDENCE_KEY,
    AGED_BACKLOG_EVIDENCE_KEY,
    REVISED_CONTRACT_RESISTS_EVIDENCE_KEY,
)


@dataclass(frozen=True)
class LessonSixteenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `primary_definition`/`guardrails` are the real FINAL EXECUTED metric
    contract, after the one revision - METHOD scores these two fields
    only, never the Final Metric Brief's own claims (the same METHOD-
    scores-execution/REASONING-scores-claims split established by L13's
    own follow-up and every deepened lesson since).

    `prior_success_verdict` is a real, separate cold-pick captured right
    after Stress Test A's own primary-metric reveal but BEFORE its
    guardrail reveal - a genuine before-signal for OVERCONFIDENCE,
    deliberately kept distinct from the Final Brief's own
    `guardrail_breach_action` field so a real recalibration bonus can fire
    only for an actual premature-then-corrected trajectory, never
    inferred after the fact."""

    primary_definition: str | None
    guardrails: tuple[str, ...]
    prior_success_verdict: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return self.primary_definition is not None and len(self.decision) > 0


def _score_method(result: LessonSixteenResult) -> tuple[float, FeedbackObservation | None]:
    """Tiered, never binary: 2 points for the real, structurally durable
    primary definition, 1 for the eligible-population-only definition
    (immune to denominator gaming, still vulnerable to numerator gaming),
    0 for the closed-only definition (vulnerable to both) - plus 1 point
    per real guardrail actually kept in the final executed contract
    (reopen rate catches the numerator loophole, aged backlog rate
    catches the denominator loophole; average-time-to-close counts for
    neither - a real, weaker guardrail, not a trick decoy)."""
    primary_points = {"durable": 2, "eligible_population": 1, "closed_only": 0}.get(result.primary_definition, 0)
    guardrail_points = sum(1 for key in ("reopen_rate", "aged_backlog_rate") if key in result.guardrails)
    total = primary_points + guardrail_points
    score = {4: 95.0, 3: 78.0, 2: 58.0, 1: 36.0, 0: 15.0}[total]
    if total < 4:
        return score, FeedbackObservation("lesson.l16.feedback.contract_not_fully_robust", ScoreDimension.METHOD)
    return score, None


def _reasoning_checks(result: LessonSixteenResult) -> tuple[bool, ...]:
    d = result.decision
    return (
        d.get("business_outcome") == _CORRECT_BUSINESS_OUTCOME,
        d.get("denominator_choice_rationale") == _CORRECT_DENOMINATOR_RATIONALE,
        d.get("maturity_window_reasoning") == _CORRECT_MATURITY_REASONING,
        d.get("numerator_loophole") == _CORRECT_NUMERATOR_LOOPHOLE,
        d.get("denominator_loophole") == _CORRECT_DENOMINATOR_LOOPHOLE,
    )


def _score_reasoning(result: LessonSixteenResult) -> tuple[float, FeedbackObservation | None]:
    """5 real, independent comprehension checks - deliberately about WHY
    each loophole worked and WHICH guardrail catches it, never about
    what's currently executing (a student can score high METHOD and low
    REASONING, or the reverse - see the dedicated independence tests)."""
    checks = _reasoning_checks(result)
    hits = sum(checks)
    score = {5: 95.0, 4: 80.0, 3: 62.0, 2: 45.0, 1: 28.0, 0: 10.0}[hits]
    if not checks[0]:
        return score, FeedbackObservation("lesson.l16.feedback.business_outcome_not_understood", ScoreDimension.REASONING)
    if not checks[1]:
        return score, FeedbackObservation("lesson.l16.feedback.denominator_rationale_not_understood", ScoreDimension.REASONING)
    if not checks[2]:
        return score, FeedbackObservation("lesson.l16.feedback.maturity_window_not_understood", ScoreDimension.REASONING)
    if not checks[3]:
        return score, FeedbackObservation("lesson.l16.feedback.numerator_loophole_not_understood", ScoreDimension.REASONING)
    if not checks[4]:
        return score, FeedbackObservation("lesson.l16.feedback.denominator_loophole_not_understood", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonSixteenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(1 for key in CRITICAL_EVIDENCE_KEYS if key in present)
    score = {5: 95.0, 4: 74.0, 3: 55.0, 2: 38.0, 1: 20.0, 0: 10.0}[roles_present]
    if roles_present < 5:
        return score, FeedbackObservation("lesson.l16.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_overconfidence(result: LessonSixteenResult) -> tuple[float, FeedbackObservation | None]:
    """The after-signal: does the Final Metric Brief's own
    `guardrail_breach_action` actually gate on guardrails holding, or
    does it still treat a primary-metric-only improvement as sufficient
    to ship (the same premature-verdict mentality `prior_success_verdict`
    captured earlier, now checked against the real final policy)."""
    if result.decision.get("guardrail_breach_action") == _CORRECT_GUARDRAIL_BREACH_ACTION:
        return 92.0, None
    return 30.0, FeedbackObservation("lesson.l16.feedback.guardrail_breach_action_not_defensible", ScoreDimension.OVERCONFIDENCE)


def _recalibration_observation(result: LessonSixteenResult) -> FeedbackObservation | None:
    """A real, positive trajectory signal, never punished: a student whose
    prior verdict was premature ("ship it") right after seeing the
    primary metric's own real jump, but whose Final Brief policy
    correctly gates on guardrails holding, gets real recalibration
    credit - the same before -> real evidence -> corrected-final-policy
    shape L15's own headline recalibration established."""
    if result.prior_success_verdict != _PREMATURE_PRIOR_VERDICT:
        return None
    if result.decision.get("guardrail_breach_action") != _CORRECT_GUARDRAIL_BREACH_ACTION:
        return None
    return FeedbackObservation("lesson.l16.feedback.verdict_recalibrated")


def _mastery_succeeded(result: LessonSixteenResult) -> bool:
    """Transfer requires BOTH the correct metric-system judgment (a
    completeness guardrail paired with the throughput primary) AND the
    real, distinguishing fact that completeness itself collapsed - not
    just that the rate went up (which alone would also be true of a
    perfectly honest productivity gain)."""
    judgment_correct = result.mastery_result.get("mastery_metric_system_judgment") == "productivity_needs_completeness_guardrail"
    supporting = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    real_distinguishing_fact = "completeness_collapsed" in supporting
    return judgment_correct and real_distinguishing_fact


def score_lesson_sixteen(result: LessonSixteenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    method_score, method_observation = _score_method(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)
    evidence_score, evidence_observation = _score_evidence(result)
    overconfidence_score, overconfidence_observation = _score_overconfidence(result)

    dimension_scores = {
        ScoreDimension.METHOD: method_score,
        ScoreDimension.REASONING: reasoning_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.OVERCONFIDENCE: overconfidence_score,
    }

    observations = [
        observation
        for observation in (method_observation, reasoning_observation, evidence_observation, overconfidence_observation)
        if observation is not None
    ]
    recalibration = _recalibration_observation(result)
    if recalibration is not None:
        observations.append(recalibration)
    if result.mastery_engaged and _mastery_succeeded(result):
        observations.append(FeedbackObservation("lesson.l16.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

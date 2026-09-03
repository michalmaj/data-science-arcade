from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation
from data_science_arcade.lessons.l05_sampling_mission.twist_data import round1_mechanism

DecisionChoices = dict[str, str | tuple[str, ...]]

# Which real facts matter most to cite - a student can only ever pick 2-3
# of the (up to) 8 real items the four Reveals produce, so "critical" here
# means the ones that most directly support a defensible final argument:
# the first reveal's own mechanism fact, both halves of the variability
# beat, and the final round's own coverage result. Matched by substring on
# the picked item's real label_key, the same technique l04's own
# CRITICAL_EVIDENCE_KEYS uses.
CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    "reveal1.rural_share_label",
    "reveal3.draw_a_label",
    "reveal3.draw_b_label",
    "reveal4.rural_share_label",
)


def round_quality(frame_key: str, strategy_key: str) -> float:
    """0.0-1.0: frame dominates strategy, the same priority-ordering
    discipline L04's own scoring established for its two independent real
    problems - a self-selected frame (support_tickets/loyalty_app) stays
    near-zero regardless of how carefully it's then sampled, since no
    sampling method fixes self-selection. Strategy is a real tiebreaker
    only once the frame itself is the best available one."""
    if frame_key == "tracking_export":
        base = 0.7
        bonus = {"stratified": 0.3, "simple_random": 0.15, "convenience": 0.0}
    else:
        base = 0.0
        bonus = {"stratified": 0.1, "simple_random": 0.05, "convenience": 0.0}
    return base + bonus.get(strategy_key, 0.0)


@dataclass(frozen=True)
class LessonFiveResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself. Unlike
    L04, nothing here needs a 4-way branched "state": the hidden
    population and its three frames never change based on what the
    student did in Rounds 1/4, so every Final Decision field has one
    fixed, objectively correct answer - see score_lesson_five below."""

    round1_frame: str
    round1_strategy: str
    round4_strategy: str
    prediction1: str
    prediction2: str
    decision: DecisionChoices
    round1_quality: float
    round4_quality: float
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_metric: str = ""
    mastery_interpretation: str = ""

    def completed_thoughtfully(self) -> bool:
        return bool(self.round1_frame) and bool(self.round4_strategy) and len(self.decision) > 0


def _score_data_quality(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    average = (result.round1_quality + result.round4_quality) / 2
    score = 100.0 * average
    if average >= 0.9:
        return score, None
    if average <= 0.15:
        return score, FeedbackObservation("lesson.l05.feedback.self_selected_frame_used", ScoreDimension.DATA_QUALITY)
    return score, None


_DESIGN_TO_COHERENT_ESTIMATE: dict[str, str] = {
    "stratified_export": "best_design_scoped",
    "simple_random_export": "best_design_scoped",
    "keep_tickets_bigger": "tickets_biggest",
    "average_everything": "average_every_draw",
}


def _score_method(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    hits = 0
    hits += result.decision.get("sampling_design") == "stratified_export"
    hits += result.decision.get("estimate_to_report") == "best_design_scoped"
    score = {2: 95.0, 1: 55.0, 0: 15.0}[hits]
    if hits == 2:
        return score, FeedbackObservation("lesson.l05.feedback.stratified_design_recommended", ScoreDimension.METHOD)
    if result.decision.get("sampling_design") == "keep_tickets_bigger":
        return score, FeedbackObservation("lesson.l05.feedback.size_trap_in_final_decision", ScoreDimension.METHOD)
    return score, None


def _score_evidence(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    count = min(len(result.critical_evidence_present), 3)  # EvidenceField.max_count is 3
    score = {3: 95.0, 2: 70.0, 1: 40.0, 0: 15.0}[count]
    observation = None if count >= 2 else FeedbackObservation("lesson.l05.feedback.evidence_missed_key_facts", ScoreDimension.EVIDENCE)
    return score, observation


def _score_uncertainty(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    # Five real calibration signals, not just the two end-of-lesson decision
    # fields: what the target population even is (a real, common confusion
    # with "the frame"), both predictions (calibration *before* seeing each
    # reveal, not just after), and the final limitation/claim-scope pair.
    target_population_correct = result.decision.get("target_population") == "all_deliveries"
    prediction1_correct = result.prediction1 == round1_mechanism(result.round1_frame, result.round1_strategy)
    prediction2_correct = result.prediction2 == "frame_ceiling_remains"
    limitation_correct = result.decision.get("limitation") == "rural_quickship_gap"
    claim_scope_correct = result.decision.get("claim_scope") == "carrierco_regions_scoped"
    hits = sum(
        (target_population_correct, prediction1_correct, prediction2_correct, limitation_correct, claim_scope_correct)
    )
    score = {5: 96.0, 4: 82.0, 3: 62.0, 2: 42.0, 1: 25.0, 0: 12.0}[hits]
    if result.decision.get("claim_scope") == "whole_company_one_rate":
        return score, FeedbackObservation("lesson.l05.feedback.claim_scope_overreached", ScoreDimension.UNCERTAINTY)
    if hits >= 4:
        return score, FeedbackObservation("lesson.l05.feedback.calibration_held_up", ScoreDimension.UNCERTAINTY)
    return score, None


def _score_reasoning(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    design = result.decision.get("sampling_design")
    estimate = result.decision.get("estimate_to_report")
    scope = result.decision.get("claim_scope")
    improvement = result.decision.get("next_improvement")
    design_estimate_coherent = _DESIGN_TO_COHERENT_ESTIMATE.get(design) == estimate
    scope_improvement_coherent = (scope == "carrierco_regions_scoped") == (improvement == "sync_quickship_log")
    hits = int(design_estimate_coherent) + int(scope_improvement_coherent)
    score = {2: 90.0, 1: 55.0, 0: 20.0}[hits]
    if not design_estimate_coherent and design in ("stratified_export", "simple_random_export"):
        return score, FeedbackObservation("lesson.l05.feedback.design_estimate_mismatch", ScoreDimension.REASONING)
    return score, None


def score_lesson_five(result: LessonFiveResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
    data_quality_score, data_quality_observation = _score_data_quality(result)
    method_score, method_observation = _score_method(result)
    evidence_score, evidence_observation = _score_evidence(result)
    uncertainty_score, uncertainty_observation = _score_uncertainty(result)
    reasoning_score, reasoning_observation = _score_reasoning(result)

    dimension_scores = {
        ScoreDimension.DATA_QUALITY: data_quality_score,
        ScoreDimension.METHOD: method_score,
        ScoreDimension.EVIDENCE: evidence_score,
        ScoreDimension.UNCERTAINTY: uncertainty_score,
        ScoreDimension.REASONING: reasoning_score,
    }

    observations = [
        observation
        for observation in (
            data_quality_observation,
            method_observation,
            evidence_observation,
            uncertainty_observation,
            reasoning_observation,
        )
        if observation is not None
    ]
    if result.mastery_engaged and result.mastery_interpretation == "needs_own_stratification":
        observations.append(FeedbackObservation("lesson.l05.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

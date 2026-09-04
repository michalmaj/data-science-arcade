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


def _allocation_quality(allocation: dict[str, int] | None, availability: dict[str, int]) -> float:
    """0.0-1.0: does this allocation deliberately cover Rural (the one
    small, high-risk segment that actually needs it) without collapsing
    the whole budget into a single region? Not "did you split it evenly" -
    Rural's own real availability is usually far smaller than an equal
    share, so covering it well means covering most of what's actually
    there, not a quarter of the total budget. Stratifying without a real
    allocation to show for it (everything dumped into one region) is
    barely better than not stratifying at all - the label "stratified"
    earns nothing on its own; only the allocation itself does."""
    if not allocation or sum(allocation.values()) == 0:
        return 0.0
    regions_touched = sum(1 for count in allocation.values() if count > 0)
    if regions_touched <= 1:
        return 0.1
    rural_available = availability.get("rural", 0)
    if rural_available == 0:
        return 1.0
    rural_coverage = allocation.get("rural", 0) / rural_available
    if rural_coverage >= 0.5:
        return 1.0
    if rural_coverage > 0:
        return 0.6
    return 0.2


def round_quality(
    frame_key: str,
    strategy_key: str,
    allocation: dict[str, int] | None = None,
    availability: dict[str, int] | None = None,
) -> float:
    """0.0-1.0: frame dominates strategy, the same priority-ordering
    discipline L04's own scoring established for its two independent real
    problems - a self-selected frame (support_tickets/loyalty_app) stays
    near-zero regardless of how carefully it's then sampled, since no
    sampling method fixes self-selection.

    Once the frame itself is the best available one, simple_random and
    stratified are both genuinely defensible - stratified only edges ahead
    when its own allocation actually earns it (see _allocation_quality); a
    badly-allocated "stratified" pick (the whole budget in one region)
    scores *below* a well-executed simple_random, not above it just
    because of its label. A well-designed simple random from the best
    frame is a real, if riskier, choice - not a consolation prize."""
    if frame_key == "tracking_export":
        base = 0.7
        if strategy_key == "convenience":
            return base
        if strategy_key == "simple_random":
            return base + 0.25
        if strategy_key == "stratified":
            return base + 0.3 * _allocation_quality(allocation, availability or {})
        return base
    base = 0.0
    if strategy_key == "convenience":
        return base
    if strategy_key == "simple_random":
        return base + 0.05
    if strategy_key == "stratified":
        return base + 0.1 * _allocation_quality(allocation, availability or {})
    return base


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
    reveal1_interpretation: str = ""
    reveal2_interpretation: str = ""
    reveal3_interpretation: str = ""
    reveal4_interpretation: str = ""
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_metric: str = ""
    mastery_interpretation: str = ""

    def completed_thoughtfully(self) -> bool:
        return bool(self.round1_frame) and bool(self.round4_strategy) and len(self.decision) > 0


def _score_data_quality(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    """Round 4 - the corrected, final design - dominates this score, not
    an average with Round 1. Round 1 is a prior/diagnostic: a deliberately
    tempting first pick that the lesson *wants* some students to take and
    then revise, so a permanent average would cap exactly the students who
    did the most productive learning (recognized a bad first design,
    fixed it) at whatever their tempting first click happened to score -
    directly against this lesson's own point. A genuine recovery (a weak
    Round 1 that gets corrected into a strong Round 4) earns a small
    explicit bonus instead, rewarding the trajectory without needing
    Round 1 to drag the final number down when it doesn't."""
    score = 100.0 * result.round4_quality
    if result.round1_quality <= 0.2 and result.round4_quality >= 0.9:
        score = min(100.0, score + 5.0)
        return score, FeedbackObservation(
            "lesson.l05.feedback.recovered_from_a_weak_first_design", ScoreDimension.DATA_QUALITY
        )
    if result.round4_quality <= 0.15:
        return score, FeedbackObservation("lesson.l05.feedback.self_selected_frame_used", ScoreDimension.DATA_QUALITY)
    return score, None


_DESIGN_TO_COHERENT_ESTIMATE: dict[str, str] = {
    "stratified_export": "best_design_scoped",
    "simple_random_export": "best_design_scoped",
    "keep_tickets_bigger": "tickets_biggest",
    "average_everything": "average_every_draw",
}


# Stratified edges ahead of simple_random here (1.0 vs 0.85) because it
# deliberately manages the one real coverage risk simple_random leaves to
# chance - not because the word "stratified" is inherently correct. Both
# are real, defensible designs from the best available frame; the size
# trap (the bigger, free, self-selected list) and the averaging trap
# (blending a good design's number with a bad one's) are the two answers
# that are actually wrong here.
_SAMPLING_DESIGN_QUALITY: dict[str, float] = {
    "stratified_export": 1.0,
    "simple_random_export": 0.85,
    "keep_tickets_bigger": 0.0,
    "average_everything": 0.0,
}


def _score_method(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    design = result.decision.get("sampling_design")
    design_quality = _SAMPLING_DESIGN_QUALITY.get(design, 0.0)
    estimate_correct = result.decision.get("estimate_to_report") == "best_design_scoped"
    score = 100.0 * (0.6 * design_quality + 0.4 * (1.0 if estimate_correct else 0.0))
    if design == "stratified_export" and estimate_correct:
        return score, FeedbackObservation("lesson.l05.feedback.stratified_design_recommended", ScoreDimension.METHOD)
    if design == "simple_random_export" and estimate_correct:
        return score, FeedbackObservation(
            "lesson.l05.feedback.simple_random_design_acknowledged", ScoreDimension.METHOD
        )
    if design == "keep_tickets_bigger":
        return score, FeedbackObservation("lesson.l05.feedback.size_trap_in_final_decision", ScoreDimension.METHOD)
    return score, None


def _score_evidence(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    count = min(len(result.critical_evidence_present), 3)  # EvidenceField.max_count is 3
    score = {3: 95.0, 2: 70.0, 1: 40.0, 0: 15.0}[count]
    observation = None if count >= 2 else FeedbackObservation("lesson.l05.feedback.evidence_missed_key_facts", ScoreDimension.EVIDENCE)
    return score, observation


def _score_uncertainty(result: LessonFiveResult) -> tuple[float, FeedbackObservation | None]:
    """Prediction = prior, interpretation = learning, final decision =
    transfer - weighted accordingly, not counted as equal signals. A
    prediction is an honest guess made *before* any evidence exists, so a
    wrong one costs little; an interpretation is made right after seeing a
    reveal's own real numbers, so getting it right is what actually
    demonstrates understanding and is weighted several times heavier. A
    student who guesses wrong but correctly reads every reveal that
    follows should score close to a student who guessed right from the
    start - guessing right first isn't the skill this dimension exists to
    measure."""
    reveal1_expected = round1_mechanism(result.round1_frame, result.round1_strategy)
    reveal4_expected = round1_mechanism("tracking_export", result.round4_strategy)

    prediction_points = 0.5 * (result.prediction1 == reveal1_expected) + 0.5 * (result.prediction2 == "frame_ceiling_remains")
    interpretation_points = (
        (result.reveal1_interpretation == reveal1_expected)
        + (result.reveal2_interpretation == "frame_coverage_gap")  # reveal2 is always tracking_export+simple_random
        + (result.reveal3_interpretation == "consistent_with_chance")
        + (result.reveal4_interpretation == reveal4_expected)
    )
    decision_points = (
        (result.decision.get("target_population") == "all_deliveries")
        + (result.decision.get("limitation") == "rural_quickship_gap")
        + (result.decision.get("claim_scope") == "carrierco_regions_scoped")
    )

    total_points = prediction_points + interpretation_points + decision_points  # max 1 + 4 + 3 = 8
    score = 100.0 * total_points / 8.0

    if result.decision.get("claim_scope") == "whole_company_one_rate":
        return score, FeedbackObservation("lesson.l05.feedback.claim_scope_overreached", ScoreDimension.UNCERTAINTY)
    if prediction_points < 1.0 and interpretation_points >= 3:
        return score, FeedbackObservation("lesson.l05.feedback.learned_from_the_evidence", ScoreDimension.UNCERTAINTY)
    if total_points >= 7:
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


def _mastery_transfer_succeeded(result: LessonFiveResult) -> bool:
    """Requires the correct metric *and* interpretation together, not the
    interpretation alone - the same fix already applied to L03/L04's own
    mastery scoring, reintroduced here and now caught by a regression test
    (test_mastery_transfer_requires_both_the_correct_metric_and_interpretation).
    `tracking_export` is the objectively better metric choice: it has
    roughly 10x the real Express rows of the Round 4 stratified sample
    (which was stratified by region, not delivery type) to look at, so
    checking it gives a far more reliable read on the same real question -
    a genuine correct/weaker-decoy pair, not two equally valid picks."""
    return result.mastery_metric == "tracking_export" and result.mastery_interpretation == "needs_own_stratification"


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
    if result.mastery_engaged and _mastery_transfer_succeeded(result):
        observations.append(FeedbackObservation("lesson.l05.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

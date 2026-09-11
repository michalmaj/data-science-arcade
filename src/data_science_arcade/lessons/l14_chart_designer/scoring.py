from dataclasses import dataclass, field

from data_science_arcade.lessons.framework.brief import AnalyticalBrief
from data_science_arcade.lessons.framework.definition import LessonDefinition, ScoreDimension
from data_science_arcade.lessons.framework.evaluation import FeedbackObservation, LessonEvaluation

# Tiered, not binary - real practice isn't a binary quiz. Each ask's own
# real chart-form options score 2 (best fit), 1 (defensible but less
# aligned - never treated as a full error), or 0 (answers a different
# question / semantically risky for this specific ask). The distribution
# ask has no 0-point tier: both its real options plot the exact same
# (bin, count) series - a frequency polygon is a real, defensible-but-
# weaker encoding of the same distribution, never a wrong estimand.
_STORES_FORM_POINTS: dict[str, int] = {"bar_sorted_desc": 2, "bar_natural_order": 1, "line": 0}
_DATES_FORM_POINTS: dict[str, int] = {"line": 2, "bar_chronological": 1}
_DISTRIBUTION_FORM_POINTS: dict[str, int] = {"histogram": 2, "frequency_polygon": 1}

_CORRECT_STORES_FORM = "bar_sorted_desc"
"""METHOD's own best-fit tier for the store ask - sorted-highest-first is
the closest real alignment to a "which stores are higher" ranking ask.
Deliberately NOT the same thing REASONING checks below - ordering is a
tiebreaker within "pick a bar chart," not part of understanding that a
bar chart (in either real order) is the right FORM for comparing
categories."""
_STORES_BAR_FORMS: frozenset[str] = frozenset({"bar_sorted_desc", "bar_natural_order"})
"""Either real bar chart is a correct FORM understanding for the store
ask - `bars compare magnitude between discrete categories` is equally
true regardless of which real order the bars are drawn in. A normative
check that required the specific sorted variant would be smuggling a
real ordering requirement into a check that only asks about form; if
ordering should be its own normative requirement, it needs its own
explicit ask/rationale pair, not a hidden tie-in here."""
_CORRECT_STORES_RATIONALE = "bars_compare_magnitude"
_CORRECT_DATES_FORM = "line"
_CORRECT_DATES_RATIONALE = "real_time_order_shows_change"
_CORRECT_DISTRIBUTION_FORM = "histogram"
_CORRECT_COMMUNICATION = "honest_complete_caption"

# Evidence, role-based (never "any N of M" - established L08-L13 discipline).
# Every ComparisonRevealScene reveal in this lesson sets
# comparisons_are_evidence=False; the only evidence recorded comes from
# each reveal's own interpret-click evidence_key. Unlike L12/L13, none of
# these three facts is path-aware (a store has no natural adjacency, a
# date has a real chronological position, a histogram bin counts
# observations - all true regardless of which chart form the student
# actually picked), so the simple per-option evidence_key mechanism is
# enough - no manual, update-by-key recording needed here.
STORE_CATEGORIES_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l14.evidence.store_categories",)
DATE_ORDER_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l14.evidence.date_order",)
HISTOGRAM_BINNING_EVIDENCE_KEYS: tuple[str, ...] = ("lesson.l14.evidence.histogram_binning",)

CRITICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    STORE_CATEGORIES_EVIDENCE_KEYS + DATE_ORDER_EVIDENCE_KEYS + HISTOGRAM_BINNING_EVIDENCE_KEYS
)


@dataclass(frozen=True)
class LessonFourteenResult:
    """What the student actually did, kept as plain recorded data - see
    LessonOneResult for why real per-dimension scoring is deferred to a
    dedicated scorer rather than living on this dataclass itself.

    `chart_choice_*_first`/`chart_choice_*` are each a real cold-pick-
    then-revised-pick pair (a first attempt, a real rendered consequence,
    one consolidated revision covering all three) - kept genuinely
    separate from the Final Decision so trajectory feedback can fire only
    for a real wrong-then-corrected change AT the revision step itself,
    never inferred from "first pick differs from wherever Final Decision
    ended up" (the exact bug the L09/L10/L11 follow-ups, and L13's own
    P0 follow-up, each had to fix after the fact).

    METHOD is scored purely off these three FINAL EXECUTED chart forms -
    not off `decision`'s own claims. A student who leaves a wrong chart
    form in place but correctly states, in the Final Decision, what
    should have been used, scores low METHOD (the real chart stayed
    wrong) and can still score high REASONING (the normative
    understanding is real and separately credited) - applying the L13
    follow-up's own lesson proactively, from day one, rather than
    needing a second follow-up to catch it here too."""

    chart_choice_stores_first: str | None
    chart_choice_stores: str | None
    chart_choice_dates_first: str | None
    chart_choice_dates: str | None
    chart_choice_distribution_first: str | None
    chart_choice_distribution: str | None
    decision: dict
    critical_evidence_present: tuple[str, ...] = field(default_factory=tuple)
    mastery_engaged: bool = False
    mastery_result: AnalyticalBrief = field(default_factory=dict)

    def completed_thoughtfully(self) -> bool:
        return (
            bool(self.chart_choice_stores)
            and bool(self.chart_choice_dates)
            and bool(self.chart_choice_distribution)
            and len(self.decision) > 0
        )


def _method_points(result: LessonFourteenResult) -> int:
    return (
        _STORES_FORM_POINTS.get(result.chart_choice_stores, 0)
        + _DATES_FORM_POINTS.get(result.chart_choice_dates, 0)
        + _DISTRIBUTION_FORM_POINTS.get(result.chart_choice_distribution, 0)
    )


def _method_feedback_key(result: LessonFourteenResult) -> str | None:
    if result.chart_choice_stores != _CORRECT_STORES_FORM:
        return "lesson.l14.feedback.stores_chart_not_best_fit"
    if result.chart_choice_dates != _CORRECT_DATES_FORM:
        return "lesson.l14.feedback.dates_chart_not_best_fit"
    if result.chart_choice_distribution != _CORRECT_DISTRIBUTION_FORM:
        return "lesson.l14.feedback.distribution_chart_not_best_fit"
    return None


def _score_method(result: LessonFourteenResult) -> tuple[float, FeedbackObservation | None]:
    """Breadth, tiered not binary: how close the three FINAL EXECUTED
    chart forms (after the one consolidated revision) land to each ask's
    own real best fit. Full 6 points requires all three at their best
    tier; a defensible-but-suboptimal pick (e.g. a plain chronological
    bar for the trend ask) still earns real partial credit, never scored
    as a flat error."""
    points = _method_points(result)
    score = {6: 96.0, 5: 84.0, 4: 70.0, 3: 55.0, 2: 40.0, 1: 24.0, 0: 10.0}[points]
    feedback_key = _method_feedback_key(result)
    if feedback_key is not None:
        return score, FeedbackObservation(feedback_key, ScoreDimension.METHOD)
    return score, None


def _stores_normative_understanding(result: LessonFourteenResult) -> bool:
    """Checks FORM understanding only - either real bar chart (sorted or
    natural order) paired with the real "bars compare magnitude" reason
    counts, since ordering is a separate METHOD-tier concern (see
    `_STORES_BAR_FORMS`'s own docstring), not part of what this check is
    named for."""
    d = result.decision
    return d.get("chart_form_for_stores") in _STORES_BAR_FORMS and d.get("rationale_for_stores_form") == _CORRECT_STORES_RATIONALE


def _dates_normative_understanding(result: LessonFourteenResult) -> bool:
    d = result.decision
    return d.get("chart_form_for_dates") == _CORRECT_DATES_FORM and d.get("rationale_for_dates_form") == _CORRECT_DATES_RATIONALE


def _distribution_normative_understanding(result: LessonFourteenResult) -> bool:
    return result.decision.get("chart_form_for_distribution") == _CORRECT_DISTRIBUTION_FORM


def _score_reasoning(result: LessonFourteenResult) -> tuple[float, FeedbackObservation | None]:
    """Normative comprehension, independent of what was actually
    executed (see LessonFourteenResult's own docstring) - a pure
    comprehension check against what each ask's own best form SHOULD be,
    paired with the real reason it fits, mirroring L12's own
    `_grain_understood`/L13's own `_join1_normative_understanding`."""
    stores_understood = _stores_normative_understanding(result)
    dates_understood = _dates_normative_understanding(result)
    distribution_understood = _distribution_normative_understanding(result)

    hits = int(stores_understood) + int(dates_understood) + int(distribution_understood)
    score = {3: 94.0, 2: 65.0, 1: 36.0, 0: 12.0}[hits]
    if not stores_understood:
        return score, FeedbackObservation("lesson.l14.feedback.stores_form_not_understood", ScoreDimension.REASONING)
    if not dates_understood:
        return score, FeedbackObservation("lesson.l14.feedback.dates_form_not_understood", ScoreDimension.REASONING)
    if not distribution_understood:
        return score, FeedbackObservation("lesson.l14.feedback.distribution_form_not_understood", ScoreDimension.REASONING)
    return score, None


def _score_evidence(result: LessonFourteenResult) -> tuple[float, FeedbackObservation | None]:
    present = set(result.critical_evidence_present)
    roles_present = sum(
        (
            bool(present & set(STORE_CATEGORIES_EVIDENCE_KEYS)),
            bool(present & set(DATE_ORDER_EVIDENCE_KEYS)),
            bool(present & set(HISTOGRAM_BINNING_EVIDENCE_KEYS)),
        )
    )
    score = {3: 95.0, 2: 62.0, 1: 32.0, 0: 10.0}[roles_present]
    if roles_present < 3:
        return score, FeedbackObservation("lesson.l14.feedback.evidence_missing_a_real_role", ScoreDimension.EVIDENCE)
    return score, None


def _score_communication(result: LessonFourteenResult) -> tuple[float, FeedbackObservation | None]:
    """Independent of METHOD/REASONING by construction: `communication_
    principle` is its own Final Decision field, correct or wrong
    regardless of whatever the three chart-form fields say - a student
    can get every chart form right and still pick an overclaiming or
    vague caption, or vice versa."""
    if result.decision.get("communication_principle") == _CORRECT_COMMUNICATION:
        return 95.0, None
    return 35.0, FeedbackObservation("lesson.l14.feedback.communication_principle_wrong", ScoreDimension.COMMUNICATION)


def _trajectory_observations(result: LessonFourteenResult) -> list[FeedbackObservation]:
    """Fires only for a real wrong-then-corrected change AT the one
    consolidated revision step itself - never inferred from "first pick
    differs from wherever Final Decision ended up," the exact bug the
    L09/L10/L11/L13 follow-ups each had to fix after the fact."""
    observations: list[FeedbackObservation] = []
    if (
        result.chart_choice_stores_first is not None
        and result.chart_choice_stores_first != _CORRECT_STORES_FORM
        and result.chart_choice_stores == _CORRECT_STORES_FORM
    ):
        observations.append(FeedbackObservation("lesson.l14.feedback.stores_chart_recovered_via_revision"))
    if (
        result.chart_choice_dates_first is not None
        and result.chart_choice_dates_first != _CORRECT_DATES_FORM
        and result.chart_choice_dates == _CORRECT_DATES_FORM
    ):
        observations.append(FeedbackObservation("lesson.l14.feedback.dates_chart_recovered_via_revision"))
    if (
        result.chart_choice_distribution_first is not None
        and result.chart_choice_distribution_first != _CORRECT_DISTRIBUTION_FORM
        and result.chart_choice_distribution == _CORRECT_DISTRIBUTION_FORM
    ):
        observations.append(FeedbackObservation("lesson.l14.feedback.distribution_chart_recovered_via_revision"))
    return observations


def _mastery_succeeded(result: LessonFourteenResult) -> bool:
    """The SLA-vs-target transfer task requires BOTH the correct
    recognition (a bare line chart isn't encoding-complete for a
    threshold-judgment ask - it needs a real target/reference line) AND
    a real cited distinguishing fact (that the ask names a fixed
    threshold to judge against, not just "did it move," which is
    exactly the naive "time series = line" heuristic being inverted).
    Applying the same evidence/claim pairing discipline established
    since the L12 follow-up, from day one rather than needing a fourth
    follow-up to catch a missing pairing."""
    judgment_correct = result.mastery_result.get("mastery_chart_judgment") == "needs_target_reference_line"
    evidence = set(result.mastery_result.get("mastery_supporting_evidence", ()))
    real_distinguishing_fact = "ask_names_a_fixed_threshold" in evidence
    return judgment_correct and real_distinguishing_fact


def score_lesson_fourteen(result: LessonFourteenResult, definition: LessonDefinition, hints_used: int) -> LessonEvaluation:
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
        observations.append(FeedbackObservation("lesson.l14.feedback.mastery_transfer_succeeded"))
    if hints_used > 0:
        observations.append(FeedbackObservation("lesson.feedback.hints_used"))

    return LessonEvaluation(
        dimension_scores=dimension_scores,
        observations=tuple(observations),
        hints_used=hints_used,
        completed_thoughtfully=result.completed_thoughtfully(),
    )

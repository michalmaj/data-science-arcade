from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l14_chart_designer.definition import LESSON_14
from data_science_arcade.lessons.l14_chart_designer.scoring import LessonFourteenResult, score_lesson_fourteen

GOOD_DECISION = {
    "chart_form_for_stores": "bar_sorted_desc",
    "rationale_for_stores_form": "bars_compare_magnitude",
    "chart_form_for_dates": "line",
    "rationale_for_dates_form": "real_time_order_shows_change",
    "chart_form_for_distribution": "histogram",
    "communication_principle": "honest_complete_caption",
}
ALL_ROLES_PRESENT = (
    "lesson.l14.evidence.store_categories",
    "lesson.l14.evidence.date_order",
    "lesson.l14.evidence.histogram_binning",
)


def _result(**overrides) -> LessonFourteenResult:
    defaults = dict(
        chart_choice_stores_first="bar_sorted_desc",
        chart_choice_stores="bar_sorted_desc",
        chart_choice_dates_first="line",
        chart_choice_dates="line",
        chart_choice_distribution_first="histogram",
        chart_choice_distribution="histogram",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=ALL_ROLES_PRESENT,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonFourteenResult(**defaults)


def _method_score(result: LessonFourteenResult) -> float:
    evaluation = score_lesson_fourteen(result, LESSON_14, hints_used=0)
    return evaluation.dimension_scores[ScoreDimension.METHOD]


def test_all_best_fit_forms_score_the_top_method_band():
    assert _method_score(_result()) == 96.0


def test_all_worst_reachable_forms_score_the_worst_reachable_method_band():
    # 0 (stores=line) + 1 (dates=bar_chronological, its own least tier) +
    # 1 (distribution=frequency_polygon, its own least tier - the
    # distribution ask has no 0-point tier at all, since both its real
    # options plot the same real (bin, count) series) = 2 points total.
    result = _result(chart_choice_stores="line", chart_choice_dates="bar_chronological", chart_choice_distribution="frequency_polygon")
    assert _method_score(result) == 40.0


def test_method_is_tiered_not_binary_a_defensible_pick_scores_above_a_wrong_one():
    defensible = _method_score(_result(chart_choice_stores="bar_natural_order"))
    wrong = _method_score(_result(chart_choice_stores="line"))
    best = _method_score(_result())
    assert wrong < defensible < best


def test_method_scores_the_final_executed_chart_not_the_decision_claim():
    # A student can leave the WRONG chart executed while the Final
    # Decision itself states the correct normative answer - METHOD must
    # stay low (real executed state), REASONING must stay high (real
    # comprehension), applying the L13-followup lesson proactively.
    result = _result(chart_choice_stores="line", chart_choice_dates="bar_chronological", chart_choice_distribution="frequency_polygon")
    evaluation = score_lesson_fourteen(result, LESSON_14, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 50.0
    assert evaluation.dimension_scores[ScoreDimension.REASONING] == 94.0


def test_a_correct_final_decision_claim_cannot_rewrite_a_wrong_executed_method_score():
    wrong_executed = _result(chart_choice_stores="line")
    right_executed = _result()
    wrong_score = _method_score(wrong_executed)
    right_score = _method_score(right_executed)
    assert wrong_score < right_score


def test_reasoning_requires_both_the_form_and_its_paired_rationale():
    right_form_wrong_rationale = _result(decision={**GOOD_DECISION, "rationale_for_stores_form": "either_works_equally"})
    evaluation = score_lesson_fourteen(right_form_wrong_rationale, LESSON_14, hints_used=0)
    full_credit = score_lesson_fourteen(_result(), LESSON_14, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < full_credit.dimension_scores[ScoreDimension.REASONING]


def test_stores_reasoning_accepts_either_real_bar_form_ordering_is_a_method_only_concern():
    # REASONING checks FORM understanding only ("bars compare magnitude
    # between categories") - real for either bar chart, regardless of
    # which real order it's drawn in. Requiring the specific sorted
    # variant here would smuggle a METHOD-tier ordering preference into a
    # check that's only supposed to be about form.
    natural_order_claim = _result(decision={**GOOD_DECISION, "chart_form_for_stores": "bar_natural_order"})
    sorted_claim = _result(decision={**GOOD_DECISION, "chart_form_for_stores": "bar_sorted_desc"})
    evaluation_natural = score_lesson_fourteen(natural_order_claim, LESSON_14, hints_used=0)
    evaluation_sorted = score_lesson_fourteen(sorted_claim, LESSON_14, hints_used=0)
    assert evaluation_natural.dimension_scores[ScoreDimension.REASONING] == evaluation_sorted.dimension_scores[ScoreDimension.REASONING]

    line_claim = _result(decision={**GOOD_DECISION, "chart_form_for_stores": "line"})
    evaluation_line = score_lesson_fourteen(line_claim, LESSON_14, hints_used=0)
    assert evaluation_line.dimension_scores[ScoreDimension.REASONING] < evaluation_sorted.dimension_scores[ScoreDimension.REASONING]


def test_communication_is_independent_of_method_and_reasoning():
    # High METHOD + high REASONING + WRONG communication_principle.
    high_method_bad_comm = _result(decision={**GOOD_DECISION, "communication_principle": "overclaiming_caption"})
    evaluation_a = score_lesson_fourteen(high_method_bad_comm, LESSON_14, hints_used=0)
    assert evaluation_a.dimension_scores[ScoreDimension.METHOD] == 96.0
    assert evaluation_a.dimension_scores[ScoreDimension.REASONING] == 94.0
    assert evaluation_a.dimension_scores[ScoreDimension.COMMUNICATION] == 35.0

    # Lower METHOD + good communication_principle.
    low_method_good_comm = _result(chart_choice_stores="line", chart_choice_dates="bar_chronological")
    evaluation_b = score_lesson_fourteen(low_method_good_comm, LESSON_14, hints_used=0)
    assert evaluation_b.dimension_scores[ScoreDimension.METHOD] < evaluation_a.dimension_scores[ScoreDimension.METHOD]
    assert evaluation_b.dimension_scores[ScoreDimension.COMMUNICATION] == 95.0


def test_evidence_is_role_based_missing_one_role_still_costs_real_credit():
    missing_one = _result(critical_evidence_present=ALL_ROLES_PRESENT[:2])
    full = _result()
    evaluation_missing = score_lesson_fourteen(missing_one, LESSON_14, hints_used=0)
    evaluation_full = score_lesson_fourteen(full, LESSON_14, hints_used=0)
    assert evaluation_missing.dimension_scores[ScoreDimension.EVIDENCE] < evaluation_full.dimension_scores[ScoreDimension.EVIDENCE]


def test_mastery_requires_both_the_correct_judgment_and_the_real_distinguishing_fact():
    judgment_only = _result(
        mastery_engaged=True,
        mastery_result={"mastery_chart_judgment": "needs_target_reference_line", "mastery_supporting_evidence": ("its_a_time_series",)},
    )
    both_right = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_chart_judgment": "needs_target_reference_line",
            "mastery_supporting_evidence": ("ask_names_a_fixed_threshold",),
        },
    )
    evaluation_judgment_only = score_lesson_fourteen(judgment_only, LESSON_14, hints_used=0)
    evaluation_both = score_lesson_fourteen(both_right, LESSON_14, hints_used=0)

    mastery_key = "lesson.l14.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_judgment_only.observations]
    assert mastery_key in [o.text_key for o in evaluation_both.observations]


def test_trajectory_observation_fires_only_for_a_real_revision_recovery():
    recovered = _result(chart_choice_stores_first="line", chart_choice_stores="bar_sorted_desc")
    evaluation = score_lesson_fourteen(recovered, LESSON_14, hints_used=0)
    assert "lesson.l14.feedback.stores_chart_recovered_via_revision" in [o.text_key for o in evaluation.observations]

    never_wrong = _result()
    evaluation_never_wrong = score_lesson_fourteen(never_wrong, LESSON_14, hints_used=0)
    assert "lesson.l14.feedback.stores_chart_recovered_via_revision" not in [o.text_key for o in evaluation_never_wrong.observations]

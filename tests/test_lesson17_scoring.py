from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l17_hypothesis_detective.definition import LESSON_17
from data_science_arcade.lessons.l17_hypothesis_detective.scoring import CRITICAL_EVIDENCE_KEYS, LessonSeventeenResult, score_lesson_seventeen

GOOD_PLAN = {
    "target_population": "all_eligible_returning_customers",
    "primary_outcome": "repeat_purchase_14d",
    "observation_window": "fourteen_days",
    "predicted_direction": "increase",
}
GOOD_DECISION = {
    "device_finding_status": "exploratory_discovered_after_reveal",
    "why_device_status_differs": "introduced_only_after_primary_result_visible",
    "primary_result_claim": "observed_plus_one_pp_in_predicted_direction",
    "strongest_defensible_device_claim": "real_pattern_worth_a_new_pre_specified_test",
    "next_step": "form_new_hypothesis_prespecify_test_on_new_data",
}


def _result(**overrides) -> LessonSeventeenResult:
    defaults = dict(
        hypothesis_plan=dict(GOOD_PLAN),
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonSeventeenResult(**defaults)


def _scores(result: LessonSeventeenResult) -> dict:
    return score_lesson_seventeen(result, LESSON_17, hints_used=0).dimension_scores


def test_fully_correct_plan_and_brief_scores_top_marks():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0


def test_method_is_tiered_across_the_four_plan_fields():
    all_wrong = _result(
        hypothesis_plan={
            "target_population": "app_users_only",
            "primary_outcome": "average_order_value",
            "observation_window": "thirty_days",
            "predicted_direction": "decrease",
        }
    )
    one_wrong = _result(hypothesis_plan={**GOOD_PLAN, "observation_window": "thirty_days"})
    good = _result()
    assert _scores(all_wrong)[ScoreDimension.METHOD] < _scores(one_wrong)[ScoreDimension.METHOD] < _scores(good)[ScoreDimension.METHOD]


def test_method_perfect_plan_scores_high_even_when_hypothesis_is_contradicted_by_data():
    # A student with a real, fully-specified locked plan whose hypothesis
    # the data then contradicts still scores METHOD high - METHOD never
    # reads anything reveal-derived, only the locked plan itself.
    result = _result(
        hypothesis_plan=dict(GOOD_PLAN),
        decision={**GOOD_DECISION, "primary_result_claim": "too_small_to_count_as_evidence"},
    )
    assert _scores(result)[ScoreDimension.METHOD] == 95.0


def test_method_badly_specified_plan_scores_low_even_if_it_happens_to_match_the_data():
    # A student whose eventual hypothesis happens to "match" the real
    # data while sitting on a badly specified (or silently rewritten)
    # locked plan still scores METHOD low.
    result = _result(
        hypothesis_plan={
            "target_population": "app_users_only",
            "primary_outcome": "average_order_value",
            "observation_window": "thirty_days",
            "predicted_direction": "increase",  # "lucky" match with the real observed direction
        }
    )
    assert _scores(result)[ScoreDimension.METHOD] == 36.0


def test_correct_direction_is_a_literal_constant_never_derived_from_data():
    # The business ask is "one-click reorder increases repeat purchase" -
    # this must stay correct regardless of whatever data.py's own real
    # computed rates happen to show, since it's asserted independently of
    # them, not derived from a PCT-style constant.
    from data_science_arcade.lessons.l17_hypothesis_detective import scoring

    assert scoring._CORRECT_DIRECTION == "increase"
    # A hypothetical world where the real primary result had gone the
    # other way still would not change what counts as a correctly
    # pre-specified direction - the scorer only ever reads the locked
    # plan's own field, never any reveal-derived state.
    result_matching_a_hypothetical_decrease = _result(
        hypothesis_plan={**GOOD_PLAN, "predicted_direction": "increase"},
        decision={**GOOD_DECISION, "primary_result_claim": "too_small_to_count_as_evidence"},
    )
    assert _scores(result_matching_a_hypothetical_decrease)[ScoreDimension.METHOD] == 95.0


def test_reasoning_is_tiered_across_the_three_checks():
    all_wrong = _result(
        decision={
            "device_finding_status": "confirmatory_it_was_the_real_plan",
            "why_device_status_differs": "device_was_always_part_of_the_plan",
            "next_step": "ship_the_app_only_version",
            "primary_result_claim": "observed_plus_one_pp_in_predicted_direction",
            "strongest_defensible_device_claim": "real_pattern_worth_a_new_pre_specified_test",
        }
    )
    one_wrong = _result(decision={**GOOD_DECISION, "next_step": "ship_the_app_only_version"})
    good = _result()
    assert _scores(all_wrong)[ScoreDimension.REASONING] < _scores(one_wrong)[ScoreDimension.REASONING] < _scores(good)[ScoreDimension.REASONING]


def test_uncertainty_is_tiered_across_the_two_checks():
    both_wrong = _result(
        decision={
            **GOOD_DECISION,
            "primary_result_claim": "proved_one_click_increases_repeat_purchase",
            "strongest_defensible_device_claim": "confirmed_device_specific_effect",
        }
    )
    one_wrong = _result(decision={**GOOD_DECISION, "strongest_defensible_device_claim": "confirmed_device_specific_effect"})
    good = _result()
    assert _scores(both_wrong)[ScoreDimension.UNCERTAINTY] < _scores(one_wrong)[ScoreDimension.UNCERTAINTY] < _scores(good)[ScoreDimension.UNCERTAINTY]


def test_reasoning_and_uncertainty_are_independent_case_a_high_reasoning_low_uncertainty():
    # Correctly identifies device as exploratory + correct next step, but
    # overclaims "confirmed device effect".
    result = _result(decision={**GOOD_DECISION, "strongest_defensible_device_claim": "confirmed_device_specific_effect"})
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] < 95.0


def test_reasoning_and_uncertainty_are_independent_case_b_high_uncertainty_low_reasoning():
    # Uses calibrated language throughout, but incorrectly claims device
    # was pre-specified / recommends the wrong provenance workflow.
    result = _result(
        decision={
            **GOOD_DECISION,
            "device_finding_status": "confirmatory_it_was_the_real_plan",
            "why_device_status_differs": "device_was_always_part_of_the_plan",
        }
    )
    scores = _scores(result)
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0
    assert scores[ScoreDimension.REASONING] < 92.0


def test_evidence_is_role_based_missing_one_real_role_costs_real_credit():
    missing_one = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS[:3])
    full = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS)
    assert _scores(missing_one)[ScoreDimension.EVIDENCE] < _scores(full)[ScoreDimension.EVIDENCE]


def test_mastery_requires_both_the_correct_judgment_and_the_real_distinguishing_fact():
    judgment_only = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_route_judgment": "not_borne_out_overall_late_rate_increased",
            "mastery_supporting_evidence": ("urban_late_rate_improved",),
        },
    )
    both_right = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_route_judgment": "not_borne_out_overall_late_rate_increased",
            "mastery_supporting_evidence": ("overall_late_rate_increased",),
        },
    )
    evaluation_judgment_only = score_lesson_seventeen(judgment_only, LESSON_17, hints_used=0)
    evaluation_both = score_lesson_seventeen(both_right, LESSON_17, hints_used=0)

    mastery_key = "lesson.l17.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_judgment_only.observations]
    assert mastery_key in [o.text_key for o in evaluation_both.observations]


def test_scoring_dimensions_are_exactly_method_reasoning_evidence_uncertainty():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.UNCERTAINTY}

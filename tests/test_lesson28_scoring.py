from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l28_chart_crime_lab.definition import LESSON_28
from data_science_arcade.lessons.l28_chart_crime_lab.scoring import (
    AXIS_SCALE_KEYS,
    CRITICAL_EVIDENCE_KEYS,
    DENOMINATOR_KEYS,
    DUAL_AXIS_KEYS,
    LessonTwentyEightResult,
    SATISFACTION_DATA_GAP_EVIDENCE_KEY,
    WINDOW_CONTEXT_KEYS,
    score_lesson_twenty_eight,
)

GOOD_CHOICES = {
    "satisfaction_score_claim": "zero_based",
    "active_users_claim": "full_year",
    "returns_rate_claim": "per_units_sold",
}
FLAWED_CHOICES = {
    "satisfaction_score_claim": "zoomed",
    "active_users_claim": "last_two_months",
    "returns_rate_claim": "per_customers",
}
GOOD_DECISION = {
    "why_a_truncated_axis_misleads": "same_data_difference_occupies_more_visual_space_when_the_baseline_is_truncated",
    "why_cherry_picking_misleads": "a_short_window_can_omit_material_context_the_full_period_would_show",
    "why_the_wrong_denominator_misleads": "the_denominator_must_match_the_population_the_question_implies",
    "why_a_truthful_chart_can_still_mislead": "independent_axis_scaling_can_make_different_relative_changes_look_comparable",
    "chart_review_standard": "check_both_the_real_numbers_and_the_real_presentation",
}


def _result(**overrides) -> LessonTwentyEightResult:
    defaults = dict(
        initial_verdict_choices=dict(GOOD_CHOICES),
        verdict_choices=dict(GOOD_CHOICES),
        reveal_axis_interpretation="the_data_is_the_same_the_truncated_baseline_just_gives_it_more_space",
        reveal_window_interpretation="the_same_dataset_supports_very_different_stories_depending_on_the_window",
        reveal_denominator_interpretation="the_denominator_changed_which_quarter_looks_best_not_just_the_size_of_the_numbers",
        reveal_dual_axis_interpretation="independent_axis_scaling_made_very_different_relative_changes_look_the_same",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentyEightResult(**defaults)


def _scores(result: LessonTwentyEightResult) -> dict:
    return score_lesson_twenty_eight(result, LESSON_28, hints_used=0).dimension_scores


def test_fully_correct_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_scoring_dimensions_are_exactly_four_no_communication():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE}


def test_method_reads_only_the_final_post_revision_picks():
    result = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=GOOD_CHOICES)
    assert _scores(result)[ScoreDimension.METHOD] == 95.0


def test_interpretations_never_affect_scoring():
    a = _result(
        reveal_axis_interpretation="any_non_zero_baseline_chart_is_automatically_dishonest",
        reveal_dual_axis_interpretation="dual_axis_charts_are_never_a_legitimate_choice",
    )
    b = _result()
    assert _scores(a) == _scores(b)


def test_independence_case_a_high_everything_except_calibration_underclaim():
    result = _result(decision={**GOOD_DECISION, "chart_review_standard": "if_the_underlying_numbers_are_accurate_the_chart_cannot_mislead"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 35.0


def test_independence_case_b_high_reasoning_lower_method_despite_a_real_revision_opportunity():
    result = _result(
        initial_verdict_choices=GOOD_CHOICES,
        verdict_choices={**GOOD_CHOICES, "returns_rate_claim": "per_customers"},
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.METHOD] == 65.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_independence_case_c_high_everything_except_evidence_missing_a_role():
    result = _result(critical_evidence_present=(*AXIS_SCALE_KEYS, *WINDOW_CONTEXT_KEYS, *DENOMINATOR_KEYS))  # missing dual_axis role
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 76.0  # 3 of 4 roles


def test_independence_case_d_dual_axis_mechanism_overclaimed_and_calibration_follows():
    result = _result(
        decision={
            **GOOD_DECISION,
            "why_a_truthful_chart_can_still_mislead": "dual_axis_charts_are_never_a_legitimate_choice",
            "chart_review_standard": "any_chart_using_a_design_choice_like_axis_window_or_dual_axis_is_automatically_suspect",
        }
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 76.0  # 3 of 4 checks
    assert scores[ScoreDimension.OVERCONFIDENCE] == 25.0  # overclaim
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0


def test_evidence_role_axis_scale_requires_both_of_its_own_keys():
    without_one = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != SATISFACTION_DATA_GAP_EVIDENCE_KEY))
    assert _scores(without_one)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_roles_are_not_a_strict_subset_of_each_other():
    axis_only = _result(critical_evidence_present=AXIS_SCALE_KEYS)
    assert _scores(axis_only)[ScoreDimension.EVIDENCE] < 95.0  # only 1 of 4 roles

    window_and_denominator_only = _result(critical_evidence_present=(*WINDOW_CONTEXT_KEYS, *DENOMINATOR_KEYS))
    assert _scores(window_and_denominator_only)[ScoreDimension.EVIDENCE] < 95.0  # only 2 of 4 roles

    assert _scores(_result(critical_evidence_present=(SATISFACTION_DATA_GAP_EVIDENCE_KEY,)))[ScoreDimension.EVIDENCE] == 15.0


def test_recalibration_observation_fires_only_when_initial_was_flawed_and_final_is_correct():
    recalibrated = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=GOOD_CHOICES)
    patient = _result(initial_verdict_choices=GOOD_CHOICES, verdict_choices=GOOD_CHOICES)
    still_wrong = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=FLAWED_CHOICES)

    recalibration_key = "lesson.l28.feedback.pick_recalibrated"
    recalibrated_eval = score_lesson_twenty_eight(recalibrated, LESSON_28, hints_used=0)
    patient_eval = score_lesson_twenty_eight(patient, LESSON_28, hints_used=0)
    still_wrong_eval = score_lesson_twenty_eight(still_wrong, LESSON_28, hints_used=0)

    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key not in [o.text_key for o in still_wrong_eval.observations]
    assert _scores(patient)[ScoreDimension.METHOD] == _scores(recalibrated)[ScoreDimension.METHOD]


def test_mastery_requires_the_flawed_rate_claim_the_strongest_claim_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_the_flawed_rate_shows": "a_mathematically_real_rate_but_not_the_right_denominator_for_the_question",
            "mastery_strongest_claim": "the_correctly_denominated_rate_is_the_relevant_rate_for_this_question",
            "mastery_supporting_evidence": ("fair_rate_q3_low_point",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_the_flawed_rate_shows": "a_mathematically_real_rate_but_not_the_right_denominator_for_the_question",
            "mastery_strongest_claim": "the_correctly_denominated_rate_is_the_relevant_rate_for_this_question",
            "mastery_supporting_evidence": ("fair_rate_q3_low_point", "flawed_rate_q4_low_point"),
        },
    )
    evaluation_partial = score_lesson_twenty_eight(partial, LESSON_28, hints_used=0)
    evaluation_complete = score_lesson_twenty_eight(complete, LESSON_28, hints_used=0)

    mastery_key = "lesson.l28.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]


def test_evidence_key_pool_is_exactly_nine_across_four_roles():
    assert len(CRITICAL_EVIDENCE_KEYS) == 9
    assert len(set(CRITICAL_EVIDENCE_KEYS)) == 9
    assert set(AXIS_SCALE_KEYS) | set(WINDOW_CONTEXT_KEYS) | set(DENOMINATOR_KEYS) | set(DUAL_AXIS_KEYS) == set(CRITICAL_EVIDENCE_KEYS)
    all_roles = (AXIS_SCALE_KEYS, WINDOW_CONTEXT_KEYS, DENOMINATOR_KEYS, DUAL_AXIS_KEYS)
    for i, role_a in enumerate(all_roles):
        for role_b in all_roles[i + 1 :]:
            assert set(role_a).isdisjoint(set(role_b))

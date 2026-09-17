from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l27_causality_courtroom.definition import LESSON_27
from data_science_arcade.lessons.l27_causality_courtroom.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    LessonTwentySevenResult,
    OBSERVED_DIFFERENCE_KEYS,
    RANDOMIZED_COMPARISON_KEYS,
    TOOL_SPEND_DIFFERENCE_EVIDENCE_KEY,
    score_lesson_twenty_seven,
)

GOOD_CHOICES = {
    "tool_spend_claim": "sustain_self_selection",
    "resolution_satisfaction_claim": "sustain_difficulty_not_speed",
    "training_performance_claim": "sustain_cant_separate_from_who_attended",
}
FLAWED_CHOICES = {
    "tool_spend_claim": "overrule_correlation_proves_it",
    "resolution_satisfaction_claim": "overrule_mandate_speed_everywhere",
    "training_performance_claim": "overrule_too_large_for_coincidence",
}
GOOD_DECISION = {
    "why_non_random_group_formation_undermines_a_comparison": "people_or_processes_that_land_in_a_group_may_already_differ_before_anything_happens",
    "why_the_right_verdict_still_needs_the_right_reason": "misdiagnosing_the_mechanism_can_miss_the_real_problem_even_when_the_verdict_is_right",
    "missing_evidence": "a_design_that_breaks_the_link_between_pre_existing_type_and_the_exposure_being_compared",
    "what_randomization_changes": "breaks_the_link_between_pre_existing_type_and_assigned_condition_in_expectation",
    "final_verdict": "each_needs_a_proper_comparison_group",
}


def _result(**overrides) -> LessonTwentySevenResult:
    defaults = dict(
        initial_verdict_choices=dict(GOOD_CHOICES),
        verdict_choices=dict(GOOD_CHOICES),
        reveal_observed_difference_interpretation="a_real_observed_difference_between_two_groups_not_yet_a_measured_effect",
        reveal_randomization_interpretation="the_observational_comparison_substantially_overstated_what_the_randomized_comparison_estimates",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentySevenResult(**defaults)


def _scores(result: LessonTwentySevenResult) -> dict:
    return score_lesson_twenty_seven(result, LESSON_27, hints_used=0).dimension_scores


def test_fully_correct_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 92.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_scoring_dimensions_are_exactly_four_no_uncertainty():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE}


def test_method_reads_only_the_final_post_revision_verdicts():
    result = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=GOOD_CHOICES)
    assert _scores(result)[ScoreDimension.METHOD] == 95.0


def test_interpretations_never_affect_scoring():
    a = _result(
        reveal_observed_difference_interpretation="differences_this_large_and_consistent_can_only_come_from_the_treatment_itself",
        reveal_randomization_interpretation="the_25_point_observational_gap_is_the_beta_checkouts_real_effect",
    )
    b = _result()
    assert _scores(a) == _scores(b)


def test_independence_case_a_high_everything_except_calibration_underclaim():
    result = _result(decision={**GOOD_DECISION, "final_verdict": "all_should_be_thrown_out"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 92.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 35.0


def test_independence_case_b_high_reasoning_lower_method_despite_a_real_revision_opportunity():
    result = _result(
        initial_verdict_choices=GOOD_CHOICES,
        verdict_choices={**GOOD_CHOICES, "training_performance_claim": "sustain_reviews_are_always_biased"},
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.METHOD] == 65.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_independence_case_c_high_everything_except_evidence_missing_a_role():
    result = _result(critical_evidence_present=OBSERVED_DIFFERENCE_KEYS)  # only 1 of 2 roles
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 50.0


def test_independence_case_d_right_reason_mechanism_overclaimed_and_final_verdict_follows():
    result = _result(
        decision={
            **GOOD_DECISION,
            "why_the_right_verdict_still_needs_the_right_reason": "any_skepticism_works_as_long_as_the_final_call_is_right",
            "final_verdict": "all_confirmed_effects_too_large_for_chance",
        }
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 76.0  # 3 of 4 checks
    assert scores[ScoreDimension.OVERCONFIDENCE] == 25.0  # overclaim
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 92.0


def test_evidence_role_observed_difference_requires_all_three_of_its_own_keys():
    without_one = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != TOOL_SPEND_DIFFERENCE_EVIDENCE_KEY))
    assert _scores(without_one)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_roles_are_not_a_strict_subset_of_each_other():
    observed_difference_only = _result(critical_evidence_present=OBSERVED_DIFFERENCE_KEYS)
    assert _scores(observed_difference_only)[ScoreDimension.EVIDENCE] < 92.0  # only 1 of 2 roles

    randomized_comparison_only = _result(critical_evidence_present=RANDOMIZED_COMPARISON_KEYS)
    assert _scores(randomized_comparison_only)[ScoreDimension.EVIDENCE] < 92.0

    assert _scores(_result(critical_evidence_present=(TOOL_SPEND_DIFFERENCE_EVIDENCE_KEY,)))[ScoreDimension.EVIDENCE] == 15.0


def test_recalibration_observation_fires_only_when_initial_was_flawed_and_final_is_correct():
    recalibrated = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=GOOD_CHOICES)
    patient = _result(initial_verdict_choices=GOOD_CHOICES, verdict_choices=GOOD_CHOICES)
    still_wrong = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=FLAWED_CHOICES)

    recalibration_key = "lesson.l27.feedback.verdict_recalibrated"
    recalibrated_eval = score_lesson_twenty_seven(recalibrated, LESSON_27, hints_used=0)
    patient_eval = score_lesson_twenty_seven(patient, LESSON_27, hints_used=0)
    still_wrong_eval = score_lesson_twenty_seven(still_wrong, LESSON_27, hints_used=0)

    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key not in [o.text_key for o in still_wrong_eval.observations]
    assert _scores(patient)[ScoreDimension.METHOD] == _scores(recalibrated)[ScoreDimension.METHOD]


def test_mastery_requires_the_naive_claim_the_strongest_claim_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_the_naive_comparison_shows": "reflects_both_a_possible_effect_and_pre_existing_differences_between_who_opted_in_and_who_didnt",
            "mastery_strongest_claim": "the_randomized_test_estimates_a_much_smaller_effect_than_the_naive_comparison_suggested",
            "mastery_supporting_evidence": ("naive_gap_37_points",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_the_naive_comparison_shows": "reflects_both_a_possible_effect_and_pre_existing_differences_between_who_opted_in_and_who_didnt",
            "mastery_strongest_claim": "the_randomized_test_estimates_a_much_smaller_effect_than_the_naive_comparison_suggested",
            "mastery_supporting_evidence": ("naive_gap_37_points", "randomized_estimate_5_points"),
        },
    )
    evaluation_partial = score_lesson_twenty_seven(partial, LESSON_27, hints_used=0)
    evaluation_complete = score_lesson_twenty_seven(complete, LESSON_27, hints_used=0)

    mastery_key = "lesson.l27.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]


def test_evidence_key_pool_is_exactly_five_across_two_roles():
    assert len(CRITICAL_EVIDENCE_KEYS) == 5
    assert len(set(CRITICAL_EVIDENCE_KEYS)) == 5
    assert set(OBSERVED_DIFFERENCE_KEYS) | set(RANDOMIZED_COMPARISON_KEYS) == set(CRITICAL_EVIDENCE_KEYS)
    assert set(OBSERVED_DIFFERENCE_KEYS).isdisjoint(set(RANDOMIZED_COMPARISON_KEYS))

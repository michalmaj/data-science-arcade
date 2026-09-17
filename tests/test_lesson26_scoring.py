from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l26_correlation_crime_scene.definition import LESSON_26
from data_science_arcade.lessons.l26_correlation_crime_scene.scoring import (
    CONFOUNDING_KEYS,
    CRITICAL_EVIDENCE_KEYS,
    DARK_MODE_OVERALL_CORRELATION_EVIDENCE_KEY,
    DEVICE_GROUP_SPEND_CORRELATION_EVIDENCE_KEY,
    LessonTwentySixResult,
    PUSH_OPENS_CORRELATION_EVIDENCE_KEY,
    STRONG_ASSOCIATION_KEYS,
    score_lesson_twenty_six,
)

GOOD_CHOICES = {
    "push_opens_claim": "strong_association_multiple_explanations_remain",
    "shipment_sales_claim": "reverse_ruled_out_two_remain",
    "dark_mode_claim": "device_group_is_a_strong_candidate_explanation",
}
FLAWED_CHOICES = {
    "push_opens_claim": "proves_push_causes_spend",
    "shipment_sales_claim": "must_be_the_shipment_then",
    "dark_mode_claim": "dark_mode_clearly_boosts_spend",
}
GOOD_DECISION = {
    "why_the_within_modern_comparison_matters_more": "isolates_whether_dark_mode_relates_to_spend_among_comparable_customers",
    "why_ruling_out_reverse_causation_doesnt_prove_direct": "eliminating_one_explanation_narrows_the_space_it_doesnt_confirm_whats_left",
    "why_a_strong_observed_correlation_still_isnt_a_named_cause": "establishes_a_strong_association_multiple_causal_stories_remain_compatible",
    "next_evidence": "a_randomized_test_or_ruling_out_alternatives",
    "strongest_defensible_claim": "a_real_pattern_not_a_proven_cause",
}


def _result(**overrides) -> LessonTwentySixResult:
    defaults = dict(
        initial_verdict_choices=dict(GOOD_CHOICES),
        verdict_choices=dict(GOOD_CHOICES),
        reveal_strong_association_interpretation="both_are_strong_real_patterns_worth_investigating",
        reveal_confounding_interpretation="device_group_is_a_strong_candidate_explanation_for_the_aggregate_pattern",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentySixResult(**defaults)


def _scores(result: LessonTwentySixResult) -> dict:
    return score_lesson_twenty_six(result, LESSON_26, hints_used=0).dimension_scores


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
        reveal_strong_association_interpretation="correlations_this_strong_prove_a_causal_mechanism",
        reveal_confounding_interpretation="this_proves_owning_a_modern_device_causes_higher_spend",
    )
    b = _result()
    assert _scores(a) == _scores(b)


def test_independence_case_a_high_everything_except_calibration_underclaim():
    """The specific regression the review flagged: the new nihilistic
    option must trigger the underclaim branch, not just fail to trigger
    calibrated."""
    result = _result(decision={**GOOD_DECISION, "strongest_defensible_claim": "correlation_this_strong_still_tells_us_nothing_useful"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 92.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 35.0


def test_independence_case_b_high_reasoning_lower_method_despite_a_real_revision_opportunity():
    result = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=FLAWED_CHOICES)
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.METHOD] == 15.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_independence_case_c_high_everything_except_evidence_missing_a_role():
    result = _result(critical_evidence_present=STRONG_ASSOCIATION_KEYS)  # only 1 of 2 roles
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 50.0


def test_independence_case_d_within_modern_mechanism_overclaimed_and_final_claim_follows():
    result = _result(
        decision={
            **GOOD_DECISION,
            "why_the_within_modern_comparison_matters_more": "this_proves_dark_mode_has_zero_effect_everywhere",
            "strongest_defensible_claim": "direct_causation_confirmed_every_time",
        }
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 76.0  # 3 of 4 checks
    assert scores[ScoreDimension.OVERCONFIDENCE] == 25.0  # overclaim
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 92.0


def test_evidence_role_strong_association_requires_both_of_its_own_keys():
    without_one = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != PUSH_OPENS_CORRELATION_EVIDENCE_KEY))
    assert _scores(without_one)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_confounding_requires_all_three_of_its_own_keys():
    without_one = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != DEVICE_GROUP_SPEND_CORRELATION_EVIDENCE_KEY))
    assert _scores(without_one)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_roles_are_not_a_strict_subset_of_each_other():
    strong_association_only = _result(critical_evidence_present=STRONG_ASSOCIATION_KEYS)
    assert _scores(strong_association_only)[ScoreDimension.EVIDENCE] < 92.0  # only 1 of 2 roles

    confounding_only = _result(critical_evidence_present=CONFOUNDING_KEYS)
    assert _scores(confounding_only)[ScoreDimension.EVIDENCE] < 92.0

    assert _scores(_result(critical_evidence_present=(DARK_MODE_OVERALL_CORRELATION_EVIDENCE_KEY,)))[ScoreDimension.EVIDENCE] == 15.0


def test_recalibration_observation_fires_only_when_initial_was_flawed_and_final_is_correct():
    recalibrated = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=GOOD_CHOICES)
    patient = _result(initial_verdict_choices=GOOD_CHOICES, verdict_choices=GOOD_CHOICES)
    still_wrong = _result(initial_verdict_choices=FLAWED_CHOICES, verdict_choices=FLAWED_CHOICES)

    recalibration_key = "lesson.l26.feedback.verdict_recalibrated"
    recalibrated_eval = score_lesson_twenty_six(recalibrated, LESSON_26, hints_used=0)
    patient_eval = score_lesson_twenty_six(patient, LESSON_26, hints_used=0)
    still_wrong_eval = score_lesson_twenty_six(still_wrong, LESSON_26, hints_used=0)

    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key not in [o.text_key for o in still_wrong_eval.observations]
    assert _scores(patient)[ScoreDimension.METHOD] == _scores(recalibrated)[ScoreDimension.METHOD]


def test_mastery_requires_the_gap_claim_the_strongest_claim_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_the_observational_gap_represents": "overstates_what_the_experiment_attributes_to_the_program",
            "mastery_strongest_claim": "randomized_comparison_supports_a_much_smaller_positive_effect",
            "mastery_supporting_evidence": ("observational_gap_160_dollars",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_the_observational_gap_represents": "overstates_what_the_experiment_attributes_to_the_program",
            "mastery_strongest_claim": "randomized_comparison_supports_a_much_smaller_positive_effect",
            "mastery_supporting_evidence": ("observational_gap_160_dollars", "randomized_estimate_15_dollars"),
        },
    )
    evaluation_partial = score_lesson_twenty_six(partial, LESSON_26, hints_used=0)
    evaluation_complete = score_lesson_twenty_six(complete, LESSON_26, hints_used=0)

    mastery_key = "lesson.l26.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]


def test_evidence_key_pool_is_exactly_five_across_two_roles():
    assert len(CRITICAL_EVIDENCE_KEYS) == 5
    assert len(set(CRITICAL_EVIDENCE_KEYS)) == 5
    assert set(STRONG_ASSOCIATION_KEYS) | set(CONFOUNDING_KEYS) == set(CRITICAL_EVIDENCE_KEYS)
    assert set(STRONG_ASSOCIATION_KEYS).isdisjoint(set(CONFOUNDING_KEYS))

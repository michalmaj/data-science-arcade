from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l24_survey_bureau.definition import LESSON_24
from data_science_arcade.lessons.l24_survey_bureau.scoring import (
    BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    IN_APP_POPUP_EXCLUDED_CHURNED_COUNT_EVIDENCE_KEY,
    IN_APP_POPUP_NEUTRAL_MEAN_EVIDENCE_KEY,
    LessonTwentyFourResult,
    POWER_USER_PANEL_CRITIC_COUNT_EVIDENCE_KEY,
    POWER_USER_PANEL_NEUTRAL_MEAN_EVIDENCE_KEY,
    QUIET_MAJORITY_RESPONSE_RATE_EVIDENCE_KEY,
    VOCAL_CRITIC_RESPONSE_RATE_EVIDENCE_KEY,
    VOCAL_FAN_RESPONSE_RATE_EVIDENCE_KEY,
    score_lesson_twenty_four,
)

GOOD_SURVEY_CHOICES = {"general_satisfaction_check": ("neutral", "broad_email")}
FLAWED_SURVEY_CHOICES = {"general_satisfaction_check": ("neutral", "power_user_panel")}
GOOD_DECISION = {
    "why_in_app_popup_misleads": "excludes_customers_who_already_churned",
    "why_power_user_panel_misleads": "sampling_frame_excludes_critics_entirely",
    "why_leading_wording_distorts": "systematically_pushes_satisfaction_upward_never_fixes_reach_or_response",
    "what_broad_email_neutral_still_cant_fix": "who_actually_responds_can_still_be_uneven_even_with_full_reach_and_neutral_wording",
    "strongest_defensible_claim": "most_defensible_design_but_still_a_signal_not_proof_of_everyone",
}


def _result(**overrides) -> LessonTwentyFourResult:
    defaults = dict(
        initial_survey_choices=dict(GOOD_SURVEY_CHOICES),
        survey_choices=dict(GOOD_SURVEY_CHOICES),
        reveal_coverage_bias_interpretation="in_app_popup_excludes_already_churned_critics",
        reveal_sampling_frame_interpretation="panel_sampling_frame_excludes_critics_entirely",
        reveal_nonresponse_bias_interpretation="response_rates_differ_sharply_never_a_random_cross_section",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentyFourResult(**defaults)


def _scores(result: LessonTwentyFourResult) -> dict:
    return score_lesson_twenty_four(result, LESSON_24, hints_used=0).dimension_scores


def test_fully_correct_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_scoring_dimensions_are_exactly_four_no_uncertainty():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE}


def test_method_reads_only_the_final_post_revision_choice():
    result = _result(initial_survey_choices=FLAWED_SURVEY_CHOICES, survey_choices=GOOD_SURVEY_CHOICES)
    assert _scores(result)[ScoreDimension.METHOD] == 95.0


def test_interpretations_never_affect_scoring():
    a = _result(
        reveal_coverage_bias_interpretation="in_app_popup_proves_users_are_happier",
        reveal_sampling_frame_interpretation="power_users_know_product_best_so_83_is_trustworthy",
        reveal_nonresponse_bias_interpretation="since_everyone_could_respond_the_mix_must_match_the_population",
    )
    b = _result()
    assert _scores(a) == _scores(b)


def test_independence_case_a_high_everything_except_calibration_overclaim():
    result = _result(decision={**GOOD_DECISION, "strongest_defensible_claim": "accurately_represents_all_customers"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 25.0


def test_independence_case_b_high_reasoning_lower_method_despite_real_revision_opportunity():
    result = _result(initial_survey_choices=FLAWED_SURVEY_CHOICES, survey_choices=FLAWED_SURVEY_CHOICES)
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.METHOD] == 25.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_independence_case_c_high_everything_except_evidence_incomplete():
    result = _result(
        critical_evidence_present=(POWER_USER_PANEL_NEUTRAL_MEAN_EVIDENCE_KEY, POWER_USER_PANEL_CRITIC_COUNT_EVIDENCE_KEY, BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY)
    )
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.EVIDENCE] < 95.0


def test_independence_case_d_power_panel_mechanism_misdiagnosed_and_underclaim():
    result = _result(
        decision={
            **GOOD_DECISION,
            "why_power_user_panel_misleads": "panel_too_small_to_matter",
            "strongest_defensible_claim": "tells_us_nothing_useful",
        }
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 76.0  # 3 of 4 checks
    assert scores[ScoreDimension.OVERCONFIDENCE] == 35.0  # underclaim
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0


def test_evidence_role_coverage_bias_requires_all_three_of_its_own_keys():
    without_count = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != IN_APP_POPUP_EXCLUDED_CHURNED_COUNT_EVIDENCE_KEY))
    assert _scores(without_count)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_sampling_frame_requires_all_three_of_its_own_keys():
    without_count = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != POWER_USER_PANEL_CRITIC_COUNT_EVIDENCE_KEY))
    assert _scores(without_count)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_coverage_and_sampling_frame_are_not_a_strict_subset_of_each_other():
    """The mean/mean/count shape of each role must not let citing one
    role's own facts silently satisfy the other - coverage bias and
    sampling frame bias are structurally different mechanisms."""
    coverage_only = _result(
        critical_evidence_present=(BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY, IN_APP_POPUP_NEUTRAL_MEAN_EVIDENCE_KEY, IN_APP_POPUP_EXCLUDED_CHURNED_COUNT_EVIDENCE_KEY)
    )
    scores = _scores(coverage_only)
    assert scores[ScoreDimension.EVIDENCE] < 95.0  # only 1 of 3 roles


def test_evidence_role_nonresponse_bias_requires_all_three_response_rates():
    two_of_three = _result(
        critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != QUIET_MAJORITY_RESPONSE_RATE_EVIDENCE_KEY)
    )
    assert _scores(two_of_three)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]

    critic_and_fan_only = _result(critical_evidence_present=(VOCAL_CRITIC_RESPONSE_RATE_EVIDENCE_KEY, VOCAL_FAN_RESPONSE_RATE_EVIDENCE_KEY))
    assert _scores(critic_and_fan_only)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_recalibration_observation_fires_only_when_initial_was_flawed_and_final_is_correct():
    recalibrated = _result(initial_survey_choices=FLAWED_SURVEY_CHOICES, survey_choices=GOOD_SURVEY_CHOICES)
    patient = _result(initial_survey_choices=GOOD_SURVEY_CHOICES, survey_choices=GOOD_SURVEY_CHOICES)
    still_wrong = _result(initial_survey_choices=FLAWED_SURVEY_CHOICES, survey_choices=FLAWED_SURVEY_CHOICES)

    recalibration_key = "lesson.l24.feedback.survey_combo_recalibrated"
    recalibrated_eval = score_lesson_twenty_four(recalibrated, LESSON_24, hints_used=0)
    patient_eval = score_lesson_twenty_four(patient, LESSON_24, hints_used=0)
    still_wrong_eval = score_lesson_twenty_four(still_wrong, LESSON_24, hints_used=0)

    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key not in [o.text_key for o in still_wrong_eval.observations]
    assert _scores(patient)[ScoreDimension.METHOD] == _scores(recalibrated)[ScoreDimension.METHOD]


def test_mastery_requires_what_88_represents_why_blended_is_lower_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_88_percent_represents": "only_customers_whose_delivery_succeeded",
            "mastery_why_blended_is_lower": "never_surveyed_group_has_a_separate_source_estimate",
            "mastery_supporting_evidence": ("delivery_succeeded_surveyed_88_percent",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_88_percent_represents": "only_customers_whose_delivery_succeeded",
            "mastery_why_blended_is_lower": "never_surveyed_group_has_a_separate_source_estimate",
            "mastery_supporting_evidence": ("delivery_succeeded_surveyed_88_percent", "delivery_failed_or_delayed_separate_source_20_percent"),
        },
    )
    evaluation_partial = score_lesson_twenty_four(partial, LESSON_24, hints_used=0)
    evaluation_complete = score_lesson_twenty_four(complete, LESSON_24, hints_used=0)

    mastery_key = "lesson.l24.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]

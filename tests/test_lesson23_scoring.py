from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l23_time_series_control_room.definition import LESSON_23
from data_science_arcade.lessons.l23_time_series_control_room.scoring import (
    CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY,
    CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    LessonTwentyThreeResult,
    RELEASE_WEEKEND_SAT_BASELINE_EVIDENCE_KEY,
    RELEASE_WEEKEND_SAT_CURRENT_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY,
    RELEASE_WEEKEND_SUN_CURRENT_EVIDENCE_KEY,
    score_lesson_twenty_three,
)

GOOD_LENS_CHOICES = {"release_dip_claim": "same_days_previous_period"}
MISMATCHED_LENS_CHOICES = {"release_dip_claim": "nearby_days_only"}
GOOD_DECISION = {
    "baseline_for_release_claim": "weekday_aligned_reference_period",
    "what_post_release_weekend_supports": "matches_ordinary_recurring_pattern_no_extra_deviation",
    "what_campaign_monday_supports": "real_observed_deviation_from_own_baseline",
    "why_nearby_day_comparison_misleading": "conflates_different_weekdays_own_different_baselines",
    "strongest_defensible_claim": "no_extra_release_deviation_campaign_real_not_causally_proven",
}


def _result(**overrides) -> LessonTwentyThreeResult:
    defaults = dict(
        initial_lens_choices=dict(GOOD_LENS_CHOICES),
        lens_choices=dict(GOOD_LENS_CHOICES),
        reveal_weekday_baseline_interpretation="matches_recurring_baseline_no_extra_deviation",
        reveal_campaign_deviation_interpretation="real_deviation_not_causally_proven",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentyThreeResult(**defaults)


def _scores(result: LessonTwentyThreeResult) -> dict:
    return score_lesson_twenty_three(result, LESSON_23, hints_used=0).dimension_scores


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
    result = _result(initial_lens_choices=MISMATCHED_LENS_CHOICES, lens_choices=GOOD_LENS_CHOICES)
    assert _scores(result)[ScoreDimension.METHOD] == 95.0


def test_interpretations_never_affect_scoring():
    a = _result(reveal_weekday_baseline_interpretation="release_definitely_caused_the_dip", reveal_campaign_deviation_interpretation="just_normal_noise_nothing_unusual")
    b = _result()
    assert _scores(a) == _scores(b)


def test_independence_case_a_high_everything_except_calibration_overclaim():
    result = _result(decision={**GOOD_DECISION, "strongest_defensible_claim": "release_and_campaign_both_definitely_caused_it"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 25.0


def test_independence_case_b_high_reasoning_lower_method_despite_real_revision_opportunity():
    result = _result(initial_lens_choices=MISMATCHED_LENS_CHOICES, lens_choices=MISMATCHED_LENS_CHOICES)
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.METHOD] == 25.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_independence_case_c_high_everything_except_evidence_incomplete():
    result = _result(critical_evidence_present=(CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY, CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY))
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.EVIDENCE] < 95.0


def test_independence_case_d_campaign_deviation_denied_lowers_both_reasoning_and_calibration():
    result = _result(
        decision={
            **GOOD_DECISION,
            "what_campaign_monday_supports": "just_normal_noise",
            "strongest_defensible_claim": "everything_here_is_just_calendar_noise",
        }
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 76.0  # 3 of 4 checks
    assert scores[ScoreDimension.OVERCONFIDENCE] == 35.0  # underclaim
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0


def test_evidence_role_weekday_baseline_structure_requires_all_three_baselines():
    without_sun_baseline = _result(
        critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY)
    )
    assert _scores(without_sun_baseline)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_release_window_requires_both_weekend_days_not_just_one():
    """Defending 'the release weekend matches its baseline' requires both
    Saturday and Sunday's own current+baseline pairs - one day alone
    doesn't defend a claim about the whole weekend."""
    base = (CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY, CAMPAIGN_MONDAY_BASELINE_EVIDENCE_KEY, RELEASE_WEEKEND_SAT_BASELINE_EVIDENCE_KEY, RELEASE_WEEKEND_SUN_BASELINE_EVIDENCE_KEY)
    saturday_current_only = _result(critical_evidence_present=(*base, RELEASE_WEEKEND_SAT_CURRENT_EVIDENCE_KEY))
    sunday_current_only = _result(critical_evidence_present=(*base, RELEASE_WEEKEND_SUN_CURRENT_EVIDENCE_KEY))
    both = _result(critical_evidence_present=(*base, RELEASE_WEEKEND_SAT_CURRENT_EVIDENCE_KEY, RELEASE_WEEKEND_SUN_CURRENT_EVIDENCE_KEY))

    incomplete_score = _scores(saturday_current_only)[ScoreDimension.EVIDENCE]
    assert incomplete_score == _scores(sunday_current_only)[ScoreDimension.EVIDENCE]
    assert incomplete_score < _scores(both)[ScoreDimension.EVIDENCE]
    assert _scores(both)[ScoreDimension.EVIDENCE] == 95.0


def test_evidence_role_campaign_deviation_is_its_own_required_role():
    without = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != CAMPAIGN_MONDAY_CURRENT_EVIDENCE_KEY))
    assert _scores(without)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_recalibration_observation_fires_only_when_initial_was_mismatched_and_final_is_correct():
    recalibrated = _result(initial_lens_choices=MISMATCHED_LENS_CHOICES, lens_choices=GOOD_LENS_CHOICES)
    patient = _result(initial_lens_choices=GOOD_LENS_CHOICES, lens_choices=GOOD_LENS_CHOICES)
    still_wrong = _result(initial_lens_choices=MISMATCHED_LENS_CHOICES, lens_choices=MISMATCHED_LENS_CHOICES)

    recalibration_key = "lesson.l23.feedback.lens_choice_recalibrated"
    recalibrated_eval = score_lesson_twenty_three(recalibrated, LESSON_23, hints_used=0)
    patient_eval = score_lesson_twenty_three(patient, LESSON_23, hints_used=0)
    still_wrong_eval = score_lesson_twenty_three(still_wrong, LESSON_23, hints_used=0)

    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key not in [o.text_key for o in still_wrong_eval.observations]
    assert _scores(patient)[ScoreDimension.METHOD] == _scores(recalibrated)[ScoreDimension.METHOD]


def test_mastery_requires_fair_reference_incident_interpretation_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_fair_reference": "compare_to_another_post_holiday_day",
            "mastery_incident_interpretation": "recurring_post_holiday_pattern_not_a_one_off",
            "mastery_supporting_evidence": ("spring_alert_71_percent",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_fair_reference": "compare_to_another_post_holiday_day",
            "mastery_incident_interpretation": "recurring_post_holiday_pattern_not_a_one_off",
            "mastery_supporting_evidence": ("spring_alert_71_percent", "autumn_repeat_70_percent"),
        },
    )
    evaluation_partial = score_lesson_twenty_three(partial, LESSON_23, hints_used=0)
    evaluation_complete = score_lesson_twenty_three(complete, LESSON_23, hints_used=0)

    mastery_key = "lesson.l23.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]

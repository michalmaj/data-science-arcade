from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l25_kpi_emergency_room.definition import LESSON_25
from data_science_arcade.lessons.l25_kpi_emergency_room.scoring import (
    CHECKOUT_ERROR_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    INCIDENT_COVERAGE_KEYS,
    LessonTwentyFiveResult,
    ON_TIME_DELIVERY_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
    PAGE_LOAD_TIME_BALANCED_FALSE_ALARM_COUNT_EVIDENCE_KEY,
    PAGE_LOAD_TIME_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY,
    PAGE_LOAD_TIME_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY,
    SOCIAL_MENTIONS_BALANCED_ALERT_COUNT_EVIDENCE_KEY,
    SOCIAL_MENTIONS_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY,
    THRESHOLD_TRADEOFF_KEYS,
    WRONG_METRIC_SILENCE_KEYS,
    score_lesson_twenty_five,
)

GOOD_CHOICES = {"checkout_incident_focus": ("checkout_error_rate", "tight"), "delivery_incident_focus": ("on_time_delivery_rate", "balanced")}
FLAWED_CHOICES = {"checkout_incident_focus": ("social_mentions", "balanced"), "delivery_incident_focus": ("page_load_time", "tight")}
GOOD_DECISION = {
    "compact_monitoring_set": ("checkout_error_rate", "on_time_delivery_rate"),
    "why_tight_threshold_creates_extra_false_alarms": "flags_ordinary_variation_without_improving_detection_of_the_real_incidents",
    "why_social_mentions_missed_both_observed_incidents": "did_not_align_with_either_incident_and_threshold_changes_only_shifted_which_days_alarmed",
    "what_an_alert_can_and_cant_tell_you": "something_crossed_a_real_line_worth_investigating_not_why_it_happened",
    "strongest_defensible_claim": "checkout_and_delivery_alerts_flag_real_incidents_but_dont_explain_them_and_silence_elsewhere_isnt_proof_of_health",
}


def _result(**overrides) -> LessonTwentyFiveResult:
    defaults = dict(
        initial_monitoring_choices=dict(GOOD_CHOICES),
        monitoring_choices=dict(GOOD_CHOICES),
        reveal_threshold_tradeoff_interpretation="tighter_threshold_cost_more_false_alarms_without_catching_more",
        reveal_incident_coverage_interpretation="checkout_and_delivery_metrics_caught_their_incidents_social_mentions_caught_neither",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentyFiveResult(**defaults)


def _scores(result: LessonTwentyFiveResult) -> dict:
    return score_lesson_twenty_five(result, LESSON_25, hints_used=0).dimension_scores


def test_fully_correct_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 92.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_scoring_dimensions_are_exactly_four_no_communication():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE}


def test_method_reads_only_the_final_post_revision_metric_choice():
    result = _result(initial_monitoring_choices=FLAWED_CHOICES, monitoring_choices=GOOD_CHOICES)
    assert _scores(result)[ScoreDimension.METHOD] == 92.0


def test_method_ignores_threshold_entirely_tight_and_balanced_score_identically():
    """Conflict 1's own resolution, directly regression-tested: swapping
    which threshold each request picked must never change METHOD (or any
    other dimension), since tight and balanced are byte-identical
    outcomes for both real metrics in this dataset."""
    tight_only = {"checkout_incident_focus": ("checkout_error_rate", "tight"), "delivery_incident_focus": ("on_time_delivery_rate", "tight")}
    balanced_only = {"checkout_incident_focus": ("checkout_error_rate", "balanced"), "delivery_incident_focus": ("on_time_delivery_rate", "balanced")}
    a = _result(initial_monitoring_choices=tight_only, monitoring_choices=tight_only)
    b = _result(initial_monitoring_choices=balanced_only, monitoring_choices=balanced_only)
    assert _scores(a) == _scores(b)


def test_interpretations_never_affect_scoring():
    a = _result(
        reveal_threshold_tradeoff_interpretation="any_tight_threshold_is_a_mistake_always_prefer_balanced",
        reveal_incident_coverage_interpretation="since_social_mentions_never_alerted_the_business_was_healthy_the_whole_period",
    )
    b = _result()
    assert _scores(a) == _scores(b)


def test_independence_case_a_high_everything_except_calibration_overclaim():
    result = _result(decision={**GOOD_DECISION, "strongest_defensible_claim": "the_dashboard_now_proves_nothing_else_is_wrong"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 92.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 25.0


def test_independence_case_b_high_reasoning_lower_method_despite_a_real_revision_opportunity():
    result = _result(initial_monitoring_choices=FLAWED_CHOICES, monitoring_choices=FLAWED_CHOICES)
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.METHOD] == 15.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_independence_case_c_high_everything_except_evidence_missing_a_role():
    result = _result(critical_evidence_present=THRESHOLD_TRADEOFF_KEYS)  # only 1 of 3 roles
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 92.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.EVIDENCE] < 95.0


def test_independence_case_d_wrong_metric_mechanism_misdiagnosed_and_underclaim():
    result = _result(
        decision={
            **GOOD_DECISION,
            "why_social_mentions_missed_both_observed_incidents": "the_threshold_was_set_wrong",
            "strongest_defensible_claim": "alerts_dont_tell_us_anything_useful_without_a_root_cause",
        }
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 65.0  # 2 of 3 checks
    assert scores[ScoreDimension.OVERCONFIDENCE] == 35.0  # underclaim
    assert scores[ScoreDimension.METHOD] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0


def test_evidence_role_threshold_tradeoff_requires_all_three_of_its_own_keys():
    without_one = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != PAGE_LOAD_TIME_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY))
    assert _scores(without_one)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_incident_coverage_requires_both_of_its_own_keys():
    without_one = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != ON_TIME_DELIVERY_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY))
    assert _scores(without_one)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_wrong_metric_silence_requires_both_of_its_own_keys():
    without_one = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != SOCIAL_MENTIONS_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY))
    assert _scores(without_one)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_roles_are_not_a_strict_subset_of_each_other():
    """The three roles cover structurally different mechanisms - citing
    one role's own facts must never silently satisfy another."""
    threshold_tradeoff_only = _result(critical_evidence_present=THRESHOLD_TRADEOFF_KEYS)
    scores = _scores(threshold_tradeoff_only)
    assert scores[ScoreDimension.EVIDENCE] < 95.0  # only 1 of 3 roles

    incident_coverage_only = _result(critical_evidence_present=INCIDENT_COVERAGE_KEYS)
    scores = _scores(incident_coverage_only)
    assert scores[ScoreDimension.EVIDENCE] < 95.0

    wrong_metric_silence_only = _result(critical_evidence_present=WRONG_METRIC_SILENCE_KEYS)
    scores = _scores(wrong_metric_silence_only)
    assert scores[ScoreDimension.EVIDENCE] < 95.0


def test_recalibration_observation_fires_only_when_initial_was_flawed_and_final_is_correct():
    recalibrated = _result(initial_monitoring_choices=FLAWED_CHOICES, monitoring_choices=GOOD_CHOICES)
    patient = _result(initial_monitoring_choices=GOOD_CHOICES, monitoring_choices=GOOD_CHOICES)
    still_wrong = _result(initial_monitoring_choices=FLAWED_CHOICES, monitoring_choices=FLAWED_CHOICES)

    recalibration_key = "lesson.l25.feedback.metric_choice_recalibrated"
    recalibrated_eval = score_lesson_twenty_five(recalibrated, LESSON_25, hints_used=0)
    patient_eval = score_lesson_twenty_five(patient, LESSON_25, hints_used=0)
    still_wrong_eval = score_lesson_twenty_five(still_wrong, LESSON_25, hints_used=0)

    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key not in [o.text_key for o in still_wrong_eval.observations]
    assert _scores(patient)[ScoreDimension.METHOD] == _scores(recalibrated)[ScoreDimension.METHOD]


def test_mastery_requires_what_46_cost_the_strongest_claim_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_the_46_false_alarms_cost": "real_incident_response_was_90x_slower_consistent_with_alert_fatigue",
            "mastery_strongest_claim": "high_false_alarm_volume_has_a_real_cost_even_when_the_real_incident_is_eventually_caught",
            "mastery_supporting_evidence": ("false_alarm_avg_response_4_minutes",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_what_the_46_false_alarms_cost": "real_incident_response_was_90x_slower_consistent_with_alert_fatigue",
            "mastery_strongest_claim": "high_false_alarm_volume_has_a_real_cost_even_when_the_real_incident_is_eventually_caught",
            "mastery_supporting_evidence": ("false_alarm_avg_response_4_minutes", "real_incident_avg_response_360_minutes"),
        },
    )
    evaluation_partial = score_lesson_twenty_five(partial, LESSON_25, hints_used=0)
    evaluation_complete = score_lesson_twenty_five(complete, LESSON_25, hints_used=0)

    mastery_key = "lesson.l25.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]


def test_evidence_key_pool_is_exactly_seven_across_three_roles():
    assert len(CRITICAL_EVIDENCE_KEYS) == 7
    assert len(set(CRITICAL_EVIDENCE_KEYS)) == 7
    assert set(THRESHOLD_TRADEOFF_KEYS) | set(INCIDENT_COVERAGE_KEYS) | set(WRONG_METRIC_SILENCE_KEYS) == set(CRITICAL_EVIDENCE_KEYS)
    assert PAGE_LOAD_TIME_TIGHT_FALSE_ALARM_COUNT_EVIDENCE_KEY in THRESHOLD_TRADEOFF_KEYS
    assert PAGE_LOAD_TIME_BALANCED_FALSE_ALARM_COUNT_EVIDENCE_KEY in THRESHOLD_TRADEOFF_KEYS
    assert CHECKOUT_ERROR_RATE_REAL_INCIDENTS_CAUGHT_EVIDENCE_KEY in INCIDENT_COVERAGE_KEYS
    assert SOCIAL_MENTIONS_BALANCED_ALERT_COUNT_EVIDENCE_KEY in WRONG_METRIC_SILENCE_KEYS

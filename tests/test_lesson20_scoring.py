from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l20_ab_test_commander.definition import LESSON_20
from data_science_arcade.lessons.l20_ab_test_commander.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    LessonTwentyResult,
    score_lesson_twenty,
)

GOOD_DECISION = {
    "final_verdict": "hold_full_rollout_investigate_support_guardrail",
    "why_not_a_clean_ship": "the_launch_rule_requires_every_guardrail_to_hold_too",
    "week3_stopping_rule_judgment": "no_efficacy_stopping_rule_was_pre_specified",
    "general_stopping_principle": "only_a_pre_specified_rule_efficacy_or_safety_justifies_acting_early",
    "what_explains_week3_vs_week7": "the_cumulative_estimate_moved_as_more_data_arrived_early_estimates_are_noisier",
    "why_guardrail_only_visible_at_week7": "the_support_harm_was_smaller_than_the_primary_lift_and_the_larger_sample_narrowed_its_interval_enough_to_clear_the_threshold",
}


def _result(**overrides) -> LessonTwentyResult:
    defaults = dict(
        week1_recommendation="not_sure_yet",
        week3_recommendation="hold_keep_running",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentyResult(**defaults)


def _scores(result: LessonTwentyResult) -> dict:
    return score_lesson_twenty(result, LESSON_20, hints_used=0).dimension_scores


def test_fully_correct_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_no_method_dimension_exists():
    scores = _scores(_result())
    assert ScoreDimension.METHOD not in scores


def test_scoring_dimensions_are_exactly_reasoning_evidence_uncertainty_overconfidence():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.UNCERTAINTY, ScoreDimension.OVERCONFIDENCE}


def test_independence_case_a_high_calibration_lower_reasoning():
    result = _result(decision={**GOOD_DECISION, "why_not_a_clean_ship": "primarys_not_really_significant"})
    scores = _scores(result)
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0
    assert scores[ScoreDimension.REASONING] < 95.0


def test_independence_case_b_high_reasoning_lower_calibration():
    result = _result(decision={**GOOD_DECISION, "final_verdict": "ship_full_rollout_primary_passed"})
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 25.0


def test_independence_case_c_patience_and_recalibration_score_identically():
    """Patience must not be scored lower than recalibration: a student who
    stayed patient from the start (week3='hold_keep_running') and one who
    leaned 'ship_now' at week 3 but reached the correct final verdict get
    the exact same CALIBRATION score - the recalibration is only ever a
    positive, additional observation, never a numeric bonus."""
    patient = _result(week3_recommendation="hold_keep_running", decision=GOOD_DECISION)
    recalibrated = _result(week3_recommendation="ship_now", decision=GOOD_DECISION)

    assert _scores(patient)[ScoreDimension.OVERCONFIDENCE] == _scores(recalibrated)[ScoreDimension.OVERCONFIDENCE]

    patient_eval = score_lesson_twenty(patient, LESSON_20, hints_used=0)
    recalibrated_eval = score_lesson_twenty(recalibrated, LESSON_20, hints_used=0)
    recalibration_key = "lesson.l20.feedback.verdict_recalibrated"
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]


def test_recalibration_requires_the_correct_final_verdict_not_just_a_premature_lean():
    result = _result(week3_recommendation="ship_now", decision={**GOOD_DECISION, "final_verdict": "ship_full_rollout_primary_passed"})
    evaluation = score_lesson_twenty(result, LESSON_20, hints_used=0)
    assert "lesson.l20.feedback.verdict_recalibrated" not in [o.text_key for o in evaluation.observations]


def test_independence_case_d_high_evidence_lower_uncertainty():
    result = _result(decision={**GOOD_DECISION, "what_explains_week3_vs_week7": "the_treatment_actually_got_worse"})
    scores = _scores(result)
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] < 92.0


def test_week1_recommendation_never_read_by_scoring():
    a = _result(week1_recommendation="ship_now")
    b = _result(week1_recommendation="not_sure_yet")
    assert _scores(a) == _scores(b)


def test_evidence_is_role_based_missing_one_real_role_costs_real_credit():
    missing_one = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS[:3])
    full = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS)
    assert _scores(missing_one)[ScoreDimension.EVIDENCE] < _scores(full)[ScoreDimension.EVIDENCE]


def test_calibration_distractor_verdicts_score_below_the_correct_one():
    correct = _scores(_result())[ScoreDimension.OVERCONFIDENCE]
    for wrong_verdict in ("ship_full_rollout_primary_passed", "kill_the_feature_entirely", "inconclusive_run_longer"):
        result = _result(decision={**GOOD_DECISION, "final_verdict": wrong_verdict})
        assert _scores(result)[ScoreDimension.OVERCONFIDENCE] < correct


def test_reasoning_and_uncertainty_read_only_the_decision_never_the_recommendations():
    a = _result(week1_recommendation="ship_now", week3_recommendation="ship_now", decision=GOOD_DECISION)
    b = _result(week1_recommendation="not_sure_yet", week3_recommendation="hold_keep_running", decision=GOOD_DECISION)
    scores_a, scores_b = _scores(a), _scores(b)
    assert scores_a[ScoreDimension.REASONING] == scores_b[ScoreDimension.REASONING]
    assert scores_a[ScoreDimension.UNCERTAINTY] == scores_b[ScoreDimension.UNCERTAINTY]


def test_mastery_requires_the_correct_judgment_contrast_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_stopping_judgment": "stop_now_pre_specified_safety_rule_is_met",
            "mastery_contrast_with_quickpay": "a_safety_rule_was_pre_specified_here_efficacy_never_was_for_quickpay",
            "mastery_supporting_evidence": ("interim_ci_entirely_above_the_prespecified_1pp_threshold",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_stopping_judgment": "stop_now_pre_specified_safety_rule_is_met",
            "mastery_contrast_with_quickpay": "a_safety_rule_was_pre_specified_here_efficacy_never_was_for_quickpay",
            "mastery_supporting_evidence": (
                "interim_ci_entirely_above_the_prespecified_1pp_threshold",
                "the_safety_rule_was_pre_specified_before_the_test_started",
            ),
        },
    )
    evaluation_partial = score_lesson_twenty(partial, LESSON_20, hints_used=0)
    evaluation_complete = score_lesson_twenty(complete, LESSON_20, hints_used=0)

    mastery_key = "lesson.l20.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]

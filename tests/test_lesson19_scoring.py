from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l19_power_plant.definition import LESSON_19
from data_science_arcade.lessons.l19_power_plant.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    METHOD_SCORE_BY_WEEKS,
    POWER_PROBABILITY_PAIR_KEYS,
    FINAL_PLAN_SENSITIVITY_EVIDENCE_KEY,
    PRECISE_TINY_EFFECT_EVIDENCE_KEY,
    UNDERPOWERED_CALIBRATION_EVIDENCE_KEY,
    LessonNineteenResult,
    score_lesson_nineteen,
)

GOOD_DECISION_7WK = {
    "final_design_meets_sensitivity_target": "meets_sensitivity_target",
    "what_more_sample_size_changes": "narrows_uncertainty_improves_sensitivity_not_effect_size",
    "what_mde_represents": "design_stage_probability_not_post_hoc_cutoff",
    "business_vs_statistical_detectability": "answer_different_questions_not_interchangeable",
    "underpowered_result_interpretation": "inconclusive_neither_zero_nor_worthwhile_ruled_out",
    "precise_small_effect_interpretation": "precisely_estimated_small_effect_below_threshold",
}
GOOD_DECISION_4WK = {**GOOD_DECISION_7WK, "final_design_meets_sensitivity_target": "does_not_meet_sensitivity_target"}


def _result(**overrides) -> LessonNineteenResult:
    defaults = dict(
        cold_duration_pick=7,
        final_weeks=7,
        decision=dict(GOOD_DECISION_7WK),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonNineteenResult(**defaults)


def _scores(result: LessonNineteenResult) -> dict:
    return score_lesson_nineteen(result, LESSON_19, hints_used=0).dimension_scores


def test_fully_correct_7week_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0


def test_method_is_a_real_gradient_not_binary():
    scores_by_weeks = {weeks: _scores(_result(final_weeks=weeks, decision=GOOD_DECISION_7WK if weeks == 7 else GOOD_DECISION_4WK))[ScoreDimension.METHOD] for weeks in (2, 4, 6, 7, 8, 12)}
    assert scores_by_weeks[2] < scores_by_weeks[4] < scores_by_weeks[6] < scores_by_weeks[7]
    assert scores_by_weeks[7] > scores_by_weeks[8] == scores_by_weeks[12]


def test_method_covers_all_12_possible_weeks_values_exactly_once():
    assert set(METHOD_SCORE_BY_WEEKS) == set(range(1, 13))


def test_eight_to_twelve_weeks_get_no_corrective_feedback_they_are_valid():
    for weeks in (8, 9, 10, 11, 12):
        evaluation = score_lesson_nineteen(_result(final_weeks=weeks, decision=GOOD_DECISION_7WK), LESSON_19, hints_used=0)
        method_observations = [o for o in evaluation.observations if o.dimension == ScoreDimension.METHOD]
        assert method_observations == [], f"weeks={weeks} should get no corrective METHOD feedback"


def test_method_reads_final_weeks_only_never_the_decision():
    result = _result(final_weeks=2, decision=GOOD_DECISION_7WK)  # a "perfect" brief on a bad plan
    assert _scores(result)[ScoreDimension.METHOD] == METHOD_SCORE_BY_WEEKS[2]


def test_independence_case_a_high_method_lower_reasoning():
    # Final design meets the target, but the Brief claims an observed
    # effect below MDE cannot be real.
    result = _result(final_weeks=7, decision={**GOOD_DECISION_7WK, "what_mde_represents": "a_hard_cutoff_effects_below_it_cannot_be_real"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] < 95.0


def test_independence_case_b_low_method_high_reasoning_and_uncertainty():
    # Final design left too short, but the student understands MDE/power
    # and correctly interprets both calibration cards.
    result = _result(final_weeks=2, decision={**GOOD_DECISION_7WK, "final_design_meets_sensitivity_target": "does_not_meet_sensitivity_target"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == METHOD_SCORE_BY_WEEKS[2]
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0


def test_independence_case_c_high_evidence_low_uncertainty():
    # Cites all the real numbers as Evidence, but claims the wide CI
    # crossing zero means there's no effect.
    result = _result(decision={**GOOD_DECISION_7WK, "underpowered_result_interpretation": "not_significant_so_no_real_effect"})
    scores = _scores(result)
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] < 92.0


def test_independence_case_d_uncertainty_may_be_high_reasoning_lower():
    # Understands the statistical/practical distinction, but incorrectly
    # claims a larger sample increases the true effect size.
    result = _result(decision={**GOOD_DECISION_7WK, "what_more_sample_size_changes": "makes_the_true_effect_bigger"})
    scores = _scores(result)
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0
    assert scores[ScoreDimension.REASONING] < 95.0


def test_reasoning_and_uncertainty_read_only_the_decision_never_final_weeks():
    a = _result(final_weeks=7, decision=GOOD_DECISION_7WK)
    b = _result(final_weeks=12, decision={**GOOD_DECISION_7WK, "final_design_meets_sensitivity_target": "meets_sensitivity_target"})
    scores_a, scores_b = _scores(a), _scores(b)
    assert scores_a[ScoreDimension.REASONING] == scores_b[ScoreDimension.REASONING]
    assert scores_a[ScoreDimension.UNCERTAINTY] == scores_b[ScoreDimension.UNCERTAINTY]


def test_calibration_cards_are_never_interpreted_via_mde_post_hoc():
    """The central analytical mistake this lesson exists to dismantle:
    MDE is a property of the plan, never a lens for reading a realized
    result. Neither calibration-interpretation field's own correct answer
    references MDE at all, and scoring never computes or compares any
    MDE value when checking these two fields - structurally impossible
    for the checker to smuggle in a "below/above MDE" comparison."""
    import inspect

    from data_science_arcade.lessons.l19_power_plant import scoring

    source = inspect.getsource(scoring._uncertainty_checks)
    assert "mde" not in source.lower()


def test_evidence_is_role_based_missing_one_real_role_costs_real_credit():
    missing_one = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS[:3])
    full = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS)
    assert _scores(missing_one)[ScoreDimension.EVIDENCE] < _scores(full)[ScoreDimension.EVIDENCE]


def test_power_probability_pair_role_requires_both_detection_rate_facts():
    """The 'what 80% power means' role lives in the CONTRAST between the
    4-week and 7-week detection rates - citing only one must not grant
    full role credit, and this must hold regardless of which Final Brief
    interpretation was chosen (fact-seen, not correct-interpretation,
    discipline)."""
    other_roles_only = (
        FINAL_PLAN_SENSITIVITY_EVIDENCE_KEY,
        UNDERPOWERED_CALIBRATION_EVIDENCE_KEY,
        PRECISE_TINY_EFFECT_EVIDENCE_KEY,
    )
    a_key, b_key = POWER_PROBABILITY_PAIR_KEYS

    a_only = _result(critical_evidence_present=(*other_roles_only, a_key))
    a_and_b = _result(critical_evidence_present=(*other_roles_only, a_key, b_key))

    scores_a_only = _scores(a_only)
    scores_a_and_b = _scores(a_and_b)

    # A alone: 3 of 4 roles complete (the pair role is NOT complete).
    assert scores_a_only[ScoreDimension.EVIDENCE] == {4: 95.0, 3: 74.0, 2: 50.0, 1: 25.0, 0: 10.0}[3]
    # A+B: all 4 roles complete.
    assert scores_a_and_b[ScoreDimension.EVIDENCE] == {4: 95.0, 3: 74.0, 2: 50.0, 1: 25.0, 0: 10.0}[4]
    assert scores_a_only[ScoreDimension.EVIDENCE] < scores_a_and_b[ScoreDimension.EVIDENCE]


def test_mastery_requires_the_correct_judgment_interpretation_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_design_judgment": "inadequate_for_the_2pp_target",
            "mastery_result_interpretation": "inconclusive_neither_zero_nor_worthwhile_ruled_out",
            "mastery_supporting_evidence": ("design_inadequate_for_2pp_target",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_design_judgment": "inadequate_for_the_2pp_target",
            "mastery_result_interpretation": "inconclusive_neither_zero_nor_worthwhile_ruled_out",
            "mastery_supporting_evidence": ("design_inadequate_for_2pp_target", "wide_ci_crosses_zero_and_target"),
        },
    )
    evaluation_partial = score_lesson_nineteen(partial, LESSON_19, hints_used=0)
    evaluation_complete = score_lesson_nineteen(complete, LESSON_19, hints_used=0)

    mastery_key = "lesson.l19.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]


def test_scoring_dimensions_are_exactly_method_reasoning_uncertainty_evidence():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.UNCERTAINTY, ScoreDimension.EVIDENCE}

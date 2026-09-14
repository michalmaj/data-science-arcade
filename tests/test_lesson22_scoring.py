from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l22_cohort_observatory.definition import LESSON_22
from data_science_arcade.lessons.l22_cohort_observatory.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    JAN_MONTH1_EVIDENCE_KEY,
    JAN_MONTH5_EVIDENCE_KEY,
    LessonTwentyTwoResult,
    MAY_LATEST_OBSERVED_MONTH_EVIDENCE_KEY,
    MAY_MONTH1_EVIDENCE_KEY,
    NOV_MONTH1_EVIDENCE_KEY,
    NOV_MONTH5_EVIDENCE_KEY,
    score_lesson_twenty_two,
)

GOOD_COHORT_CHOICES = {"may_retention_comparison": "same_month_comparison"}
MISMATCHED_COHORT_CHOICES = {"may_retention_comparison": "mismatched_month_comparison"}
GOOD_DECISION = {
    "business_question_horizon": "two_separate_questions_early_and_long_term",
    "correct_comparison_basis": "same_month_across_cohorts",
    "what_may_month1_supports": "real_evidence_of_leading_early_retention_so_far",
    "can_month5_be_evaluated": "no_data_doesnt_exist_yet",
    "blank_cell_meaning": "cohort_hasnt_reached_that_month_yet",
    "strongest_defensible_claim": "strong_observed_month1_long_term_not_yet_observed",
}


def _result(**overrides) -> LessonTwentyTwoResult:
    defaults = dict(
        initial_cohort_choices=dict(GOOD_COHORT_CHOICES),
        cohort_choices=dict(GOOD_COHORT_CHOICES),
        reveal_horizon_interpretation="same_age_leads_but_only_month1_observed",
        reveal_reversal_interpretation="month1_lead_was_real_but_didnt_guarantee_month5",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentyTwoResult(**defaults)


def _scores(result: LessonTwentyTwoResult) -> dict:
    return score_lesson_twenty_two(result, LESSON_22, hints_used=0).dimension_scores


def test_fully_correct_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_scoring_dimensions_are_exactly_five():
    scores = _scores(_result())
    assert set(scores) == {
        ScoreDimension.METHOD,
        ScoreDimension.REASONING,
        ScoreDimension.EVIDENCE,
        ScoreDimension.UNCERTAINTY,
        ScoreDimension.OVERCONFIDENCE,
    }


def test_method_reads_only_the_final_post_revision_choice():
    result = _result(initial_cohort_choices=MISMATCHED_COHORT_CHOICES, cohort_choices=GOOD_COHORT_CHOICES)
    assert _scores(result)[ScoreDimension.METHOD] == 95.0


def test_interpretations_never_affect_scoring():
    """Zero InterpretOption.evidence_key anywhere: a student who picks the
    wrong interpretation of a reveal still saw the exact same real numbers
    and can cite them later - only the decision fields and the cited
    evidence itself are ever scored."""
    a = _result(reveal_horizon_interpretation="too_immature_to_tell_anything", reveal_reversal_interpretation="early_number_wasnt_real")
    b = _result()
    assert _scores(a) == _scores(b)


def test_independence_case_a_high_method_reasoning_uncertainty_lower_calibration():
    result = _result(decision={**GOOD_DECISION, "strongest_defensible_claim": "may_clearly_improved_retention_overall"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0
    assert scores[ScoreDimension.OVERCONFIDENCE] < 92.0


def test_independence_case_b_high_reasoning_lower_method_despite_real_revision_opportunity():
    result = _result(initial_cohort_choices=MISMATCHED_COHORT_CHOICES, cohort_choices=MISMATCHED_COHORT_CHOICES)
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.METHOD] < 95.0


def test_independence_case_c_high_evidence_reasoning_lower_uncertainty():
    result = _result(decision={**GOOD_DECISION, "blank_cell_meaning": "zero_percent_everyone_churned"})
    scores = _scores(result)
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.UNCERTAINTY] < 92.0


def test_independence_case_d_high_uncertainty_lower_calibration():
    """A student can correctly understand that Month 5 isn't observed yet
    (UNCERTAINTY high) while still underclaiming what May's real Month 1
    lead actually supports (CALIBRATION low) - a genuinely separate
    failure mode."""
    result = _result(decision={**GOOD_DECISION, "strongest_defensible_claim": "cant_say_anything_about_may_yet"})
    scores = _scores(result)
    assert scores[ScoreDimension.UNCERTAINTY] == 92.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 35.0


def test_evidence_role_horizon_availability_is_its_own_required_role():
    without = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != MAY_LATEST_OBSERVED_MONTH_EVIDENCE_KEY))
    assert _scores(without)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_early_same_age_requires_both_may_and_jan_month1():
    without_jan_month1 = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != JAN_MONTH1_EVIDENCE_KEY))
    assert _scores(without_jan_month1)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_mismatched_age_contrast_requires_both_may_and_jan_month5():
    without_jan_month5 = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k != JAN_MONTH5_EVIDENCE_KEY))
    assert _scores(without_jan_month5)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_evidence_role_ranking_reversal_requires_all_four_not_partial():
    """Defending 'November really led at Month 1, then lost by Month 5'
    requires all four real numbers - citing only one of November's own two
    readings isn't enough to support the claim."""
    base = (MAY_MONTH1_EVIDENCE_KEY, JAN_MONTH1_EVIDENCE_KEY, MAY_LATEST_OBSERVED_MONTH_EVIDENCE_KEY, JAN_MONTH5_EVIDENCE_KEY)
    nov_month1_only = _result(critical_evidence_present=(*base, NOV_MONTH1_EVIDENCE_KEY))
    nov_month5_only = _result(critical_evidence_present=(*base, NOV_MONTH5_EVIDENCE_KEY))
    both = _result(critical_evidence_present=(*base, NOV_MONTH1_EVIDENCE_KEY, NOV_MONTH5_EVIDENCE_KEY))

    incomplete_score = _scores(nov_month1_only)[ScoreDimension.EVIDENCE]
    assert incomplete_score == _scores(nov_month5_only)[ScoreDimension.EVIDENCE]
    assert incomplete_score < _scores(both)[ScoreDimension.EVIDENCE]
    assert _scores(both)[ScoreDimension.EVIDENCE] == 95.0


def test_recalibration_observation_fires_only_when_initial_was_mismatched_and_final_is_correct():
    recalibrated = _result(initial_cohort_choices=MISMATCHED_COHORT_CHOICES, cohort_choices=GOOD_COHORT_CHOICES)
    patient = _result(initial_cohort_choices=GOOD_COHORT_CHOICES, cohort_choices=GOOD_COHORT_CHOICES)
    still_wrong = _result(initial_cohort_choices=MISMATCHED_COHORT_CHOICES, cohort_choices=MISMATCHED_COHORT_CHOICES)

    recalibration_key = "lesson.l22.feedback.comparison_basis_recalibrated"
    recalibrated_eval = score_lesson_twenty_two(recalibrated, LESSON_22, hints_used=0)
    patient_eval = score_lesson_twenty_two(patient, LESSON_22, hints_used=0)
    still_wrong_eval = score_lesson_twenty_two(still_wrong, LESSON_22, hints_used=0)

    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key not in [o.text_key for o in still_wrong_eval.observations]
    assert _scores(patient)[ScoreDimension.METHOD] == _scores(recalibrated)[ScoreDimension.METHOD]


def test_mastery_requires_fair_comparison_claim_strength_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_fair_comparison": "compare_n_to_others_own_week1",
            "mastery_claim_strength": "n_strongest_observed_week1_week8_unknown",
            "mastery_supporting_evidence": ("n_week1_82_percent",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_fair_comparison": "compare_n_to_others_own_week1",
            "mastery_claim_strength": "n_strongest_observed_week1_week8_unknown",
            "mastery_supporting_evidence": ("n_week1_82_percent", "h_reversal_week1_78_vs_week8_44"),
        },
    )
    evaluation_partial = score_lesson_twenty_two(partial, LESSON_22, hints_used=0)
    evaluation_complete = score_lesson_twenty_two(complete, LESSON_22, hints_used=0)

    mastery_key = "lesson.l22.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]

from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l15_segment_detective.definition import LESSON_15
from data_science_arcade.lessons.l15_segment_detective.scoring import LessonFifteenResult, score_lesson_fifteen

GOOD_DECISION = {
    "observed_overall_result": "rose_28_4_to_33_2",
    "within_device_result": "both_declined",
    "statements_relationship": "both_true_different_comparisons",
    "what_explains_the_reversal": "mix_shifted_toward_higher_converting_group",
    "standardized_interpretation": "no_within_device_gain_at_fixed_mix",
    "strongest_defensible_claim": "names_both_facts_respects_causal_boundary",
}
ALL_CENTRAL_ROLES = (
    "lesson.l15.evidence.overall_change",
    "lesson.l15.evidence.device_rates",
    "lesson.l15.evidence.device_share",
    "lesson.l15.evidence.standardized_comparison",
)


def _result(**overrides) -> LessonFifteenResult:
    defaults = dict(
        prior_headline="need_to_check_composition_first",
        first_dimension="device",
        region_inspected=True,
        revised_headline="overall_up_within_device_down",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=ALL_CENTRAL_ROLES,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonFifteenResult(**defaults)


def _scores(result: LessonFifteenResult) -> dict:
    return score_lesson_fifteen(result, LESSON_15, hints_used=0).dimension_scores


def test_good_decision_scores_top_reasoning_and_evidence():
    scores = _scores(_result())
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_reasoning_is_tiered_not_binary_across_the_four_checks():
    all_wrong = _result(
        decision={
            **GOOD_DECISION,
            "observed_overall_result": "fell_28_4_to_33_2",
            "within_device_result": "both_improved",
            "statements_relationship": "aggregate_misleading_within_device_real",
            "what_explains_the_reversal": "desktop_simply_declined",
            "standardized_interpretation": "proves_product_regressed",
        }
    )
    one_wrong = _result(decision={**GOOD_DECISION, "what_explains_the_reversal": "desktop_simply_declined"})
    good = _result()
    assert _scores(all_wrong)[ScoreDimension.REASONING] < _scores(one_wrong)[ScoreDimension.REASONING] < _scores(good)[ScoreDimension.REASONING]


def test_overall_and_within_device_reasoning_check_requires_both_fields():
    right_overall_wrong_within = _result(decision={**GOOD_DECISION, "within_device_result": "both_improved"})
    good = _result()
    assert _scores(right_overall_wrong_within)[ScoreDimension.REASONING] < _scores(good)[ScoreDimension.REASONING]


def test_evidence_is_role_based_missing_one_central_role_costs_real_credit():
    missing_one = _result(critical_evidence_present=ALL_CENTRAL_ROLES[:3])
    full = _result()
    assert _scores(missing_one)[ScoreDimension.EVIDENCE] < _scores(full)[ScoreDimension.EVIDENCE]


def test_evidence_never_requires_the_bonus_roles():
    # Region-null and weighted-reconstruction are real but non-required -
    # a student with all 4 central roles and none of the bonus ones still
    # gets full EVIDENCE credit.
    central_only = _result(critical_evidence_present=ALL_CENTRAL_ROLES)
    assert _scores(central_only)[ScoreDimension.EVIDENCE] == 95.0


def test_overconfidence_scores_the_final_claim_not_the_prior_headline():
    bad_claim = _result(decision={**GOOD_DECISION, "strongest_defensible_claim": "mobile_traffic_caused_deterioration"})
    assert _scores(bad_claim)[ScoreDimension.OVERCONFIDENCE] < _scores(_result())[ScoreDimension.OVERCONFIDENCE]


def test_recalibration_bonus_fires_only_for_a_real_premature_to_correct_path():
    app_result = _result(prior_headline="conversion_improved", revised_headline="overall_up_within_device_down")
    evaluation = score_lesson_fifteen(app_result, LESSON_15, hints_used=0)
    assert "lesson.l15.feedback.headline_recalibrated" in [o.text_key for o in evaluation.observations]


def test_recalibration_bonus_does_not_fire_if_the_final_claim_is_wrong():
    result = _result(
        prior_headline="conversion_improved",
        revised_headline="overall_up_within_device_down",
        decision={**GOOD_DECISION, "strongest_defensible_claim": "aggregate_number_is_wrong"},
    )
    evaluation = score_lesson_fifteen(result, LESSON_15, hints_used=0)
    assert "lesson.l15.feedback.headline_recalibrated" not in [o.text_key for o in evaluation.observations]


def test_recalibration_bonus_does_not_fire_for_a_student_who_started_correct():
    # Starting at the correct, neutral headline is not "premature" -
    # nothing to recalibrate away from.
    result = _result(prior_headline="need_to_check_composition_first", revised_headline="overall_up_within_device_down")
    evaluation = score_lesson_fifteen(result, LESSON_15, hints_used=0)
    assert "lesson.l15.feedback.headline_recalibrated" not in [o.text_key for o in evaluation.observations]


def test_a_student_who_starts_uncertain_and_stays_coherent_scores_full_marks():
    result = _result(prior_headline="need_to_check_composition_first", revised_headline="overall_up_within_device_down")
    scores = _scores(result)
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_revision_field_never_offers_the_stage_two_neutral_cold_prior_option():
    # P0 regression: the headline-revision field used to share its own
    # option set with the cold prior reveal, so "need more context" - a
    # defensible answer BEFORE investigation - stayed pickable as the
    # supposedly "corrected" answer even after the student had already
    # seen device rates/share, the region check, the weighted
    # reconstruction, and the common-mix comparison. The revision field's
    # own real options must never include that cold-prior key at all.
    from data_science_arcade.lessons.l15_segment_detective.scenario import HEADLINE_REVISION_FIELD

    revision_keys = {option.key for option in HEADLINE_REVISION_FIELD.options}
    assert "need_to_check_composition_first" not in revision_keys
    assert "overall_up_within_device_down" in revision_keys


def test_recalibration_bonus_requires_the_real_substantive_revision_not_a_repeated_cold_read():
    # A student who "revises" into one of the still-premature options
    # (never having actually updated) gets no recalibration credit,
    # regardless of what their prior was.
    result = _result(prior_headline="conversion_improved", revised_headline="revised_conversion_improved")
    evaluation = score_lesson_fifteen(result, LESSON_15, hints_used=0)
    assert "lesson.l15.feedback.headline_recalibrated" not in [o.text_key for o in evaluation.observations]


def test_mastery_requires_both_the_correct_judgment_and_the_real_distinguishing_fact():
    judgment_only = _result(
        mastery_engaged=True,
        mastery_result={"mastery_reversal_judgment": "no_reversal_real_improvement", "mastery_supporting_evidence": ("overall_improved",)},
    )
    both_right = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_reversal_judgment": "no_reversal_real_improvement",
            "mastery_supporting_evidence": ("both_carriers_improved",),
        },
    )
    evaluation_judgment_only = score_lesson_fifteen(judgment_only, LESSON_15, hints_used=0)
    evaluation_both = score_lesson_fifteen(both_right, LESSON_15, hints_used=0)

    mastery_key = "lesson.l15.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_judgment_only.observations]
    assert mastery_key in [o.text_key for o in evaluation_both.observations]


def test_method_and_communication_dimensions_are_not_scored():
    scores = _scores(_result())
    assert ScoreDimension.METHOD not in scores
    assert ScoreDimension.COMMUNICATION not in scores
    assert set(scores) == {ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE}

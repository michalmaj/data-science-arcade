from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l11_distribution_observatory.definition import LESSON_11
from data_science_arcade.lessons.l11_distribution_observatory.scoring import (
    CENTER_LOCATION_EVIDENCE_KEYS,
    CRITICAL_EVIDENCE_KEYS,
    SEGMENT_EXPLAINS_EVIDENCE_KEYS,
    SHAPE_MIXTURE_EVIDENCE_KEYS,
    UPPER_TAIL_EVIDENCE_KEYS,
    LessonElevenResult,
    _mastery_succeeded,
    score_lesson_eleven,
)

GOOD_PRIOR = {"finance_prior_pick": "mean", "product_prior_pick": "median", "ops_prior_pick": "p90"}
GOOD_DECISION = {
    "finance_summary_choice": "mean",
    "product_typical_order_claim": "median_with_limitation",
    "ops_capacity_summary": "p90",
    "shape_interpretation": "two_separate_populations",
    "communication_recommendation": "differentiated_summaries_per_audience",
    "evidence": CRITICAL_EVIDENCE_KEYS,
}


def _result(**overrides) -> LessonElevenResult:
    base = dict(
        business_asks_prior=GOOD_PRIOR,
        decision=GOOD_DECISION,
        segment_interpretation_seen="segments_explain_mixture",
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
    )
    base.update(overrides)
    return LessonElevenResult(**base)


def test_a_fully_correct_playthrough_scores_at_the_top_of_every_dimension():
    evaluation = score_lesson_eleven(_result(), LESSON_11, hints_used=0)
    for dimension in LESSON_11.scoring_dimensions:
        assert evaluation.dimension_scores[dimension] >= 92.0, dimension


def test_score_lesson_eleven_only_scores_the_lessons_own_declared_dimensions():
    evaluation = score_lesson_eleven(_result(), LESSON_11, hints_used=0)
    assert set(evaluation.dimension_scores) == set(LESSON_11.scoring_dimensions)


# --- METHOD: final Decision fields only, never the unscored prior pass ----


def test_method_scores_only_the_final_decision_never_the_prior_business_asks():
    wrong_prior_correct_final = _result(business_asks_prior={"finance_prior_pick": "median", "product_prior_pick": "mean", "ops_prior_pick": "mean"})
    evaluation = score_lesson_eleven(wrong_prior_correct_final, LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 94.0


def test_method_drops_for_each_wrong_final_pick():
    one_wrong = _result(decision=dict(GOOD_DECISION, finance_summary_choice="median"))
    evaluation = score_lesson_eleven(one_wrong, LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 60.0
    assert any(o.text_key == "lesson.l11.feedback.finance_summary_wrong" for o in evaluation.observations)


def test_product_typical_order_denying_the_mixture_is_scored_wrong():
    denies_mixture = _result(decision=dict(GOOD_DECISION, product_typical_order_claim="median_denies_mixture"))
    evaluation = score_lesson_eleven(denies_mixture, LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 94.0
    assert any(o.text_key == "lesson.l11.feedback.product_summary_wrong" for o in evaluation.observations)


def test_mean_as_typical_order_trap_is_scored_wrong():
    mean_as_typical = _result(decision=dict(GOOD_DECISION, product_typical_order_claim="mean_as_typical"))
    evaluation = score_lesson_eleven(mean_as_typical, LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 94.0


# --- REASONING vs COMMUNICATION: real, independent signals ----------------


def test_reasoning_and_communication_are_independent_not_redundant_signals():
    # Perfect REASONING coherence with a wrong communication_recommendation
    # (still self-consistent, just factually the wrong pick) must not drag
    # REASONING down - the wrongness itself is COMMUNICATION's own job, not
    # a coherence failure. Real, differentiated final picks keep the
    # coherence check vacuously satisfied.
    result = _result(decision=dict(GOOD_DECISION, communication_recommendation="one_global_number_for_everyone"))
    evaluation = score_lesson_eleven(result, LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] == 92.0
    assert evaluation.dimension_scores[ScoreDimension.COMMUNICATION] < 92.0
    assert any(o.text_key == "lesson.l11.feedback.communication_recommendation_wrong" for o in evaluation.observations)


def test_communication_fails_when_the_final_picks_are_not_actually_differentiated():
    undifferentiated = _result(
        decision=dict(
            GOOD_DECISION,
            finance_summary_choice="mean",
            ops_capacity_summary="mean",
            product_typical_order_claim="mean_as_typical",
        )
    )
    evaluation = score_lesson_eleven(undifferentiated, LESSON_11, hints_used=0)
    assert any(o.text_key == "lesson.l11.feedback.reporting_not_actually_differentiated" for o in evaluation.observations)


def test_shape_claim_incoherent_when_the_final_shape_pick_itself_is_wrong():
    result = _result(decision=dict(GOOD_DECISION, shape_interpretation="roughly_symmetric"))
    evaluation = score_lesson_eleven(result, LESSON_11, hints_used=0)
    assert any(o.text_key == "lesson.l11.feedback.shape_claim_incoherent" for o in evaluation.observations)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 92.0


def test_product_claim_self_contradicted_when_limitation_claimed_but_the_reveal_was_never_recognized():
    # A real, independent fact from shape_claim_coherent's own check: the
    # final shape_interpretation pick is itself correct, but the student's
    # own segment_reveal interpret choice never actually recognized the
    # segments as explaining the mixture - a genuine self-contradiction
    # with product's own correct "median, but only for the consumer half"
    # claim, not just a re-check of the same field (regression guard: this
    # observation was previously unreachable - see scoring.py's own
    # docstring on _product_shape_coherent).
    result = _result(segment_interpretation_seen="segments_dont_matter")
    evaluation = score_lesson_eleven(result, LESSON_11, hints_used=0)
    assert any(o.text_key == "lesson.l11.feedback.product_claim_self_contradicted" for o in evaluation.observations)


# --- EVIDENCE: role-based, never "any N of M" ------------------------------


def test_evidence_scores_the_number_of_distinct_roles_present_not_raw_item_count():
    all_four_roles = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS)
    evaluation = score_lesson_eleven(all_four_roles, LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 97.0


def test_evidence_drops_when_a_real_role_is_entirely_missing():
    missing_upper_tail = _result(
        critical_evidence_present=CENTER_LOCATION_EVIDENCE_KEYS + SHAPE_MIXTURE_EVIDENCE_KEYS + SEGMENT_EXPLAINS_EVIDENCE_KEYS
    )
    evaluation = score_lesson_eleven(missing_upper_tail, LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 80.0
    assert any(o.text_key == "lesson.l11.feedback.evidence_missing_a_real_role" for o in evaluation.observations)


def test_evidence_with_zero_roles_scores_at_the_bottom_band():
    evaluation = score_lesson_eleven(_result(critical_evidence_present=()), LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 12.0


def test_evidence_role_keys_are_all_distinct():
    assert len(set(CRITICAL_EVIDENCE_KEYS)) == len(CRITICAL_EVIDENCE_KEYS) == 4
    assert set(CRITICAL_EVIDENCE_KEYS) == set(
        CENTER_LOCATION_EVIDENCE_KEYS + UPPER_TAIL_EVIDENCE_KEYS + SHAPE_MIXTURE_EVIDENCE_KEYS + SEGMENT_EXPLAINS_EVIDENCE_KEYS
    )


# --- Trajectory: a wrong prior pick is never a permanent cap --------------


def test_trajectory_observation_only_fires_after_a_real_revision_and_a_real_recovery():
    never_revised = _result(business_asks_prior={"finance_prior_pick": "median", "product_prior_pick": "mean", "ops_prior_pick": "mean"}, business_asks_revised=False)
    evaluation = score_lesson_eleven(never_revised, LESSON_11, hints_used=0)
    assert not any("recovered_via_revision" in o.text_key for o in evaluation.observations)

    revised = _result(business_asks_prior={"finance_prior_pick": "median", "product_prior_pick": "mean", "ops_prior_pick": "mean"}, business_asks_revised=True)
    evaluation = score_lesson_eleven(revised, LESSON_11, hints_used=0)
    assert any(o.text_key == "lesson.l11.feedback.finance_recovered_via_revision" for o in evaluation.observations)
    assert any(o.text_key == "lesson.l11.feedback.product_recovered_via_revision" for o in evaluation.observations)
    assert any(o.text_key == "lesson.l11.feedback.ops_recovered_via_revision" for o in evaluation.observations)


def test_a_wrong_prior_pick_never_caps_the_final_method_score_once_corrected():
    result = _result(business_asks_prior={"finance_prior_pick": "p90", "product_prior_pick": "p90", "ops_prior_pick": "mean"}, business_asks_revised=True)
    evaluation = score_lesson_eleven(result, LESSON_11, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 94.0


# --- Mastery: a correct-sounding conclusion needs a real supporting fact --


def test_mastery_requires_both_the_correct_interpretation_and_a_real_distinguishing_fact():
    correct_and_grounded = _result(
        mastery_engaged=True,
        mastery_result={"mastery_interpretation": "no_practically_different", "mastery_supporting_evidence": ("different_spread_or_std",)},
    )
    assert _mastery_succeeded(correct_and_grounded) is True


def test_mastery_fails_when_the_only_cited_fact_is_the_shared_mean_alone():
    # Regression guard: "same mean" is true but insufficient on its own -
    # a known bug pattern this codebase has hit twice before (L03, L04),
    # where a correct-sounding conclusion was accepted without a real
    # distinguishing fact behind it.
    correct_but_ungrounded = _result(
        mastery_engaged=True,
        mastery_result={"mastery_interpretation": "no_practically_different", "mastery_supporting_evidence": ("same_mean",)},
    )
    assert _mastery_succeeded(correct_but_ungrounded) is False


def test_mastery_fails_when_the_interpretation_itself_is_wrong_even_with_a_real_fact_cited():
    wrong_interpretation = _result(
        mastery_engaged=True,
        mastery_result={"mastery_interpretation": "yes_same_process", "mastery_supporting_evidence": ("different_spread_or_std",)},
    )
    assert _mastery_succeeded(wrong_interpretation) is False


def test_mastery_success_observation_only_appears_when_mastery_was_engaged():
    grounded_but_not_engaged = _result(
        mastery_engaged=False,
        mastery_result={"mastery_interpretation": "no_practically_different", "mastery_supporting_evidence": ("different_spread_or_std",)},
    )
    evaluation = score_lesson_eleven(grounded_but_not_engaged, LESSON_11, hints_used=0)
    assert not any(o.text_key == "lesson.l11.feedback.mastery_transfer_succeeded" for o in evaluation.observations)

    grounded_and_engaged = _result(
        mastery_engaged=True,
        mastery_result={"mastery_interpretation": "no_practically_different", "mastery_supporting_evidence": ("different_spread_or_std",)},
    )
    evaluation = score_lesson_eleven(grounded_and_engaged, LESSON_11, hints_used=0)
    assert any(o.text_key == "lesson.l11.feedback.mastery_transfer_succeeded" for o in evaluation.observations)


def test_hints_used_adds_a_shared_generic_observation():
    evaluation = score_lesson_eleven(_result(), LESSON_11, hints_used=2)
    assert any(o.text_key == "lesson.feedback.hints_used" for o in evaluation.observations)


def test_completed_thoughtfully_requires_both_a_prior_pass_and_a_real_decision():
    assert _result().completed_thoughtfully() is True
    assert _result(business_asks_prior={}).completed_thoughtfully() is False
    assert _result(decision={}).completed_thoughtfully() is False

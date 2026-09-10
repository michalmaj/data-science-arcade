from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l12_groupby_kitchen.definition import LESSON_12
from data_science_arcade.lessons.l12_groupby_kitchen.scoring import (
    AOV_ROLLUP_EVIDENCE_KEYS,
    CRITICAL_EVIDENCE_KEYS,
    CUSTOMER_ROLLUP_EVIDENCE_KEYS,
    OUTPUT_GRAIN_EVIDENCE_KEYS,
    REPEAT_CUSTOMER_EVIDENCE_KEYS,
    LessonTwelveResult,
    _mastery_succeeded,
    score_lesson_twelve,
)

GOOD_METRIC_CHOICES = {
    "orders": "count_order_id",
    "revenue": "sum_revenue",
    "unique_customers": "nunique_customer_id",
    "aov": "mean_revenue",
}
GOOD_DECISION = {
    "raw_observation_unit": "order",
    "grouped_output_grain": "store",
    "safe_rollup_metrics": ("orders", "revenue"),
    "network_customer_method": "distinct_network_wide",
    "network_aov_method": "order_level_or_weighted",
    "evidence": CRITICAL_EVIDENCE_KEYS,
}


def _result(**overrides) -> LessonTwelveResult:
    base = dict(
        group_by="by_store",
        metric_choices=GOOD_METRIC_CHOICES,
        decision=GOOD_DECISION,
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
    )
    base.update(overrides)
    return LessonTwelveResult(**base)


def test_a_fully_correct_playthrough_scores_at_the_top_of_every_dimension():
    evaluation = score_lesson_twelve(_result(), LESSON_12, hints_used=0)
    for dimension in LESSON_12.scoring_dimensions:
        assert evaluation.dimension_scores[dimension] >= 93.0, dimension


def test_score_lesson_twelve_only_scores_the_lessons_own_declared_dimensions():
    evaluation = score_lesson_twelve(_result(), LESSON_12, hints_used=0)
    assert set(evaluation.dimension_scores) == set(LESSON_12.scoring_dimensions)
    assert ScoreDimension.REPRODUCIBILITY not in evaluation.dimension_scores


# --- METHOD: scores the pipeline's own FINAL state ------------------------


def test_method_drops_for_a_wrong_group_by():
    result = _result(group_by="by_customer")
    evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 96.0
    assert any(o.text_key == "lesson.l12.feedback.group_by_wrong" for o in evaluation.observations)


def test_method_drops_for_each_wrong_metric_slot():
    for slot_key, wrong_option in [
        ("orders", "sum_revenue_as_orders"),
        ("revenue", "mean_revenue_as_revenue"),
        ("unique_customers", "count_order_id_as_customers"),
        ("aov", "sum_revenue_as_aov"),
    ]:
        result = _result(metric_choices=dict(GOOD_METRIC_CHOICES, **{slot_key: wrong_option}))
        evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
        assert evaluation.dimension_scores[ScoreDimension.METHOD] < 96.0, slot_key
        assert any(o.text_key == f"lesson.l12.feedback.{slot_key}_metric_wrong" for o in evaluation.observations), slot_key


def test_method_drops_for_each_wrong_network_rollup_method():
    wrong_customer = _result(decision=dict(GOOD_DECISION, network_customer_method="sum_per_store"))
    evaluation = score_lesson_twelve(wrong_customer, LESSON_12, hints_used=0)
    assert any(o.text_key == "lesson.l12.feedback.network_customer_method_wrong" for o in evaluation.observations)

    wrong_aov = _result(decision=dict(GOOD_DECISION, network_aov_method="mean_of_store_aovs"))
    evaluation = score_lesson_twelve(wrong_aov, LESSON_12, hints_used=0)
    assert any(o.text_key == "lesson.l12.feedback.network_aov_method_wrong" for o in evaluation.observations)


def test_method_is_never_gated_by_a_cold_first_pass_the_result_only_carries_the_final_state():
    # There's no separate "prior" field for the store-summary pipeline -
    # a revision simply overwrites group_by/metric_choices, so a fully
    # correct final state always scores at the top regardless of
    # whatever the first attempt looked like (which isn't even part of
    # LessonTwelveResult).
    result = _result()
    evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 96.0


# --- REASONING: grain/estimand coherence -----------------------------------


def test_reasoning_grain_check_is_normative_not_tied_to_the_students_own_pipeline():
    # Guardrail 5: a wrong (customer-level) pipeline must not prevent a
    # real REASONING credit for correctly stating what the table SHOULD
    # have been.
    result = _result(group_by="by_customer", decision=dict(GOOD_DECISION, raw_observation_unit="order", grouped_output_grain="store"))
    evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] == 93.0


def test_reasoning_fails_when_the_grain_claim_itself_is_wrong():
    result = _result(decision=dict(GOOD_DECISION, grouped_output_grain="customer"))
    evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
    assert any(o.text_key == "lesson.l12.feedback.grain_not_understood" for o in evaluation.observations)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 93.0


def test_reasoning_catches_the_safe_rollup_customers_self_contradiction():
    result = _result(decision=dict(GOOD_DECISION, safe_rollup_metrics=("orders", "unique_customers")))
    evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
    assert any(o.text_key == "lesson.l12.feedback.safe_rollup_customers_incoherent" for o in evaluation.observations)


def test_reasoning_catches_the_safe_rollup_aov_self_contradiction():
    result = _result(decision=dict(GOOD_DECISION, safe_rollup_metrics=("revenue", "aov")))
    evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
    assert any(o.text_key == "lesson.l12.feedback.safe_rollup_aov_incoherent" for o in evaluation.observations)


def test_reasoning_vs_method_are_independent_signals():
    # A wrong pipeline (low METHOD) with a fully coherent, correct final
    # argument (high REASONING) - and the mirror case: a correct
    # pipeline (high METHOD) with an internally self-contradictory final
    # argument (low REASONING).
    low_method_high_reasoning = _result(group_by="by_customer")
    evaluation = score_lesson_twelve(low_method_high_reasoning, LESSON_12, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 96.0
    assert evaluation.dimension_scores[ScoreDimension.REASONING] == 93.0

    high_method_low_reasoning = _result(decision=dict(GOOD_DECISION, safe_rollup_metrics=("orders", "unique_customers")))
    evaluation = score_lesson_twelve(high_method_low_reasoning, LESSON_12, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 96.0
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 93.0


# --- EVIDENCE: role-based, never "any N of M" ------------------------------


def test_evidence_scores_the_number_of_distinct_roles_present_not_raw_item_count():
    evaluation = score_lesson_twelve(_result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS), LESSON_12, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 97.0


def test_evidence_drops_when_a_real_role_is_entirely_missing():
    missing_aov_rollup = _result(
        critical_evidence_present=OUTPUT_GRAIN_EVIDENCE_KEYS + REPEAT_CUSTOMER_EVIDENCE_KEYS + CUSTOMER_ROLLUP_EVIDENCE_KEYS
    )
    evaluation = score_lesson_twelve(missing_aov_rollup, LESSON_12, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 80.0
    assert any(o.text_key == "lesson.l12.feedback.evidence_missing_a_real_role" for o in evaluation.observations)


def test_evidence_with_zero_roles_scores_at_the_bottom_band():
    evaluation = score_lesson_twelve(_result(critical_evidence_present=()), LESSON_12, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 12.0


def test_evidence_role_keys_are_all_distinct():
    assert len(set(CRITICAL_EVIDENCE_KEYS)) == len(CRITICAL_EVIDENCE_KEYS) == 4
    assert set(CRITICAL_EVIDENCE_KEYS) == set(
        OUTPUT_GRAIN_EVIDENCE_KEYS + REPEAT_CUSTOMER_EVIDENCE_KEYS + CUSTOMER_ROLLUP_EVIDENCE_KEYS + AOV_ROLLUP_EVIDENCE_KEYS
    )


# --- Trajectory: only a change that happened AT the revision itself -------


def test_trajectory_observation_only_fires_after_a_real_revision_and_a_real_recovery():
    wrong_prior = {"network_customer_method": "sum_per_store", "network_aov_method": "mean_of_store_aovs"}
    never_revised = _result(rollup_prior=wrong_prior, rollup_revised_picks=None)
    evaluation = score_lesson_twelve(never_revised, LESSON_12, hints_used=0)
    assert not any("recovered_via_revision" in o.text_key for o in evaluation.observations)

    good_revised = {"network_customer_method": "distinct_network_wide", "network_aov_method": "order_level_or_weighted"}
    revised = _result(rollup_prior=wrong_prior, rollup_revised_picks=good_revised)
    evaluation = score_lesson_twelve(revised, LESSON_12, hints_used=0)
    assert any(o.text_key == "lesson.l12.feedback.customer_method_recovered_via_revision" for o in evaluation.observations)
    assert any(o.text_key == "lesson.l12.feedback.aov_method_recovered_via_revision" for o in evaluation.observations)


def test_trajectory_never_fires_when_the_revision_itself_stayed_wrong():
    wrong_prior = {"network_customer_method": "sum_per_store", "network_aov_method": "mean_of_store_aovs"}
    still_wrong = {"network_customer_method": "sum_per_store", "network_aov_method": "mean_of_store_aovs"}
    result = _result(rollup_prior=wrong_prior, rollup_revised_picks=still_wrong)
    evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
    assert not any("recovered_via_revision" in o.text_key for o in evaluation.observations)


def test_trajectory_is_never_inferred_from_final_decision_alone():
    # The core guardrail-4 fix: even though Final Decision ends up fully
    # correct, no revision was ever engaged (rollup_revised_picks is
    # None) - "recovered via revision" must not fire just because prior
    # differs from wherever Final Decision landed.
    wrong_prior = {"network_customer_method": "sum_per_store", "network_aov_method": "mean_of_store_aovs"}
    result = _result(rollup_prior=wrong_prior, rollup_revised_picks=None, decision=GOOD_DECISION)
    evaluation = score_lesson_twelve(result, LESSON_12, hints_used=0)
    assert not any("recovered_via_revision" in o.text_key for o in evaluation.observations)


# --- Mastery: two separate judgments, each needing its OWN genuinely
# relevant supporting fact - customer overlap justifies why unique
# purchasers can't be summed, channel-volume differences justify why the
# average value per conversion needs weighting. Accepting either fact as
# interchangeable support for either claim would be exactly the
# "correct claim + unrelated true fact" regression L03/L04/L11 all
# needed a guard for.

GOOD_MASTERY_RESULT = {
    "mastery_purchaser_sum": "cant_sum_overlap",
    "mastery_avg_value_method": "raw_or_weighted",
    "mastery_supporting_evidence": ("channel_volumes_differ", "customers_overlap_channels"),
}


def test_mastery_requires_both_correct_judgments_each_with_its_own_real_fact():
    result = _result(mastery_engaged=True, mastery_result=GOOD_MASTERY_RESULT)
    assert _mastery_succeeded(result) is True


def test_mastery_fails_when_the_only_cited_fact_is_that_the_averages_share_a_style():
    result = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_purchaser_sum": "cant_sum_overlap",
            "mastery_avg_value_method": "raw_or_weighted",
            "mastery_supporting_evidence": ("same_style_averages",),
        },
    )
    assert _mastery_succeeded(result) is False


def test_mastery_fails_when_either_judgment_itself_is_wrong_even_with_both_real_facts_cited():
    wrong_purchaser_sum = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_purchaser_sum": "sum_is_fine",
            "mastery_avg_value_method": "raw_or_weighted",
            "mastery_supporting_evidence": ("channel_volumes_differ", "customers_overlap_channels"),
        },
    )
    assert _mastery_succeeded(wrong_purchaser_sum) is False

    wrong_avg_value_method = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_purchaser_sum": "cant_sum_overlap",
            "mastery_avg_value_method": "mean_of_channel_averages",
            "mastery_supporting_evidence": ("channel_volumes_differ", "customers_overlap_channels"),
        },
    )
    assert _mastery_succeeded(wrong_avg_value_method) is False


def test_mastery_fails_when_the_two_real_facts_are_cited_but_not_paired_to_their_own_claim():
    # The exact bug this follow-up fixed: customer overlap doesn't justify
    # weighting the average, and channel-volume differences don't justify
    # why purchasers can't be summed - citing both facts is not enough if
    # the specific judgment each one is meant to support is missing.
    only_purchaser_sum_correct = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_purchaser_sum": "cant_sum_overlap",
            "mastery_avg_value_method": "mean_of_channel_averages",
            "mastery_supporting_evidence": ("channel_volumes_differ", "customers_overlap_channels"),
        },
    )
    assert _mastery_succeeded(only_purchaser_sum_correct) is False

    only_avg_value_evidenced = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_purchaser_sum": "cant_sum_overlap",
            "mastery_avg_value_method": "raw_or_weighted",
            "mastery_supporting_evidence": ("channel_volumes_differ",),
        },
    )
    assert _mastery_succeeded(only_avg_value_evidenced) is False


def test_mastery_success_observation_only_appears_when_mastery_was_engaged():
    grounded_but_not_engaged = _result(mastery_engaged=False, mastery_result=GOOD_MASTERY_RESULT)
    evaluation = score_lesson_twelve(grounded_but_not_engaged, LESSON_12, hints_used=0)
    assert not any(o.text_key == "lesson.l12.feedback.mastery_transfer_succeeded" for o in evaluation.observations)

    grounded_and_engaged = _result(mastery_engaged=True, mastery_result=GOOD_MASTERY_RESULT)
    evaluation = score_lesson_twelve(grounded_and_engaged, LESSON_12, hints_used=0)
    assert any(o.text_key == "lesson.l12.feedback.mastery_transfer_succeeded" for o in evaluation.observations)


def test_hints_used_adds_a_shared_generic_observation():
    evaluation = score_lesson_twelve(_result(), LESSON_12, hints_used=2)
    assert any(o.text_key == "lesson.feedback.hints_used" for o in evaluation.observations)


def test_completed_thoughtfully_requires_both_a_group_by_and_a_real_decision():
    assert _result().completed_thoughtfully() is True
    assert _result(group_by=None).completed_thoughtfully() is False
    assert _result(decision={}).completed_thoughtfully() is False

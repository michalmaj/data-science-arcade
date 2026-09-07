from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l09_outlier_patrol.definition import LESSON_09
from data_science_arcade.lessons.l09_outlier_patrol.scoring import (
    BULK_EVIDENCE_KEYS,
    CRITICAL_EVIDENCE_KEYS,
    ERROR_PROVENANCE_EVIDENCE_KEYS,
    INCIDENT_EVIDENCE_KEYS,
    LessonNineResult,
    SEGMENT_EVIDENCE_KEYS,
    _mastery_succeeded,
    score_lesson_nine,
)

GOOD_ROUND1_RESOLUTION = {"fulfillment_cost": "no_blanket_action"}
GOOD_ROUND2_RESOLUTION = {
    "fulfillment_cost": "correct_via_invoice",
    "order_type": "keep_as_is",
    "incident_reference": "keep_and_flag_as_documented_incident",
}
GOOD_DIAGNOSIS = {
    "decimal_row_diagnosis": "data_entry_error",
    "bulk_row_diagnosis": "rare_but_legitimate",
    "anomaly_row_diagnosis": "documented_anomaly",
}
GOOD_DECISION = {
    "confirmed_data_errors": "decimal_row_only",
    "bulk_order_population_basis": "order_type_metadata",
    "incident_treatment": "keep_and_flag",
    "segment_treatment": "segment_aware_thresholds",
    "typical_standard_order_cost_kpi": "typical_correct",
    "total_fulfillment_exposure_kpi": "total_correct",
    "prevention_action": "entry_time_sanity_check",
    "safe_claim": "both_numbers_scoped_honestly",
}


def _result(**overrides) -> LessonNineResult:
    base = dict(
        round1_resolution=GOOD_ROUND1_RESOLUTION,
        round2_resolution=GOOD_ROUND2_RESOLUTION,
        diagnosis=GOOD_DIAGNOSIS,
        decision=dict(GOOD_DECISION, evidence=("e1", "e2")),
        critical_evidence_present=(
            SEGMENT_EVIDENCE_KEYS[0],
            ERROR_PROVENANCE_EVIDENCE_KEYS[0],
            BULK_EVIDENCE_KEYS[0],
            INCIDENT_EVIDENCE_KEYS[0],
        ),
    )
    base.update(overrides)
    return LessonNineResult(**base)


def test_a_fully_correct_playthrough_scores_at_the_top_of_every_dimension():
    evaluation = score_lesson_nine(_result(), LESSON_09, hints_used=0)
    for dimension in LESSON_09.scoring_dimensions:
        assert evaluation.dimension_scores[dimension] >= 90.0, dimension


def test_data_quality_is_scored_from_the_final_treatment_not_the_diagnosis():
    # A wrong initial diagnosis followed by the correct final treatment
    # must score full DATA_QUALITY credit - final understanding, not the
    # first guess.
    result = _result(diagnosis={"decimal_row_diagnosis": "rare_but_legitimate", "bulk_row_diagnosis": "data_entry_error", "anomaly_row_diagnosis": "no_real_basis_to_override"})
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0
    assert any(o.text_key == "lesson.l09.feedback.diagnosis_recovered_via_treatment" for o in evaluation.observations)


def test_data_quality_drops_when_the_final_treatment_is_wrong():
    result = _result(round2_resolution={"fulfillment_cost": "keep_as_is", "order_type": "keep_as_is", "incident_reference": "keep_and_flag_as_documented_incident"})
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.DATA_QUALITY] < 100.0
    assert any(o.text_key == "lesson.l09.feedback.decimal_row_mistreated" for o in evaluation.observations)


def test_method_does_not_reward_the_blanket_drop_even_if_treatments_are_correct():
    result = _result(round1_resolution={"fulfillment_cost": "drop_outside_fence"})
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 94.0
    assert any(o.text_key == "lesson.l09.feedback.blanket_policy_applied" for o in evaluation.observations)


def test_reproducibility_gives_the_naive_blanket_drop_real_partial_credit():
    # A wrong-but-fully-deterministic blanket rule is still a real,
    # restatable rule - never a flat zero on REPRODUCIBILITY, even
    # though it scores low on METHOD.
    correct = score_lesson_nine(_result(), LESSON_09, hints_used=0)
    naive = score_lesson_nine(_result(round1_resolution={"fulfillment_cost": "drop_outside_fence"}), LESSON_09, hints_used=0)
    assert naive.dimension_scores[ScoreDimension.METHOD] < correct.dimension_scores[ScoreDimension.METHOD]
    assert naive.dimension_scores[ScoreDimension.REPRODUCIBILITY] > 15.0
    assert naive.dimension_scores[ScoreDimension.REPRODUCIBILITY] < correct.dimension_scores[ScoreDimension.REPRODUCIBILITY]


def test_reasoning_catches_bulk_exclusion_claimed_without_its_own_evidence():
    # Excluding the bulk order from the typical-cost population must
    # never be coherent just because the right option was clicked - the
    # bulk evidence itself has to actually be cited.
    result = _result(critical_evidence_present=(SEGMENT_EVIDENCE_KEYS[0], ERROR_PROVENANCE_EVIDENCE_KEYS[0], INCIDENT_EVIDENCE_KEYS[0]))
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.bulk_basis_not_grounded" for o in evaluation.observations)


def test_reasoning_catches_bulk_basis_claim_that_contradicts_execution():
    # Claiming the correct basis while actually dropping the bulk row in
    # Round 2 is incoherent - the claim has to match what was executed.
    result = _result(round2_resolution=dict(GOOD_ROUND2_RESOLUTION, order_type="drop_row"))
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.bulk_basis_not_grounded" for o in evaluation.observations)


def test_reasoning_typical_kpi_distinguishes_corrected_from_uncorrected_decimal():
    # The median is robust enough that (88, 47.0) is reachable with or
    # without the decimal correction - the kpi_result claim's own
    # coherence must depend on which one actually happened, not just the
    # displayed number. (confirmed_data_errors is set to "none_of_them"
    # in both variants here, matching the real uncorrected state, so the
    # only difference between the two is the typical_kpi claim itself.)
    dishonest_result = _result(
        round2_resolution=dict(GOOD_ROUND2_RESOLUTION, fulfillment_cost="keep_as_is"),
        decision=dict(GOOD_DECISION, confirmed_data_errors="none_of_them", typical_standard_order_cost_kpi="typical_correct", evidence=("e1", "e2")),
    )
    honest_result = _result(
        round2_resolution=dict(GOOD_ROUND2_RESOLUTION, fulfillment_cost="keep_as_is"),
        decision=dict(GOOD_DECISION, confirmed_data_errors="none_of_them", typical_standard_order_cost_kpi="typical_decimal_uncorrected", evidence=("e1", "e2")),
    )
    dishonest_evaluation = score_lesson_nine(dishonest_result, LESSON_09, hints_used=0)
    honest_evaluation = score_lesson_nine(honest_result, LESSON_09, hints_used=0)
    assert honest_evaluation.dimension_scores[ScoreDimension.REASONING] > dishonest_evaluation.dimension_scores[ScoreDimension.REASONING]


def test_reasoning_catches_total_kpi_that_wrongly_excludes_the_bulk_order():
    # The real pipeline here keeps the bulk order (the correct, executed
    # treatment) - claiming the total excludes it anyway is a real,
    # catchable incoherence: the same row can be outside one estimand
    # and required for another, and the claim has to track which.
    result = _result(
        decision=dict(GOOD_DECISION, total_fulfillment_exposure_kpi="total_bulk_wrongly_excluded", evidence=("e1", "e2")),
    )
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.total_kpi_contradicts_own_pipeline" for o in evaluation.observations)


def test_evidence_requires_the_segment_fact_specifically():
    result = _result(critical_evidence_present=(ERROR_PROVENANCE_EVIDENCE_KEYS[0], BULK_EVIDENCE_KEYS[0], INCIDENT_EVIDENCE_KEYS[0]))
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.evidence_missing_segment_fact" for o in evaluation.observations)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] < 95.0


def test_evidence_requires_at_least_one_row_fact_alongside_the_segment_fact():
    result = _result(critical_evidence_present=(SEGMENT_EVIDENCE_KEYS[0],))
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.evidence_missing_row_fact" for o in evaluation.observations)


def test_round1_recovered_via_revision_observation_fires():
    result = _result(
        round1_resolution=GOOD_ROUND1_RESOLUTION,
        initial_round1_resolution={"fulfillment_cost": "drop_outside_fence"},
        round1_revised=True,
    )
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.round1_recovered_via_revision" for o in evaluation.observations)


def test_mastery_requires_the_exact_correct_answer_on_both_fields():
    assert _mastery_succeeded(
        _result(mastery_must_not_remove=frozenset({"escalation_ticket"}), mastery_needs_correction=frozenset({"error_ticket"}))
    )
    assert not _mastery_succeeded(
        _result(mastery_must_not_remove=frozenset({"error_ticket"}), mastery_needs_correction=frozenset({"escalation_ticket"}))
    )


def test_critical_evidence_keys_cover_all_four_roles():
    assert set(CRITICAL_EVIDENCE_KEYS) == set(SEGMENT_EVIDENCE_KEYS) | set(ERROR_PROVENANCE_EVIDENCE_KEYS) | set(
        BULK_EVIDENCE_KEYS
    ) | set(INCIDENT_EVIDENCE_KEYS)

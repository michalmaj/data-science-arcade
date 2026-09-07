from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l09_outlier_patrol.definition import LESSON_09
from data_science_arcade.lessons.l09_outlier_patrol.scoring import (
    BULK_EVIDENCE_KEYS,
    CRITICAL_EVIDENCE_KEYS,
    ERROR_PROVENANCE_EVIDENCE_KEYS,
    INCIDENT_EVIDENCE_KEYS,
    LessonNineResult,
    SEGMENT_EVIDENCE_KEYS,
    _kpi_defensibility_coherent,
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
    "segment_treatment": "interpret_in_context_no_auto_remove",
    "typical_kpi_defensibility": "report_defensible",
    "total_kpi_defensibility": "report_defensible",
    "prevention_action": "entry_time_sanity_check",
    "safe_claim": "both_numbers_scoped_honestly",
}
ALL_FOUR_EVIDENCE_ROLES = (
    SEGMENT_EVIDENCE_KEYS[0],
    ERROR_PROVENANCE_EVIDENCE_KEYS[0],
    BULK_EVIDENCE_KEYS[0],
    INCIDENT_EVIDENCE_KEYS[0],
)


def _result(**overrides) -> LessonNineResult:
    base = dict(
        round1_resolution=GOOD_ROUND1_RESOLUTION,
        round2_resolution=GOOD_ROUND2_RESOLUTION,
        diagnosis=GOOD_DIAGNOSIS,
        decision=dict(GOOD_DECISION, evidence=("e1", "e2", "e3", "e4")),
        critical_evidence_present=ALL_FOUR_EVIDENCE_ROLES,
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


def test_method_requires_segment_evidence_for_the_segment_claim():
    # The segment-scope claim can't be coherent just because the right
    # option was clicked - the segment contrast evidence has to actually
    # be cited too, the same discipline applied to the bulk/error/
    # incident claims under REASONING.
    result = _result(critical_evidence_present=(ERROR_PROVENANCE_EVIDENCE_KEYS[0], BULK_EVIDENCE_KEYS[0], INCIDENT_EVIDENCE_KEYS[0]))
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 94.0
    assert any(o.text_key == "lesson.l09.feedback.segment_scope_wrong" for o in evaluation.observations)


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


def test_reasoning_catches_errors_claim_without_its_own_invoice_evidence():
    result = _result(critical_evidence_present=(SEGMENT_EVIDENCE_KEYS[0], BULK_EVIDENCE_KEYS[0], INCIDENT_EVIDENCE_KEYS[0]))
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.confirmed_errors_claim_incoherent" for o in evaluation.observations)


def test_reasoning_catches_incident_claim_without_its_own_evidence():
    result = _result(critical_evidence_present=(SEGMENT_EVIDENCE_KEYS[0], ERROR_PROVENANCE_EVIDENCE_KEYS[0], BULK_EVIDENCE_KEYS[0]))
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.incident_claim_doesnt_match_execution" for o in evaluation.observations)


def test_every_reachable_pipeline_state_has_an_honest_kpi_reporting_path():
    # The whole point of the redesign: a pipeline state that matches no
    # pre-authored dollar figure (the P0 this follow-up fixes) still has
    # a real, correct answer - "provisional" - since defensibility is a
    # closed-form boolean computed directly from the real resolutions,
    # never an enumerated lookup table. These are the exact two real
    # states the user reported as previously unreportable ($4,264 from
    # cap_at_fence + otherwise-correct Round 2, and $5,200 from a
    # correct Round 1/decimal fix with the incident row dropped).
    cap_at_fence_result = _result(round1_resolution={"fulfillment_cost": "cap_at_fence"})
    assert cap_at_fence_result.final_total_state() == (89, 4264.0)
    assert cap_at_fence_result.typical_kpi_defensible() is False
    assert cap_at_fence_result.total_kpi_defensible() is False

    dropped_incident_result = _result(round2_resolution=dict(GOOD_ROUND2_RESOLUTION, incident_reference="drop_row"))
    assert dropped_incident_result.final_total_state() == (88, 5200.0)
    assert dropped_incident_result.typical_kpi_defensible() is False
    assert dropped_incident_result.total_kpi_defensible() is False

    # Both states are still fully, honestly reportable as "provisional" -
    # never blocked by a missing enumerated option.
    for state_result in (cap_at_fence_result, dropped_incident_result):
        assert _kpi_defensibility_coherent("report_provisional", state_result.typical_kpi_defensible())
        assert _kpi_defensibility_coherent("report_provisional", state_result.total_kpi_defensible())


def test_reasoning_rewards_an_honest_provisional_claim_over_a_false_defensible_one():
    # Same real defect (decimal left uncorrected) in both variants, so
    # errors_coherent is identically False either way - the only real
    # difference is whether the KPI claim honestly reflects that the
    # result isn't defensible.
    dishonest_result = _result(
        round2_resolution=dict(GOOD_ROUND2_RESOLUTION, fulfillment_cost="keep_as_is"),
        decision=dict(GOOD_DECISION, confirmed_data_errors="none_of_them", typical_kpi_defensibility="report_defensible", evidence=("e1", "e2", "e3", "e4")),
    )
    honest_result = _result(
        round2_resolution=dict(GOOD_ROUND2_RESOLUTION, fulfillment_cost="keep_as_is"),
        decision=dict(GOOD_DECISION, confirmed_data_errors="none_of_them", typical_kpi_defensibility="report_provisional", evidence=("e1", "e2", "e3", "e4")),
    )
    dishonest_evaluation = score_lesson_nine(dishonest_result, LESSON_09, hints_used=0)
    honest_evaluation = score_lesson_nine(honest_result, LESSON_09, hints_used=0)
    assert honest_evaluation.dimension_scores[ScoreDimension.REASONING] > dishonest_evaluation.dimension_scores[ScoreDimension.REASONING]


def test_reasoning_catches_total_kpi_claimed_defensible_when_it_isnt():
    # Round 1's naive cap_at_fence pick is the one real defect here -
    # every per-row Round 2 pick is still correct, so errors/bulk/
    # incident all stay coherent and the total_kpi claim's own
    # incoherence is what actually surfaces.
    result = _result(
        round1_resolution={"fulfillment_cost": "cap_at_fence"},
        decision=dict(GOOD_DECISION, typical_kpi_defensibility="report_provisional", total_kpi_defensibility="report_defensible", evidence=("e1", "e2", "e3", "e4")),
    )
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.total_kpi_contradicts_own_pipeline" for o in evaluation.observations)


def test_reasoning_typical_kpi_is_defensible_independent_of_the_bulk_rows_own_treatment():
    # Dropping the bulk row breaks total exposure's own defensibility but
    # never typical cost's - the bulk order was never in that
    # population to begin with, regardless of its own Round 2 pick.
    result = _result(round2_resolution=dict(GOOD_ROUND2_RESOLUTION, order_type="drop_row"))
    assert result.typical_kpi_defensible() is True
    assert result.total_kpi_defensible() is False


def test_evidence_role_based_partial_bands():
    four_roles = score_lesson_nine(_result(), LESSON_09, hints_used=0)
    three_roles = score_lesson_nine(
        _result(critical_evidence_present=ALL_FOUR_EVIDENCE_ROLES[:3]), LESSON_09, hints_used=0
    )
    two_unrelated_roles = score_lesson_nine(
        _result(critical_evidence_present=(ERROR_PROVENANCE_EVIDENCE_KEYS[0], BULK_EVIDENCE_KEYS[0])), LESSON_09, hints_used=0
    )
    zero_roles = score_lesson_nine(_result(critical_evidence_present=()), LESSON_09, hints_used=0)

    scores = [
        four_roles.dimension_scores[ScoreDimension.EVIDENCE],
        three_roles.dimension_scores[ScoreDimension.EVIDENCE],
        two_unrelated_roles.dimension_scores[ScoreDimension.EVIDENCE],
        zero_roles.dimension_scores[ScoreDimension.EVIDENCE],
    ]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == max(scores)
    # Citing 2 unrelated facts must not reach the near-full band a
    # mechanical "any 2+" check would have granted.
    assert two_unrelated_roles.dimension_scores[ScoreDimension.EVIDENCE] < 90.0
    assert not any(o.text_key == "lesson.l09.feedback.evidence_missing_a_real_role" for o in four_roles.observations)
    assert any(o.text_key == "lesson.l09.feedback.evidence_missing_a_real_role" for o in two_unrelated_roles.observations)


def test_round1_recovered_via_revision_observation_fires():
    result = _result(
        round1_resolution=GOOD_ROUND1_RESOLUTION,
        initial_round1_resolution={"fulfillment_cost": "drop_outside_fence"},
        round1_revised=True,
    )
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.round1_recovered_via_revision" for o in evaluation.observations)


def test_round2_recovered_via_revision_observation_fires():
    result = _result(
        round2_resolution=GOOD_ROUND2_RESOLUTION,
        initial_round2_resolution={"fulfillment_cost": "keep_as_is", "order_type": "drop_row", "incident_reference": "drop_row"},
        round2_revised=True,
    )
    evaluation = score_lesson_nine(result, LESSON_09, hints_used=0)
    assert any(o.text_key == "lesson.l09.feedback.round2_recovered_via_revision" for o in evaluation.observations)


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

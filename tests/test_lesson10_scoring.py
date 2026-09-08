from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l10_validation_gate.definition import LESSON_10
from data_science_arcade.lessons.l10_validation_gate.scoring import (
    BASELINE_EVIDENCE_KEYS,
    CONCENTRATION_EVIDENCE_KEYS,
    CORRECTED_KPI_EVIDENCE_KEYS,
    CRITICAL_EVIDENCE_KEYS,
    FINAL_STATE_EVIDENCE_KEYS,
    GATE_RESULT_EVIDENCE_KEYS,
    LessonTenResult,
    NAIVE_KPI_EVIDENCE_KEYS,
    _mastery_succeeded,
    score_lesson_ten,
)
from data_science_arcade.lessons.l10_validation_gate.twist_data import CORRECT_BATCH_ACTION_KEY, CORRECT_ROUND1_KEY

GOOD_ROUND1_RESOLUTION = {"review_status": CORRECT_ROUND1_KEY}
GOOD_BATCH_ACTION_RESOLUTION = {"review_status": CORRECT_BATCH_ACTION_KEY}
GOOD_GATE_RESOLUTION = {
    "optional_field_severity": "warn_at_threshold",
    "optional_field_threshold": "flag_over_2pct",
    "invariant_tolerance": "small_tolerance_atol_1",
    "invariant_severity": "block",
}
GOOD_DECISION = {
    "baseline_gate_meaning": "six_conditions_only",
    "missing_coverage": "cross_field_invariant_check",
    "invariant_action": "block",
    "batch_scope_decision": "block_whole_batch_replay",
    "pass_meaning": "satisfies_written_checks_only",
    "published_total_defensibility": "report_defensible",
    "prevention_ownership": "cross_field_validation_required",
}
ALL_EVIDENCE_KEYS = (
    BASELINE_EVIDENCE_KEYS[0],
    NAIVE_KPI_EVIDENCE_KEYS[0],
    GATE_RESULT_EVIDENCE_KEYS[0],
    CONCENTRATION_EVIDENCE_KEYS[0],
    CORRECTED_KPI_EVIDENCE_KEYS[0],
)


def _result(**overrides) -> LessonTenResult:
    base = dict(
        round1_resolution=GOOD_ROUND1_RESOLUTION,
        batch_action_resolution=GOOD_BATCH_ACTION_RESOLUTION,
        gate_resolution=GOOD_GATE_RESOLUTION,
        decision=dict(GOOD_DECISION, evidence=ALL_EVIDENCE_KEYS),
        baseline_interpretation="six_conditions_held",
        critical_evidence_present=ALL_EVIDENCE_KEYS,
    )
    base.update(overrides)
    return LessonTenResult(**base)


def test_a_fully_correct_playthrough_scores_at_the_top_of_every_dimension():
    evaluation = score_lesson_ten(_result(), LESSON_10, hints_used=0)
    for dimension in LESSON_10.scoring_dimensions:
        assert evaluation.dimension_scores[dimension] >= 82.0, dimension


def test_data_quality_accepts_either_real_invariant_tolerance_configuration():
    exact_match = score_lesson_ten(
        _result(gate_resolution=dict(GOOD_GATE_RESOLUTION, invariant_tolerance="exact_match_atol_0")), LESSON_10, hints_used=0
    )
    small_tolerance = score_lesson_ten(_result(), LESSON_10, hints_used=0)
    assert exact_match.dimension_scores[ScoreDimension.DATA_QUALITY] == small_tolerance.dimension_scores[ScoreDimension.DATA_QUALITY]
    assert exact_match.dimension_scores[ScoreDimension.DATA_QUALITY] == 100.0


def test_data_quality_drops_when_the_gate_builder_never_authors_the_invariant_check():
    result = _result(gate_resolution=dict(GOOD_GATE_RESOLUTION, invariant_tolerance="no_invariant_check"))
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.DATA_QUALITY] < 100.0
    assert any(o.text_key == "lesson.l10.feedback.invariant_check_not_authored_well" for o in evaluation.observations)


def test_method_does_not_penalize_approving_for_publication():
    # Round 1's approve/hold pick is deliberately not part of core METHOD
    # (it's an OVERCONFIDENCE-only trajectory signal) - approving alone
    # must never drag METHOD down when the final gate and batch action
    # are both correct.
    approved = score_lesson_ten(_result(round1_resolution={"review_status": "approve_for_publication"}), LESSON_10, hints_used=0)
    held = score_lesson_ten(_result(), LESSON_10, hints_used=0)
    assert approved.dimension_scores[ScoreDimension.METHOD] == held.dimension_scores[ScoreDimension.METHOD] == 94.0


def test_method_penalizes_a_gate_that_never_authors_the_invariant_check():
    result = _result(gate_resolution=dict(GOOD_GATE_RESOLUTION, invariant_tolerance="no_invariant_check"))
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 94.0
    assert any(o.text_key == "lesson.l10.feedback.gate_not_correctly_designed" for o in evaluation.observations)


def test_method_penalizes_an_invariant_check_authored_at_the_wrong_severity():
    result = _result(gate_resolution=dict(GOOD_GATE_RESOLUTION, invariant_severity="warn_only"))
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 94.0
    assert any(o.text_key == "lesson.l10.feedback.gate_not_correctly_designed" for o in evaluation.observations)


def test_method_does_not_reward_quarantining_the_bad_rows():
    result = _result(batch_action_resolution={"review_status": "quarantine_and_report_rest"})
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 94.0
    assert any(o.text_key == "lesson.l10.feedback.batch_action_wrong" for o in evaluation.observations)


def test_reproducibility_gives_a_real_but_wrong_calibration_partial_credit():
    # A wrong-but-fully-specified check (zero tolerance, not "no check at
    # all") is still a real, restatable rule - never a flat zero on
    # REPRODUCIBILITY even though it scores low on DATA_QUALITY.
    correct = score_lesson_ten(_result(), LESSON_10, hints_used=0)
    miscalibrated = score_lesson_ten(
        _result(gate_resolution=dict(GOOD_GATE_RESOLUTION, optional_field_threshold="zero_tolerance")), LESSON_10, hints_used=0
    )
    assert miscalibrated.dimension_scores[ScoreDimension.REPRODUCIBILITY] == correct.dimension_scores[ScoreDimension.REPRODUCIBILITY]

    opted_out = score_lesson_ten(
        _result(gate_resolution=dict(GOOD_GATE_RESOLUTION, invariant_tolerance="no_invariant_check")), LESSON_10, hints_used=0
    )
    assert opted_out.dimension_scores[ScoreDimension.REPRODUCIBILITY] < correct.dimension_scores[ScoreDimension.REPRODUCIBILITY]
    assert opted_out.dimension_scores[ScoreDimension.REPRODUCIBILITY] > 0.0


def test_reasoning_catches_missing_coverage_claimed_without_authoring_the_check():
    result = _result(gate_resolution=dict(GOOD_GATE_RESOLUTION, invariant_tolerance="no_invariant_check"))
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert any(o.text_key == "lesson.l10.feedback.coverage_claim_incoherent" for o in evaluation.observations)


def test_reasoning_catches_batch_scope_claim_contradicting_the_real_pipeline():
    result = _result(batch_action_resolution={"review_status": "publish_anyway"})
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert any(o.text_key == "lesson.l10.feedback.batch_scope_claim_incoherent" for o in evaluation.observations)


def test_reasoning_catches_baseline_claim_contradicting_the_students_own_interpretation():
    result = _result(baseline_interpretation="data_fully_correct")
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert any(o.text_key == "lesson.l10.feedback.baseline_claim_incoherent" for o in evaluation.observations)


def test_every_reachable_pipeline_state_has_an_honest_defensibility_path():
    # Mirrors L09's own KPI-defensibility fix: every real reachable final
    # state must have SOME honest reporting option, never a dollar figure
    # with no matching claim.
    for batch_action_key in ("quarantine_and_report_rest", "publish_anyway", "investigate_only"):
        result = _result(
            batch_action_resolution={"review_status": batch_action_key},
            decision=dict(
                GOOD_DECISION,
                published_total_defensibility="report_provisional",
                evidence=(*ALL_EVIDENCE_KEYS[:-1], FINAL_STATE_EVIDENCE_KEYS[0]),
            ),
            critical_evidence_present=(*ALL_EVIDENCE_KEYS[:-1], FINAL_STATE_EVIDENCE_KEYS[0]),
        )
        assert result.published_total_defensible() is False
        evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
        assert not any(o.text_key == "lesson.l10.feedback.defensibility_claim_incoherent" for o in evaluation.observations)

    blocked = _result()
    assert blocked.published_total_defensible() is True


def test_evidence_requires_all_five_real_roles():
    partial = _result(critical_evidence_present=ALL_EVIDENCE_KEYS[:2])
    evaluation = score_lesson_ten(partial, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] < 62.0
    assert any(o.text_key == "lesson.l10.feedback.evidence_missing_a_real_role" for o in evaluation.observations)

    full = score_lesson_ten(_result(), LESSON_10, hints_used=0)
    assert full.dimension_scores[ScoreDimension.EVIDENCE] == 97.0


def test_evidence_role_five_accepts_either_corrected_total_or_final_state_unresolved():
    # A student on a real non-replay path never reaches a corrected
    # batch - FINAL_STATE_EVIDENCE_KEYS is the honest role there instead,
    # and must satisfy the same role CORRECTED_KPI_EVIDENCE_KEYS does on
    # the replay path.
    non_replay_evidence = (*ALL_EVIDENCE_KEYS[:-1], FINAL_STATE_EVIDENCE_KEYS[0])
    result = _result(
        batch_action_resolution={"review_status": "publish_anyway"},
        critical_evidence_present=non_replay_evidence,
        decision=dict(GOOD_DECISION, published_total_defensibility="report_provisional", evidence=non_replay_evidence),
    )
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 97.0


def test_overconfidence_rewards_recalibration_after_initially_approving():
    result = _result(initial_round1_resolution={"review_status": "approve_for_publication"}, round1_revised=True)
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.OVERCONFIDENCE] == 96.0
    assert any(o.text_key == "lesson.l10.feedback.recalibrated_after_overclaiming" for o in evaluation.observations)


def test_overconfidence_penalizes_never_recalibrating_the_pass_meaning_claim():
    result = _result(
        initial_round1_resolution={"review_status": "approve_for_publication"},
        decision=dict(GOOD_DECISION, pass_meaning="guaranteed_correct", evidence=ALL_EVIDENCE_KEYS),
    )
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.OVERCONFIDENCE] == 25.0
    assert any(o.text_key == "lesson.l10.feedback.overclaimed_and_never_recalibrated" for o in evaluation.observations)


def test_overconfidence_does_not_penalize_a_student_who_never_approved():
    result = _result(decision=dict(GOOD_DECISION, pass_meaning="guaranteed_correct", evidence=ALL_EVIDENCE_KEYS))
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.OVERCONFIDENCE] == 45.0


def test_gate_recovered_via_revision_observation_fires_on_a_real_recovery():
    result = _result(
        initial_gate_resolution=dict(GOOD_GATE_RESOLUTION, invariant_tolerance="no_invariant_check"),
        gate_revised=True,
    )
    evaluation = score_lesson_ten(result, LESSON_10, hints_used=0)
    assert any(o.text_key == "lesson.l10.feedback.gate_recovered_via_revision" for o in evaluation.observations)


def test_mastery_succeeded_requires_all_three_correct_picks():
    correct = {
        "mastery_missing_rule": "cross_field_invariant_check",
        "mastery_severity": "block",
        "mastery_pass_meaning": "satisfies_written_checks_only",
    }
    assert _mastery_succeeded(_result(mastery_result=correct)) is True
    assert _mastery_succeeded(_result(mastery_result=dict(correct, mastery_severity="warn_only"))) is False


def test_completed_thoughtfully_requires_both_decisions_and_a_real_final_decision():
    incomplete = LessonTenResult(round1_resolution={}, batch_action_resolution={}, gate_resolution={}, decision={})
    assert incomplete.completed_thoughtfully() is False
    assert _result().completed_thoughtfully() is True


def test_critical_evidence_keys_cover_all_six_roles():
    assert len(CRITICAL_EVIDENCE_KEYS) == 6
    assert set(CRITICAL_EVIDENCE_KEYS) == set(ALL_EVIDENCE_KEYS) | set(FINAL_STATE_EVIDENCE_KEYS)

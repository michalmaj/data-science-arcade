from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l13_join_junction.definition import LESSON_13
from data_science_arcade.lessons.l13_join_junction.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    FAN_OUT_EVIDENCE_KEYS,
    JOIN1_CONSEQUENCE_EVIDENCE_KEYS,
    MULTI_CHECK_VALIDATION_EVIDENCE_KEYS,
    ORDERS_KEY_EVIDENCE_KEYS,
    PROMOTIONS_KEY_EVIDENCE_KEYS,
    REPAIR_CONSEQUENCE_EVIDENCE_KEYS,
    LessonThirteenResult,
    _mastery_succeeded,
    score_lesson_thirteen,
)

GOOD_DECISION = {
    "orders_join_type": "left",
    "orders_join_row_count": "120",
    "promotions_key_cardinality": "many_to_one_from_promotions",
    "promotions_join_needs_preaggregation": "preaggregate_first",
    "promotions_row_count_after_repair": "120",
    "validation_sufficiency": "no_needs_multiple_checks",
    "evidence": CRITICAL_EVIDENCE_KEYS,
}


def _result(**overrides) -> LessonThirteenResult:
    base = dict(
        join1_first_choice="left",
        join1_choice="left",
        promotions_repair_first_choice="preaggregate_first",
        promotions_repair_choice="preaggregate_first",
        decision=GOOD_DECISION,
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
    )
    base.update(overrides)
    return LessonThirteenResult(**base)


# --- METHOD: scored purely off the FINAL EXECUTED pipeline state -----------


def test_a_fully_correct_final_executed_pipeline_scores_the_top_method_band():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 96.0


def test_method_ignores_the_final_decisions_own_claims_and_scores_the_real_pipeline():
    # The P0 regression this follow-up fixes: leaving the real pipeline on
    # inner while claiming "left" in the Join Brief must NOT earn METHOD
    # credit - Final Decision can never "rewrite history."
    result = _result(join1_first_choice="inner", join1_choice="inner", decision=dict(GOOD_DECISION, orders_join_type="left"))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 96.0
    assert any(o.text_key == "lesson.l13.feedback.join1_pipeline_wrong" for o in evaluation.observations)


def test_a_wrong_final_executed_repair_lowers_method_even_with_a_correct_decision_claim():
    result = _result(promotions_repair_first_choice="join_raw_directly", promotions_repair_choice="join_raw_directly")
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 96.0
    assert any(o.text_key == "lesson.l13.feedback.promotions_repair_pipeline_wrong" for o in evaluation.observations)


def test_a_student_who_leaves_a_wrong_pipeline_but_understands_the_fix_scores_method_low_reasoning_high():
    # The exact example the user gave: wrong pipeline left in place, but
    # the Final Decision correctly states what SHOULD have been done.
    result = _result(
        join1_first_choice="inner",
        join1_choice="inner",
        promotions_repair_first_choice="join_raw_directly",
        promotions_repair_choice="join_raw_directly",
        decision=GOOD_DECISION,  # correctly claims left/120 and preaggregate_first/120
    )
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 14.0  # both real facts wrong
    assert evaluation.dimension_scores[ScoreDimension.REASONING] == 95.0  # full normative understanding, still correct


# --- REASONING: normative understanding + coherence, independent of the
# real pipeline's own state -------------------------------------------


def test_reasoning_is_full_when_every_claim_is_correct_and_evidenced():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] == 95.0


def test_reasoning_drops_when_the_join1_claim_is_normatively_wrong():
    result = _result(decision=dict(GOOD_DECISION, orders_join_type="inner", orders_join_row_count="108"))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 95.0
    assert any(o.text_key == "lesson.l13.feedback.join1_not_understood" for o in evaluation.observations)


def test_reasoning_drops_when_the_promotions_key_cardinality_claim_is_wrong():
    result = _result(decision=dict(GOOD_DECISION, promotions_key_cardinality="one_to_one"))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 95.0
    assert any(o.text_key == "lesson.l13.feedback.promotions_key_cardinality_wrong" for o in evaluation.observations)


def test_reasoning_drops_when_the_repair_claim_is_normatively_wrong():
    result = _result(
        decision=dict(GOOD_DECISION, promotions_join_needs_preaggregation="join_raw_directly", promotions_row_count_after_repair="147")
    )
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 95.0
    assert any(o.text_key == "lesson.l13.feedback.repair_not_understood" for o in evaluation.observations)


def test_reasoning_drops_when_the_validation_claim_has_no_supporting_evidence():
    result = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k not in MULTI_CHECK_VALIDATION_EVIDENCE_KEYS))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 95.0
    assert any(o.text_key == "lesson.l13.feedback.validation_claim_unevidenced" for o in evaluation.observations)


# --- EVIDENCE - 6 real roles ------------------------------------------------


def test_evidence_is_full_with_all_six_real_roles():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 97.0


def test_evidence_drops_when_a_real_role_is_missing():
    result = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k not in REPAIR_CONSEQUENCE_EVIDENCE_KEYS))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] < 97.0
    assert any(o.text_key == "lesson.l13.feedback.evidence_missing_a_real_role" for o in evaluation.observations)


def test_no_data_quality_or_reproducibility_dimension_is_ever_scored():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=0)
    assert ScoreDimension.DATA_QUALITY not in evaluation.dimension_scores
    assert ScoreDimension.REPRODUCIBILITY not in evaluation.dimension_scores


# --- Trajectory: real wrong-then-corrected AT the revision step itself ----


def test_join1_trajectory_fires_only_for_a_real_recovery_at_the_revision_step():
    result = _result(join1_first_choice="inner", join1_choice="left")
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert any(o.text_key == "lesson.l13.feedback.orders_join_type_recovered_via_revision" for o in evaluation.observations)


def test_join1_trajectory_does_not_fire_when_the_first_pick_was_already_correct():
    result = _result(join1_first_choice="left", join1_choice="left")
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert not any("recovered_via_revision" in o.text_key for o in evaluation.observations)


def test_repair_trajectory_fires_only_for_a_real_recovery_at_the_revision_step():
    result = _result(promotions_repair_first_choice="dedupe_keep_first", promotions_repair_choice="preaggregate_first")
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert any(o.text_key == "lesson.l13.feedback.promotions_repair_recovered_via_revision" for o in evaluation.observations)


def test_repair_trajectory_does_not_fire_when_the_revision_was_declined_and_stayed_wrong():
    result = _result(promotions_repair_first_choice="join_raw_directly", promotions_repair_choice="join_raw_directly")
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert not any("recovered_via_revision" in o.text_key for o in evaluation.observations)


# --- Mastery: two real facts, each paired to its own claim -----------------


def test_mastery_requires_the_correct_grain_judgment_and_the_real_distinguishing_fact():
    result = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_row_growth_judgment": "expected_real_grain",
            "mastery_supporting_evidence": ("shipment_has_multiple_real_checkpoints",),
        },
    )
    assert _mastery_succeeded(result) is True


def test_mastery_fails_when_the_only_cited_fact_is_the_naive_heuristic_itself():
    result = _result(
        mastery_engaged=True,
        mastery_result={"mastery_row_growth_judgment": "expected_real_grain", "mastery_supporting_evidence": ("row_count_grew",)},
    )
    assert _mastery_succeeded(result) is False


def test_mastery_fails_when_the_grain_judgment_itself_is_wrong_even_with_the_real_fact_cited():
    result = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_row_growth_judgment": "needs_repair_like_promotions",
            "mastery_supporting_evidence": ("shipment_has_multiple_real_checkpoints",),
        },
    )
    assert _mastery_succeeded(result) is False


def test_mastery_success_observation_only_appears_when_mastery_was_engaged():
    grounded_but_not_engaged = _result(
        mastery_engaged=False,
        mastery_result={
            "mastery_row_growth_judgment": "expected_real_grain",
            "mastery_supporting_evidence": ("shipment_has_multiple_real_checkpoints",),
        },
    )
    evaluation = score_lesson_thirteen(grounded_but_not_engaged, LESSON_13, hints_used=0)
    assert not any(o.text_key == "lesson.l13.feedback.mastery_transfer_succeeded" for o in evaluation.observations)

    grounded_and_engaged = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_row_growth_judgment": "expected_real_grain",
            "mastery_supporting_evidence": ("shipment_has_multiple_real_checkpoints",),
        },
    )
    evaluation = score_lesson_thirteen(grounded_and_engaged, LESSON_13, hints_used=0)
    assert any(o.text_key == "lesson.l13.feedback.mastery_transfer_succeeded" for o in evaluation.observations)


def test_hints_used_adds_a_shared_generic_observation():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=2)
    assert any(o.text_key == "lesson.feedback.hints_used" for o in evaluation.observations)


def test_completed_thoughtfully_requires_a_join1_choice_a_repair_choice_and_a_real_decision():
    assert _result().completed_thoughtfully() is True
    assert _result(join1_choice=None).completed_thoughtfully() is False
    assert _result(promotions_repair_choice=None).completed_thoughtfully() is False
    assert _result(decision={}).completed_thoughtfully() is False


def test_all_six_evidence_role_constants_are_disjoint_and_cover_critical_keys():
    roles = (
        ORDERS_KEY_EVIDENCE_KEYS,
        JOIN1_CONSEQUENCE_EVIDENCE_KEYS,
        PROMOTIONS_KEY_EVIDENCE_KEYS,
        FAN_OUT_EVIDENCE_KEYS,
        REPAIR_CONSEQUENCE_EVIDENCE_KEYS,
        MULTI_CHECK_VALIDATION_EVIDENCE_KEYS,
    )
    seen: set[str] = set()
    for role in roles:
        for key in role:
            assert key not in seen
            seen.add(key)
    assert seen == set(CRITICAL_EVIDENCE_KEYS)

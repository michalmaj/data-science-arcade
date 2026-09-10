from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l13_join_junction.definition import LESSON_13
from data_science_arcade.lessons.l13_join_junction.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    FAN_OUT_EVIDENCE_KEYS,
    JOIN1_CONSEQUENCE_EVIDENCE_KEYS,
    MULTI_CHECK_VALIDATION_EVIDENCE_KEYS,
    ORDERS_KEY_EVIDENCE_KEYS,
    PROMOTIONS_KEY_EVIDENCE_KEYS,
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
        decision=GOOD_DECISION,
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
    )
    base.update(overrides)
    return LessonThirteenResult(**base)


# --- METHOD ------------------------------------------------------------


def test_a_fully_correct_final_decision_scores_the_top_method_band():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 96.0


def test_a_wrong_orders_join_type_lowers_method_and_reports_the_real_feedback_key():
    result = _result(decision=dict(GOOD_DECISION, orders_join_type="inner", orders_join_row_count="108"))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] < 96.0
    assert any(o.text_key == "lesson.l13.feedback.orders_join_type_wrong" for o in evaluation.observations)


def test_method_is_scored_off_the_final_decision_not_the_earlier_stage_pick():
    # join1_first_choice/join1_choice describe the interactive practice
    # pick - only decision["orders_join_type"] is the real scored fact,
    # matching L12's own rollup_prior/rollup_revised_picks vs. Final
    # Decision separation.
    result = _result(join1_first_choice="inner", join1_choice="inner", decision=GOOD_DECISION)
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.METHOD] == 96.0


# --- REASONING -----------------------------------------------------------


def test_reasoning_is_full_when_every_claim_is_internally_coherent():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] == 93.0


def test_reasoning_drops_when_the_row_count_contradicts_the_stated_join_type():
    # Claiming "left" while also claiming "108" (inner's own real number)
    # is self-contradictory, independent of whether "left" is itself the
    # objectively correct pick.
    result = _result(decision=dict(GOOD_DECISION, orders_join_row_count="108"))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 93.0
    assert any(o.text_key == "lesson.l13.feedback.join1_incoherent" for o in evaluation.observations)


def test_reasoning_drops_when_the_repair_row_count_contradicts_the_preaggregation_claim():
    # Claiming pre-aggregation is needed while still reporting 147 (the
    # raw-join number) is incoherent.
    result = _result(decision=dict(GOOD_DECISION, promotions_row_count_after_repair="147"))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 93.0
    assert any(o.text_key == "lesson.l13.feedback.repair_incoherent" for o in evaluation.observations)


def test_a_wrong_but_internally_consistent_repair_claim_stays_reasoning_coherent():
    # Claiming raw-join-is-fine (wrong on the merits, METHOD's own job)
    # while honestly reporting the real 147-row consequence of that
    # claim is internally coherent, even though substantively wrong.
    result = _result(
        decision=dict(GOOD_DECISION, promotions_join_needs_preaggregation="join_raw_directly", promotions_row_count_after_repair="147")
    )
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] == 93.0


def test_reasoning_drops_when_the_validation_claim_has_no_supporting_evidence():
    result = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k not in MULTI_CHECK_VALIDATION_EVIDENCE_KEYS))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.REASONING] < 93.0
    assert any(o.text_key == "lesson.l13.feedback.validation_claim_unevidenced" for o in evaluation.observations)


# --- EVIDENCE --------------------------------------------------------------


def test_evidence_is_full_with_all_five_real_roles():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] == 97.0


def test_evidence_drops_when_a_real_role_is_missing():
    result = _result(critical_evidence_present=tuple(k for k in CRITICAL_EVIDENCE_KEYS if k not in FAN_OUT_EVIDENCE_KEYS))
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert evaluation.dimension_scores[ScoreDimension.EVIDENCE] < 97.0
    assert any(o.text_key == "lesson.l13.feedback.evidence_missing_a_real_role" for o in evaluation.observations)


def test_no_data_quality_or_reproducibility_dimension_is_ever_scored():
    evaluation = score_lesson_thirteen(_result(), LESSON_13, hints_used=0)
    assert ScoreDimension.DATA_QUALITY not in evaluation.dimension_scores
    assert ScoreDimension.REPRODUCIBILITY not in evaluation.dimension_scores


# --- Trajectory: real wrong-then-corrected AT the revision step itself ----


def test_trajectory_fires_only_for_a_real_recovery_at_the_revision_step():
    result = _result(join1_first_choice="inner", join1_choice="left")
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert any(o.text_key == "lesson.l13.feedback.orders_join_type_recovered_via_revision" for o in evaluation.observations)


def test_trajectory_does_not_fire_when_the_first_pick_was_already_correct():
    result = _result(join1_first_choice="left", join1_choice="left")
    evaluation = score_lesson_thirteen(result, LESSON_13, hints_used=0)
    assert not any("recovered_via_revision" in o.text_key for o in evaluation.observations)


def test_trajectory_does_not_fire_when_the_revision_was_declined_and_stayed_wrong():
    result = _result(join1_first_choice="inner", join1_choice="inner")
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
    # "row count grew" is exactly the naive heuristic being inverted -
    # citing it as if it were the distinguishing fact must not count.
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


def test_completed_thoughtfully_requires_both_a_join1_choice_and_a_real_decision():
    assert _result().completed_thoughtfully() is True
    assert _result(join1_choice=None).completed_thoughtfully() is False
    assert _result(decision={}).completed_thoughtfully() is False


def test_all_five_evidence_role_constants_are_disjoint_and_cover_critical_keys():
    roles = (
        ORDERS_KEY_EVIDENCE_KEYS,
        JOIN1_CONSEQUENCE_EVIDENCE_KEYS,
        PROMOTIONS_KEY_EVIDENCE_KEYS,
        FAN_OUT_EVIDENCE_KEYS,
        MULTI_CHECK_VALIDATION_EVIDENCE_KEYS,
    )
    seen: set[str] = set()
    for role in roles:
        for key in role:
            assert key not in seen
            seen.add(key)
    assert seen == set(CRITICAL_EVIDENCE_KEYS)

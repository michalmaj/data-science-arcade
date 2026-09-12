from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l18_randomization_control_room.data import ID_PARITY, SIMPLE_RANDOM, STRATIFIED_RANDOM
from data_science_arcade.lessons.l18_randomization_control_room.definition import LESSON_18
from data_science_arcade.lessons.l18_randomization_control_room.scoring import CRITICAL_EVIDENCE_KEYS, LessonEighteenResult, score_lesson_eighteen

GOOD_DECISION_STRATIFIED = {
    "mechanism_classification": "valid_random_within_strata",
    "what_makes_assignment_randomized": "decided_by_random_mechanism_before_outcome",
    "what_equal_group_sizes_establish": "establishes_nothing_about_mechanism_alone",
    "how_to_interpret_small_realized_imbalance": "does_not_invalidate_valid_randomization",
    "why_stratify_on_platform": "guarantees_balance_on_a_known_covariate_randomness_within_strata",
    "what_must_stay_sealed_during_assignment": "determined_without_outcomes_or_post_treatment_info",
}
GOOD_DECISION_PARITY = {**GOOD_DECISION_STRATIFIED, "mechanism_classification": "deterministic_not_randomized"}
GOOD_DECISION_SIMPLE = {**GOOD_DECISION_STRATIFIED, "mechanism_classification": "valid_random_fixed_size"}


def _result(**overrides) -> LessonEighteenResult:
    defaults = dict(
        initial_design=STRATIFIED_RANDOM,
        final_design=STRATIFIED_RANDOM,
        decision=dict(GOOD_DECISION_STRATIFIED),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonEighteenResult(**defaults)


def _scores(result: LessonEighteenResult) -> dict:
    return score_lesson_eighteen(result, LESSON_18, hints_used=0).dimension_scores


def test_fully_correct_stratified_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0


def test_method_is_a_real_3_tier_gradient_over_the_final_design():
    parity = _scores(_result(final_design=ID_PARITY, decision=GOOD_DECISION_PARITY))
    simple = _scores(_result(final_design=SIMPLE_RANDOM, decision=GOOD_DECISION_SIMPLE))
    stratified = _scores(_result(final_design=STRATIFIED_RANDOM, decision=GOOD_DECISION_STRATIFIED))
    assert parity[ScoreDimension.METHOD] < simple[ScoreDimension.METHOD] < stratified[ScoreDimension.METHOD]


def test_method_reads_final_design_only_never_the_decision():
    # A perfect Final Brief sitting on top of a badly executed (parity)
    # final design still scores METHOD low - the Brief can never rewrite
    # what was actually executed.
    result = _result(final_design=ID_PARITY, decision=GOOD_DECISION_PARITY)
    assert _scores(result)[ScoreDimension.METHOD] == 20.0


def test_simple_random_gets_no_corrective_feedback_it_is_a_valid_design():
    result = _result(final_design=SIMPLE_RANDOM, decision=GOOD_DECISION_SIMPLE)
    evaluation = score_lesson_eighteen(result, LESSON_18, hints_used=0)
    method_observations = [o for o in evaluation.observations if o.dimension == ScoreDimension.METHOD]
    assert method_observations == []


def test_parity_gets_a_real_corrective_method_observation():
    result = _result(final_design=ID_PARITY, decision=GOOD_DECISION_PARITY)
    evaluation = score_lesson_eighteen(result, LESSON_18, hints_used=0)
    assert "lesson.l18.feedback.parity_is_not_randomized" in [o.text_key for o in evaluation.observations]


def test_independence_case_a_high_method_lower_reasoning():
    # Executes stratified (best), but the Final Brief claims exact
    # 600/600 alone proves it was random.
    result = _result(
        final_design=STRATIFIED_RANDOM,
        decision={**GOOD_DECISION_STRATIFIED, "what_equal_group_sizes_establish": "proves_the_assignment_was_random"},
    )
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] < 95.0


def test_independence_case_b_low_method_decent_reasoning():
    # Leaves parity as the final executed design, but correctly explains
    # in the Brief why parity isn't randomized.
    result = _result(final_design=ID_PARITY, decision=GOOD_DECISION_PARITY)
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 20.0
    assert scores[ScoreDimension.REASONING] == 95.0


def test_independence_case_c_high_method_and_high_reasoning():
    # Executes simple random (mild realized imbalance) and correctly says
    # that alone doesn't invalidate it.
    result = _result(final_design=SIMPLE_RANDOM, decision=GOOD_DECISION_SIMPLE)
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 78.0
    assert scores[ScoreDimension.REASONING] == 95.0


def test_mechanism_classification_field_1_is_scored_against_the_real_final_design_not_a_fixed_constant():
    stratified_with_wrong_classification = _result(
        final_design=STRATIFIED_RANDOM, decision={**GOOD_DECISION_STRATIFIED, "mechanism_classification": "deterministic_not_randomized"}
    )
    parity_with_right_classification = _result(final_design=ID_PARITY, decision=GOOD_DECISION_PARITY)
    assert _scores(stratified_with_wrong_classification)[ScoreDimension.REASONING] < 95.0
    assert _scores(parity_with_right_classification)[ScoreDimension.REASONING] == 95.0


def test_reasoning_is_tiered_across_the_six_checks():
    all_wrong = _result(
        final_design=STRATIFIED_RANDOM,
        decision={
            "mechanism_classification": "deterministic_not_randomized",
            "what_makes_assignment_randomized": "group_sizes_came_out_even",
            "what_equal_group_sizes_establish": "proves_the_assignment_was_random",
            "how_to_interpret_small_realized_imbalance": "proves_the_randomization_failed",
            "why_stratify_on_platform": "platform_decides_which_group_a_customer_joins",
            "what_must_stay_sealed_during_assignment": "just_the_outcome_column_needs_to_be_hidden_from_view",
        },
    )
    one_wrong = _result(final_design=STRATIFIED_RANDOM, decision={**GOOD_DECISION_STRATIFIED, "why_stratify_on_platform": "removes_the_need_for_randomization_entirely"})
    good = _result()
    assert _scores(all_wrong)[ScoreDimension.REASONING] < _scores(one_wrong)[ScoreDimension.REASONING] < _scores(good)[ScoreDimension.REASONING]


def test_evidence_is_role_based_missing_one_real_role_costs_real_credit():
    missing_one = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS[:2])
    full = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS)
    assert _scores(missing_one)[ScoreDimension.EVIDENCE] < _scores(full)[ScoreDimension.EVIDENCE]


def test_mastery_requires_the_correct_judgment_imbalance_treatment_and_matching_evidence():
    judgment_only = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_mechanism_judgment": "genuinely_randomly_assigned_per_provenance",
            "mastery_imbalance_meaning": "real_diagnostic_fact_not_invalidating",
            "mastery_supporting_evidence": ("distance_gap_is_a_real_but_modest_imbalance",),
        },
    )
    all_correct = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_mechanism_judgment": "genuinely_randomly_assigned_per_provenance",
            "mastery_imbalance_meaning": "real_diagnostic_fact_not_invalidating",
            "mastery_supporting_evidence": ("provenance_log_confirms_seeded_random_assignment",),
        },
    )
    evaluation_missing_evidence = score_lesson_eighteen(judgment_only, LESSON_18, hints_used=0)
    evaluation_all_correct = score_lesson_eighteen(all_correct, LESSON_18, hints_used=0)

    mastery_key = "lesson.l18.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_missing_evidence.observations]
    assert mastery_key in [o.text_key for o in evaluation_all_correct.observations]


def test_scoring_dimensions_are_exactly_method_reasoning_evidence():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE}

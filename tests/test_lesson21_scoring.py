from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l21_funnel_factory.definition import LESSON_21
from data_science_arcade.lessons.l21_funnel_factory.scoring import (
    BASIS_CHECK_PREVIOUS_EVIDENCE_KEY,
    BASIS_CHECK_TOP_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY,
    DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
    DEFINITION_CHECK_RAW_EVIDENCE_KEY,
    INSTRUMENTATION_GAP_EVIDENCE_KEY,
    LOCAL_ADD_TO_CART_EVIDENCE_KEY,
    LOCAL_ORDER_CONFIRMED_EVIDENCE_KEY,
    LessonTwentyOneResult,
    score_lesson_twenty_one,
)

GOOD_FUNNEL_CHOICES = {
    "mobile_dropout_complaint": "complete_cart_tracking",
    "payment_step_complaint": "percent_of_previous_step",
    "cart_abandonment_complaint": "unique_session_cart",
}
GOOD_DECISION = {
    "checkout_investigation_conclusion": "blame_cart_to_checkout_step",
    "why_legacy_undercounts": "tracking_pixel_missing_on_newer_app_builds",
    "percent_basis_question": "finds_the_step_thats_uniquely_bad_locally",
    "general_lesson": "justify_definition_independent_of_result",
}
ALL_EVIDENCE = (
    INSTRUMENTATION_GAP_EVIDENCE_KEY,
    DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
    DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY,
    DEFINITION_CHECK_RAW_EVIDENCE_KEY,
    BASIS_CHECK_TOP_EVIDENCE_KEY,
    BASIS_CHECK_PREVIOUS_EVIDENCE_KEY,
    LOCAL_ADD_TO_CART_EVIDENCE_KEY,
    LOCAL_ORDER_CONFIRMED_EVIDENCE_KEY,
)


def _result(**overrides) -> LessonTwentyOneResult:
    defaults = dict(
        initial_funnel_choices=dict(GOOD_FUNNEL_CHOICES),
        funnel_choices=dict(GOOD_FUNNEL_CHOICES),
        reveal_a_interpretation="same_step_can_look_broken_plausible_or_excellent_by_definition",
        reveal_b_interpretation="top_shows_cumulative_survival_previous_finds_the_local_loss",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonTwentyOneResult(**defaults)


def _scores(result: LessonTwentyOneResult) -> dict:
    return score_lesson_twenty_one(result, LESSON_21, hints_used=0).dimension_scores


def test_fully_correct_playthrough_scores_at_the_top():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0


def test_scoring_dimensions_are_exactly_method_reasoning_evidence():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE}


def test_method_reads_only_the_final_post_revision_choices():
    """A wrong initial pick, corrected by the final pass, still scores
    full METHOD - only funnel_choices (final) matters, never
    initial_funnel_choices."""
    result = _result(initial_funnel_choices={"mobile_dropout_complaint": "legacy_cart_tracking"}, funnel_choices=GOOD_FUNNEL_CHOICES)
    assert _scores(result)[ScoreDimension.METHOD] == 95.0


def test_independence_case_a_high_method_lower_reasoning():
    result = _result(decision={**GOOD_DECISION, "why_legacy_undercounts": "customers_really_added_to_cart_less", "percent_basis_question": "always_more_accurate"})
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] < 95.0


def test_independence_case_b_high_reasoning_lower_method_despite_real_revision_opportunity():
    """The corrected, now-honestly-reachable state: a student understood
    the Final Brief perfectly, but after a real revision opportunity
    still kept a motivated-reasoning pick wrong."""
    result = _result(
        initial_funnel_choices={**GOOD_FUNNEL_CHOICES, "mobile_dropout_complaint": "legacy_cart_tracking"},
        funnel_choices={**GOOD_FUNNEL_CHOICES, "mobile_dropout_complaint": "legacy_cart_tracking"},
        decision=GOOD_DECISION,
    )
    scores = _scores(result)
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.METHOD] < 95.0


def test_independence_case_c_high_evidence_lower_method_and_reasoning():
    result = _result(
        funnel_choices={"mobile_dropout_complaint": "legacy_cart_tracking"},
        decision={},
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
    )
    scores = _scores(result)
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.METHOD] < 95.0
    assert scores[ScoreDimension.REASONING] < 95.0


def test_independence_case_d_scores_identical_regardless_of_reveal_interpretation():
    a = _result(reveal_a_interpretation="any_definition_is_equally_valid", reveal_b_interpretation="percent_of_top_is_always_the_more_honest_number")
    b = _result(reveal_a_interpretation="same_step_can_look_broken_plausible_or_excellent_by_definition", reveal_b_interpretation="top_shows_cumulative_survival_previous_finds_the_local_loss")
    assert _scores(a) == _scores(b)


def test_evidence_role_definition_sensitivity_requires_at_least_two_of_three():
    one_only = _result(
        critical_evidence_present=(
            INSTRUMENTATION_GAP_EVIDENCE_KEY,
            DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
            BASIS_CHECK_TOP_EVIDENCE_KEY,
            BASIS_CHECK_PREVIOUS_EVIDENCE_KEY,
            LOCAL_ADD_TO_CART_EVIDENCE_KEY,
        )
    )
    two_of_three = _result(
        critical_evidence_present=(
            INSTRUMENTATION_GAP_EVIDENCE_KEY,
            DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
            DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY,
            BASIS_CHECK_TOP_EVIDENCE_KEY,
            BASIS_CHECK_PREVIOUS_EVIDENCE_KEY,
            LOCAL_ADD_TO_CART_EVIDENCE_KEY,
        )
    )
    assert _scores(one_only)[ScoreDimension.EVIDENCE] < _scores(two_of_three)[ScoreDimension.EVIDENCE]


def test_evidence_role_conversion_basis_contrast_requires_both_not_either():
    top_only = _result(
        critical_evidence_present=(
            INSTRUMENTATION_GAP_EVIDENCE_KEY,
            DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
            DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY,
            BASIS_CHECK_TOP_EVIDENCE_KEY,
            LOCAL_ADD_TO_CART_EVIDENCE_KEY,
        )
    )
    both = _result(
        critical_evidence_present=(
            INSTRUMENTATION_GAP_EVIDENCE_KEY,
            DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
            DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY,
            BASIS_CHECK_TOP_EVIDENCE_KEY,
            BASIS_CHECK_PREVIOUS_EVIDENCE_KEY,
            LOCAL_ADD_TO_CART_EVIDENCE_KEY,
        )
    )
    assert _scores(top_only)[ScoreDimension.EVIDENCE] < _scores(both)[ScoreDimension.EVIDENCE]


def test_evidence_role_local_bottleneck_requires_previous_basis_plus_both_neighbors():
    """Defending 'add_to_cart -> checkout_started is the WORST local
    transition in the defended funnel' requires showing both relevant
    neighboring transitions (add_to_cart's own local rate AND
    order_confirmed's own local rate) - citing checkout_started plus only
    one of them isn't enough to support a superlative claim."""
    base = (
        INSTRUMENTATION_GAP_EVIDENCE_KEY,
        DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
        DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY,
        BASIS_CHECK_TOP_EVIDENCE_KEY,
        BASIS_CHECK_PREVIOUS_EVIDENCE_KEY,
    )
    previous_and_add_to_cart_only = _result(critical_evidence_present=(*base, LOCAL_ADD_TO_CART_EVIDENCE_KEY))
    previous_and_order_confirmed_only = _result(critical_evidence_present=(*base, LOCAL_ORDER_CONFIRMED_EVIDENCE_KEY))
    previous_and_both_neighbors = _result(critical_evidence_present=(*base, LOCAL_ADD_TO_CART_EVIDENCE_KEY, LOCAL_ORDER_CONFIRMED_EVIDENCE_KEY))

    incomplete_score = _scores(previous_and_add_to_cart_only)[ScoreDimension.EVIDENCE]
    assert incomplete_score == _scores(previous_and_order_confirmed_only)[ScoreDimension.EVIDENCE]
    assert incomplete_score < _scores(previous_and_both_neighbors)[ScoreDimension.EVIDENCE]
    assert _scores(previous_and_both_neighbors)[ScoreDimension.EVIDENCE] == 95.0


def test_evidence_role_instrumentation_gap_is_its_own_required_role():
    without = _result(critical_evidence_present=tuple(k for k in ALL_EVIDENCE if k != INSTRUMENTATION_GAP_EVIDENCE_KEY))
    assert _scores(without)[ScoreDimension.EVIDENCE] < _scores(_result())[ScoreDimension.EVIDENCE]


def test_recalibration_observation_fires_only_when_initial_had_a_miss_and_final_is_fully_correct():
    recalibrated = _result(
        initial_funnel_choices={**GOOD_FUNNEL_CHOICES, "mobile_dropout_complaint": "legacy_cart_tracking"},
        funnel_choices=GOOD_FUNNEL_CHOICES,
    )
    patient = _result(initial_funnel_choices=GOOD_FUNNEL_CHOICES, funnel_choices=GOOD_FUNNEL_CHOICES)
    still_wrong = _result(
        initial_funnel_choices={**GOOD_FUNNEL_CHOICES, "mobile_dropout_complaint": "legacy_cart_tracking"},
        funnel_choices={**GOOD_FUNNEL_CHOICES, "mobile_dropout_complaint": "legacy_cart_tracking"},
    )

    recalibration_key = "lesson.l21.feedback.funnel_choices_recalibrated"
    recalibrated_eval = score_lesson_twenty_one(recalibrated, LESSON_21, hints_used=0)
    patient_eval = score_lesson_twenty_one(patient, LESSON_21, hints_used=0)
    still_wrong_eval = score_lesson_twenty_one(still_wrong, LESSON_21, hints_used=0)

    assert recalibration_key in [o.text_key for o in recalibrated_eval.observations]
    assert recalibration_key not in [o.text_key for o in patient_eval.observations]
    assert recalibration_key not in [o.text_key for o in still_wrong_eval.observations]
    # And patience is never scored lower than recalibration.
    assert _scores(patient)[ScoreDimension.METHOD] == _scores(recalibrated)[ScoreDimension.METHOD]


def test_mastery_requires_the_correct_judgment_why_and_both_evidence_facts():
    partial = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_real_bottleneck": "profile_completed",
            "mastery_why_missed": "the_flawed_signup_event_made_a_healthy_step_look_broken_hiding_the_real_one",
            "mastery_supporting_evidence": ("flawed_signup_rate_35_vs_correct_81_percent",),
        },
    )
    complete = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_real_bottleneck": "profile_completed",
            "mastery_why_missed": "the_flawed_signup_event_made_a_healthy_step_look_broken_hiding_the_real_one",
            "mastery_supporting_evidence": ("flawed_signup_rate_35_vs_correct_81_percent", "profile_completion_real_rate_42_percent"),
        },
    )
    evaluation_partial = score_lesson_twenty_one(partial, LESSON_21, hints_used=0)
    evaluation_complete = score_lesson_twenty_one(complete, LESSON_21, hints_used=0)

    mastery_key = "lesson.l21.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_partial.observations]
    assert mastery_key in [o.text_key for o in evaluation_complete.observations]

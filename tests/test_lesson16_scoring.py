from data_science_arcade.lessons.framework.definition import ScoreDimension
from data_science_arcade.lessons.l16_metric_forge.definition import LESSON_16
from data_science_arcade.lessons.l16_metric_forge.scoring import CRITICAL_EVIDENCE_KEYS, LessonSixteenResult, score_lesson_sixteen

GOOD_DECISION = {
    "business_outcome": "durable_not_a_single_number",
    "denominator_choice_rationale": "cant_shrink_by_leaving_open",
    "maturity_window_reasoning": "immature_hasnt_had_its_window",
    "numerator_loophole": "closing_without_finishing",
    "denominator_loophole": "closed_only_denominator_hides_backlog",
    "guardrail_breach_action": "gate_on_guardrails",
}


def _result(**overrides) -> LessonSixteenResult:
    defaults = dict(
        primary_definition="durable",
        guardrails=("reopen_rate", "aged_backlog_rate"),
        prior_success_verdict="not_yet_needs_guardrails",
        decision=dict(GOOD_DECISION),
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        mastery_engaged=False,
        mastery_result={},
    )
    defaults.update(overrides)
    return LessonSixteenResult(**defaults)


def _scores(result: LessonSixteenResult) -> dict:
    return score_lesson_sixteen(result, LESSON_16, hints_used=0).dimension_scores


def test_fully_robust_contract_and_correct_brief_scores_top_marks():
    scores = _scores(_result())
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] == 95.0
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.OVERCONFIDENCE] == 92.0


def test_method_is_tiered_by_the_final_executed_contract_only():
    durable_both_guardrails = _result(primary_definition="durable", guardrails=("reopen_rate", "aged_backlog_rate"))
    eligible_one_guardrail = _result(primary_definition="eligible_population", guardrails=("reopen_rate",))
    closed_only_no_guardrails = _result(primary_definition="closed_only", guardrails=())
    a = _scores(durable_both_guardrails)[ScoreDimension.METHOD]
    b = _scores(eligible_one_guardrail)[ScoreDimension.METHOD]
    c = _scores(closed_only_no_guardrails)[ScoreDimension.METHOD]
    assert a > b > c


def test_avg_time_to_close_guardrail_earns_no_method_credit():
    with_real_guardrails = _result(guardrails=("reopen_rate", "aged_backlog_rate"))
    with_decoy_guardrail = _result(guardrails=("avg_time_to_close",))
    assert _scores(with_real_guardrails)[ScoreDimension.METHOD] > _scores(with_decoy_guardrail)[ScoreDimension.METHOD]


def test_high_method_low_reasoning_independence():
    # A student who executes the fully robust contract but can't
    # correctly explain why it works.
    result = _result(
        primary_definition="durable",
        guardrails=("reopen_rate", "aged_backlog_rate"),
        decision={
            **GOOD_DECISION,
            "numerator_loophole": "definition_a_denominator_is_broken",
            "denominator_loophole": "definition_a_is_just_as_vulnerable",
        },
    )
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 95.0
    assert scores[ScoreDimension.REASONING] < 80.0


def test_low_method_decent_reasoning_independence():
    # A student who leaves a real gap in their own executed contract but
    # correctly identifies both loopholes and their guardrails in the brief.
    result = _result(primary_definition="closed_only", guardrails=())
    scores = _scores(result)
    assert scores[ScoreDimension.METHOD] == 15.0
    assert scores[ScoreDimension.REASONING] == 95.0


def test_high_evidence_low_reasoning_independence():
    # Real stress-test facts cited, but the wrong conclusion drawn from them.
    result = _result(
        critical_evidence_present=CRITICAL_EVIDENCE_KEYS,
        decision={**GOOD_DECISION, "numerator_loophole": "we_need_a_csat_guardrail_instead"},
    )
    scores = _scores(result)
    assert scores[ScoreDimension.EVIDENCE] == 95.0
    assert scores[ScoreDimension.REASONING] < 95.0


def test_reasoning_is_tiered_across_the_five_checks():
    all_wrong = _result(
        decision={
            "business_outcome": "primary_metric_alone",
            "denominator_choice_rationale": "its_simpler_to_compute",
            "maturity_window_reasoning": "makes_the_number_look_better",
            "numerator_loophole": "definition_a_denominator_is_broken",
            "denominator_loophole": "definition_a_is_just_as_vulnerable",
            "guardrail_breach_action": "ship_anyway",
        }
    )
    one_wrong = _result(decision={**GOOD_DECISION, "numerator_loophole": "definition_a_denominator_is_broken"})
    good = _result()
    assert _scores(all_wrong)[ScoreDimension.REASONING] < _scores(one_wrong)[ScoreDimension.REASONING] < _scores(good)[ScoreDimension.REASONING]


def test_evidence_is_role_based_missing_one_real_role_costs_real_credit():
    missing_one = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS[:4])
    full = _result(critical_evidence_present=CRITICAL_EVIDENCE_KEYS)
    assert _scores(missing_one)[ScoreDimension.EVIDENCE] < _scores(full)[ScoreDimension.EVIDENCE]


def test_overconfidence_scores_the_final_guardrail_breach_policy():
    bad_policy = _result(decision={**GOOD_DECISION, "guardrail_breach_action": "ship_anyway"})
    assert _scores(bad_policy)[ScoreDimension.OVERCONFIDENCE] < _scores(_result())[ScoreDimension.OVERCONFIDENCE]


def test_recalibration_bonus_fires_only_for_a_real_premature_to_correct_path():
    result = _result(prior_success_verdict="ship_it_success", decision={**GOOD_DECISION, "guardrail_breach_action": "gate_on_guardrails"})
    evaluation = score_lesson_sixteen(result, LESSON_16, hints_used=0)
    assert "lesson.l16.feedback.verdict_recalibrated" in [o.text_key for o in evaluation.observations]


def test_recalibration_bonus_does_not_fire_if_the_final_policy_is_wrong():
    result = _result(prior_success_verdict="ship_it_success", decision={**GOOD_DECISION, "guardrail_breach_action": "ship_anyway"})
    evaluation = score_lesson_sixteen(result, LESSON_16, hints_used=0)
    assert "lesson.l16.feedback.verdict_recalibrated" not in [o.text_key for o in evaluation.observations]


def test_recalibration_bonus_does_not_fire_for_a_student_who_started_correct():
    result = _result(prior_success_verdict="not_yet_needs_guardrails")
    evaluation = score_lesson_sixteen(result, LESSON_16, hints_used=0)
    assert "lesson.l16.feedback.verdict_recalibrated" not in [o.text_key for o in evaluation.observations]


def test_mastery_requires_both_the_correct_judgment_and_the_real_distinguishing_fact():
    judgment_only = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_metric_system_judgment": "productivity_needs_completeness_guardrail",
            "mastery_supporting_evidence": ("narrow_optimization_hits_forty",),
        },
    )
    both_right = _result(
        mastery_engaged=True,
        mastery_result={
            "mastery_metric_system_judgment": "productivity_needs_completeness_guardrail",
            "mastery_supporting_evidence": ("completeness_collapsed",),
        },
    )
    evaluation_judgment_only = score_lesson_sixteen(judgment_only, LESSON_16, hints_used=0)
    evaluation_both = score_lesson_sixteen(both_right, LESSON_16, hints_used=0)

    mastery_key = "lesson.l16.feedback.mastery_transfer_succeeded"
    assert mastery_key not in [o.text_key for o in evaluation_judgment_only.observations]
    assert mastery_key in [o.text_key for o in evaluation_both.observations]


def test_scoring_dimensions_are_exactly_method_reasoning_evidence_overconfidence():
    scores = _scores(_result())
    assert set(scores) == {ScoreDimension.METHOD, ScoreDimension.REASONING, ScoreDimension.EVIDENCE, ScoreDimension.OVERCONFIDENCE}

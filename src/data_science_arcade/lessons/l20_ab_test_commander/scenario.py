from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l20_ab_test_commander import data as d
from data_science_arcade.lessons.l20_ab_test_commander.definition import LESSON_20
from data_science_arcade.lessons.l20_ab_test_commander.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    DECISION_PROTOCOL_EVIDENCE_KEY,
    REFUND_GUARDRAIL_CLEAN_EVIDENCE_KEY,
    SUPPORT_GUARDRAIL_BREACH_EVIDENCE_KEY,
    WEEK3_PRIMARY_READING_EVIDENCE_KEY,
    WEEK7_PRIMARY_PASS_EVIDENCE_KEY,
    LessonTwentyResult,
    score_lesson_twenty,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.experiment_monitor_scene import ExperimentCheckpoint, ExperimentMetricRow, ExperimentMonitorScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l20_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l20_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_briefing.line3"),
    )
)
INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_investigation.line3"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l20_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l20_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_debrief.line3"),
    )
)
MASTERY_DIALOGUE_KEYS = (
    "dialogue.l20_mastery.line1",
    "dialogue.l20_mastery.line2",
    "dialogue.l20_mastery.line3",
    "dialogue.l20_mastery.line4",
)

# --- Experiment monitoring - week 1 -> week 3 -> week 7, linear, every
# student sees every checkpoint regardless of what they recommend. -------

RECOMMENDATION_OPTIONS: tuple[BriefOption, ...] = (
    BriefOption("ship_now", "lesson.l20.monitor.recommendation.option.ship_now"),
    BriefOption("hold_keep_running", "lesson.l20.monitor.recommendation.option.hold_keep_running"),
    BriefOption("not_sure_yet", "lesson.l20.monitor.recommendation.option.not_sure_yet"),
)


def _primary_status_key(cleared: bool) -> str:
    return "lesson.l20.monitor.status.primary_passes" if cleared else "lesson.l20.monitor.status.primary_not_yet"


def _guardrail_status_key(breached: bool) -> str:
    return "lesson.l20.monitor.status.guardrail_breach" if breached else "lesson.l20.monitor.status.guardrail_clean"


def _build_checkpoint(dataset, week: int) -> ExperimentCheckpoint:
    is_final = week == d.PLANNED_END_WEEK
    rows = []
    for metric_key, label_key in (
        (d.PRIMARY, "lesson.l20.monitor.row.primary"),
        (d.SUPPORT_GUARDRAIL, "lesson.l20.monitor.row.support_guardrail"),
        (d.REFUND_GUARDRAIL, "lesson.l20.monitor.row.refund_guardrail"),
    ):
        control_rate = d.rate_at_checkpoint(dataset, week, metric_key, "control")
        treatment_rate = d.rate_at_checkpoint(dataset, week, metric_key, "treatment")
        diff, ci_lower, ci_upper = d.diff_and_ci_at_checkpoint(dataset, week, metric_key)
        is_guardrail = metric_key != d.PRIMARY
        threshold_cleared = d.guardrail_breached(ci_lower) if is_guardrail else d.primary_passes(ci_lower)
        warn = is_guardrail and threshold_cleared
        status_key = _guardrail_status_key(threshold_cleared) if is_guardrail else _primary_status_key(threshold_cleared)
        evidence_key = None
        if is_final and metric_key == d.SUPPORT_GUARDRAIL:
            evidence_key = SUPPORT_GUARDRAIL_BREACH_EVIDENCE_KEY
        elif is_final and metric_key == d.REFUND_GUARDRAIL:
            evidence_key = REFUND_GUARDRAIL_CLEAN_EVIDENCE_KEY
        rows.append(
            ExperimentMetricRow(
                label_key=label_key,
                control_rate=control_rate,
                treatment_rate=treatment_rate,
                diff=diff,
                ci_lower=ci_lower,
                ci_upper=ci_upper,
                threshold_cleared=threshold_cleared,
                warn=warn,
                status_label_key=status_key,
                evidence_key=evidence_key,
            )
        )

    return ExperimentCheckpoint(
        week=week,
        is_final=is_final,
        rows=tuple(rows),
        mirror_action_label_key="lesson.l20.monitor.action_label",
        mirror_python_code=d.checkpoint_mirror_code(dataset, week),
        record_key=f"week{week}_checkpoint_read",
        recommendation_record_key=None if is_final else f"week{week}_recommendation",
    )


# --- Mandatory contrast beat - shown to every student regardless of path.
# References week3_primary_diff/primary_diff (already recorded by the
# monitor scene's own checkpoint actions) but never re-assigns them - a
# comment-only python_code line, matching the established discipline that
# a lesson's own base values are referenced, never re-derived mid-mirror.


def _pp(value: float) -> str:
    return f"{value:+.2f}pp"


def _week3_vs_week7_comparisons(dataset) -> tuple[ComparisonValue, ...]:
    week3_diff, _lo, _hi = d.diff_and_ci_at_checkpoint(dataset, 3, d.PRIMARY)
    week7_diff, _lo7, _hi7 = d.diff_and_ci_at_checkpoint(dataset, d.PLANNED_END_WEEK, d.PRIMARY)
    return (
        ComparisonValue(
            WEEK3_PRIMARY_READING_EVIDENCE_KEY,
            week3_diff * 100,
            python_code="# week3_primary_diff was already computed at the week-3 checkpoint",
            value_format=_pp,
        ),
        ComparisonValue(
            WEEK7_PRIMARY_PASS_EVIDENCE_KEY,
            week7_diff * 100,
            python_code="# primary_diff was already computed at the week-7 checkpoint",
            value_format=_pp,
        ),
    )


CONTRAST_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l20.contrast_reveal.interpret.option.{key}")
    for key in (
        "the_larger_later_sample_is_more_reliable_not_because_week3_was_fake",
        "week3_should_be_trusted_because_it_came_first",
        "they_measure_different_things_so_neither_is_more_reliable",
    )
)

# --- Final Decision Brief - 6 fields + Evidence --------------------------

FINAL_VERDICT_FIELD = BriefField(
    key="final_verdict",
    prompt_key="lesson.l20.decision.final_verdict.prompt",
    options=(
        BriefOption("hold_full_rollout_investigate_support_guardrail", "lesson.l20.decision.final_verdict.option.hold_full_rollout_investigate_support_guardrail"),
        BriefOption("ship_full_rollout_primary_passed", "lesson.l20.decision.final_verdict.option.ship_full_rollout_primary_passed"),
        BriefOption("kill_the_feature_entirely", "lesson.l20.decision.final_verdict.option.kill_the_feature_entirely"),
        BriefOption("inconclusive_run_longer", "lesson.l20.decision.final_verdict.option.inconclusive_run_longer"),
    ),
)
WHY_NOT_A_CLEAN_SHIP_FIELD = BriefField(
    key="why_not_a_clean_ship",
    prompt_key="lesson.l20.decision.why_not_a_clean_ship.prompt",
    options=(
        BriefOption("the_launch_rule_requires_every_guardrail_to_hold_too", "lesson.l20.decision.why_not_a_clean_ship.option.the_launch_rule_requires_every_guardrail_to_hold_too"),
        BriefOption("primarys_not_really_significant", "lesson.l20.decision.why_not_a_clean_ship.option.primarys_not_really_significant"),
        BriefOption("guardrails_only_matter_if_primary_fails", "lesson.l20.decision.why_not_a_clean_ship.option.guardrails_only_matter_if_primary_fails"),
    ),
)
WEEK3_STOPPING_RULE_JUDGMENT_FIELD = BriefField(
    key="week3_stopping_rule_judgment",
    prompt_key="lesson.l20.decision.week3_stopping_rule_judgment.prompt",
    options=(
        BriefOption("no_efficacy_stopping_rule_was_pre_specified", "lesson.l20.decision.week3_stopping_rule_judgment.option.no_efficacy_stopping_rule_was_pre_specified"),
        BriefOption("yes_week3_already_cleared_everything", "lesson.l20.decision.week3_stopping_rule_judgment.option.yes_week3_already_cleared_everything"),
        BriefOption("yes_more_data_only_ever_confirms", "lesson.l20.decision.week3_stopping_rule_judgment.option.yes_more_data_only_ever_confirms"),
    ),
)
GENERAL_STOPPING_PRINCIPLE_FIELD = BriefField(
    key="general_stopping_principle",
    prompt_key="lesson.l20.decision.general_stopping_principle.prompt",
    options=(
        BriefOption(
            "only_a_pre_specified_rule_efficacy_or_safety_justifies_acting_early",
            "lesson.l20.decision.general_stopping_principle.option.only_a_pre_specified_rule_efficacy_or_safety_justifies_acting_early",
        ),
        BriefOption("never_look_at_interim_data", "lesson.l20.decision.general_stopping_principle.option.never_look_at_interim_data"),
        BriefOption("any_clean_positive_read_justifies_stopping", "lesson.l20.decision.general_stopping_principle.option.any_clean_positive_read_justifies_stopping"),
    ),
)
WEEK3_VS_WEEK7_EXPLANATION_FIELD = BriefField(
    key="what_explains_week3_vs_week7",
    prompt_key="lesson.l20.decision.week3_vs_week7_explanation.prompt",
    options=(
        BriefOption(
            "the_cumulative_estimate_moved_as_more_data_arrived_early_estimates_are_noisier",
            "lesson.l20.decision.week3_vs_week7_explanation.option.the_cumulative_estimate_moved_as_more_data_arrived_early_estimates_are_noisier",
        ),
        BriefOption("the_treatment_actually_got_worse", "lesson.l20.decision.week3_vs_week7_explanation.option.the_treatment_actually_got_worse"),
        BriefOption("different_things_were_being_measured", "lesson.l20.decision.week3_vs_week7_explanation.option.different_things_were_being_measured"),
    ),
)
GUARDRAIL_VISIBILITY_EXPLANATION_FIELD = BriefField(
    key="why_guardrail_only_visible_at_week7",
    prompt_key="lesson.l20.decision.guardrail_visibility_explanation.prompt",
    options=(
        BriefOption(
            "the_support_harm_was_smaller_than_the_primary_lift_and_the_larger_sample_narrowed_its_interval_enough_to_clear_the_threshold",
            "lesson.l20.decision.guardrail_visibility_explanation.option.the_support_harm_was_smaller_than_the_primary_lift_and_the_larger_sample_narrowed_its_interval_enough_to_clear_the_threshold",
        ),
        BriefOption("the_metric_definition_changed", "lesson.l20.decision.guardrail_visibility_explanation.option.the_metric_definition_changed"),
        BriefOption("guardrails_are_never_detectable_early", "lesson.l20.decision.guardrail_visibility_explanation.option.guardrails_are_never_detectable_early"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l20.decision.evidence.prompt", min_count=3, max_count=4)
DECISION_FIELDS: tuple[BriefField, ...] = (
    FINAL_VERDICT_FIELD,
    WHY_NOT_A_CLEAN_SHIP_FIELD,
    WEEK3_STOPPING_RULE_JUDGMENT_FIELD,
    GENERAL_STOPPING_PRINCIPLE_FIELD,
    WEEK3_VS_WEEK7_EXPLANATION_FIELD,
    GUARDRAIL_VISIBILITY_EXPLANATION_FIELD,
)

# --- Optional mastery: NovaMart Logistics courier route-batching -------

MASTERY_STOPPING_JUDGMENT_FIELD = BriefField(
    key="mastery_stopping_judgment",
    prompt_key="lesson.l20.mastery.field.stopping_judgment.prompt",
    options=(
        BriefOption("stop_now_pre_specified_safety_rule_is_met", "lesson.l20.mastery.option.stopping_judgment.stop_now_pre_specified_safety_rule_is_met"),
        BriefOption("keep_running_only_the_full_sample_can_decide", "lesson.l20.mastery.option.stopping_judgment.keep_running_only_the_full_sample_can_decide"),
        BriefOption("cant_tell_without_more_data", "lesson.l20.mastery.option.stopping_judgment.cant_tell_without_more_data"),
    ),
)
MASTERY_CONTRAST_FIELD = BriefField(
    key="mastery_contrast_with_quickpay",
    prompt_key="lesson.l20.mastery.field.contrast.prompt",
    options=(
        BriefOption(
            "a_safety_rule_was_pre_specified_here_efficacy_never_was_for_quickpay",
            "lesson.l20.mastery.option.contrast.a_safety_rule_was_pre_specified_here_efficacy_never_was_for_quickpay",
        ),
        BriefOption("stopping_early_is_always_wrong", "lesson.l20.mastery.option.contrast.stopping_early_is_always_wrong"),
        BriefOption("any_ci_excluding_zero_justifies_stopping", "lesson.l20.mastery.option.contrast.any_ci_excluding_zero_justifies_stopping"),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l20.mastery.field.evidence.prompt",
    options=(
        BriefOption("interim_ci_entirely_above_the_prespecified_1pp_threshold", "lesson.l20.mastery.option.evidence.interim_ci_entirely_above_the_prespecified_1pp_threshold"),
        BriefOption("the_safety_rule_was_pre_specified_before_the_test_started", "lesson.l20.mastery.option.evidence.the_safety_rule_was_pre_specified_before_the_test_started"),
        BriefOption("group_sizes_being_equal_proves_safety", "lesson.l20.mastery.option.evidence.group_sizes_being_equal_proves_safety"),
        BriefOption("outcome_data_confirms_it_worked", "lesson.l20.mastery.option.evidence.outcome_data_confirms_it_worked"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 20's real synthesis case: NovaMart Go / Quick Pay's
    own week 1 -> week 3 -> week 7 checkpoints, continuing L18's assignment
    and L19's power plan (both stay fully sealed here too). No METHOD -
    every student watches the identical, already-collected dataset; the
    real signal is REASONING/EVIDENCE/UNCERTAINTY/CALIBRATION over a fixed
    decision contract that is never softened to fit the data."""
    collected: dict = {}
    context = LessonContext()
    dataset = d.generate_checkout_experiment()
    checkpoints = tuple(_build_checkpoint(dataset, week) for week in d.CHECKPOINT_WEEKS)

    def _restore_context_if_present() -> None:
        data_ = collected.get("analytical_context")
        if data_ is not None:
            context.restore_from_dict(data_)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        def on_complete():
            _sync_context_into_collected()
            advance()

        return DialogueScene(
            app,
            INVESTIGATION_DIALOGUE,
            on_complete=on_complete,
            context=context,
            record_label_key="lesson.l20.investigation.protocol_action_label",
            record_evidence_key=DECISION_PROTOCOL_EVIDENCE_KEY,
            record_key="decision_protocol",
        )

    # --- Experiment monitoring - one linear pass, week 1 -> 3 -> 7 -------

    def experiment_monitoring(advance):
        def on_complete(recommendations: dict[int, str]):
            collected["week1_recommendation"] = recommendations.get(1)
            collected["week3_recommendation"] = recommendations.get(3)
            _sync_context_into_collected()
            advance()

        return ExperimentMonitorScene(
            app,
            title_key="lesson.l20.monitor.title",
            checkpoints=checkpoints,
            total_planned_weeks=d.PLANNED_END_WEEK,
            context=context,
            on_complete=on_complete,
            recommendation_prompt_key="lesson.l20.monitor.recommendation.prompt",
            recommendation_options=RECOMMENDATION_OPTIONS,
            recommendation_action_label_key="lesson.l20.monitor.recommendation.action_label",
            final_continue_label_key="lesson.l20.monitor.continue_to_brief",
        )

    # --- Mandatory contrast beat ------------------------------------------

    def week3_vs_week7_contrast_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l20.contrast_reveal.title",
            narrative_keys=("dialogue.l20_contrast_reveal.line1",),
            comparisons=_week3_vs_week7_comparisons(dataset),
            interpret_prompt_key="lesson.l20.contrast_reveal.interpret_prompt",
            interpret_options=CONTRAST_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Final Decision Brief ---

    def final_decision_brief(advance):
        def on_complete(choices):
            collected["decision"] = choices
            context.set_decision(
                DecisionState(
                    choices={k: v for k, v in choices.items() if isinstance(v, str)},
                    supporting_evidence_ids=tuple(choices["evidence"]),
                )
            )
            _sync_context_into_collected()
            advance()

        return DecisionBuilderScene(
            app,
            "lesson.l20.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l20.mastery.title",
                (MASTERY_STOPPING_JUDGMENT_FIELD, MASTERY_CONTRAST_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l20.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

    # --- Feedback / Debrief ---

    def _critical_evidence_present(selected_evidence_ids: set[str]) -> tuple[str, ...]:
        present: set[str] = set()
        for item in context.evidence:
            if item.id not in selected_evidence_ids:
                continue
            for critical_key in CRITICAL_EVIDENCE_KEYS:
                if critical_key in item.label_key:
                    present.add(critical_key)
        return tuple(sorted(present))

    def _build_result() -> LessonTwentyResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentyResult(
            week1_recommendation=collected.get("week1_recommendation"),
            week3_recommendation=collected.get("week3_recommendation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_20.number, 0)
        evaluation = score_lesson_twenty(result, LESSON_20, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        experiment_monitoring,
        week3_vs_week7_contrast_reveal,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=20,
        collected=collected,
        definition=LESSON_20,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

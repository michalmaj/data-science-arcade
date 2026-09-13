from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.power import proportion_difference_ci
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l19_power_plant import data as d
from data_science_arcade.lessons.l19_power_plant.definition import LESSON_19
from data_science_arcade.lessons.l19_power_plant.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    FINAL_PLAN_SENSITIVITY_EVIDENCE_KEY,
    PRECISE_TINY_EFFECT_EVIDENCE_KEY,
    REFERENCE_INADEQUATE_DESIGN_EVIDENCE_KEY,
    UNDERPOWERED_CALIBRATION_EVIDENCE_KEY,
    LessonNineteenResult,
    score_lesson_nineteen,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.power_planner_scene import PowerPlannerScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -----------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l19_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l19_briefing.line2"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l19_briefing.line3"),
    )
)
INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_investigation.line2"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l19_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_debrief.line3"),
    )
)
PLANNER_NARRATIVE_KEYS = ("dialogue.l19_planner.line1", "dialogue.l19_planner.line2")
MASTERY_DIALOGUE_KEYS = ("dialogue.l19_mastery.line1", "dialogue.l19_mastery.line2", "dialogue.l19_mastery.line3")

# --- Cold pick - blind, no numbers shown ------------------------------

COLD_DURATION_PICK_FIELD = BriefField(
    key="cold_duration_pick",
    prompt_key="lesson.l19.cold_pick.prompt",
    hint_key="lesson.l19.cold_pick.hint",
    options=tuple(BriefOption(str(weeks), f"lesson.l19.cold_pick.option.{weeks}weeks") for weeks in d.COLD_PICK_WEEK_OPTIONS),
)

# --- "What 80% power means" - real seeded Monte Carlo, two FIXED
# reference designs, never the student's own final pick. ----------------


def _pct_about(value: float) -> str:
    return f"~{round(value)}%"


POWER_REVEAL_COMPARISONS = (
    ComparisonValue(
        REFERENCE_INADEQUATE_DESIGN_EVIDENCE_KEY,
        d.REFERENCE_DESIGN_A_DETECTION_RATE * 100,
        python_code=d.REFERENCE_DESIGN_A_MIRROR,
        value_format=_pct_about,
    ),
    ComparisonValue(
        "lesson.l19.power_reveal.design_b_label",
        d.REFERENCE_DESIGN_B_DETECTION_RATE * 100,
        python_code=d.REFERENCE_DESIGN_B_MIRROR,
        value_format=_pct_about,
    ),
)
POWER_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l19.power_reveal.interpret.option.{key}")
    for key in (
        "detection_probability_across_repeated_samples",
        "seven_week_design_proves_the_effect_exists",
        "four_week_caught_it_sometimes_so_its_fine",
    )
)

# --- Two mandatory calibration reveals ---------------------------------


def _calibration_comparisons(dataset, mirror_codes: tuple[str, str, str]) -> tuple[ComparisonValue, ...]:
    control_conversions, control_n = d.calibration_counts(dataset, "control")
    treatment_conversions, treatment_n = d.calibration_counts(dataset, "treatment")
    control_rate = control_conversions / control_n
    treatment_rate = treatment_conversions / treatment_n
    ci_lower, ci_upper = proportion_difference_ci(control_conversions, control_n, treatment_conversions, treatment_n)
    control_code, treatment_code, ci_code = mirror_codes
    return (
        ComparisonValue("lesson.l19.calibration.control_rate_label", control_rate * 100, python_code=control_code, value_format=lambda v: f"{v:.1f}%"),
        ComparisonValue("lesson.l19.calibration.treatment_rate_label", treatment_rate * 100, python_code=treatment_code, value_format=lambda v: f"{v:.1f}%"),
        ComparisonValue("lesson.l19.calibration.ci_lower_label", ci_lower * 100, python_code=ci_code, value_format=lambda v: f"{v:+.2f}pp"),
        ComparisonValue("lesson.l19.calibration.ci_upper_label", ci_upper * 100, value_format=lambda v: f"{v:+.2f}pp"),
    )


UNDERPOWERED_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l19.underpowered_reveal.interpret.option.{key}", evidence_key=UNDERPOWERED_CALIBRATION_EVIDENCE_KEY)
    for key in ("inconclusive_substantial_uncertainty_remains", "not_significant_so_no_real_effect", "positive_estimate_means_it_works")
)
HIGH_N_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l19.high_n_reveal.interpret.option.{key}", evidence_key=PRECISE_TINY_EFFECT_EVIDENCE_KEY)
    for key in ("statistically_distinguishable_but_below_threshold", "statistically_significant_so_ship_it", "narrow_interval_means_effect_is_zero")
)

# --- Final Power Brief - 6 fields + Evidence ----------------------------

FINAL_DESIGN_CLASSIFICATION_FIELD = BriefField(
    key="final_design_meets_sensitivity_target",
    prompt_key="lesson.l19.decision.final_design_classification.prompt",
    options=(
        BriefOption("meets_sensitivity_target", "lesson.l19.decision.final_design_classification.option.meets_sensitivity_target"),
        BriefOption("does_not_meet_sensitivity_target", "lesson.l19.decision.final_design_classification.option.does_not_meet_sensitivity_target"),
    ),
)
SAMPLE_SIZE_EFFECT_FIELD = BriefField(
    key="what_more_sample_size_changes",
    prompt_key="lesson.l19.decision.sample_size_effect.prompt",
    options=(
        BriefOption(
            "narrows_uncertainty_improves_sensitivity_not_effect_size", "lesson.l19.decision.sample_size_effect.option.narrows_uncertainty_improves_sensitivity_not_effect_size"
        ),
        BriefOption("makes_the_true_effect_bigger", "lesson.l19.decision.sample_size_effect.option.makes_the_true_effect_bigger"),
        BriefOption("has_no_real_impact_on_anything", "lesson.l19.decision.sample_size_effect.option.has_no_real_impact_on_anything"),
    ),
)
MDE_REPRESENTS_FIELD = BriefField(
    key="what_mde_represents",
    prompt_key="lesson.l19.decision.mde_represents.prompt",
    options=(
        BriefOption("design_stage_probability_not_post_hoc_cutoff", "lesson.l19.decision.mde_represents.option.design_stage_probability_not_post_hoc_cutoff"),
        BriefOption("a_hard_cutoff_effects_below_it_cannot_be_real", "lesson.l19.decision.mde_represents.option.a_hard_cutoff_effects_below_it_cannot_be_real"),
        BriefOption("a_guarantee_the_true_effect_equals_this_value", "lesson.l19.decision.mde_represents.option.a_guarantee_the_true_effect_equals_this_value"),
    ),
)
BUSINESS_VS_STATISTICAL_FIELD = BriefField(
    key="business_vs_statistical_detectability",
    prompt_key="lesson.l19.decision.business_vs_statistical.prompt",
    options=(
        BriefOption("answer_different_questions_not_interchangeable", "lesson.l19.decision.business_vs_statistical.option.answer_different_questions_not_interchangeable"),
        BriefOption("theyre_the_same_number_by_definition", "lesson.l19.decision.business_vs_statistical.option.theyre_the_same_number_by_definition"),
        BriefOption("statistical_detectability_matters_more", "lesson.l19.decision.business_vs_statistical.option.statistical_detectability_matters_more"),
    ),
)
UNDERPOWERED_RESULT_INTERPRETATION_FIELD = BriefField(
    key="underpowered_result_interpretation",
    prompt_key="lesson.l19.decision.underpowered_interpretation.prompt",
    options=(
        BriefOption(
            "inconclusive_neither_zero_nor_worthwhile_ruled_out", "lesson.l19.decision.underpowered_interpretation.option.inconclusive_neither_zero_nor_worthwhile_ruled_out"
        ),
        BriefOption("not_significant_so_no_real_effect", "lesson.l19.decision.underpowered_interpretation.option.not_significant_so_no_real_effect"),
        BriefOption("positive_estimate_means_it_works", "lesson.l19.decision.underpowered_interpretation.option.positive_estimate_means_it_works"),
    ),
)
PRECISE_SMALL_EFFECT_INTERPRETATION_FIELD = BriefField(
    key="precise_small_effect_interpretation",
    prompt_key="lesson.l19.decision.precise_small_effect_interpretation.prompt",
    options=(
        BriefOption(
            "precisely_estimated_small_effect_below_threshold", "lesson.l19.decision.precise_small_effect_interpretation.option.precisely_estimated_small_effect_below_threshold"
        ),
        BriefOption("statistically_significant_so_worth_shipping", "lesson.l19.decision.precise_small_effect_interpretation.option.statistically_significant_so_worth_shipping"),
        BriefOption("narrow_interval_means_the_effect_is_zero", "lesson.l19.decision.precise_small_effect_interpretation.option.narrow_interval_means_the_effect_is_zero"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l19.decision.evidence.prompt", min_count=3, max_count=4)
DECISION_FIELDS: tuple[BriefField, ...] = (
    FINAL_DESIGN_CLASSIFICATION_FIELD,
    SAMPLE_SIZE_EFFECT_FIELD,
    MDE_REPRESENTS_FIELD,
    BUSINESS_VS_STATISTICAL_FIELD,
    UNDERPOWERED_RESULT_INTERPRETATION_FIELD,
    PRECISE_SMALL_EFFECT_INTERPRETATION_FIELD,
)

# --- Optional mastery: NovaMart Logistics late-delivery reduction -------

MASTERY_DESIGN_JUDGMENT_FIELD = BriefField(
    key="mastery_design_judgment",
    prompt_key="lesson.l19.mastery.field.design_judgment.prompt",
    options=(
        BriefOption("inadequate_for_the_2pp_target", "lesson.l19.mastery.option.design_judgment.inadequate_for_the_2pp_target"),
        BriefOption("adequate_for_the_2pp_target", "lesson.l19.mastery.option.design_judgment.adequate_for_the_2pp_target"),
        BriefOption("cant_tell_without_more_info", "lesson.l19.mastery.option.design_judgment.cant_tell_without_more_info"),
    ),
)
MASTERY_RESULT_INTERPRETATION_FIELD = BriefField(
    key="mastery_result_interpretation",
    prompt_key="lesson.l19.mastery.field.result_interpretation.prompt",
    options=(
        BriefOption(
            "inconclusive_neither_zero_nor_worthwhile_ruled_out", "lesson.l19.mastery.option.result_interpretation.inconclusive_neither_zero_nor_worthwhile_ruled_out"
        ),
        BriefOption("proves_no_real_improvement", "lesson.l19.mastery.option.result_interpretation.proves_no_real_improvement"),
        BriefOption("proves_the_full_2pp_improvement", "lesson.l19.mastery.option.result_interpretation.proves_the_full_2pp_improvement"),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l19.mastery.field.evidence.prompt",
    options=(
        BriefOption("design_inadequate_for_2pp_target", "lesson.l19.mastery.option.evidence.design_inadequate_for_2pp_target"),
        BriefOption("wide_ci_crosses_zero_and_target", "lesson.l19.mastery.option.evidence.wide_ci_crosses_zero_and_target"),
        BriefOption("group_sizes_being_equal_proves_power", "lesson.l19.mastery.option.evidence.group_sizes_being_equal_proves_power"),
        BriefOption("outcome_data_confirms_it_worked", "lesson.l19.mastery.option.evidence.outcome_data_confirms_it_worked"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_nineteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 19's real investigation: one continuous NovaMart
    Go / Quick Pay planning case (L18's own outcome stays fully sealed
    here too - this lesson never touches it). A blind cold pick seeds one
    live PowerPlannerScene visit (real revision = moving the stepper
    before Confirm, no offer/skip gate needed - see that scene's own
    docstring); two mandatory calibration reveals and one mandatory
    power-as-probability reveal are shown to every student regardless of
    path. METHOD reads only `collected["final_weeks"]`, never anything
    the Final Power Brief claims."""
    collected: dict = {}
    context = LessonContext()
    underpowered_dataset = d.generate_underpowered_calibration()
    high_n_dataset = d.generate_high_n_calibration()

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
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    # --- Cold pick -> one live planner visit --------------------------

    def cold_duration_pick(advance):
        def on_complete(choices):
            weeks = int(choices["cold_duration_pick"])
            collected["cold_duration_pick"] = weeks
            advance()

        return BriefBuilderScene(app, "lesson.l19.cold_pick.title", (COLD_DURATION_PICK_FIELD,), on_complete, guided=True)

    def power_planning(advance):
        def on_confirm(weeks: int):
            collected["final_weeks"] = weeks
            _sync_context_into_collected()
            advance()

        return PowerPlannerScene(
            app,
            title_key="lesson.l19.planner.title",
            narrative_keys=PLANNER_NARRATIVE_KEYS,
            initial_weeks=collected["cold_duration_pick"],
            min_weeks=d.MIN_WEEKS,
            max_weeks=d.MAX_WEEKS,
            weekly_n_per_arm=d.WEEKLY_N_PER_ARM,
            baseline_rate=d.BASELINE_RATE,
            business_minimum_effect=d.BUSINESS_MINIMUM_EFFECT,
            on_confirm=on_confirm,
            context=context,
            record_key="power_plan",
            mirror_action_label_key="lesson.l19.planner.action_label",
            mirror_python_code_for=d.plan_mirror_code,
            evidence_key=FINAL_PLAN_SENSITIVITY_EVIDENCE_KEY,
        )

    # --- Mandatory reveals - shown to every student regardless of path ---

    def power_as_probability_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l19.power_reveal.title",
            narrative_keys=("dialogue.l19_power_reveal.line1",),
            comparisons=POWER_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l19.power_reveal.interpret_prompt",
            interpret_options=POWER_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def underpowered_calibration_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l19.underpowered_reveal.title",
            narrative_keys=("dialogue.l19_underpowered_reveal.line1",),
            comparisons=_calibration_comparisons(underpowered_dataset, d.UNDERPOWERED_CALIBRATION_MIRROR),
            interpret_prompt_key="lesson.l19.underpowered_reveal.interpret_prompt",
            interpret_options=UNDERPOWERED_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def precise_small_effect_calibration_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l19.high_n_reveal.title",
            narrative_keys=("dialogue.l19_high_n_reveal.line1",),
            comparisons=_calibration_comparisons(high_n_dataset, d.HIGH_N_CALIBRATION_MIRROR),
            interpret_prompt_key="lesson.l19.high_n_reveal.interpret_prompt",
            interpret_options=HIGH_N_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Final Power Brief ---

    def final_power_brief(advance):
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
            "lesson.l19.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l19.mastery.title",
                (MASTERY_DESIGN_JUDGMENT_FIELD, MASTERY_RESULT_INTERPRETATION_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l19.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonNineteenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonNineteenResult(
            cold_duration_pick=collected.get("cold_duration_pick", 0),
            final_weeks=collected.get("final_weeks", 0),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_19.number, 0)
        evaluation = score_lesson_nineteen(result, LESSON_19, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        cold_duration_pick,
        power_planning,
        power_as_probability_reveal,
        underpowered_calibration_reveal,
        precise_small_effect_calibration_reveal,
        final_power_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=19,
        collected=collected,
        definition=LESSON_19,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

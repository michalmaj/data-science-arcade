from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l27_causality_courtroom.case_data import (
    compute_group_mean_difference,
    correlation_mirror_code,
    generate_resolution_satisfaction_data,
    generate_tool_spend_data,
    generate_training_performance_data,
    group_mean_difference_mirror_code,
)
from data_science_arcade.lessons.l27_causality_courtroom.definition import LESSON_27
from data_science_arcade.lessons.l27_causality_courtroom.requests import CORRELATION_REQUESTS
from data_science_arcade.lessons.l27_causality_courtroom.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    CHECKOUT_BETA_OBSERVATIONAL_GAP_EVIDENCE_KEY,
    CHECKOUT_BETA_RANDOMIZED_GAP_EVIDENCE_KEY,
    LessonTwentySevenResult,
    OBSERVED_DIFFERENCE_KEYS,
    RANDOMIZED_COMPARISON_KEYS,
    RESOLUTION_SATISFACTION_DIFFERENCE_EVIDENCE_KEY,
    TOOL_SPEND_DIFFERENCE_EVIDENCE_KEY,
    TRAINING_PERFORMANCE_DIFFERENCE_EVIDENCE_KEY,
    score_lesson_twenty_seven,
)
from data_science_arcade.lessons.l27_causality_courtroom.twist_data import conversion_rate, generate_checkout_beta_data, group_gap_mirror_code
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l27_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l27_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_investigation.line3"),
    )
)

REVISION_INTRO_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l27_revision_intro.line1"),))

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l27_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_debrief.line3"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l27_mastery.line1",
    "dialogue.l27_mastery.line2",
    "dialogue.l27_mastery.line3",
)

# --- Two mandatory reveals - fixed, real reference values computed from
# the real scenario datasets. Zero InterpretOption.evidence_key anywhere:
# a student who picks the WRONG interpretation still saw the exact same
# real numbers and can cite them later. ------------------------------------


def _mirror_python_code_for(request, var_name: str) -> str:
    return correlation_mirror_code(request.key, var_name)


def _signed_dollars(value: float) -> str:
    sign = "-" if value < 0 else "+"
    return f"{sign}${abs(value):.2f}"


def _signed_points(value: float) -> str:
    return f"{value:+.1f}"


def _pct(value: float) -> str:
    return f"{value:.0%}"


def _pp(value: float) -> str:
    # For a genuine difference-of-two-rates quantity (not a rate itself) -
    # matches the pp-suffixed convention L15/L17-L20 already use for this
    # exact "point gap" shape, avoiding the percent/percentage-point
    # ambiguity a plain _pct would read as here.
    return f"{value * 100:+.0f}pp"


# --- Reveal A: "Observed Difference Is Not a Treatment Effect" - the real,
# signed, business-interpretable group-mean difference for each of the
# three cases, never shown before (the picker only ever shows r). ---------

_TOOL_SPEND = generate_tool_spend_data()
_RESOLUTION_SATISFACTION = generate_resolution_satisfaction_data()
_TRAINING_PERFORMANCE = generate_training_performance_data()

_TOOL_SPEND_DIFFERENCE = compute_group_mean_difference(_TOOL_SPEND, "tool_used", "impulse_spend")
_RESOLUTION_SATISFACTION_DIFFERENCE = compute_group_mean_difference(_RESOLUTION_SATISFACTION, "resolved_under_1hr", "satisfaction_score")
_TRAINING_PERFORMANCE_DIFFERENCE = compute_group_mean_difference(_TRAINING_PERFORMANCE, "completed_training", "performance_score")

GROUP_DIFFERENCES_REVEAL_COMPARISONS = (
    ComparisonValue(
        TOOL_SPEND_DIFFERENCE_EVIDENCE_KEY,
        _TOOL_SPEND_DIFFERENCE,
        python_code=group_mean_difference_mirror_code("tool_spend", "tool_used", "impulse_spend", "group_differences_reveal_tool_spend"),
        value_format=_signed_dollars,
    ),
    ComparisonValue(
        RESOLUTION_SATISFACTION_DIFFERENCE_EVIDENCE_KEY,
        _RESOLUTION_SATISFACTION_DIFFERENCE,
        python_code=group_mean_difference_mirror_code(
            "resolution_satisfaction", "resolved_under_1hr", "satisfaction_score", "group_differences_reveal_resolution"
        ),
        value_format=_signed_points,
    ),
    ComparisonValue(
        TRAINING_PERFORMANCE_DIFFERENCE_EVIDENCE_KEY,
        _TRAINING_PERFORMANCE_DIFFERENCE,
        python_code=group_mean_difference_mirror_code(
            "training_performance", "completed_training", "performance_score", "group_differences_reveal_training"
        ),
        value_format=_signed_points,
    ),
)
GROUP_DIFFERENCES_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l27.group_differences_reveal.interpret.option.{key}")
    for key in (
        "a_real_observed_difference_between_two_groups_not_yet_a_measured_effect",
        "differences_this_large_and_consistent_can_only_come_from_the_treatment_itself",
        "none_of_these_differences_are_trustworthy_since_no_group_was_randomly_assigned",
    )
)

# --- Reveal B: "What Randomization Changes" - checkout_beta's own
# observational gap and randomized gap, side by side, the first real
# randomized comparison shown anywhere in the lesson. ----------------------

_CHECKOUT_BETA = generate_checkout_beta_data()
_CHECKOUT_BETA_OBSERVATIONAL_GAP = conversion_rate(_CHECKOUT_BETA, "beta_opt_in") - conversion_rate(_CHECKOUT_BETA, "non_beta")
_CHECKOUT_BETA_RANDOMIZED_GAP = conversion_rate(_CHECKOUT_BETA, "randomized_treatment") - conversion_rate(_CHECKOUT_BETA, "randomized_control")

RANDOMIZATION_REVEAL_COMPARISONS = (
    ComparisonValue(
        CHECKOUT_BETA_OBSERVATIONAL_GAP_EVIDENCE_KEY,
        _CHECKOUT_BETA_OBSERVATIONAL_GAP,
        python_code=group_gap_mirror_code("checkout_beta", "beta_opt_in", "non_beta", "randomization_reveal_observational"),
        value_format=_pp,
    ),
    ComparisonValue(
        CHECKOUT_BETA_RANDOMIZED_GAP_EVIDENCE_KEY,
        _CHECKOUT_BETA_RANDOMIZED_GAP,
        python_code=group_gap_mirror_code("checkout_beta", "randomized_treatment", "randomized_control", "randomization_reveal_randomized"),
        value_format=_pp,
    ),
)
RANDOMIZATION_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l27.randomization_reveal.interpret.option.{key}")
    for key in (
        "the_observational_comparison_substantially_overstated_what_the_randomized_comparison_estimates",
        "the_25_point_observational_gap_is_the_beta_checkouts_real_effect",
        "since_the_randomized_effect_is_so_small_the_new_checkout_clearly_doesnt_matter_at_all",
    )
)

# --- Final Decision Brief - 4 REASONING fields + 1 CALIBRATION field + Evidence --

WHY_NON_RANDOM_GROUP_FORMATION_FIELD = BriefField(
    key="why_non_random_group_formation_undermines_a_comparison",
    prompt_key="lesson.l27.field.why_non_random_group_formation_undermines_a_comparison.prompt",
    options=(
        BriefOption(
            "people_or_processes_that_land_in_a_group_may_already_differ_before_anything_happens",
            "lesson.l27.option.why_non_random_group_formation_undermines_a_comparison.people_or_processes_that_land_in_a_group_may_already_differ_before_anything_happens",
        ),
        BriefOption(
            "a_correlation_this_strong_can_only_be_the_treatment",
            "lesson.l27.option.why_non_random_group_formation_undermines_a_comparison.a_correlation_this_strong_can_only_be_the_treatment",
        ),
        BriefOption(
            "the_groups_use_different_outcome_scales",
            "lesson.l27.option.why_non_random_group_formation_undermines_a_comparison.the_groups_use_different_outcome_scales",
        ),
    ),
)
WHY_THE_RIGHT_VERDICT_STILL_NEEDS_THE_RIGHT_REASON_FIELD = BriefField(
    key="why_the_right_verdict_still_needs_the_right_reason",
    prompt_key="lesson.l27.field.why_the_right_verdict_still_needs_the_right_reason.prompt",
    options=(
        BriefOption(
            "misdiagnosing_the_mechanism_can_miss_the_real_problem_even_when_the_verdict_is_right",
            "lesson.l27.option.why_the_right_verdict_still_needs_the_right_reason.misdiagnosing_the_mechanism_can_miss_the_real_problem_even_when_the_verdict_is_right",
        ),
        BriefOption(
            "any_skepticism_works_as_long_as_the_final_call_is_right",
            "lesson.l27.option.why_the_right_verdict_still_needs_the_right_reason.any_skepticism_works_as_long_as_the_final_call_is_right",
        ),
        BriefOption(
            "the_reasoning_behind_a_sustained_objection_doesnt_need_recording",
            "lesson.l27.option.why_the_right_verdict_still_needs_the_right_reason.the_reasoning_behind_a_sustained_objection_doesnt_need_recording",
        ),
    ),
)
MISSING_EVIDENCE_FIELD = BriefField(
    key="missing_evidence",
    prompt_key="lesson.l27.field.missing_evidence.prompt",
    options=(
        BriefOption(
            "a_design_that_breaks_the_link_between_pre_existing_type_and_the_exposure_being_compared",
            "lesson.l27.option.missing_evidence.a_design_that_breaks_the_link_between_pre_existing_type_and_the_exposure_being_compared",
        ),
        BriefOption("more_of_the_same_observational_data", "lesson.l27.option.missing_evidence.more_of_the_same_observational_data"),
        BriefOption("ask_the_self_selected_group", "lesson.l27.option.missing_evidence.ask_the_self_selected_group"),
    ),
)
WHAT_RANDOMIZATION_CHANGES_FIELD = BriefField(
    key="what_randomization_changes",
    prompt_key="lesson.l27.field.what_randomization_changes.prompt",
    options=(
        BriefOption(
            "breaks_the_link_between_pre_existing_type_and_assigned_condition_in_expectation",
            "lesson.l27.option.what_randomization_changes.breaks_the_link_between_pre_existing_type_and_assigned_condition_in_expectation",
        ),
        BriefOption(
            "randomization_removes_all_bias_completely_and_forever",
            "lesson.l27.option.what_randomization_changes.randomization_removes_all_bias_completely_and_forever",
        ),
        BriefOption(
            "randomization_doesnt_actually_change_the_comparison",
            "lesson.l27.option.what_randomization_changes.randomization_doesnt_actually_change_the_comparison",
        ),
    ),
)
FINAL_VERDICT_FIELD = BriefField(
    key="final_verdict",
    prompt_key="lesson.l27.field.final_verdict.prompt",
    options=(
        BriefOption("each_needs_a_proper_comparison_group", "lesson.l27.option.final_verdict.each_needs_a_proper_comparison_group"),
        BriefOption(
            "all_confirmed_effects_too_large_for_chance", "lesson.l27.option.final_verdict.all_confirmed_effects_too_large_for_chance"
        ),
        BriefOption("all_should_be_thrown_out", "lesson.l27.option.final_verdict.all_should_be_thrown_out"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l27.decision.evidence.prompt", min_count=3, max_count=5)
DECISION_FIELDS: tuple[BriefField, ...] = (
    WHY_NON_RANDOM_GROUP_FORMATION_FIELD,
    WHY_THE_RIGHT_VERDICT_STILL_NEEDS_THE_RIGHT_REASON_FIELD,
    MISSING_EVIDENCE_FIELD,
    WHAT_RANDOMIZATION_CHANGES_FIELD,
    FINAL_VERDICT_FIELD,
)

# --- Optional mastery: a new, small NovaMart express-shipping dataset - no
# existing L27 dataset was left over to promote (checkout_beta is this
# lesson's own mandatory Twist). Mirrors checkout_beta's own dramatic-
# naive/modest-real shape deliberately, since mastery tests the same
# reflex in a new domain, never a different one. Copy stays in estimate
# language throughout - never "real effect", matching the main flow. ------

MASTERY_WHAT_THE_NAIVE_COMPARISON_SHOWS_FIELD = BriefField(
    key="mastery_what_the_naive_comparison_shows",
    prompt_key="lesson.l27.mastery.field.what_the_naive_comparison_shows.prompt",
    options=(
        BriefOption(
            "reflects_both_a_possible_effect_and_pre_existing_differences_between_who_opted_in_and_who_didnt",
            "lesson.l27.mastery.option.what_the_naive_comparison_shows.reflects_both_a_possible_effect_and_pre_existing_differences_between_who_opted_in_and_who_didnt",
        ),
        BriefOption(
            "is_entirely_the_offers_own_effect", "lesson.l27.mastery.option.what_the_naive_comparison_shows.is_entirely_the_offers_own_effect"
        ),
        BriefOption(
            "cannot_be_trusted_at_all_even_as_a_starting_signal",
            "lesson.l27.mastery.option.what_the_naive_comparison_shows.cannot_be_trusted_at_all_even_as_a_starting_signal",
        ),
    ),
)
MASTERY_STRONGEST_CLAIM_FIELD = BriefField(
    key="mastery_strongest_claim",
    prompt_key="lesson.l27.mastery.field.strongest_claim.prompt",
    options=(
        BriefOption(
            "the_randomized_test_estimates_a_much_smaller_effect_than_the_naive_comparison_suggested",
            "lesson.l27.mastery.option.strongest_claim.the_randomized_test_estimates_a_much_smaller_effect_than_the_naive_comparison_suggested",
        ),
        BriefOption("the_37_point_gap_is_the_offers_real_value", "lesson.l27.mastery.option.strongest_claim.the_37_point_gap_is_the_offers_real_value"),
        BriefOption(
            "since_the_randomized_effect_is_small_express_shipping_clearly_doesnt_matter",
            "lesson.l27.mastery.option.strongest_claim.since_the_randomized_effect_is_small_express_shipping_clearly_doesnt_matter",
        ),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l27.mastery.field.evidence.prompt",
    options=(
        BriefOption("naive_gap_37_points", "lesson.l27.mastery.option.evidence.naive_gap_37_points"),
        BriefOption("randomized_estimate_5_points", "lesson.l27.mastery.option.evidence.randomized_estimate_5_points"),
        BriefOption("observational_sample_size_800", "lesson.l27.mastery.option.evidence.observational_sample_size_800"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_seven_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 27's real investigation: three genuinely
    independent self-selected/process-based courtroom cases, tested twice
    - an initial CorrelationScene pass (guided=False - a motivated-
    reasoning trap, not a hidden-information one, since the live evidence
    panel already shows each case's own given selection/confounding
    mechanism before any pick), two mandatory reveals (a real observed-
    difference reveal, a real randomization reveal), then a real revision
    pass seeded with the first pass's own pick."""
    collected: dict = {}
    context = LessonContext()

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

    # --- Initial correlation pass - a motivated-reasoning trap, not a
    # hidden-information one: each case's own given selection/confounding
    # mechanism is already narrated in the live evidence panel before
    # commit. -------------------------------------------------------------

    def initial_case_pass(advance):
        def on_complete(choices):
            collected["initial_verdict_choices"] = choices
            _sync_context_into_collected()
            advance()

        return CorrelationScene(
            app,
            "lesson.l27.investigation_title",
            CORRELATION_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            mirror_python_code_for=_mirror_python_code_for,
        )

    # --- Two mandatory reveals - shown to every student regardless of
    # path. Each names a genuinely distinct mechanism. --------------------

    def group_differences_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_observed_difference_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l27.group_differences_reveal.title",
            narrative_keys=("dialogue.l27_group_differences_reveal.line1", "dialogue.l27_group_differences_reveal.line2"),
            comparisons=GROUP_DIFFERENCES_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l27.group_differences_reveal.interpret_prompt",
            interpret_options=GROUP_DIFFERENCES_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def randomization_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_randomization_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l27.randomization_reveal.title",
            narrative_keys=("dialogue.l27_randomization_reveal.line1", "dialogue.l27_randomization_reveal.line2"),
            comparisons=RANDOMIZATION_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l27.randomization_reveal.interpret_prompt",
            interpret_options=RANDOMIZATION_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Revision intro + a real revision pass, seeded with the first
    # pass's own pick. -----------------------------------------------------

    def revision_intro(advance):
        return DialogueScene(app, REVISION_INTRO_DIALOGUE, on_complete=advance)

    def revision_case_pass(advance):
        def on_complete(choices):
            collected["verdict_choices"] = choices
            _sync_context_into_collected()
            advance()

        return CorrelationScene(
            app,
            "lesson.l27.investigation_title",
            CORRELATION_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            initial_choices=collected.get("initial_verdict_choices"),
            mirror_python_code_for=_mirror_python_code_for,
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
            "lesson.l27.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l27.mastery.title",
                (MASTERY_WHAT_THE_NAIVE_COMPARISON_SHOWS_FIELD, MASTERY_STRONGEST_CLAIM_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l27.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonTwentySevenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentySevenResult(
            initial_verdict_choices=collected.get("initial_verdict_choices", {}),
            verdict_choices=collected.get("verdict_choices", {}),
            reveal_observed_difference_interpretation=collected.get("reveal_observed_difference_interpretation"),
            reveal_randomization_interpretation=collected.get("reveal_randomization_interpretation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_27.number, 0)
        evaluation = score_lesson_twenty_seven(result, LESSON_27, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        initial_case_pass,
        group_differences_reveal,
        randomization_reveal,
        revision_intro,
        revision_case_pass,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=27,
        collected=collected,
        definition=LESSON_27,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

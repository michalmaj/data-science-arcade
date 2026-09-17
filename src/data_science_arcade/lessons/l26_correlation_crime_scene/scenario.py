from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l26_correlation_crime_scene.correlation_data import (
    compute_device_group_correlation,
    correlation_mirror_code,
    correlation_within_mirror_code,
    device_group_correlation_mirror_code,
    generate_dark_mode_data,
)
from data_science_arcade.lessons.l26_correlation_crime_scene.definition import LESSON_26
from data_science_arcade.lessons.l26_correlation_crime_scene.requests import (
    CORRELATION_REQUESTS,
    DARK_MODE_CORRELATION,
    DARK_MODE_WITHIN_MODERN_CORRELATION,
    PUSH_OPENS_CORRELATION,
    SHIPMENT_SALES_CORRELATION,
)
from data_science_arcade.lessons.l26_correlation_crime_scene.scoring import (
    CRITICAL_EVIDENCE_KEYS,
    DARK_MODE_OVERALL_CORRELATION_EVIDENCE_KEY,
    DARK_MODE_WITHIN_MODERN_CORRELATION_EVIDENCE_KEY,
    DEVICE_GROUP_SPEND_CORRELATION_EVIDENCE_KEY,
    LessonTwentySixResult,
    PUSH_OPENS_CORRELATION_EVIDENCE_KEY,
    SHIPMENT_CORRELATION_EVIDENCE_KEY,
    score_lesson_twenty_six,
)
from data_science_arcade.lessons.l26_correlation_crime_scene.twist_data import generate_loyalty_ltv_data
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
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
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l26_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l26_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_investigation.line3"),
    )
)

REVISION_INTRO_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l26_revision_intro.line1"),))

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l26_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_debrief.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_debrief.line4"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l26_mastery.line1",
    "dialogue.l26_mastery.line2",
    "dialogue.l26_mastery.line3",
)

# --- Two mandatory reveals - fixed, real reference values computed from
# the three real scenario datasets. Zero InterpretOption.evidence_key
# anywhere: a student who picks the WRONG interpretation still saw the
# exact same real numbers and can cite them later. ------------------------


def _mirror_python_code_for(request, var_name: str) -> str:
    return correlation_mirror_code(request.key, var_name)


def _bare_pct(value: float) -> str:
    return f"{value:.2f}"


# --- Reveal A: "A Strong Observed Association" - push_opens and shipment
# correlations, already shown live in the picker, placed side by side as
# real, formally citable Evidence for the first time. ---------------------

STRONG_ASSOCIATION_REVEAL_COMPARISONS = (
    ComparisonValue(
        PUSH_OPENS_CORRELATION_EVIDENCE_KEY,
        PUSH_OPENS_CORRELATION,
        python_code=correlation_mirror_code("push_opens_claim", "association_reveal_push_opens"),
        value_format=_bare_pct,
    ),
    ComparisonValue(
        SHIPMENT_CORRELATION_EVIDENCE_KEY,
        SHIPMENT_SALES_CORRELATION,
        python_code=correlation_mirror_code("shipment_sales_claim", "association_reveal_shipment"),
        value_format=_bare_pct,
    ),
)
STRONG_ASSOCIATION_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l26.strong_association_reveal.interpret.option.{key}")
    for key in (
        "both_are_strong_real_patterns_worth_investigating",
        "correlations_this_strong_prove_a_causal_mechanism",
        "correlations_this_strong_contain_no_useful_information",
    )
)

# --- Reveal B: "A Strong Alternative Explanation" - two real numbers not
# shown anywhere before: device_group's own correlation with spend, and
# the dark_mode-spend correlation within the modern-device subgroup
# specifically (the only subgroup where dark_mode_enabled actually
# varies - the older-device subgroup has zero variance and its own
# correlation is undefined, never computed or shown). ---------------------

_DARK_MODE_DATASET = generate_dark_mode_data()
_DEVICE_GROUP_SPEND_CORRELATION = compute_device_group_correlation(_DARK_MODE_DATASET, "device_group", "modern", "weekly_spend")

CONFOUNDING_REVEAL_COMPARISONS = (
    ComparisonValue(
        DARK_MODE_OVERALL_CORRELATION_EVIDENCE_KEY,
        DARK_MODE_CORRELATION,
        python_code=correlation_mirror_code("dark_mode_claim", "confounding_reveal_overall"),
        value_format=_bare_pct,
    ),
    ComparisonValue(
        DEVICE_GROUP_SPEND_CORRELATION_EVIDENCE_KEY,
        _DEVICE_GROUP_SPEND_CORRELATION,
        python_code=device_group_correlation_mirror_code("device_group", "modern", "weekly_spend", "confounding_reveal_device_group"),
        value_format=_bare_pct,
    ),
    ComparisonValue(
        DARK_MODE_WITHIN_MODERN_CORRELATION_EVIDENCE_KEY,
        DARK_MODE_WITHIN_MODERN_CORRELATION,
        python_code=correlation_within_mirror_code("device_group", "modern", "dark_mode_enabled", "weekly_spend", "confounding_reveal_within_modern"),
        value_format=_bare_pct,
    ),
)
CONFOUNDING_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l26.confounding_reveal.interpret.option.{key}")
    for key in (
        "device_group_is_a_strong_candidate_explanation_for_the_aggregate_pattern",
        "this_proves_owning_a_modern_device_causes_higher_spend",
        "the_correlation_changing_after_splitting_the_group_doesnt_mean_anything",
    )
)

# --- Final Decision Brief - 4 REASONING fields + 1 CALIBRATION field + Evidence --

WHY_THE_WITHIN_MODERN_COMPARISON_MATTERS_MORE_FIELD = BriefField(
    key="why_the_within_modern_comparison_matters_more",
    prompt_key="lesson.l26.field.why_the_within_modern_comparison_matters_more.prompt",
    options=(
        BriefOption(
            "isolates_whether_dark_mode_relates_to_spend_among_comparable_customers",
            "lesson.l26.option.why_the_within_modern_comparison_matters_more.isolates_whether_dark_mode_relates_to_spend_among_comparable_customers",
        ),
        BriefOption(
            "the_raw_correlation_is_always_the_one_to_trust",
            "lesson.l26.option.why_the_within_modern_comparison_matters_more.the_raw_correlation_is_always_the_one_to_trust",
        ),
        BriefOption(
            "this_proves_dark_mode_has_zero_effect_everywhere",
            "lesson.l26.option.why_the_within_modern_comparison_matters_more.this_proves_dark_mode_has_zero_effect_everywhere",
        ),
    ),
)
WHY_RULING_OUT_REVERSE_CAUSATION_DOESNT_PROVE_DIRECT_FIELD = BriefField(
    key="why_ruling_out_reverse_causation_doesnt_prove_direct",
    prompt_key="lesson.l26.field.why_ruling_out_reverse_causation_doesnt_prove_direct.prompt",
    options=(
        BriefOption(
            "eliminating_one_explanation_narrows_the_space_it_doesnt_confirm_whats_left",
            "lesson.l26.option.why_ruling_out_reverse_causation_doesnt_prove_direct.eliminating_one_explanation_narrows_the_space_it_doesnt_confirm_whats_left",
        ),
        BriefOption(
            "if_reverse_is_impossible_direct_causation_is_the_only_option_left",
            "lesson.l26.option.why_ruling_out_reverse_causation_doesnt_prove_direct.if_reverse_is_impossible_direct_causation_is_the_only_option_left",
        ),
        BriefOption(
            "ruling_out_one_direction_doesnt_actually_tell_you_anything",
            "lesson.l26.option.why_ruling_out_reverse_causation_doesnt_prove_direct.ruling_out_one_direction_doesnt_actually_tell_you_anything",
        ),
    ),
)
WHY_A_STRONG_OBSERVED_CORRELATION_STILL_ISNT_A_NAMED_CAUSE_FIELD = BriefField(
    key="why_a_strong_observed_correlation_still_isnt_a_named_cause",
    prompt_key="lesson.l26.field.why_a_strong_observed_correlation_still_isnt_a_named_cause.prompt",
    options=(
        BriefOption(
            "establishes_a_strong_association_multiple_causal_stories_remain_compatible",
            "lesson.l26.option.why_a_strong_observed_correlation_still_isnt_a_named_cause.establishes_a_strong_association_multiple_causal_stories_remain_compatible",
        ),
        BriefOption(
            "with_a_strong_enough_correlation_the_mechanism_no_longer_matters",
            "lesson.l26.option.why_a_strong_observed_correlation_still_isnt_a_named_cause.with_a_strong_enough_correlation_the_mechanism_no_longer_matters",
        ),
        BriefOption(
            "the_association_is_useless_because_observational_data_can_never_tell_us_anything",
            "lesson.l26.option.why_a_strong_observed_correlation_still_isnt_a_named_cause.the_association_is_useless_because_observational_data_can_never_tell_us_anything",
        ),
    ),
)
NEXT_EVIDENCE_FIELD = BriefField(
    key="next_evidence",
    prompt_key="lesson.l26.field.next_evidence.prompt",
    options=(
        BriefOption("a_randomized_test_or_ruling_out_alternatives", "lesson.l26.option.next_evidence.a_randomized_test_or_ruling_out_alternatives"),
        BriefOption("a_bigger_sample_of_the_same_data", "lesson.l26.option.next_evidence.a_bigger_sample_of_the_same_data"),
        BriefOption("a_more_confident_stakeholder", "lesson.l26.option.next_evidence.a_more_confident_stakeholder"),
    ),
)
STRONGEST_DEFENSIBLE_CLAIM_FIELD = BriefField(
    key="strongest_defensible_claim",
    prompt_key="lesson.l26.field.strongest_defensible_claim.prompt",
    options=(
        BriefOption("a_real_pattern_not_a_proven_cause", "lesson.l26.option.strongest_defensible_claim.a_real_pattern_not_a_proven_cause"),
        BriefOption("direct_causation_confirmed_every_time", "lesson.l26.option.strongest_defensible_claim.direct_causation_confirmed_every_time"),
        BriefOption(
            "correlation_this_strong_still_tells_us_nothing_useful",
            "lesson.l26.option.strongest_defensible_claim.correlation_this_strong_still_tells_us_nothing_useful",
        ),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l26.decision.evidence.prompt", min_count=3, max_count=5)
DECISION_FIELDS: tuple[BriefField, ...] = (
    WHY_THE_WITHIN_MODERN_COMPARISON_MATTERS_MORE_FIELD,
    WHY_RULING_OUT_REVERSE_CAUSATION_DOESNT_PROVE_DIRECT_FIELD,
    WHY_A_STRONG_OBSERVED_CORRELATION_STILL_ISNT_A_NAMED_CAUSE_FIELD,
    NEXT_EVIDENCE_FIELD,
    STRONGEST_DEFENSIBLE_CLAIM_FIELD,
)

# --- Optional mastery: NovaMart loyalty-program LTV dataset, promoted
# unchanged from this lesson's own old mandatory Twist slot (Conflict 2's
# resolution - L27's own spec Twist is this exact story, verbatim; L26's
# own spec Twist is already fully satisfied by the confounding reveal
# above). Copy stays deliberately outcome-only (the student interprets a
# given randomized-test result, never designs one) and avoids "selection
# bias" as a formal term, and never claims a precise percentage
# decomposition of the observational gap - only that the randomized
# estimate is much smaller. ------------------------------------------------

MASTERY_WHAT_THE_OBSERVATIONAL_GAP_REPRESENTS_FIELD = BriefField(
    key="mastery_what_the_observational_gap_represents",
    prompt_key="lesson.l26.mastery.field.what_the_observational_gap_represents.prompt",
    options=(
        BriefOption(
            "overstates_what_the_experiment_attributes_to_the_program",
            "lesson.l26.mastery.option.what_the_observational_gap_represents.overstates_what_the_experiment_attributes_to_the_program",
        ),
        BriefOption(
            "the_observational_gap_is_fully_accurate_the_randomized_test_just_used_fewer_people",
            "lesson.l26.mastery.option.what_the_observational_gap_represents.the_observational_gap_is_fully_accurate_the_randomized_test_just_used_fewer_people",
        ),
        BriefOption(
            "the_two_numbers_measure_the_same_thing_so_it_doesnt_matter_which_you_use",
            "lesson.l26.mastery.option.what_the_observational_gap_represents.the_two_numbers_measure_the_same_thing_so_it_doesnt_matter_which_you_use",
        ),
    ),
)
MASTERY_STRONGEST_CLAIM_FIELD = BriefField(
    key="mastery_strongest_claim",
    prompt_key="lesson.l26.mastery.field.strongest_claim.prompt",
    options=(
        BriefOption(
            "randomized_comparison_supports_a_much_smaller_positive_effect",
            "lesson.l26.mastery.option.strongest_claim.randomized_comparison_supports_a_much_smaller_positive_effect",
        ),
        BriefOption(
            "the_observational_160_dollar_gap_is_the_programs_real_value",
            "lesson.l26.mastery.option.strongest_claim.the_observational_160_dollar_gap_is_the_programs_real_value",
        ),
        BriefOption(
            "the_program_obviously_has_no_useful_effect_at_all",
            "lesson.l26.mastery.option.strongest_claim.the_program_obviously_has_no_useful_effect_at_all",
        ),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l26.mastery.field.evidence.prompt",
    options=(
        BriefOption("observational_gap_160_dollars", "lesson.l26.mastery.option.evidence.observational_gap_160_dollars"),
        BriefOption("randomized_estimate_15_dollars", "lesson.l26.mastery.option.evidence.randomized_estimate_15_dollars"),
        BriefOption("observational_sample_size_10000", "lesson.l26.mastery.option.evidence.observational_sample_size_10000"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_six_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 26's real investigation: three genuinely
    independent real correlations, each narrowing a different subset of
    causal explanations, tested twice - an initial CorrelationScene pass
    (guided=False - a motivated-reasoning trap, not a hidden-information
    one, since the live evidence panel is already real and inspectable
    before commit), two mandatory synthesis reveals (a strong-association
    reveal, a confounding reveal - two genuinely distinct mechanisms),
    then a real revision pass seeded with the first pass's own pick."""
    collected: dict = {}
    context = LessonContext()
    loyalty_data = generate_loyalty_ltv_data()

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
    # hidden-information one: the live evidence panel is already real and
    # inspectable before commit. -------------------------------------------

    def initial_correlation_pass(advance):
        def on_complete(choices):
            collected["initial_verdict_choices"] = choices
            _sync_context_into_collected()
            advance()

        return CorrelationScene(
            app,
            "lesson.l26.investigation_title",
            CORRELATION_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            mirror_python_code_for=_mirror_python_code_for,
        )

    # --- Two mandatory reveals - shown to every student regardless of
    # path. Each names a genuinely distinct mechanism. --------------------

    def strong_association_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_strong_association_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l26.strong_association_reveal.title",
            narrative_keys=("dialogue.l26_strong_association_reveal.line1", "dialogue.l26_strong_association_reveal.line2"),
            comparisons=STRONG_ASSOCIATION_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l26.strong_association_reveal.interpret_prompt",
            interpret_options=STRONG_ASSOCIATION_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def confounding_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_confounding_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l26.confounding_reveal.title",
            narrative_keys=("dialogue.l26_confounding_reveal.line1", "dialogue.l26_confounding_reveal.line2"),
            comparisons=CONFOUNDING_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l26.confounding_reveal.interpret_prompt",
            interpret_options=CONFOUNDING_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Revision intro + a real revision pass, seeded with the first
    # pass's own pick. -----------------------------------------------------

    def revision_intro(advance):
        return DialogueScene(app, REVISION_INTRO_DIALOGUE, on_complete=advance)

    def revision_correlation_pass(advance):
        def on_complete(choices):
            collected["verdict_choices"] = choices
            _sync_context_into_collected()
            advance()

        return CorrelationScene(
            app,
            "lesson.l26.investigation_title",
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
            "lesson.l26.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l26.mastery.title",
                (MASTERY_WHAT_THE_OBSERVATIONAL_GAP_REPRESENTS_FIELD, MASTERY_STRONGEST_CLAIM_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l26.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonTwentySixResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentySixResult(
            initial_verdict_choices=collected.get("initial_verdict_choices", {}),
            verdict_choices=collected.get("verdict_choices", {}),
            reveal_strong_association_interpretation=collected.get("reveal_strong_association_interpretation"),
            reveal_confounding_interpretation=collected.get("reveal_confounding_interpretation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_26.number, 0)
        evaluation = score_lesson_twenty_six(result, LESSON_26, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        initial_correlation_pass,
        strong_association_reveal,
        confounding_reveal,
        revision_intro,
        revision_correlation_pass,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=26,
        collected=collected,
        definition=LESSON_26,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

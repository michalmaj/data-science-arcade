from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l21_funnel_factory import checkout_events as d
from data_science_arcade.lessons.l21_funnel_factory.definition import LESSON_21
from data_science_arcade.lessons.l21_funnel_factory.requests import (
    COMPLETE_CART_TRACKING,
    FUNNEL_REQUESTS,
    LEGACY_CART_TRACKING,
    PERCENT_OF_PREVIOUS_STEP,
    PERCENT_OF_TOTAL_VISITS,
    RAW_CART_EVENTS,
)
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
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.funnel_builder_scene import FunnelBuilderScene
from data_science_arcade.ui.funnel_chart import step_percent_of_previous, step_percent_of_top
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l21_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l21_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l21_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l21_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l21_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l21_investigation.line3"),
    )
)

INSTRUMENTATION_EXPLANATION_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l21_instrumentation.line1"),)
)

REVISION_INTRO_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l21_revision_intro.line1"),))

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l21_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l21_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l21_debrief.line3"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l21_mastery.line1",
    "dialogue.l21_mastery.line2",
    "dialogue.l21_mastery.line3",
)

# --- Two mandatory reveals - fixed, independent reference definitions,
# never the student's own picks (same canonical-substitution discipline
# as L18-L20: distinct variable names, zero dependency on prior state). -


def _pct1(value: float) -> str:
    return f"{value:.1f}%"


def _step_index(definition, step_key: str) -> int:
    return next(i for i, step in enumerate(definition.steps) if step.key == step_key)


def _previous_pct(definition, step_key: str) -> float:
    return step_percent_of_previous(definition.steps, _step_index(definition, step_key)) * 100


def _top_pct(definition, step_key: str) -> float:
    return step_percent_of_top(definition.steps, _step_index(definition, step_key)) * 100


DEFINITION_AXIS_COMPARISONS = (
    ComparisonValue(
        DEFINITION_CHECK_LEGACY_EVIDENCE_KEY,
        _previous_pct(LEGACY_CART_TRACKING, "add_to_cart"),
        python_code=d.funnel_mirror_code(LEGACY_CART_TRACKING, "definition_check_legacy"),
        value_format=_pct1,
    ),
    ComparisonValue(
        DEFINITION_CHECK_COMPLETE_EVIDENCE_KEY,
        _previous_pct(COMPLETE_CART_TRACKING, "add_to_cart"),
        python_code=d.funnel_mirror_code(COMPLETE_CART_TRACKING, "definition_check_complete"),
        value_format=_pct1,
    ),
    ComparisonValue(
        DEFINITION_CHECK_RAW_EVIDENCE_KEY,
        _previous_pct(RAW_CART_EVENTS, "add_to_cart"),
        python_code=d.funnel_mirror_code(RAW_CART_EVENTS, "definition_check_raw"),
        value_format=_pct1,
    ),
)
DEFINITION_AXIS_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l21.definition_axis_reveal.interpret.option.{key}")
    for key in (
        "same_step_can_look_broken_plausible_or_excellent_by_definition",
        "any_definition_is_equally_valid",
        "pick_whichever_definition_sounds_most_complete",
    )
)

BASIS_AXIS_COMPARISONS = (
    ComparisonValue(
        BASIS_CHECK_TOP_EVIDENCE_KEY,
        _top_pct(PERCENT_OF_TOTAL_VISITS, "checkout_started"),
        python_code=d.funnel_mirror_code(PERCENT_OF_TOTAL_VISITS, "basis_check_top"),
        value_format=_pct1,
    ),
    ComparisonValue(
        BASIS_CHECK_PREVIOUS_EVIDENCE_KEY,
        _previous_pct(PERCENT_OF_PREVIOUS_STEP, "checkout_started"),
        python_code=d.funnel_mirror_code(PERCENT_OF_PREVIOUS_STEP, "basis_check_previous"),
        value_format=_pct1,
    ),
    ComparisonValue(
        LOCAL_ADD_TO_CART_EVIDENCE_KEY,
        _previous_pct(PERCENT_OF_PREVIOUS_STEP, "add_to_cart"),
        python_code="# add_to_cart's own row, already computed above by basis_check_previous",
        value_format=_pct1,
    ),
    ComparisonValue(
        LOCAL_ORDER_CONFIRMED_EVIDENCE_KEY,
        _previous_pct(PERCENT_OF_PREVIOUS_STEP, "order_confirmed"),
        python_code="# order_confirmed's own row, already computed above by basis_check_previous",
        value_format=_pct1,
    ),
)
BASIS_AXIS_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l21.basis_axis_reveal.interpret.option.{key}")
    for key in (
        "top_shows_cumulative_survival_previous_finds_the_local_loss",
        "more_definitions_tested_means_more_accurate",
        "percent_of_top_is_always_the_more_honest_number",
    )
)

# --- Final Decision Brief - 4 fields + Evidence --------------------------

INVESTIGATION_CONCLUSION_FIELD = BriefField(
    key="checkout_investigation_conclusion",
    prompt_key="lesson.l21.field.checkout_investigation_conclusion.prompt",
    hint_key="lesson.l21.field.checkout_investigation_conclusion.hint",
    options=(
        BriefOption("blame_product_page", "lesson.l21.option.checkout_investigation_conclusion.blame_product_page"),
        BriefOption("blame_cart_to_checkout_step", "lesson.l21.option.checkout_investigation_conclusion.blame_cart_to_checkout_step"),
        BriefOption("blame_payment_step", "lesson.l21.option.checkout_investigation_conclusion.blame_payment_step"),
    ),
)
WHY_LEGACY_UNDERCOUNTS_FIELD = BriefField(
    key="why_legacy_undercounts",
    prompt_key="lesson.l21.field.why_legacy_undercounts.prompt",
    options=(
        BriefOption("tracking_pixel_missing_on_newer_app_builds", "lesson.l21.option.why_legacy_undercounts.tracking_pixel_missing_on_newer_app_builds"),
        BriefOption("customers_really_added_to_cart_less", "lesson.l21.option.why_legacy_undercounts.customers_really_added_to_cart_less"),
        BriefOption("the_newer_app_itself_is_broken", "lesson.l21.option.why_legacy_undercounts.the_newer_app_itself_is_broken"),
    ),
)
PERCENT_BASIS_QUESTION_FIELD = BriefField(
    key="percent_basis_question",
    prompt_key="lesson.l21.field.percent_basis_question.prompt",
    options=(
        BriefOption("finds_the_step_thats_uniquely_bad_locally", "lesson.l21.option.percent_basis_question.finds_the_step_thats_uniquely_bad_locally"),
        BriefOption("always_more_accurate", "lesson.l21.option.percent_basis_question.always_more_accurate"),
        BriefOption("shows_overall_funnel_health", "lesson.l21.option.percent_basis_question.shows_overall_funnel_health"),
    ),
)
GENERAL_LESSON_FIELD = BriefField(
    key="general_lesson",
    prompt_key="lesson.l21.field.general_lesson.prompt",
    options=(
        BriefOption("any_definition_is_equally_valid", "lesson.l21.option.general_lesson.any_definition_is_equally_valid"),
        BriefOption("more_definitions_tested_means_more_accurate", "lesson.l21.option.general_lesson.more_definitions_tested_means_more_accurate"),
        BriefOption("justify_definition_independent_of_result", "lesson.l21.option.general_lesson.justify_definition_independent_of_result"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l21.decision.evidence.prompt", min_count=5, max_count=8)
DECISION_FIELDS: tuple[BriefField, ...] = (
    INVESTIGATION_CONCLUSION_FIELD,
    WHY_LEGACY_UNDERCOUNTS_FIELD,
    PERCENT_BASIS_QUESTION_FIELD,
    GENERAL_LESSON_FIELD,
)

# --- Optional mastery: NovaMart app onboarding funnel, a different domain

MASTERY_REAL_BOTTLENECK_FIELD = BriefField(
    key="mastery_real_bottleneck",
    prompt_key="lesson.l21.mastery.field.real_bottleneck.prompt",
    options=(
        BriefOption("signup", "lesson.l21.mastery.option.real_bottleneck.signup"),
        BriefOption("profile_completed", "lesson.l21.mastery.option.real_bottleneck.profile_completed"),
        BriefOption("app_install", "lesson.l21.mastery.option.real_bottleneck.app_install"),
    ),
)
MASTERY_WHY_MISSED_FIELD = BriefField(
    key="mastery_why_missed",
    prompt_key="lesson.l21.mastery.field.why_missed.prompt",
    options=(
        BriefOption(
            "the_flawed_signup_event_made_a_healthy_step_look_broken_hiding_the_real_one",
            "lesson.l21.mastery.option.why_missed.the_flawed_signup_event_made_a_healthy_step_look_broken_hiding_the_real_one",
        ),
        BriefOption("profile_completion_is_always_low", "lesson.l21.mastery.option.why_missed.profile_completion_is_always_low"),
        BriefOption("not_enough_data", "lesson.l21.mastery.option.why_missed.not_enough_data"),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l21.mastery.field.evidence.prompt",
    options=(
        BriefOption("flawed_signup_rate_35_vs_correct_81_percent", "lesson.l21.mastery.option.evidence.flawed_signup_rate_35_vs_correct_81_percent"),
        BriefOption("profile_completion_real_rate_42_percent", "lesson.l21.mastery.option.evidence.profile_completion_real_rate_42_percent"),
        BriefOption("app_install_count_was_5000", "lesson.l21.mastery.option.evidence.app_install_count_was_5000"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_one_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 21's real investigation: one continuous NovaMart
    checkout-funnel case, defended along two independent axes (what
    counts as reaching a step; what denominator a conversion rate answers
    against). An initial FunnelBuilderScene pass (guided=False - a
    motivated-reasoning trap, not a hidden-information one) is followed by
    two mandatory synthesis reveals, then a real revision pass seeded with
    the first pass's own picks - a student's own initial motivated read
    becomes something they can act on, never something that permanently
    caps METHOD."""
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

    def instrumentation_explanation(advance):
        def on_complete():
            _sync_context_into_collected()
            advance()

        return DialogueScene(
            app,
            INSTRUMENTATION_EXPLANATION_DIALOGUE,
            on_complete=on_complete,
            context=context,
            record_label_key="lesson.l21.instrumentation.action_label",
            record_evidence_key=INSTRUMENTATION_GAP_EVIDENCE_KEY,
            record_key="instrumentation_gap",
        )

    # --- Initial funnel pass - a motivated-reasoning trap, not a hidden-
    # information one: every candidate chart is already fully real and
    # inspectable before commit. ------------------------------------------

    def initial_funnel_pass(advance):
        def on_complete(choices):
            collected["initial_funnel_choices"] = choices
            _sync_context_into_collected()
            advance()

        return FunnelBuilderScene(
            app,
            "lesson.l21.builder_title",
            FUNNEL_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            mirror_python_code_for=d.funnel_mirror_code,
        )

    # --- Two mandatory reveals - shown to every student regardless of path

    def definition_axis_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_a_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l21.definition_axis_reveal.title",
            narrative_keys=("dialogue.l21_definition_axis_reveal.line1",),
            comparisons=DEFINITION_AXIS_COMPARISONS,
            interpret_prompt_key="lesson.l21.definition_axis_reveal.interpret_prompt",
            interpret_options=DEFINITION_AXIS_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def basis_axis_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_b_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l21.basis_axis_reveal.title",
            narrative_keys=("dialogue.l21_basis_axis_reveal.line1",),
            comparisons=BASIS_AXIS_COMPARISONS,
            interpret_prompt_key="lesson.l21.basis_axis_reveal.interpret_prompt",
            interpret_options=BASIS_AXIS_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Revision intro + a real revision pass, seeded with the first
    # pass's own picks. -----------------------------------------------------

    def revision_intro(advance):
        return DialogueScene(app, REVISION_INTRO_DIALOGUE, on_complete=advance)

    def revision_funnel_pass(advance):
        def on_complete(choices):
            collected["funnel_choices"] = choices
            _sync_context_into_collected()
            advance()

        return FunnelBuilderScene(
            app,
            "lesson.l21.builder_title",
            FUNNEL_REQUESTS,
            on_complete,
            guided=False,
            context=context,
            initial_choices=collected.get("initial_funnel_choices"),
            mirror_python_code_for=d.funnel_mirror_code,
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
            "lesson.l21.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l21.mastery.title",
                (MASTERY_REAL_BOTTLENECK_FIELD, MASTERY_WHY_MISSED_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l21.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonTwentyOneResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentyOneResult(
            initial_funnel_choices=collected.get("initial_funnel_choices", {}),
            funnel_choices=collected.get("funnel_choices", {}),
            reveal_a_interpretation=collected.get("reveal_a_interpretation"),
            reveal_b_interpretation=collected.get("reveal_b_interpretation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_21.number, 0)
        evaluation = score_lesson_twenty_one(result, LESSON_21, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        instrumentation_explanation,
        initial_funnel_pass,
        definition_axis_reveal,
        basis_axis_reveal,
        revision_intro,
        revision_funnel_pass,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=21,
        collected=collected,
        definition=LESSON_21,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

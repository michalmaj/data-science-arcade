from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l24_survey_bureau.definition import LESSON_24
from data_science_arcade.lessons.l24_survey_bureau.population_data import (
    RESPONSE_RATE_BY_SEGMENT,
    generate_population_data,
    response_rate_mirror_code,
    simulate_survey,
    survey_mean_mirror_code,
    survey_reach_count_mirror_code,
)
from data_science_arcade.lessons.l24_survey_bureau.requests import BROAD_EMAIL, IN_APP_POPUP, NEUTRAL_WORDING, POWER_USER_PANEL, SURVEY_REQUESTS
from data_science_arcade.lessons.l24_survey_bureau.scoring import (
    BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    IN_APP_POPUP_EXCLUDED_CHURNED_COUNT_EVIDENCE_KEY,
    IN_APP_POPUP_NEUTRAL_MEAN_EVIDENCE_KEY,
    LessonTwentyFourResult,
    POWER_USER_PANEL_CRITIC_COUNT_EVIDENCE_KEY,
    POWER_USER_PANEL_NEUTRAL_MEAN_EVIDENCE_KEY,
    QUIET_MAJORITY_RESPONSE_RATE_EVIDENCE_KEY,
    VOCAL_CRITIC_RESPONSE_RATE_EVIDENCE_KEY,
    VOCAL_FAN_RESPONSE_RATE_EVIDENCE_KEY,
    score_lesson_twenty_four,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.survey_builder_scene import SurveyBuilderScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l24_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l24_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_investigation.line2"),
    )
)

REVISION_INTRO_DIALOGUE = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l24_revision_intro.line1"),))

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l24_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_debrief.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_debrief.line4"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l24_mastery.line1",
    "dialogue.l24_mastery.line2",
    "dialogue.l24_mastery.line3",
)

# --- Three mandatory reveals - fixed, real reference values computed from
# the same NovaMart price-change population. Zero InterpretOption.
# evidence_key anywhere: a student who picks the WRONG interpretation
# still saw the exact same real numbers and can cite them later. ---------

_POPULATION_DATASET = generate_population_data()


def _pct0(value: float) -> str:
    return f"{value:.0%}"


def _bare_int(value: float) -> str:
    return f"{value:.0f}"


_BROAD_EMAIL_NEUTRAL_MEAN = simulate_survey(_POPULATION_DATASET, BROAD_EMAIL, NEUTRAL_WORDING)[1]
_IN_APP_POPUP_NEUTRAL_MEAN = simulate_survey(_POPULATION_DATASET, IN_APP_POPUP, NEUTRAL_WORDING)[1]
_POWER_USER_PANEL_NEUTRAL_MEAN = simulate_survey(_POPULATION_DATASET, POWER_USER_PANEL, NEUTRAL_WORDING)[1]

COVERAGE_BIAS_REVEAL_COMPARISONS = (
    ComparisonValue(
        BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY,
        _BROAD_EMAIL_NEUTRAL_MEAN,
        python_code=survey_mean_mirror_code(BROAD_EMAIL, NEUTRAL_WORDING, "coverage_reveal_broad_email"),
        value_format=_pct0,
    ),
    ComparisonValue(
        IN_APP_POPUP_NEUTRAL_MEAN_EVIDENCE_KEY,
        _IN_APP_POPUP_NEUTRAL_MEAN,
        python_code=survey_mean_mirror_code(IN_APP_POPUP, NEUTRAL_WORDING, "coverage_reveal_in_app_popup"),
        value_format=_pct0,
    ),
    ComparisonValue(
        IN_APP_POPUP_EXCLUDED_CHURNED_COUNT_EVIDENCE_KEY,
        27.0,
        python_code=survey_reach_count_mirror_code("vocal_critic", "still_active == False", "coverage_reveal_excluded_count"),
        value_format=_bare_int,
    ),
)
COVERAGE_BIAS_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l24.coverage_bias_reveal.interpret.option.{key}")
    for key in (
        "in_app_popup_excludes_already_churned_critics",
        "in_app_popup_proves_users_are_happier",
        "channels_are_basically_the_same_just_noise",
    )
)

SAMPLING_FRAME_REVEAL_COMPARISONS = (
    ComparisonValue(
        BROAD_EMAIL_NEUTRAL_MEAN_EVIDENCE_KEY,
        _BROAD_EMAIL_NEUTRAL_MEAN,
        python_code=survey_mean_mirror_code(BROAD_EMAIL, NEUTRAL_WORDING, "sampling_frame_reveal_broad_email"),
        value_format=_pct0,
    ),
    ComparisonValue(
        POWER_USER_PANEL_NEUTRAL_MEAN_EVIDENCE_KEY,
        _POWER_USER_PANEL_NEUTRAL_MEAN,
        python_code=survey_mean_mirror_code(POWER_USER_PANEL, NEUTRAL_WORDING, "sampling_frame_reveal_power_panel"),
        value_format=_pct0,
    ),
    ComparisonValue(
        POWER_USER_PANEL_CRITIC_COUNT_EVIDENCE_KEY,
        0.0,
        python_code=survey_reach_count_mirror_code("vocal_critic", "is_power_user == True", "sampling_frame_reveal_critic_count"),
        value_format=_bare_int,
    ),
)
SAMPLING_FRAME_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l24.sampling_frame_reveal.interpret.option.{key}")
    for key in (
        "panel_sampling_frame_excludes_critics_entirely",
        "power_users_know_product_best_so_83_is_trustworthy",
        "panel_too_small_to_tell_us_anything",
    )
)

NONRESPONSE_BIAS_REVEAL_COMPARISONS = (
    ComparisonValue(
        VOCAL_CRITIC_RESPONSE_RATE_EVIDENCE_KEY,
        RESPONSE_RATE_BY_SEGMENT["vocal_critic"],
        python_code=response_rate_mirror_code("vocal_critic", "nonresponse_reveal_critic_rate"),
        value_format=_pct0,
    ),
    ComparisonValue(
        VOCAL_FAN_RESPONSE_RATE_EVIDENCE_KEY,
        RESPONSE_RATE_BY_SEGMENT["vocal_fan"],
        python_code=response_rate_mirror_code("vocal_fan", "nonresponse_reveal_fan_rate"),
        value_format=_pct0,
    ),
    ComparisonValue(
        QUIET_MAJORITY_RESPONSE_RATE_EVIDENCE_KEY,
        RESPONSE_RATE_BY_SEGMENT["quiet_majority"],
        python_code=response_rate_mirror_code("quiet_majority", "nonresponse_reveal_majority_rate"),
        value_format=_pct0,
    ),
)
NONRESPONSE_BIAS_REVEAL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l24.nonresponse_bias_reveal.interpret.option.{key}")
    for key in (
        "response_rates_differ_sharply_never_a_random_cross_section",
        "since_everyone_could_respond_the_mix_must_match_the_population",
        "response_rate_differences_only_matter_if_wording_is_biased",
    )
)

# --- Final Decision Brief - 4 fields + Evidence --------------------------

WHY_IN_APP_POPUP_MISLEADS_FIELD = BriefField(
    key="why_in_app_popup_misleads",
    prompt_key="lesson.l24.field.why_in_app_popup_misleads.prompt",
    options=(
        BriefOption("excludes_customers_who_already_churned", "lesson.l24.option.why_in_app_popup_misleads.excludes_customers_who_already_churned"),
        BriefOption("too_few_respondents", "lesson.l24.option.why_in_app_popup_misleads.too_few_respondents"),
        BriefOption("uses_leading_wording", "lesson.l24.option.why_in_app_popup_misleads.uses_leading_wording"),
    ),
)
WHY_POWER_USER_PANEL_MISLEADS_FIELD = BriefField(
    key="why_power_user_panel_misleads",
    prompt_key="lesson.l24.field.why_power_user_panel_misleads.prompt",
    options=(
        BriefOption(
            "sampling_frame_excludes_critics_entirely", "lesson.l24.option.why_power_user_panel_misleads.sampling_frame_excludes_critics_entirely"
        ),
        BriefOption("panel_too_small_to_matter", "lesson.l24.option.why_power_user_panel_misleads.panel_too_small_to_matter"),
        BriefOption("power_users_dont_understand_the_survey", "lesson.l24.option.why_power_user_panel_misleads.power_users_dont_understand_the_survey"),
    ),
)
WHY_LEADING_WORDING_DISTORTS_FIELD = BriefField(
    key="why_leading_wording_distorts",
    prompt_key="lesson.l24.field.why_leading_wording_distorts.prompt",
    options=(
        BriefOption(
            "systematically_pushes_satisfaction_upward_never_fixes_reach_or_response",
            "lesson.l24.option.why_leading_wording_distorts.systematically_pushes_satisfaction_upward_never_fixes_reach_or_response",
        ),
        BriefOption("only_affects_undecided_respondents", "lesson.l24.option.why_leading_wording_distorts.only_affects_undecided_respondents"),
        BriefOption("only_matters_for_broad_email", "lesson.l24.option.why_leading_wording_distorts.only_matters_for_broad_email"),
    ),
)
WHAT_BROAD_EMAIL_NEUTRAL_STILL_CANT_FIX_FIELD = BriefField(
    key="what_broad_email_neutral_still_cant_fix",
    prompt_key="lesson.l24.field.what_broad_email_neutral_still_cant_fix.prompt",
    options=(
        BriefOption(
            "who_actually_responds_can_still_be_uneven_even_with_full_reach_and_neutral_wording",
            "lesson.l24.option.what_broad_email_neutral_still_cant_fix.who_actually_responds_can_still_be_uneven_even_with_full_reach_and_neutral_wording",
        ),
        BriefOption(
            "broad_email_neutral_is_fully_representative", "lesson.l24.option.what_broad_email_neutral_still_cant_fix.broad_email_neutral_is_fully_representative"
        ),
        BriefOption(
            "nothing_more_can_ever_be_known_once_optimized",
            "lesson.l24.option.what_broad_email_neutral_still_cant_fix.nothing_more_can_ever_be_known_once_optimized",
        ),
    ),
)
STRONGEST_DEFENSIBLE_CLAIM_FIELD = BriefField(
    key="strongest_defensible_claim",
    prompt_key="lesson.l24.field.strongest_defensible_claim.prompt",
    options=(
        BriefOption(
            "most_defensible_design_but_still_a_signal_not_proof_of_everyone",
            "lesson.l24.option.strongest_defensible_claim.most_defensible_design_but_still_a_signal_not_proof_of_everyone",
        ),
        BriefOption("accurately_represents_all_customers", "lesson.l24.option.strongest_defensible_claim.accurately_represents_all_customers"),
        BriefOption("tells_us_nothing_useful", "lesson.l24.option.strongest_defensible_claim.tells_us_nothing_useful"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l24.decision.evidence.prompt", min_count=3, max_count=8)
DECISION_FIELDS: tuple[BriefField, ...] = (
    WHY_IN_APP_POPUP_MISLEADS_FIELD,
    WHY_POWER_USER_PANEL_MISLEADS_FIELD,
    WHY_LEADING_WORDING_DISTORTS_FIELD,
    WHAT_BROAD_EMAIL_NEUTRAL_STILL_CANT_FIX_FIELD,
    STRONGEST_DEFENSIBLE_CLAIM_FIELD,
)

# --- Optional mastery: NovaMart delivery-survey coverage exclusion, a
# different domain reproducing the same coverage-bias mechanism. ---------

MASTERY_WHAT_88_PERCENT_REPRESENTS_FIELD = BriefField(
    key="mastery_what_88_percent_represents",
    prompt_key="lesson.l24.mastery.field.what_88_percent_represents.prompt",
    options=(
        BriefOption("only_customers_whose_delivery_succeeded", "lesson.l24.mastery.option.what_88_percent_represents.only_customers_whose_delivery_succeeded"),
        BriefOption(
            "a_random_15_percent_sample_was_excluded_for_cost", "lesson.l24.mastery.option.what_88_percent_represents.a_random_15_percent_sample_was_excluded_for_cost"
        ),
        BriefOption("everyone_was_surveyed_equally", "lesson.l24.mastery.option.what_88_percent_represents.everyone_was_surveyed_equally"),
    ),
)
MASTERY_WHY_BLENDED_IS_LOWER_FIELD = BriefField(
    key="mastery_why_blended_is_lower",
    prompt_key="lesson.l24.mastery.field.why_blended_is_lower.prompt",
    options=(
        BriefOption(
            "never_surveyed_group_has_a_separate_source_estimate", "lesson.l24.mastery.option.why_blended_is_lower.never_surveyed_group_has_a_separate_source_estimate"
        ),
        BriefOption("its_a_rounding_artifact", "lesson.l24.mastery.option.why_blended_is_lower.its_a_rounding_artifact"),
        BriefOption("the_blended_number_is_simply_wrong", "lesson.l24.mastery.option.why_blended_is_lower.the_blended_number_is_simply_wrong"),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l24.mastery.field.evidence.prompt",
    options=(
        BriefOption("delivery_succeeded_surveyed_88_percent", "lesson.l24.mastery.option.evidence.delivery_succeeded_surveyed_88_percent"),
        BriefOption(
            "delivery_failed_or_delayed_separate_source_20_percent", "lesson.l24.mastery.option.evidence.delivery_failed_or_delayed_separate_source_20_percent"
        ),
        BriefOption("blended_provided_estimate_77_8_percent", "lesson.l24.mastery.option.evidence.blended_provided_estimate_77_8_percent"),
    ),
    min_count=2,
    max_count=2,
)


def build_lesson_twenty_four_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 24's real investigation: one continuous NovaMart
    price-change satisfaction survey, one real decision (which wording +
    channel combo defends the satisfaction claim), tested twice - an
    initial SurveyBuilderScene pass (guided=False - a motivated-reasoning
    trap, not a hidden-information one), three mandatory synthesis
    reveals (coverage bias, sampling frame bias, nonresponse bias - three
    genuinely distinct mechanisms, never compressed into one), then a
    real revision pass seeded with the first pass's own pick."""
    collected: dict = {}
    context = LessonContext()
    population = _POPULATION_DATASET

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

    # --- Initial survey pass - a motivated-reasoning trap, not a hidden-
    # information one: the live result preview is already real and
    # inspectable before commit. --------------------------------------

    def initial_survey_pass(advance):
        def on_complete(choices):
            collected["initial_survey_choices"] = choices
            _sync_context_into_collected()
            advance()

        return SurveyBuilderScene(
            app,
            "lesson.l24.builder_title",
            population,
            SURVEY_REQUESTS,
            simulate_survey,
            on_complete,
            guided=False,
            context=context,
            mirror_python_code_for=survey_mean_mirror_code,
        )

    # --- Three mandatory reveals - shown to every student regardless of
    # path. Each names a genuinely distinct mechanism. ------------------

    def coverage_bias_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_coverage_bias_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l24.coverage_bias_reveal.title",
            narrative_keys=("dialogue.l24_coverage_bias_reveal.line1", "dialogue.l24_coverage_bias_reveal.line2"),
            comparisons=COVERAGE_BIAS_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l24.coverage_bias_reveal.interpret_prompt",
            interpret_options=COVERAGE_BIAS_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def sampling_frame_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_sampling_frame_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l24.sampling_frame_reveal.title",
            narrative_keys=("dialogue.l24_sampling_frame_reveal.line1",),
            comparisons=SAMPLING_FRAME_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l24.sampling_frame_reveal.interpret_prompt",
            interpret_options=SAMPLING_FRAME_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    def nonresponse_bias_reveal(advance):
        def on_complete(interpretation):
            collected["reveal_nonresponse_bias_interpretation"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l24.nonresponse_bias_reveal.title",
            narrative_keys=("dialogue.l24_nonresponse_bias_reveal.line1", "dialogue.l24_nonresponse_bias_reveal.line2"),
            comparisons=NONRESPONSE_BIAS_REVEAL_COMPARISONS,
            interpret_prompt_key="lesson.l24.nonresponse_bias_reveal.interpret_prompt",
            interpret_options=NONRESPONSE_BIAS_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=True,
        )

    # --- Revision intro + a real revision pass, seeded with the first
    # pass's own pick. -----------------------------------------------------

    def revision_intro(advance):
        return DialogueScene(app, REVISION_INTRO_DIALOGUE, on_complete=advance)

    def revision_survey_pass(advance):
        def on_complete(choices):
            collected["survey_choices"] = choices
            _sync_context_into_collected()
            advance()

        return SurveyBuilderScene(
            app,
            "lesson.l24.builder_title",
            population,
            SURVEY_REQUESTS,
            simulate_survey,
            on_complete,
            guided=False,
            context=context,
            initial_choices=collected.get("initial_survey_choices"),
            mirror_python_code_for=survey_mean_mirror_code,
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
            "lesson.l24.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l24.mastery.title",
                (MASTERY_WHAT_88_PERCENT_REPRESENTS_FIELD, MASTERY_WHY_BLENDED_IS_LOWER_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l24.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

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

    def _build_result() -> LessonTwentyFourResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentyFourResult(
            initial_survey_choices=collected.get("initial_survey_choices", {}),
            survey_choices=collected.get("survey_choices", {}),
            reveal_coverage_bias_interpretation=collected.get("reveal_coverage_bias_interpretation"),
            reveal_sampling_frame_interpretation=collected.get("reveal_sampling_frame_interpretation"),
            reveal_nonresponse_bias_interpretation=collected.get("reveal_nonresponse_bias_interpretation"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_24.number, 0)
        evaluation = score_lesson_twenty_four(result, LESSON_24, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        investigation,
        initial_survey_pass,
        coverage_bias_reveal,
        sampling_frame_reveal,
        nonresponse_bias_reveal,
        revision_intro,
        revision_survey_pass,
        final_decision_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=24,
        collected=collected,
        definition=LESSON_24,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

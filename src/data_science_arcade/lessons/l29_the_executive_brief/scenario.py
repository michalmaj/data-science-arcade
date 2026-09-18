from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l29_the_executive_brief.definition import LESSON_29
from data_science_arcade.lessons.l29_the_executive_brief.findings import FINDINGS_POOL, SHORTLIST_TARGET_COUNT
from data_science_arcade.lessons.l29_the_executive_brief.scoring import LessonTwentyNineResult, score_lesson_twenty_nine
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.finding_picker_scene import FindingPickerScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask - the stated decision is explicit and fixed for the whole
# lesson: should NovaMart keep the checkout redesign in production, and
# what should leadership monitor next? Every field below is scored
# against THIS decision, never an implicit "brief the redesign" mandate. --

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l29_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l29_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_investigation.line3"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l29_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l29_debrief.line3"),
    )
)

MASTERY_DIALOGUE_KEYS = (
    "dialogue.l29_mastery.line1",
    "dialogue.l29_mastery.line2",
    "dialogue.l29_mastery.line3",
)

# --- Final Decision Brief - EvidenceField (Cut 2's own 5->3 citation)
# first, then 5 BriefFields. lead_finding/supporting_chart come right
# after the citation step so supporting_chart's own consistency check
# (scoring.py's CHART_FINDING_BY_OPTION) reads a lead the student has
# already committed to. ---------------------------------------------------

DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l29.decision.evidence.prompt", min_count=3, max_count=3)

LEAD_FINDING_FIELD = BriefField(
    key="lead_finding",
    prompt_key="lesson.l29.field.lead_finding.prompt",
    hint_key="lesson.l29.field.lead_finding.hint",
    options=(
        BriefOption("checkout_completion", "lesson.l29.option.lead_finding.checkout_completion"),
        BriefOption("payment_step_abandonment", "lesson.l29.option.lead_finding.payment_step_abandonment"),
        BriefOption("order_value_and_returns_steady", "lesson.l29.option.lead_finding.order_value_and_returns_steady"),
    ),
)
SUPPORTING_CHART_FIELD = BriefField(
    key="supporting_chart",
    prompt_key="lesson.l29.field.supporting_chart.prompt",
    hint_key="lesson.l29.field.supporting_chart.hint",
    options=(
        BriefOption("checkout_completion_over_time", "lesson.l29.option.supporting_chart.checkout_completion_over_time"),
        BriefOption("payment_step_abandonment_over_time", "lesson.l29.option.supporting_chart.payment_step_abandonment_over_time"),
        BriefOption(
            "order_value_and_returns_steady_over_time", "lesson.l29.option.supporting_chart.order_value_and_returns_steady_over_time"
        ),
        BriefOption("social_mentions_over_time", "lesson.l29.option.supporting_chart.social_mentions_over_time"),
        BriefOption("stock_price_over_time", "lesson.l29.option.supporting_chart.stock_price_over_time"),
    ),
)
CONFIDENCE_LEVEL_FIELD = BriefField(
    key="confidence_level",
    prompt_key="lesson.l29.field.confidence_level.prompt",
    hint_key="lesson.l29.field.confidence_level.hint",
    options=(
        BriefOption("very_high_a_clear_triumph", "lesson.l29.option.confidence_level.very_high_a_clear_triumph"),
        BriefOption("high_sustained_with_consistent_evidence", "lesson.l29.option.confidence_level.high_sustained_with_consistent_evidence"),
        BriefOption("low_could_be_noise", "lesson.l29.option.confidence_level.low_could_be_noise"),
    ),
)
RECOMMENDATION_FIELD = BriefField(
    key="recommendation",
    prompt_key="lesson.l29.field.recommendation.prompt",
    hint_key="lesson.l29.field.recommendation.hint",
    options=(
        BriefOption("revert_immediately", "lesson.l29.option.recommendation.revert_immediately"),
        BriefOption("keep_and_monitor_returns", "lesson.l29.option.recommendation.keep_and_monitor_returns"),
        BriefOption("expand_everywhere_no_monitoring", "lesson.l29.option.recommendation.expand_everywhere_no_monitoring"),
    ),
)
CAVEATS_FIELD = BriefField(
    key="caveats",
    prompt_key="lesson.l29.field.caveats.prompt",
    hint_key="lesson.l29.field.caveats.hint",
    options=(
        BriefOption("sample_size_was_tiny", "lesson.l29.option.caveats.sample_size_was_tiny"),
        BriefOption("competitor_redesigned_too", "lesson.l29.option.caveats.competitor_redesigned_too"),
        BriefOption("leadership_might_not_like_it", "lesson.l29.option.caveats.leadership_might_not_like_it"),
    ),
)
DECISION_FIELDS: tuple[BriefField, ...] = (
    LEAD_FINDING_FIELD,
    SUPPORTING_CHART_FIELD,
    CONFIDENCE_LEVEL_FIELD,
    RECOMMENDATION_FIELD,
    CAVEATS_FIELD,
)

# --- Optional mastery: the former Twist dataset (app_downloads vs.
# session_length_minutes), promoted wholesale - real, unused once removed
# from the main flow, same "dramatic-but-unconnected vs. modest-but-
# relevant" shape in a new domain. Static, pre-verified label text,
# matching every sibling lesson's own mastery precedent (never a live
# Dataset call inside the mastery scene itself). ---------------------------

MASTERY_WHICH_METRIC_FIELD = BriefField(
    key="mastery_which_metric_actually_mattered",
    prompt_key="lesson.l29.mastery.field.which_metric_actually_mattered.prompt",
    options=(
        BriefOption(
            "app_downloads_dramatic_but_unrelated", "lesson.l29.mastery.option.which_metric_actually_mattered.app_downloads_dramatic_but_unrelated"
        ),
        BriefOption(
            "session_length_directly_relevant_to_engagement_question",
            "lesson.l29.mastery.option.which_metric_actually_mattered.session_length_directly_relevant_to_engagement_question",
        ),
        BriefOption(
            "neither_number_tells_us_anything", "lesson.l29.mastery.option.which_metric_actually_mattered.neither_number_tells_us_anything"
        ),
    ),
)
MASTERY_STRONGEST_CLAIM_FIELD = BriefField(
    key="mastery_strongest_claim",
    prompt_key="lesson.l29.mastery.field.strongest_claim.prompt",
    options=(
        BriefOption("a_real_but_modest_engagement_gain", "lesson.l29.mastery.option.strongest_claim.a_real_but_modest_engagement_gain"),
        BriefOption(
            "the_500_percent_download_spike_proves_the_update_was_a_massive_success",
            "lesson.l29.mastery.option.strongest_claim.the_500_percent_download_spike_proves_the_update_was_a_massive_success",
        ),
        BriefOption(
            "a_2_percent_change_is_too_small_to_matter_at_all", "lesson.l29.mastery.option.strongest_claim.a_2_percent_change_is_too_small_to_matter_at_all"
        ),
    ),
)


def build_lesson_twenty_nine_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 29's real brief-construction flow: a single real
    two-cut filter over the same 8-finding pool - Cut 1 (`finding_shortlist`,
    `FindingPickerScene`, 8->5) keeps only the findings that bear on the
    stated decision at all; Cut 2 (`final_decision_brief`, `DecisionBuilderScene`)
    narrows those 5 to the true 3-finding headline via a real `EvidenceField`
    citation, then builds the rest of the brief around it. No reveal, no
    revision pass: every field's correct answer is derivable from the same
    8-item pool visible from the very first click, so there is nothing a
    reveal could legally change - see `docs`/plan notes for the full
    reasoning, not repeated here."""
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

    # --- Cut 1: which findings bear on the stated decision at all - a
    # motivated-reasoning trap, not a hidden-information one: every
    # finding's own real number and own given context is visible before
    # any pick. ---------------------------------------------------------

    def finding_shortlist(advance):
        def on_complete(choices):
            collected["shortlist_choices"] = choices
            _sync_context_into_collected()
            advance()

        return FindingPickerScene(
            app,
            "lesson.l29.picker_title",
            "lesson.l29.picker_prompt",
            FINDINGS_POOL,
            SHORTLIST_TARGET_COUNT,
            on_complete,
            guided=False,
            context=context,
        )

    # --- Cut 2: the true 3-finding headline (EvidenceField), then the
    # rest of the brief built around it. ---------------------------------

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
            "lesson.l29.decision_title",
            steps=(DECISION_EVIDENCE_FIELD, *DECISION_FIELDS),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l29.mastery.title",
                (MASTERY_WHICH_METRIC_FIELD, MASTERY_STRONGEST_CLAIM_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l29.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

    # --- Feedback / Debrief ---

    def _cited_finding_keys(selected_evidence_ids: set[str]) -> frozenset[str]:
        label_to_key = {finding.label_key: finding.key for finding in FINDINGS_POOL}
        keys: set[str] = set()
        for item in context.evidence:
            if item.id not in selected_evidence_ids:
                continue
            key = label_to_key.get(item.label_key)
            if key is not None:
                keys.add(key)
        return frozenset(keys)

    def _build_result() -> LessonTwentyNineResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonTwentyNineResult(
            shortlist_choices=collected.get("shortlist_choices", ()),
            cited_finding_keys=_cited_finding_keys(selected_evidence_ids),
            decision=decision,
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_29.number, 0)
        evaluation = score_lesson_twenty_nine(result, LESSON_29, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [briefing, investigation, finding_shortlist, final_decision_brief, mastery_challenge, feedback, debrief]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=29,
        collected=collected,
        definition=LESSON_29,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

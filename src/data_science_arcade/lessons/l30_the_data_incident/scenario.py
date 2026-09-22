from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l30_the_data_incident.definition import LESSON_30
from data_science_arcade.lessons.l30_the_data_incident.leads import MINIMUM_LEADS_REQUIRED, build_investigation_leads
from data_science_arcade.lessons.l30_the_data_incident.scoring import LessonThirtyResult, score_lesson_thirty
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.investigation_hub_scene import InvestigationHubScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.workbench.context import LessonContext

# No standalone Twist stage: the spec's "initial executive narrative is
# incomplete or wrong" is realized by the briefing's own alarming framing
# turning out to be wrong *through investigation* (the regional_breakdown
# lead's own baseline_check request), never handed to the student in a
# forced reveal - see leads.py's own comment on why that fact must be
# genuinely investigation-discoverable, not narrated for free.
BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l30_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l30_briefing.line2"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l30_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l30_briefing.line4"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l30_briefing.line5"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l30_debrief.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l30_debrief.line2"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l30_debrief.line3"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l30_debrief.line4"),
    )
)

WHAT_HAPPENED_FIELD = BriefField(
    key="what_happened",
    prompt_key="lesson.l30.field.what_happened.prompt",
    hint_key="lesson.l30.field.what_happened.hint",
    options=(
        BriefOption("east_promo_reverted", "lesson.l30.option.what_happened.east_promo_reverted"),
        BriefOption("redesign_broke_checkout", "lesson.l30.option.what_happened.redesign_broke_checkout"),
        BriefOption("companywide_decline", "lesson.l30.option.what_happened.companywide_decline"),
        BriefOption("insufficient_evidence_investigate_further", "lesson.l30.option.what_happened.insufficient_evidence_investigate_further"),
    ),
)

# Not part of DECISION_FIELDS below (matching L01's own convention): its
# choices are rendered live from `context.evidence`, not a fixed
# BriefOption list, so it has no static text for the option-width checks
# every BriefField/MultiChoiceField goes through - see build_lesson_thirty_runner's
# own `steps=` for where this rejoins the sequence.
SUPPORTING_EVIDENCE_FIELD = EvidenceField(key="supporting_evidence", prompt_key="lesson.l30.field.supporting_evidence.prompt", min_count=1, max_count=5)

DECISION_FIELDS: tuple[BriefField | MultiChoiceField, ...] = (
    WHAT_HAPPENED_FIELD,
    BriefField(
        key="root_cause_confidence",
        prompt_key="lesson.l30.field.root_cause_confidence.prompt",
        hint_key="lesson.l30.field.root_cause_confidence.hint",
        options=(
            BriefOption("low_too_early", "lesson.l30.option.root_cause_confidence.low_too_early"),
            BriefOption("high_but_bounded", "lesson.l30.option.root_cause_confidence.high_but_bounded"),
            BriefOption("certain_promo_caused_exact_uplift", "lesson.l30.option.root_cause_confidence.certain_promo_caused_exact_uplift"),
        ),
    ),
    MultiChoiceField(
        key="remaining_uncertainties",
        prompt_key="lesson.l30.field.remaining_uncertainties.prompt",
        hint_key="lesson.l30.field.remaining_uncertainties.hint",
        options=(
            BriefOption("promo_causal_lift_unknown", "lesson.l30.option.remaining_uncertainties.promo_causal_lift_unknown"),
            BriefOption("redesign_not_fully_checked", "lesson.l30.option.remaining_uncertainties.redesign_not_fully_checked"),
            BriefOption("nothing_left_uncertain", "lesson.l30.option.remaining_uncertainties.nothing_left_uncertain"),
        ),
        min_count=1,
        max_count=3,
    ),
    BriefField(
        key="business_impact",
        prompt_key="lesson.l30.field.business_impact.prompt",
        hint_key="lesson.l30.field.business_impact.hint",
        options=(
            BriefOption("no_ongoing_loss_reversion", "lesson.l30.option.business_impact.no_ongoing_loss_reversion"),
            BriefOption("severe_ongoing_loss", "lesson.l30.option.business_impact.severe_ongoing_loss"),
            BriefOption("unclear_insufficient_investigation", "lesson.l30.option.business_impact.unclear_insufficient_investigation"),
        ),
    ),
    BriefField(
        key="recommended_action",
        prompt_key="lesson.l30.field.recommended_action.prompt",
        hint_key="lesson.l30.field.recommended_action.hint",
        options=(
            BriefOption("do_not_revert_measure_separately", "lesson.l30.option.recommended_action.do_not_revert_measure_separately"),
            BriefOption("revert_redesign", "lesson.l30.option.recommended_action.revert_redesign"),
            BriefOption("investigate_before_deciding", "lesson.l30.option.recommended_action.investigate_before_deciding"),
        ),
    ),
    BriefField(
        key="follow_up_measurement",
        prompt_key="lesson.l30.field.follow_up_measurement.prompt",
        hint_key="lesson.l30.field.follow_up_measurement.hint",
        options=(
            BriefOption("design_promo_incrementality_check", "lesson.l30.option.follow_up_measurement.design_promo_incrementality_check"),
            BriefOption("track_per_region", "lesson.l30.option.follow_up_measurement.track_per_region"),
            BriefOption("no_further_tracking", "lesson.l30.option.follow_up_measurement.no_further_tracking"),
        ),
    ),
)


def build_lesson_thirty_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 30's investigation - briefing, investigation hub,
    decision, debrief. Unlike the pre-deepening version, a real
    `LessonContext` is threaded through every lead (see leads.py's own
    `build_investigation_leads`), so which leads get investigated - and
    which choice is made inside each - genuinely determines what's
    citable at the Decision stage and how scoring.py grades it. Returns
    the runner plus a dict that fills in with the player's results -
    `result` holds the final LessonThirtyResult once both the
    investigation and the decision have completed."""
    collected: dict = {}
    context = LessonContext()

    def _restore_context_if_present() -> None:
        data = collected.get("analytical_context")
        if data is not None:
            context.restore_from_dict(data)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation_hub(advance):
        def on_complete(leads_investigated):
            collected["leads_investigated"] = leads_investigated
            advance()

        return InvestigationHubScene(
            app,
            "lesson.l30.hub_title",
            "lesson.l30.hub_prompt",
            build_investigation_leads(app, context, collected, _sync_context_into_collected),
            MINIMUM_LEADS_REQUIRED,
            on_complete,
        )

    def decision(advance):
        def on_complete(decision_choices):
            collected["decision"] = decision_choices
            advance()

        steps = (WHAT_HAPPENED_FIELD, SUPPORTING_EVIDENCE_FIELD, *DECISION_FIELDS[1:])
        return DecisionBuilderScene(app, "lesson.l30.decision_title", steps, context, on_complete, guided=True)

    def _build_result() -> LessonThirtyResult:
        return LessonThirtyResult(
            leads_investigated=collected.get("leads_investigated", frozenset()),
            gathered_evidence=context.evidence,
            regional_cut_choice=collected.get("regional_cut_choice"),
            baseline_check_choice=collected.get("baseline_check_choice"),
            checkout_health_choice=collected.get("checkout_health_choice"),
            dedup_choice=collected.get("dedup_choice"),
            promo_verdict_choice=collected.get("promo_verdict_choice"),
            redesign_verdict_choice=collected.get("redesign_verdict_choice"),
            monitoring_choice=collected.get("monitoring_choice"),
            dashboard_choice=collected.get("dashboard_choice"),
            decision=collected.get("decision", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_30.number, 0)
        evaluation = score_lesson_thirty(result, LESSON_30, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = _build_result()
        on_finished(collected["result"])

    stages = [briefing, investigation_hub, decision, feedback, debrief]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=30,
        collected=collected,
        definition=LESSON_30,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

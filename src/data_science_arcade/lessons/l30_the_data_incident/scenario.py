from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l30_the_data_incident.incident_data import (
    generate_incident_data,
    region_baseline_average,
    value_at,
)
from data_science_arcade.lessons.l30_the_data_incident.leads import MINIMUM_LEADS_REQUIRED, build_investigation_leads
from data_science_arcade.lessons.l30_the_data_incident.scoring import LessonThirtyResult
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.investigation_hub_scene import InvestigationHubScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l30_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l30_briefing.line2"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l30_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l30_briefing.line4"),
    )
)

INVESTIGATION_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l30_investigation_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l30_investigation_intro.line2"),
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

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="what_happened",
        prompt_key="lesson.l30.field.what_happened.prompt",
        hint_key="lesson.l30.field.what_happened.hint",
        options=(
            BriefOption("redesign_broke_checkout", "lesson.l30.option.what_happened.redesign_broke_checkout"),
            BriefOption("east_promo_reverted", "lesson.l30.option.what_happened.east_promo_reverted"),
            BriefOption("companywide_decline", "lesson.l30.option.what_happened.companywide_decline"),
        ),
    ),
    BriefField(
        key="evidence",
        prompt_key="lesson.l30.field.evidence.prompt",
        hint_key="lesson.l30.field.evidence.hint",
        options=(
            BriefOption("correlation_low", "lesson.l30.option.evidence.correlation_low"),
            BriefOption("completion_rate_dropped", "lesson.l30.option.evidence.completion_rate_dropped"),
            BriefOption("east_matches_baseline", "lesson.l30.option.evidence.east_matches_baseline"),
        ),
    ),
    BriefField(
        key="root_cause_confidence",
        prompt_key="lesson.l30.field.root_cause_confidence.prompt",
        hint_key="lesson.l30.field.root_cause_confidence.hint",
        options=(
            BriefOption("high_multiple_signals", "lesson.l30.option.root_cause_confidence.high_multiple_signals"),
            BriefOption("low_too_early", "lesson.l30.option.root_cause_confidence.low_too_early"),
            BriefOption("certain_case_closed", "lesson.l30.option.root_cause_confidence.certain_case_closed"),
        ),
    ),
    BriefField(
        key="business_impact",
        prompt_key="lesson.l30.field.business_impact.prompt",
        hint_key="lesson.l30.field.business_impact.hint",
        options=(
            BriefOption("severe_ongoing_loss", "lesson.l30.option.business_impact.severe_ongoing_loss"),
            BriefOption("minimal_normal_week", "lesson.l30.option.business_impact.minimal_normal_week"),
            BriefOption("revert_redesign_impact", "lesson.l30.option.business_impact.revert_redesign_impact"),
        ),
    ),
    BriefField(
        key="uncertainty",
        prompt_key="lesson.l30.field.uncertainty.prompt",
        hint_key="lesson.l30.field.uncertainty.hint",
        options=(
            BriefOption("nothing_left_uncertain", "lesson.l30.option.uncertainty.nothing_left_uncertain"),
            BriefOption("redesign_still_suspect", "lesson.l30.option.uncertainty.redesign_still_suspect"),
            BriefOption("promo_roi_unclear", "lesson.l30.option.uncertainty.promo_roi_unclear"),
        ),
    ),
    BriefField(
        key="recommended_action",
        prompt_key="lesson.l30.field.recommended_action.prompt",
        hint_key="lesson.l30.field.recommended_action.hint",
        options=(
            BriefOption("fix_the_dashboard", "lesson.l30.option.recommended_action.fix_the_dashboard"),
            BriefOption("revert_redesign", "lesson.l30.option.recommended_action.revert_redesign"),
            BriefOption("run_promo_again", "lesson.l30.option.recommended_action.run_promo_again"),
        ),
    ),
    BriefField(
        key="follow_up_measurement",
        prompt_key="lesson.l30.field.follow_up_measurement.prompt",
        hint_key="lesson.l30.field.follow_up_measurement.hint",
        options=(
            BriefOption("track_total_only", "lesson.l30.option.follow_up_measurement.track_total_only"),
            BriefOption("track_per_region", "lesson.l30.option.follow_up_measurement.track_per_region"),
            BriefOption("no_further_tracking", "lesson.l30.option.follow_up_measurement.no_further_tracking"),
        ),
    ),
)


def build_lesson_thirty_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 30's investigation - a 6-stage sequence, not every
    prior lesson's 8, since the investigation hub itself replaces the
    guided-work/independent-intro/independent-challenge split: there is
    only one investigation, and its whole point is that the player - not
    a guided-then-independent script - decides which of it to do and in
    what order. Returns the runner plus a dict that fills in with the
    player's results - `result` holds the final LessonThirtyResult once
    both the investigation and the decision brief have completed."""
    collected: dict = {}
    incident_dataset = generate_incident_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation_intro(advance):
        return DialogueScene(app, INVESTIGATION_INTRO_DIALOGUE, on_complete=advance)

    def investigation_hub(advance):
        def on_complete(leads_investigated):
            collected["leads_investigated"] = leads_investigated
            advance()

        return InvestigationHubScene(
            app,
            "lesson.l30.hub_title",
            "lesson.l30.hub_prompt",
            build_investigation_leads(app),
            MINIMUM_LEADS_REQUIRED,
            on_complete,
        )

    def twist(advance):
        east_baseline = region_baseline_average(incident_dataset, "east")
        east_week_7 = value_at(incident_dataset, "east", 7, "revenue")
        east_week_8 = value_at(incident_dataset, "east", 8, "revenue")
        return TwistRevealScene(
            app,
            title_key="lesson.l30.twist_title",
            narrative_keys=("dialogue.l30_twist.line1", "dialogue.l30_twist.line2"),
            dataset=incident_dataset,
            comparisons=(
                ("lesson.l30.twist_week7_label", (east_week_7 - east_baseline) / east_baseline),
                ("lesson.l30.twist_week8_label", (east_week_8 - east_baseline) / east_baseline),
            ),
            value_format=lambda value: f"{value:+.1%}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l30.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonThirtyResult(
            leads_investigated=collected.get("leads_investigated", frozenset()),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation_intro, investigation_hub, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

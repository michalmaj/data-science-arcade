from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l01_question_first.scoring import LessonOneResult
from data_science_arcade.lessons.l01_question_first.twist_data import (
    RECENT_WINDOW_START,
    generate_twist_orders,
    repeat_purchase_rate,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l01_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l01_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_independent_intro.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l01_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l01_debrief.line3"),
    )
)

BRIEF_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="entity",
        prompt_key="lesson.l01.field.entity.prompt",
        hint_key="lesson.l01.field.entity.hint",
        options=(
            BriefOption("customer", "lesson.l01.option.entity.customer"),
            BriefOption("household", "lesson.l01.option.entity.household"),
            BriefOption("account", "lesson.l01.option.entity.account"),
        ),
    ),
    BriefField(
        key="time_horizon",
        prompt_key="lesson.l01.field.time_horizon.prompt",
        hint_key="lesson.l01.field.time_horizon.hint",
        options=(
            BriefOption("last_30_days", "lesson.l01.option.time_horizon.last_30_days"),
            BriefOption("last_90_days", "lesson.l01.option.time_horizon.last_90_days"),
            BriefOption("last_12_months", "lesson.l01.option.time_horizon.last_12_months"),
            BriefOption("since_signup", "lesson.l01.option.time_horizon.since_signup"),
        ),
    ),
    BriefField(
        key="behavior",
        prompt_key="lesson.l01.field.behavior.prompt",
        hint_key="lesson.l01.field.behavior.hint",
        options=(
            BriefOption("repeat_purchase", "lesson.l01.option.behavior.repeat_purchase"),
            BriefOption("any_purchase", "lesson.l01.option.behavior.any_purchase"),
            BriefOption("app_login", "lesson.l01.option.behavior.app_login"),
            BriefOption("subscription_renewal", "lesson.l01.option.behavior.subscription_renewal"),
        ),
    ),
    BriefField(
        key="population",
        prompt_key="lesson.l01.field.population.prompt",
        hint_key="lesson.l01.field.population.hint",
        options=(
            BriefOption("all_customers", "lesson.l01.option.population.all_customers"),
            BriefOption("active_last_year", "lesson.l01.option.population.active_last_year"),
            BriefOption("new_last_6_months", "lesson.l01.option.population.new_last_6_months"),
        ),
    ),
    BriefField(
        key="metric",
        prompt_key="lesson.l01.field.metric.prompt",
        hint_key="lesson.l01.field.metric.hint",
        options=(
            BriefOption("retention_rate", "lesson.l01.option.metric.retention_rate"),
            BriefOption("purchase_frequency", "lesson.l01.option.metric.purchase_frequency"),
            BriefOption("churn_rate", "lesson.l01.option.metric.churn_rate"),
            BriefOption("days_since_last_order", "lesson.l01.option.metric.days_since_last_order"),
        ),
    ),
    BriefField(
        key="decision_support",
        prompt_key="lesson.l01.field.decision_support.prompt",
        hint_key="lesson.l01.field.decision_support.hint",
        options=(
            BriefOption("loyalty_program", "lesson.l01.option.decision_support.loyalty_program"),
            BriefOption("escalate", "lesson.l01.option.decision_support.escalate"),
            BriefOption("segment_investigation", "lesson.l01.option.decision_support.segment_investigation"),
        ),
    ),
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="window_choice",
        prompt_key="lesson.l01.field.window_choice.prompt",
        hint_key="lesson.l01.field.window_choice.hint",
        options=(
            BriefOption("use_30_days", "lesson.l01.option.window_choice.use_30_days"),
            BriefOption("use_12_months", "lesson.l01.option.window_choice.use_12_months"),
            BriefOption("need_both", "lesson.l01.option.window_choice.need_both"),
        ),
    ),
    BriefField(
        key="limitation",
        prompt_key="lesson.l01.field.limitation.prompt",
        hint_key="lesson.l01.field.limitation.hint",
        options=(
            BriefOption("no_causal_reason", "lesson.l01.option.limitation.no_causal_reason"),
            BriefOption("no_seasonality", "lesson.l01.option.limitation.no_seasonality"),
            BriefOption("no_segment_detail", "lesson.l01.option.limitation.no_segment_detail"),
        ),
    ),
)


def build_lesson_one_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles the 6-act stage sequence (spec §18) for Lesson 01. Returns
    the runner plus a dict that fills in with the player's choices as they
    progress - `result` holds the final LessonOneResult once all three
    brief-building stages have completed."""
    collected: dict = {}
    twist_dataset = generate_twist_orders()
    recent_rate = repeat_purchase_rate(twist_dataset, RECENT_WINDOW_START)
    full_period_rate = repeat_purchase_rate(twist_dataset, None)

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(brief):
            collected["guided_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l01.brief_title", BRIEF_FIELDS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(brief):
            collected["independent_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l01.brief_title", BRIEF_FIELDS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l01.twist_title",
            narrative_keys=("dialogue.l01_twist.line1", "dialogue.l01_twist.line2"),
            dataset=twist_dataset,
            recent_label_key="lesson.l01.twist_recent_label",
            recent_rate=recent_rate,
            full_period_label_key="lesson.l01.twist_full_label",
            full_period_rate=full_period_rate,
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l01.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonOneResult(
            guided_brief=collected.get("guided_brief", {}),
            independent_brief=collected.get("independent_brief", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

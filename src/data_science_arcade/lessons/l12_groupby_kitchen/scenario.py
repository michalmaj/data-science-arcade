from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l12_groupby_kitchen.definition import LESSON_12
from data_science_arcade.lessons.l12_groupby_kitchen.orders import distinct_customers_by_store, generate_orders, order_count_by_store
from data_science_arcade.lessons.l12_groupby_kitchen.requests import AGGREGATION_REQUESTS
from data_science_arcade.lessons.l12_groupby_kitchen.scoring import LessonTwelveResult
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.pipeline_builder_scene import PipelineBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l12_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l12_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l12_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l12_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l12_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l12_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l12_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l12_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l12_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l12_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="customer_count_fix",
        prompt_key="lesson.l12.field.customer_count_fix.prompt",
        hint_key="lesson.l12.field.customer_count_fix.hint",
        options=(
            BriefOption("distinct_per_store", "lesson.l12.option.customer_count_fix.distinct_per_store"),
            BriefOption("keep_counting_rows", "lesson.l12.option.customer_count_fix.keep_counting_rows"),
            BriefOption("distinct_network_wide", "lesson.l12.option.customer_count_fix.distinct_network_wide"),
        ),
    ),
    BriefField(
        key="grouping_risk",
        prompt_key="lesson.l12.field.grouping_risk.prompt",
        hint_key="lesson.l12.field.grouping_risk.hint",
        options=(
            BriefOption("wrong_key_changes_meaning", "lesson.l12.option.grouping_risk.wrong_key_changes_meaning"),
            BriefOption("groupby_is_always_correct", "lesson.l12.option.grouping_risk.groupby_is_always_correct"),
            BriefOption("only_matters_at_scale", "lesson.l12.option.grouping_risk.only_matters_at_scale"),
        ),
    ),
)


def build_lesson_twelve_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 12's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwelveResult once both pipeline stages
    and the decision brief have completed."""
    collected: dict = {}
    orders = generate_orders()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return PipelineBuilderScene(app, "lesson.l12.pipeline_title", orders, AGGREGATION_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return PipelineBuilderScene(app, "lesson.l12.pipeline_title", orders, AGGREGATION_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l12.twist_title",
            narrative_keys=("dialogue.l12_twist.line1", "dialogue.l12_twist.line2"),
            dataset=orders,
            comparisons=(
                ("lesson.l12.twist_naive_s02_label", float(order_count_by_store(orders, "S02"))),
                ("lesson.l12.twist_true_s02_label", float(distinct_customers_by_store(orders, "S02"))),
                ("lesson.l12.twist_naive_total_label", float(len(orders.frame))),
                ("lesson.l12.twist_true_total_label", float(orders.frame["customer_id"].nunique())),
            ),
            value_format=lambda value: f"{value:.0f}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l12.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwelveResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=12, collected=collected, definition=LESSON_12
    )
    return runner, collected

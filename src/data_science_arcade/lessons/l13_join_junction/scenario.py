from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l13_join_junction.customers_orders import generate_customers, generate_orders
from data_science_arcade.lessons.l13_join_junction.definition import LESSON_13
from data_science_arcade.lessons.l13_join_junction.requests import JOIN_REQUESTS
from data_science_arcade.lessons.l13_join_junction.scoring import LessonThirteenResult
from data_science_arcade.lessons.l13_join_junction.twist_data import generate_promotions, naive_joined_revenue, true_total_revenue
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.junction_scene import JunctionScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l13_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l13_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l13_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l13_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l13_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l13_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l13_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l13_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l13_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l13_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="revenue_repair",
        prompt_key="lesson.l13.field.revenue_repair.prompt",
        hint_key="lesson.l13.field.revenue_repair.hint",
        options=(
            BriefOption("sum_from_original_orders", "lesson.l13.option.revenue_repair.sum_from_original_orders"),
            BriefOption("divide_after_join", "lesson.l13.option.revenue_repair.divide_after_join"),
            BriefOption("pick_one_promotion", "lesson.l13.option.revenue_repair.pick_one_promotion"),
        ),
    ),
    BriefField(
        key="join_lesson",
        prompt_key="lesson.l13.field.join_lesson.prompt",
        hint_key="lesson.l13.field.join_lesson.hint",
        options=(
            BriefOption("verify_after_joining", "lesson.l13.option.join_lesson.verify_after_joining"),
            BriefOption("joins_never_change_totals", "lesson.l13.option.join_lesson.joins_never_change_totals"),
            BriefOption("only_many_to_many_risky", "lesson.l13.option.join_lesson.only_many_to_many_risky"),
        ),
    ),
)


def build_lesson_thirteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 13's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonThirteenResult once both junction
    stages and the decision brief have completed."""
    collected: dict = {}
    orders = generate_orders()
    customers = generate_customers()
    promotions = generate_promotions()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return JunctionScene(app, "lesson.l13.junction_title", orders, customers, "customer_id", JOIN_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return JunctionScene(app, "lesson.l13.junction_title", orders, customers, "customer_id", JOIN_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l13.twist_title",
            narrative_keys=("dialogue.l13_twist.line1", "dialogue.l13_twist.line2"),
            dataset=orders,
            comparisons=(
                ("lesson.l13.twist_naive_label", naive_joined_revenue(orders, promotions)),
                ("lesson.l13.twist_true_label", true_total_revenue()),
            ),
            value_format=lambda value: f"${value:,.2f}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l13.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonThirteenResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=13, collected=collected, definition=LESSON_13
    )
    return runner, collected

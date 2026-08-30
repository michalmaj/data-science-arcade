from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l06_schema_repair_shop.definition import LESSON_06
from data_science_arcade.lessons.l06_schema_repair_shop.sales_export import REPAIR_ISSUES, generate_sales_export
from data_science_arcade.lessons.l06_schema_repair_shop.scoring import LessonSixResult
from data_science_arcade.lessons.l06_schema_repair_shop.twist_data import (
    correctly_dated_rate,
    generate_date_parse_results,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l06_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l06_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l06_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l06_independent_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l06_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l06_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l06_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="schema_judgment",
        prompt_key="lesson.l06.field.schema_judgment.prompt",
        hint_key="lesson.l06.field.schema_judgment.hint",
        options=(
            BriefOption("approve_as_is", "lesson.l06.option.schema_judgment.approve_as_is"),
            BriefOption("reject_date_first", "lesson.l06.option.schema_judgment.reject_date_first"),
            BriefOption("approve_with_flag", "lesson.l06.option.schema_judgment.approve_with_flag"),
        ),
    ),
    BriefField(
        key="unresolved_ambiguity",
        prompt_key="lesson.l06.field.unresolved_ambiguity.prompt",
        hint_key="lesson.l06.field.unresolved_ambiguity.hint",
        options=(
            BriefOption("single_rule_insufficient", "lesson.l06.option.unresolved_ambiguity.single_rule_insufficient"),
            BriefOption("silent_failure_risk", "lesson.l06.option.unresolved_ambiguity.silent_failure_risk"),
            BriefOption("date_format_per_market", "lesson.l06.option.unresolved_ambiguity.date_format_per_market"),
        ),
    ),
)


def build_lesson_six_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 06's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonSixResult once both workbench stages
    and the decision brief have completed."""
    collected: dict = {}
    date_results = generate_date_parse_results()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(resolution):
            collected["guided_resolution"] = resolution
            advance()

        return WorkbenchScene(app, generate_sales_export(), REPAIR_ISSUES, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(resolution):
            collected["independent_resolution"] = resolution
            advance()

        return WorkbenchScene(app, generate_sales_export(), REPAIR_ISSUES, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l06.twist_title",
            narrative_keys=("dialogue.l06_twist.line1", "dialogue.l06_twist.line2"),
            dataset=date_results,
            comparisons=(
                ("lesson.l06.twist_us_label", correctly_dated_rate(date_results, "US")),
                ("lesson.l06.twist_de_label", correctly_dated_rate(date_results, "DE")),
                ("lesson.l06.twist_overall_label", correctly_dated_rate(date_results)),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l06.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonSixResult(
            guided_resolution=collected.get("guided_resolution", {}),
            independent_resolution=collected.get("independent_resolution", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=6, collected=collected, definition=LESSON_06
    )
    return runner, collected

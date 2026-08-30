from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l10_validation_gate.checks import VALIDATION_CHECKS
from data_science_arcade.lessons.l10_validation_gate.definition import LESSON_10
from data_science_arcade.lessons.l10_validation_gate.scoring import LessonTenResult
from data_science_arcade.lessons.l10_validation_gate.twist_data import (
    generate_orders_feed,
    naive_average,
    true_average,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l10_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l10_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l10_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l10_independent_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l10_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l10_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l10_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="additional_check_needed",
        prompt_key="lesson.l10.field.additional_check_needed.prompt",
        hint_key="lesson.l10.field.additional_check_needed.hint",
        options=(
            BriefOption("unit_consistency_check", "lesson.l10.option.additional_check_needed.unit_consistency_check"),
            BriefOption("cross_field_consistency", "lesson.l10.option.additional_check_needed.cross_field_consistency"),
            BriefOption("no_additional_check_needed", "lesson.l10.option.additional_check_needed.no_additional_check_needed"),
        ),
    ),
    BriefField(
        key="validation_principle",
        prompt_key="lesson.l10.field.validation_principle.prompt",
        hint_key="lesson.l10.field.validation_principle.hint",
        options=(
            BriefOption("passing_checks_not_correctness", "lesson.l10.option.validation_principle.passing_checks_not_correctness"),
            BriefOption("more_checks_always_better", "lesson.l10.option.validation_principle.more_checks_always_better"),
            BriefOption("manual_review_solves_it", "lesson.l10.option.validation_principle.manual_review_solves_it"),
        ),
    ),
)


def build_lesson_ten_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 10's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTenResult once both check-calibration
    stages and the decision brief have completed."""
    collected: dict = {}
    orders_feed = generate_orders_feed()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(rules):
            collected["guided_rules"] = rules
            advance()

        return FlowBuilderScene(app, "lesson.l10.board_title", VALIDATION_CHECKS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(rules):
            collected["independent_rules"] = rules
            advance()

        return FlowBuilderScene(app, "lesson.l10.board_title", VALIDATION_CHECKS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l10.twist_title",
            narrative_keys=("dialogue.l10_twist.line1", "dialogue.l10_twist.line2"),
            dataset=orders_feed,
            comparisons=(
                ("lesson.l10.twist_naive_label", naive_average(orders_feed)),
                ("lesson.l10.twist_true_label", true_average(orders_feed)),
            ),
            value_format=lambda value: f"${value:,.2f}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l10.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTenResult(
            guided_rules=collected.get("guided_rules", {}),
            independent_rules=collected.get("independent_rules", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=10, collected=collected, definition=LESSON_10
    )
    return runner, collected

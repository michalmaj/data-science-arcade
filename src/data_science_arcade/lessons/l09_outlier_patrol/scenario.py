from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l09_outlier_patrol.scoring import LessonNineResult
from data_science_arcade.lessons.l09_outlier_patrol.transactions import OUTLIER_CASES
from data_science_arcade.lessons.l09_outlier_patrol.twist_data import category_rate, generate_flagged_transactions
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.flow_builder_scene import FlowBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l09_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l09_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l09_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l09_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l09_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l09_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l09_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l09_independent_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l09_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l09_debrief.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l09_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l09_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="rule_approach",
        prompt_key="lesson.l09.field.rule_approach.prompt",
        hint_key="lesson.l09.field.rule_approach.hint",
        options=(
            BriefOption("context_aware_review", "lesson.l09.option.rule_approach.context_aware_review"),
            BriefOption("raise_threshold", "lesson.l09.option.rule_approach.raise_threshold"),
            BriefOption("keep_rule_flag_only", "lesson.l09.option.rule_approach.keep_rule_flag_only"),
        ),
    ),
    BriefField(
        key="remaining_limitation",
        prompt_key="lesson.l09.field.remaining_limitation.prompt",
        hint_key="lesson.l09.field.remaining_limitation.hint",
        options=(
            BriefOption("review_capacity", "lesson.l09.option.remaining_limitation.review_capacity"),
            BriefOption("category_boundary_fuzzy", "lesson.l09.option.remaining_limitation.category_boundary_fuzzy"),
            BriefOption("delayed_decisions", "lesson.l09.option.remaining_limitation.delayed_decisions"),
        ),
    ),
)


def build_lesson_nine_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 09's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonNineResult once both case-review stages
    and the decision brief have completed."""
    collected: dict = {}
    flagged = generate_flagged_transactions()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(actions):
            collected["guided_actions"] = actions
            advance()

        return FlowBuilderScene(app, "lesson.l09.board_title", OUTLIER_CASES, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(actions):
            collected["independent_actions"] = actions
            advance()

        return FlowBuilderScene(app, "lesson.l09.board_title", OUTLIER_CASES, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l09.twist_title",
            narrative_keys=("dialogue.l09_twist.line1", "dialogue.l09_twist.line2"),
            dataset=flagged,
            comparisons=(
                ("lesson.l09.twist_fraud_label", category_rate(flagged, "fraud")),
                ("lesson.l09.twist_legitimate_label", category_rate(flagged, "legitimate")),
                ("lesson.l09.twist_unit_error_label", category_rate(flagged, "unit_error")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l09.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonNineResult(
            guided_actions=collected.get("guided_actions", {}),
            independent_actions=collected.get("independent_actions", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

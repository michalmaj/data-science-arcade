from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l08_duplicate_detective.candidate_pairs import CANDIDATE_PAIRS
from data_science_arcade.lessons.l08_duplicate_detective.scoring import LessonEightResult
from data_science_arcade.lessons.l08_duplicate_detective.twist_data import (
    generate_match_results,
    precision,
    recall,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.record_pair_scene import RecordPairScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l08_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l08_briefing.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_briefing.line3"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l08_briefing.line4"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l08_independent_intro.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_independent_intro.line2"),
    )
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l08_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l08_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l08_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="matching_rule_choice",
        prompt_key="lesson.l08.field.matching_rule_choice.prompt",
        hint_key="lesson.l08.field.matching_rule_choice.hint",
        options=(
            BriefOption("conservative", "lesson.l08.option.matching_rule_choice.conservative"),
            BriefOption("aggressive", "lesson.l08.option.matching_rule_choice.aggressive"),
            BriefOption("conservative_with_review", "lesson.l08.option.matching_rule_choice.conservative_with_review"),
        ),
    ),
    BriefField(
        key="tradeoff_reasoning",
        prompt_key="lesson.l08.field.tradeoff_reasoning.prompt",
        hint_key="lesson.l08.field.tradeoff_reasoning.hint",
        options=(
            BriefOption("false_merge_cost", "lesson.l08.option.tradeoff_reasoning.false_merge_cost"),
            BriefOption("missed_duplicate_cost", "lesson.l08.option.tradeoff_reasoning.missed_duplicate_cost"),
            BriefOption("asymmetric_risk", "lesson.l08.option.tradeoff_reasoning.asymmetric_risk"),
        ),
    ),
)


def build_lesson_eight_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 08's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonEightResult once both record-pair
    stages and the decision brief have completed."""
    collected: dict = {}
    match_results = generate_match_results()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(decisions):
            collected["guided_decisions"] = decisions
            advance()

        return RecordPairScene(
            app, "lesson.l08.board_title", "lesson.l08.board_prompt", CANDIDATE_PAIRS, on_complete, guided=True
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(decisions):
            collected["independent_decisions"] = decisions
            advance()

        return RecordPairScene(
            app, "lesson.l08.board_title", "lesson.l08.board_prompt", CANDIDATE_PAIRS, on_complete, guided=False
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l08.twist_title",
            narrative_keys=("dialogue.l08_twist.line1", "dialogue.l08_twist.line2"),
            dataset=match_results,
            comparisons=(
                ("lesson.l08.twist_aggressive_precision_label", precision(match_results, "aggressive_merge")),
                ("lesson.l08.twist_conservative_precision_label", precision(match_results, "conservative_merge")),
                ("lesson.l08.twist_conservative_recall_label", recall(match_results, "conservative_merge")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l08.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonEightResult(
            guided_decisions=collected.get("guided_decisions", {}),
            independent_decisions=collected.get("independent_decisions", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

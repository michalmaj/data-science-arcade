from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l20_ab_test_commander.checkpoints import CHECKOUT_CHECKPOINTS
from data_science_arcade.lessons.l20_ab_test_commander.definition import LESSON_20
from data_science_arcade.lessons.l20_ab_test_commander.experiment_data import TOTAL_RUNTIME_DAYS
from data_science_arcade.lessons.l20_ab_test_commander.scoring import LessonTwentyResult
from data_science_arcade.lessons.l20_ab_test_commander.twist_data import click_through_rate, generate_reranking_data
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.checkpoint_monitor_scene import CheckpointMonitorScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l20_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l20_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_investigation.line2"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l20_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l20_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l20_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l20_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l20_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="checkout_experiment_verdict",
        prompt_key="lesson.l20.field.checkout_experiment_verdict.prompt",
        hint_key="lesson.l20.field.checkout_experiment_verdict.hint",
        options=(
            BriefOption("do_not_ship", "lesson.l20.option.checkout_experiment_verdict.do_not_ship"),
            BriefOption("ship", "lesson.l20.option.checkout_experiment_verdict.ship"),
            BriefOption("run_longer", "lesson.l20.option.checkout_experiment_verdict.run_longer"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l20.field.general_lesson.prompt",
        hint_key="lesson.l20.field.general_lesson.hint",
        options=(
            BriefOption("more_data_only_ever_confirms_early_reads", "lesson.l20.option.general_lesson.more_data_only_ever_confirms_early_reads"),
            BriefOption("stopping_early_only_risks_missing_a_win", "lesson.l20.option.general_lesson.stopping_early_only_risks_missing_a_win"),
            BriefOption("peeking_early_can_point_either_way", "lesson.l20.option.general_lesson.peeking_early_can_point_either_way"),
        ),
    ),
)


def build_lesson_twenty_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 20's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentyResult once both monitoring
    stages and the decision brief have completed."""
    collected: dict = {}
    reranking_data = generate_reranking_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(final_checkpoint):
            collected["guided_final_checkpoint"] = final_checkpoint
            advance()

        return CheckpointMonitorScene(
            app,
            "lesson.l20.dashboard_title",
            CHECKOUT_CHECKPOINTS,
            TOTAL_RUNTIME_DAYS,
            on_complete,
            guided=True,
            hint_key="lesson.l20.dashboard_hint",
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(final_checkpoint):
            collected["independent_final_checkpoint"] = final_checkpoint
            advance()

        return CheckpointMonitorScene(
            app,
            "lesson.l20.dashboard_title",
            CHECKOUT_CHECKPOINTS,
            TOTAL_RUNTIME_DAYS,
            on_complete,
            guided=False,
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l20.twist_title",
            narrative_keys=("dialogue.l20_twist.line1", "dialogue.l20_twist.line2"),
            dataset=reranking_data,
            comparisons=(
                ("lesson.l20.twist_before_label", click_through_rate(reranking_data, "before_rollout")),
                ("lesson.l20.twist_after_label", click_through_rate(reranking_data, "after_rollout")),
            ),
            on_complete=advance,
            # Default .0% rounding would flatten 7.2%/6.1% to "7%"/"6%",
            # losing the very digit the point (a real, small decline) rests on.
            value_format=lambda value: f"{value:.1%}",
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l20.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentyResult(
            guided_final_checkpoint=collected.get("guided_final_checkpoint", 0),
            independent_final_checkpoint=collected.get("independent_final_checkpoint", 0),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=20, collected=collected, definition=LESSON_20
    )
    return runner, collected

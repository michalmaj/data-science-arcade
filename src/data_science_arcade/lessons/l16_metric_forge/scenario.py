from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l16_metric_forge.requests import METRIC_REQUESTS
from data_science_arcade.lessons.l16_metric_forge.scoring import LessonSixteenResult
from data_science_arcade.lessons.l16_metric_forge.twist_data import churn_mean, generate_churn_data
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l16_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l16_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l16_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l16_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l16_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l16_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l16_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l16_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l16_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l16_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="metric_system_design",
        prompt_key="lesson.l16.field.metric_system_design.prompt",
        hint_key="lesson.l16.field.metric_system_design.hint",
        options=(
            BriefOption("primary_plus_guardrails", "lesson.l16.option.metric_system_design.primary_plus_guardrails"),
            BriefOption("primary_only", "lesson.l16.option.metric_system_design.primary_only"),
            BriefOption("many_metrics_equally", "lesson.l16.option.metric_system_design.many_metrics_equally"),
        ),
    ),
    BriefField(
        key="goodhart_lesson",
        prompt_key="lesson.l16.field.goodhart_lesson.prompt",
        hint_key="lesson.l16.field.goodhart_lesson.hint",
        options=(
            BriefOption("any_target_can_be_gamed", "lesson.l16.option.goodhart_lesson.any_target_can_be_gamed"),
            BriefOption("only_bad_metrics_get_gamed", "lesson.l16.option.goodhart_lesson.only_bad_metrics_get_gamed"),
            BriefOption("guardrails_slow_progress", "lesson.l16.option.goodhart_lesson.guardrails_slow_progress"),
        ),
    ),
)


def build_lesson_sixteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 16's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonSixteenResult once both simulator
    stages and the decision brief have completed."""
    collected: dict = {}
    churn_data = generate_churn_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return SegmentSlicerScene(
            app,
            "lesson.l16.simulator_title",
            METRIC_REQUESTS,
            on_complete,
            guided=True,
            row_column_label_key="lesson.l16.row_column_label",
            before_column_label_key="lesson.l16.before_column_label",
            after_column_label_key="lesson.l16.after_column_label",
            pick_hint_key="lesson.l16.pick_a_metric_hint",
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return SegmentSlicerScene(
            app,
            "lesson.l16.simulator_title",
            METRIC_REQUESTS,
            on_complete,
            guided=False,
            row_column_label_key="lesson.l16.row_column_label",
            before_column_label_key="lesson.l16.before_column_label",
            after_column_label_key="lesson.l16.after_column_label",
            pick_hint_key="lesson.l16.pick_a_metric_hint",
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l16.twist_title",
            narrative_keys=("dialogue.l16_twist.line1", "dialogue.l16_twist.line2"),
            dataset=churn_data,
            comparisons=(
                ("lesson.l16.twist_churn_before_label", churn_mean(churn_data, "before")),
                ("lesson.l16.twist_churn_after_label", churn_mean(churn_data, "after")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l16.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonSixteenResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l14_chart_designer.requests import CHART_REQUESTS
from data_science_arcade.lessons.l14_chart_designer.scoring import LessonFourteenResult
from data_science_arcade.lessons.l14_chart_designer.store_metrics import generate_returns, return_rate
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l14_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l14_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l14_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l14_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l14_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="correct_return_metric",
        prompt_key="lesson.l14.field.correct_return_metric.prompt",
        hint_key="lesson.l14.field.correct_return_metric.hint",
        options=(
            BriefOption("report_rate_not_count", "lesson.l14.option.correct_return_metric.report_rate_not_count"),
            BriefOption("keep_raw_counts", "lesson.l14.option.correct_return_metric.keep_raw_counts"),
            BriefOption("network_wide_only", "lesson.l14.option.correct_return_metric.network_wide_only"),
        ),
    ),
    BriefField(
        key="chart_integrity_lesson",
        prompt_key="lesson.l14.field.chart_integrity_lesson.prompt",
        hint_key="lesson.l14.field.chart_integrity_lesson.hint",
        options=(
            BriefOption("check_the_denominator", "lesson.l14.option.chart_integrity_lesson.check_the_denominator"),
            BriefOption("accurate_numbers_are_enough", "lesson.l14.option.chart_integrity_lesson.accurate_numbers_are_enough"),
            BriefOption("zoomed_axes_always_better", "lesson.l14.option.chart_integrity_lesson.zoomed_axes_always_better"),
        ),
    ),
)


def build_lesson_fourteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 14's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonFourteenResult once both chart stages
    and the decision brief have completed."""
    collected: dict = {}
    returns = generate_returns()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return ChartDesignerScene(app, "lesson.l14.chart_title", CHART_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return ChartDesignerScene(app, "lesson.l14.chart_title", CHART_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l14.twist_title",
            narrative_keys=("dialogue.l14_twist.line1", "dialogue.l14_twist.line2"),
            dataset=returns,
            comparisons=(
                ("lesson.l14.twist_s01_rate_label", return_rate(returns, "S01")),
                ("lesson.l14.twist_s02_rate_label", return_rate(returns, "S02")),
                ("lesson.l14.twist_s03_rate_label", return_rate(returns, "S03")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l14.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonFourteenResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

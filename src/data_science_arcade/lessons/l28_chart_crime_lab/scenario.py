from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l28_chart_crime_lab.requests import CHART_REQUESTS
from data_science_arcade.lessons.l28_chart_crime_lab.scoring import LessonTwentyEightResult
from data_science_arcade.lessons.l28_chart_crime_lab.twist_data import generate_spend_signups_data, percent_change
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l28_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l28_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l28_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l28_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l28_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="chart_review_standard",
        prompt_key="lesson.l28.field.chart_review_standard.prompt",
        hint_key="lesson.l28.field.chart_review_standard.hint",
        options=(
            BriefOption("numbers_correct_is_enough", "lesson.l28.option.chart_review_standard.numbers_correct_is_enough"),
            BriefOption("numbers_and_visuals_both_honest", "lesson.l28.option.chart_review_standard.numbers_and_visuals_both_honest"),
            BriefOption("only_the_written_report_matters", "lesson.l28.option.chart_review_standard.only_the_written_report_matters"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l28.field.general_lesson.prompt",
        hint_key="lesson.l28.field.general_lesson.hint",
        options=(
            BriefOption("honest_numbers_cant_mislead", "lesson.l28.option.general_lesson.honest_numbers_cant_mislead"),
            BriefOption("same_data_looks_different_scaled_and_sliced", "lesson.l28.option.general_lesson.same_data_looks_different_scaled_and_sliced"),
            BriefOption("dual_axis_is_always_the_right_choice", "lesson.l28.option.general_lesson.dual_axis_is_always_the_right_choice"),
        ),
    ),
)


def build_lesson_twenty_eight_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 28's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentyEightResult once both chart
    stages and the decision brief have completed.

    Reuses ChartDesignerScene directly, generalized to let a recipe
    override the request's own categories/values (a cherry-picked window,
    a different denominator) - not just how the same numbers are scaled,
    the way Lesson 14 already used it."""
    collected: dict = {}
    spend_signups = generate_spend_signups_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return ChartDesignerScene(app, "lesson.l28.chart_title", CHART_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return ChartDesignerScene(app, "lesson.l28.chart_title", CHART_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l28.twist_title",
            narrative_keys=("dialogue.l28_twist.line1", "dialogue.l28_twist.line2"),
            dataset=spend_signups,
            comparisons=(
                ("lesson.l28.twist_spend_change_label", percent_change(spend_signups, "marketing_spend")),
                ("lesson.l28.twist_signups_change_label", percent_change(spend_signups, "signups")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l28.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentyEightResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l11_distribution_observatory.lenses import build_distribution_lenses
from data_science_arcade.lessons.l11_distribution_observatory.order_values import generate_order_values, segment_mean
from data_science_arcade.lessons.l11_distribution_observatory.scoring import LessonElevenResult
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.distribution_scene import DistributionScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l11_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l11_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l11_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l11_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l11_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l11_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l11_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l11_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l11_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l11_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="reporting_approach",
        prompt_key="lesson.l11.field.reporting_approach.prompt",
        hint_key="lesson.l11.field.reporting_approach.hint",
        options=(
            BriefOption("segment_aware_pair", "lesson.l11.option.reporting_approach.segment_aware_pair"),
            BriefOption("keep_median", "lesson.l11.option.reporting_approach.keep_median"),
            BriefOption("switch_to_mean", "lesson.l11.option.reporting_approach.switch_to_mean"),
        ),
    ),
    BriefField(
        key="summary_limitation",
        prompt_key="lesson.l11.field.summary_limitation.prompt",
        hint_key="lesson.l11.field.summary_limitation.hint",
        options=(
            BriefOption("distinct_subpopulations", "lesson.l11.option.summary_limitation.distinct_subpopulations"),
            BriefOption("nothing_if_median", "lesson.l11.option.summary_limitation.nothing_if_median"),
            BriefOption("nothing_if_more_data", "lesson.l11.option.summary_limitation.nothing_if_more_data"),
        ),
    ),
)


def build_lesson_eleven_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 11's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonElevenResult once both lens stages and
    the decision brief have completed."""
    collected: dict = {}
    order_values = generate_order_values()
    values = list(order_values.frame["order_value"])
    lenses = build_distribution_lenses(order_values)

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return DistributionScene(app, "lesson.l11.chart_title", values, lenses, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return DistributionScene(app, "lesson.l11.chart_title", values, lenses, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l11.twist_title",
            narrative_keys=("dialogue.l11_twist.line1", "dialogue.l11_twist.line2"),
            dataset=order_values,
            comparisons=(
                ("lesson.l11.twist_reported_label", float(order_values.frame["order_value"].median())),
                ("lesson.l11.twist_consumer_label", segment_mean(order_values, "consumer")),
                ("lesson.l11.twist_business_label", segment_mean(order_values, "business")),
            ),
            value_format=lambda value: f"${value:,.2f}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l11.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonElevenResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

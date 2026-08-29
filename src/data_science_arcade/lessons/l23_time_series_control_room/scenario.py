from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l23_time_series_control_room.kpi_data import build_time_series, generate_kpi_data
from data_science_arcade.lessons.l23_time_series_control_room.requests import TIME_SERIES_REQUESTS
from data_science_arcade.lessons.l23_time_series_control_room.scoring import LessonTwentyThreeResult
from data_science_arcade.lessons.l23_time_series_control_room.twist_data import generate_delivery_alert_data, on_time_rate
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.timeseries_scene import TimeSeriesScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l23_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l23_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l23_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l23_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l23_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l23_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="escalation_verdict",
        prompt_key="lesson.l23.field.escalation_verdict.prompt",
        hint_key="lesson.l23.field.escalation_verdict.hint",
        options=(
            BriefOption("no_it_was_all_calendar_noise", "lesson.l23.option.escalation_verdict.no_it_was_all_calendar_noise"),
            BriefOption("yes_but_only_the_campaign_result", "lesson.l23.option.escalation_verdict.yes_but_only_the_campaign_result"),
            BriefOption("yes_all_three_are_real_changes", "lesson.l23.option.escalation_verdict.yes_all_three_are_real_changes"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l23.field.general_lesson.prompt",
        hint_key="lesson.l23.field.general_lesson.hint",
        options=(
            BriefOption("any_dip_near_an_event_is_caused_by_it", "lesson.l23.option.general_lesson.any_dip_near_an_event_is_caused_by_it"),
            BriefOption("always_compare_to_the_same_calendar_days", "lesson.l23.option.general_lesson.always_compare_to_the_same_calendar_days"),
            BriefOption("weekly_patterns_dont_matter_much", "lesson.l23.option.general_lesson.weekly_patterns_dont_matter_much"),
        ),
    ),
)


def build_lesson_twenty_three_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 23's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentyThreeResult once both chart
    stages and the decision brief have completed."""
    collected: dict = {}
    kpi_data = generate_kpi_data()
    current_period = build_time_series(kpi_data, "current", "timeseries.current_period_label")
    previous_period = build_time_series(kpi_data, "previous", "timeseries.previous_period_label")
    delivery_data = generate_delivery_alert_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return TimeSeriesScene(app, "lesson.l23.chart_title", current_period, previous_period, TIME_SERIES_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return TimeSeriesScene(app, "lesson.l23.chart_title", current_period, previous_period, TIME_SERIES_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l23.twist_title",
            narrative_keys=("dialogue.l23_twist.line1", "dialogue.l23_twist.line2"),
            dataset=delivery_data,
            comparisons=(
                ("lesson.l23.twist_alert_day_label", on_time_rate(delivery_data, "day_after_spring_holiday")),
                ("lesson.l23.twist_normal_day_label", on_time_rate(delivery_data, "normal_weekday")),
                ("lesson.l23.twist_repeat_holiday_label", on_time_rate(delivery_data, "day_after_autumn_holiday")),
                ("lesson.l23.twist_recovered_label", on_time_rate(delivery_data, "two_days_after_spring_holiday")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l23.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentyThreeResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

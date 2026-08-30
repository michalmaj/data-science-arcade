from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l25_kpi_emergency_room.definition import LESSON_25
from data_science_arcade.lessons.l25_kpi_emergency_room.incident_log import generate_incident_log, simulate_monitoring
from data_science_arcade.lessons.l25_kpi_emergency_room.requests import MONITORING_REQUESTS
from data_science_arcade.lessons.l25_kpi_emergency_room.scoring import LessonTwentyFiveResult
from data_science_arcade.lessons.l25_kpi_emergency_room.twist_data import alert_count, generate_alert_fatigue_data, response_minutes
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l25_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l25_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l25_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l25_debrief.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l25_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l25_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="system_verdict",
        prompt_key="lesson.l25.field.system_verdict.prompt",
        hint_key="lesson.l25.field.system_verdict.hint",
        options=(
            BriefOption("every_metric_tightest_threshold", "lesson.l25.option.system_verdict.every_metric_tightest_threshold"),
            BriefOption("a_few_metrics_sensible_thresholds", "lesson.l25.option.system_verdict.a_few_metrics_sensible_thresholds"),
            BriefOption("one_easy_vanity_metric", "lesson.l25.option.system_verdict.one_easy_vanity_metric"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l25.field.general_lesson.prompt",
        hint_key="lesson.l25.field.general_lesson.hint",
        options=(
            BriefOption("tighter_threshold_always_catches_more", "lesson.l25.option.general_lesson.tighter_threshold_always_catches_more"),
            BriefOption("more_alerts_isnt_better_monitoring", "lesson.l25.option.general_lesson.more_alerts_isnt_better_monitoring"),
            BriefOption("which_metric_matters_less_than_coverage", "lesson.l25.option.general_lesson.which_metric_matters_less_than_coverage"),
        ),
    ),
)


def build_lesson_twenty_five_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 25's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentyFiveResult once both monitoring
    stages and the decision brief have completed."""
    collected: dict = {}
    incident_log = generate_incident_log()
    alert_fatigue = generate_alert_fatigue_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return AlertConfigScene(app, "lesson.l25.builder_title", incident_log, MONITORING_REQUESTS, simulate_monitoring, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return AlertConfigScene(app, "lesson.l25.builder_title", incident_log, MONITORING_REQUESTS, simulate_monitoring, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l25.twist_title",
            narrative_keys=("dialogue.l25_twist.line1", "dialogue.l25_twist.line2"),
            dataset=alert_fatigue,
            comparisons=(
                ("lesson.l25.twist_false_alarm_count_label", alert_count(alert_fatigue, "false_alarm")),
                ("lesson.l25.twist_real_incident_count_label", alert_count(alert_fatigue, "real_incident")),
                ("lesson.l25.twist_false_alarm_response_label", response_minutes(alert_fatigue, "false_alarm")),
                ("lesson.l25.twist_real_incident_response_label", response_minutes(alert_fatigue, "real_incident")),
            ),
            value_format=lambda value: f"{value:.0f}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l25.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentyFiveResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=25, collected=collected, definition=LESSON_25
    )
    return runner, collected

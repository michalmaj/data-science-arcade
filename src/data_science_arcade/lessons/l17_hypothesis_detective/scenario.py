from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l17_hypothesis_detective.definition import LESSON_17
from data_science_arcade.lessons.l17_hypothesis_detective.requests import HYPOTHESIS_REQUESTS
from data_science_arcade.lessons.l17_hypothesis_detective.scoring import LessonSeventeenResult
from data_science_arcade.lessons.l17_hypothesis_detective.twist_data import device_repeat_rate, generate_device_split_data
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.prediction_scene import PredictionScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l17_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l17_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l17_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l17_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l17_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="posthoc_pattern_response",
        prompt_key="lesson.l17.field.posthoc_pattern_response.prompt",
        hint_key="lesson.l17.field.posthoc_pattern_response.hint",
        options=(
            BriefOption("announce_as_confirmed_driver", "lesson.l17.option.posthoc_pattern_response.announce_as_confirmed_driver"),
            BriefOption("treat_as_new_hypothesis", "lesson.l17.option.posthoc_pattern_response.treat_as_new_hypothesis"),
            BriefOption("ignore_it_entirely", "lesson.l17.option.posthoc_pattern_response.ignore_it_entirely"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l17.field.general_lesson.prompt",
        hint_key="lesson.l17.field.general_lesson.hint",
        options=(
            BriefOption("only_confident_prediction_matters", "lesson.l17.option.general_lesson.only_confident_prediction_matters"),
            BriefOption("big_enough_pattern_skips_testing", "lesson.l17.option.general_lesson.big_enough_pattern_skips_testing"),
            BriefOption("posthoc_needs_its_own_test", "lesson.l17.option.general_lesson.posthoc_needs_its_own_test"),
        ),
    ),
)


def build_lesson_seventeen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 17's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonSeventeenResult once both prediction
    stages and the decision brief have completed."""
    collected: dict = {}
    device_data = generate_device_split_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return PredictionScene(app, "lesson.l17.simulator_title", HYPOTHESIS_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return PredictionScene(app, "lesson.l17.simulator_title", HYPOTHESIS_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l17.twist_title",
            narrative_keys=("dialogue.l17_twist.line1", "dialogue.l17_twist.line2"),
            dataset=device_data,
            comparisons=(
                ("lesson.l17.twist_app_before_label", device_repeat_rate(device_data, "app", "before")),
                ("lesson.l17.twist_app_after_label", device_repeat_rate(device_data, "app", "after")),
                ("lesson.l17.twist_website_before_label", device_repeat_rate(device_data, "website", "before")),
                ("lesson.l17.twist_website_after_label", device_repeat_rate(device_data, "website", "after")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l17.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonSeventeenResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=17, collected=collected, definition=LESSON_17
    )
    return runner, collected

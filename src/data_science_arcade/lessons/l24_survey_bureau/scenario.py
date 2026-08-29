from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l24_survey_bureau.population_data import generate_population_data, simulate_survey
from data_science_arcade.lessons.l24_survey_bureau.requests import SURVEY_REQUESTS
from data_science_arcade.lessons.l24_survey_bureau.scoring import LessonTwentyFourResult
from data_science_arcade.lessons.l24_survey_bureau.twist_data import blended_satisfaction_rate, generate_delivery_survey_data, satisfaction_rate
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.survey_builder_scene import SurveyBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l24_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l24_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l24_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l24_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l24_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="survey_interpretation",
        prompt_key="lesson.l24.field.survey_interpretation.prompt",
        hint_key="lesson.l24.field.survey_interpretation.hint",
        options=(
            BriefOption("exactly_how_all_customers_feel", "lesson.l24.option.survey_interpretation.exactly_how_all_customers_feel"),
            BriefOption("a_useful_signal_not_proof", "lesson.l24.option.survey_interpretation.a_useful_signal_not_proof"),
            BriefOption("tells_us_nothing_useful", "lesson.l24.option.survey_interpretation.tells_us_nothing_useful"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l24.field.general_lesson.prompt",
        hint_key="lesson.l24.field.general_lesson.hint",
        options=(
            BriefOption("bigger_sample_fixes_bias", "lesson.l24.option.general_lesson.bigger_sample_fixes_bias"),
            BriefOption("who_responds_isnt_random", "lesson.l24.option.general_lesson.who_responds_isnt_random"),
            BriefOption("wording_only_matters_when_obvious", "lesson.l24.option.general_lesson.wording_only_matters_when_obvious"),
        ),
    ),
)


def build_lesson_twenty_four_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 24's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentyFourResult once both survey
    stages and the decision brief have completed."""
    collected: dict = {}
    population = generate_population_data()
    delivery_survey = generate_delivery_survey_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return SurveyBuilderScene(app, "lesson.l24.builder_title", population, SURVEY_REQUESTS, simulate_survey, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return SurveyBuilderScene(app, "lesson.l24.builder_title", population, SURVEY_REQUESTS, simulate_survey, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l24.twist_title",
            narrative_keys=("dialogue.l24_twist.line1", "dialogue.l24_twist.line2"),
            dataset=delivery_survey,
            comparisons=(
                ("lesson.l24.twist_surveyed_label", satisfaction_rate(delivery_survey, "delivery_succeeded")),
                ("lesson.l24.twist_never_surveyed_label", satisfaction_rate(delivery_survey, "delivery_failed_or_delayed")),
                ("lesson.l24.twist_blended_label", blended_satisfaction_rate(delivery_survey)),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l24.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentyFourResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

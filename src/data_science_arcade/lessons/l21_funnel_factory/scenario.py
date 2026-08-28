from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l21_funnel_factory.requests import FUNNEL_REQUESTS
from data_science_arcade.lessons.l21_funnel_factory.scoring import LessonTwentyOneResult
from data_science_arcade.lessons.l21_funnel_factory.twist_data import generate_onboarding_data, profile_completion_rate, signup_rate
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.funnel_builder_scene import FunnelBuilderScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l21_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l21_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l21_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l21_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l21_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l21_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l21_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l21_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l21_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l21_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="checkout_investigation_conclusion",
        prompt_key="lesson.l21.field.checkout_investigation_conclusion.prompt",
        hint_key="lesson.l21.field.checkout_investigation_conclusion.hint",
        options=(
            BriefOption("blame_product_page", "lesson.l21.option.checkout_investigation_conclusion.blame_product_page"),
            BriefOption("blame_cart_to_checkout_step", "lesson.l21.option.checkout_investigation_conclusion.blame_cart_to_checkout_step"),
            BriefOption("blame_payment_step", "lesson.l21.option.checkout_investigation_conclusion.blame_payment_step"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l21.field.general_lesson.prompt",
        hint_key="lesson.l21.field.general_lesson.hint",
        options=(
            BriefOption("any_definition_is_equally_valid", "lesson.l21.option.general_lesson.any_definition_is_equally_valid"),
            BriefOption(
                "more_definitions_tested_means_more_accurate", "lesson.l21.option.general_lesson.more_definitions_tested_means_more_accurate"
            ),
            BriefOption(
                "justify_definition_independent_of_result", "lesson.l21.option.general_lesson.justify_definition_independent_of_result"
            ),
        ),
    ),
)


def build_lesson_twenty_one_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 21's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentyOneResult once both funnel
    stages and the decision brief have completed."""
    collected: dict = {}
    onboarding_data = generate_onboarding_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return FunnelBuilderScene(app, "lesson.l21.builder_title", FUNNEL_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return FunnelBuilderScene(app, "lesson.l21.builder_title", FUNNEL_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l21.twist_title",
            narrative_keys=("dialogue.l21_twist.line1", "dialogue.l21_twist.line2"),
            dataset=onboarding_data,
            comparisons=(
                ("lesson.l21.twist_flawed_signup_label", signup_rate(onboarding_data, flawed=True)),
                ("lesson.l21.twist_correct_signup_label", signup_rate(onboarding_data, flawed=False)),
                ("lesson.l21.twist_profile_label", profile_completion_rate(onboarding_data)),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l21.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentyOneResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

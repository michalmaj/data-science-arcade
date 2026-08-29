from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l26_correlation_crime_scene.requests import CORRELATION_REQUESTS
from data_science_arcade.lessons.l26_correlation_crime_scene.scoring import LessonTwentySixResult
from data_science_arcade.lessons.l26_correlation_crime_scene.twist_data import average_ltv, generate_loyalty_ltv_data
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l26_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l26_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l26_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l26_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l26_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="what_is_supported",
        prompt_key="lesson.l26.field.what_is_supported.prompt",
        hint_key="lesson.l26.field.what_is_supported.hint",
        options=(
            BriefOption("direct_causation_confirmed_every_time", "lesson.l26.option.what_is_supported.direct_causation_confirmed_every_time"),
            BriefOption("a_real_pattern_not_a_proven_cause", "lesson.l26.option.what_is_supported.a_real_pattern_not_a_proven_cause"),
            BriefOption("strong_correlation_is_as_good_as_experiment", "lesson.l26.option.what_is_supported.strong_correlation_is_as_good_as_experiment"),
        ),
    ),
    BriefField(
        key="next_evidence",
        prompt_key="lesson.l26.field.next_evidence.prompt",
        hint_key="lesson.l26.field.next_evidence.hint",
        options=(
            BriefOption("a_bigger_sample_of_the_same_data", "lesson.l26.option.next_evidence.a_bigger_sample_of_the_same_data"),
            BriefOption("a_randomized_test_or_ruling_out_alternatives", "lesson.l26.option.next_evidence.a_randomized_test_or_ruling_out_alternatives"),
            BriefOption("a_more_confident_stakeholder", "lesson.l26.option.next_evidence.a_more_confident_stakeholder"),
        ),
    ),
)


def build_lesson_twenty_six_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 26's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentySixResult once both investigation
    stages and the decision brief have completed."""
    collected: dict = {}
    loyalty_data = generate_loyalty_ltv_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return CorrelationScene(app, "lesson.l26.investigation_title", CORRELATION_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return CorrelationScene(app, "lesson.l26.investigation_title", CORRELATION_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l26.twist_title",
            narrative_keys=("dialogue.l26_twist.line1", "dialogue.l26_twist.line2"),
            dataset=loyalty_data,
            comparisons=(
                ("lesson.l26.twist_observational_member_label", average_ltv(loyalty_data, "observational_member")),
                ("lesson.l26.twist_observational_nonmember_label", average_ltv(loyalty_data, "observational_nonmember")),
                ("lesson.l26.twist_randomized_treatment_label", average_ltv(loyalty_data, "randomized_treatment")),
                ("lesson.l26.twist_randomized_control_label", average_ltv(loyalty_data, "randomized_control")),
            ),
            value_format=lambda value: f"${value:.0f}",
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l26.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentySixResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

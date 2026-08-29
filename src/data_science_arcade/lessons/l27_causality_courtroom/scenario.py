from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l27_causality_courtroom.requests import CORRELATION_REQUESTS
from data_science_arcade.lessons.l27_causality_courtroom.scoring import LessonTwentySevenResult
from data_science_arcade.lessons.l27_causality_courtroom.twist_data import conversion_rate, generate_checkout_beta_data
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l27_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l27_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l27_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l27_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l27_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="final_verdict",
        prompt_key="lesson.l27.field.final_verdict.prompt",
        hint_key="lesson.l27.field.final_verdict.hint",
        options=(
            BriefOption("all_confirmed_effects_too_large_for_chance", "lesson.l27.option.final_verdict.all_confirmed_effects_too_large_for_chance"),
            BriefOption("each_needs_a_proper_comparison_group", "lesson.l27.option.final_verdict.each_needs_a_proper_comparison_group"),
            BriefOption("all_should_be_thrown_out", "lesson.l27.option.final_verdict.all_should_be_thrown_out"),
        ),
    ),
    BriefField(
        key="missing_evidence",
        prompt_key="lesson.l27.field.missing_evidence.prompt",
        hint_key="lesson.l27.field.missing_evidence.hint",
        options=(
            BriefOption("more_of_the_same_observational_data", "lesson.l27.option.missing_evidence.more_of_the_same_observational_data"),
            BriefOption("ask_the_self_selected_group", "lesson.l27.option.missing_evidence.ask_the_self_selected_group"),
            BriefOption("randomly_assign_the_treatment", "lesson.l27.option.missing_evidence.randomly_assign_the_treatment"),
        ),
    ),
)


def build_lesson_twenty_seven_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 27's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentySevenResult once both case
    stages and the decision brief have completed.

    Reuses CorrelationScene and its framework dataclasses directly from
    Lesson 26 rather than building a new scene - see IMPLEMENTATION_STATE
    for why the human reviewer chose that over a new interaction shape."""
    collected: dict = {}
    checkout_beta = generate_checkout_beta_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return CorrelationScene(app, "lesson.l27.investigation_title", CORRELATION_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return CorrelationScene(app, "lesson.l27.investigation_title", CORRELATION_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l27.twist_title",
            narrative_keys=("dialogue.l27_twist.line1", "dialogue.l27_twist.line2"),
            dataset=checkout_beta,
            comparisons=(
                ("lesson.l27.twist_beta_label", conversion_rate(checkout_beta, "beta_opt_in")),
                ("lesson.l27.twist_nonbeta_label", conversion_rate(checkout_beta, "non_beta")),
                ("lesson.l27.twist_randomized_treatment_label", conversion_rate(checkout_beta, "randomized_treatment")),
                ("lesson.l27.twist_randomized_control_label", conversion_rate(checkout_beta, "randomized_control")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l27.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentySevenResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

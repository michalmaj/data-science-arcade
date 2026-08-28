from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l22_cohort_observatory.cohort_data import build_cohort_matrix, generate_cohort_data, retention_rate
from data_science_arcade.lessons.l22_cohort_observatory.requests import COHORT_REQUESTS
from data_science_arcade.lessons.l22_cohort_observatory.scoring import LessonTwentyTwoResult
from data_science_arcade.lessons.l22_cohort_observatory.twist_data import generate_november_cohort_data, november_retention_rate
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.cohort_matrix_scene import CohortMatrixScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l22_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l22_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l22_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l22_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l22_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="retention_verdict",
        prompt_key="lesson.l22.field.retention_verdict.prompt",
        hint_key="lesson.l22.field.retention_verdict.hint",
        options=(
            BriefOption("yes_clearly_improved", "lesson.l22.option.retention_verdict.yes_clearly_improved"),
            BriefOption("too_early_to_tell", "lesson.l22.option.retention_verdict.too_early_to_tell"),
            BriefOption("no_clearly_declined", "lesson.l22.option.retention_verdict.no_clearly_declined"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l22.field.general_lesson.prompt",
        hint_key="lesson.l22.field.general_lesson.hint",
        options=(
            BriefOption("newer_always_means_better", "lesson.l22.option.general_lesson.newer_always_means_better"),
            BriefOption(
                "once_a_cohort_looks_good_early_it_stays_good", "lesson.l22.option.general_lesson.once_a_cohort_looks_good_early_it_stays_good"
            ),
            BriefOption("same_age_comparison_is_the_only_fair_one", "lesson.l22.option.general_lesson.same_age_comparison_is_the_only_fair_one"),
        ),
    ),
)


def build_lesson_twenty_two_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 22's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonTwentyTwoResult once both matrix
    stages and the decision brief have completed."""
    collected: dict = {}
    cohort_data = generate_cohort_data()
    matrix = build_cohort_matrix(cohort_data)
    november_data = generate_november_cohort_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return CohortMatrixScene(app, "lesson.l22.matrix_title", matrix, COHORT_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return CohortMatrixScene(app, "lesson.l22.matrix_title", matrix, COHORT_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l22.twist_title",
            narrative_keys=("dialogue.l22_twist.line1", "dialogue.l22_twist.line2"),
            dataset=november_data,
            comparisons=(
                ("lesson.l22.twist_november_month1_label", november_retention_rate(november_data, 1)),
                ("lesson.l22.twist_january_month1_label", retention_rate(cohort_data, "jan", 1)),
                ("lesson.l22.twist_november_month5_label", november_retention_rate(november_data, 5)),
                ("lesson.l22.twist_january_month5_label", retention_rate(cohort_data, "jan", 5)),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l22.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonTwentyTwoResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

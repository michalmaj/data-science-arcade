from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l15_segment_detective.funnel_data import generate_device_funnel, overall_rate
from data_science_arcade.lessons.l15_segment_detective.requests import SEGMENT_REQUESTS
from data_science_arcade.lessons.l15_segment_detective.scoring import LessonFifteenResult
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l15_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l15_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l15_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l15_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l15_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l15_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l15_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l15_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l15_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l15_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="correct_level_of_analysis",
        prompt_key="lesson.l15.field.correct_level_of_analysis.prompt",
        hint_key="lesson.l15.field.correct_level_of_analysis.hint",
        options=(
            BriefOption("report_both_levels", "lesson.l15.option.correct_level_of_analysis.report_both_levels"),
            BriefOption("trust_aggregate_only", "lesson.l15.option.correct_level_of_analysis.trust_aggregate_only"),
            BriefOption("trust_segments_only", "lesson.l15.option.correct_level_of_analysis.trust_segments_only"),
        ),
    ),
    BriefField(
        key="paradox_lesson",
        prompt_key="lesson.l15.field.paradox_lesson.prompt",
        hint_key="lesson.l15.field.paradox_lesson.hint",
        options=(
            BriefOption("mix_shift_can_hide_declines", "lesson.l15.option.paradox_lesson.mix_shift_can_hide_declines"),
            BriefOption("aggregate_always_wrong", "lesson.l15.option.paradox_lesson.aggregate_always_wrong"),
            BriefOption("only_matters_for_two_groups", "lesson.l15.option.paradox_lesson.only_matters_for_two_groups"),
        ),
    ),
)


def build_lesson_fifteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 15's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonFifteenResult once both slicer stages
    and the decision brief have completed."""
    collected: dict = {}
    device_funnel = generate_device_funnel()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return SegmentSlicerScene(app, "lesson.l15.slicer_title", SEGMENT_REQUESTS, on_complete, guided=True)

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return SegmentSlicerScene(app, "lesson.l15.slicer_title", SEGMENT_REQUESTS, on_complete, guided=False)

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l15.twist_title",
            narrative_keys=("dialogue.l15_twist.line1", "dialogue.l15_twist.line2"),
            dataset=device_funnel,
            comparisons=(
                ("lesson.l15.twist_q1_label", overall_rate(device_funnel, "Q1")),
                ("lesson.l15.twist_q2_label", overall_rate(device_funnel, "Q2")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l15.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonFifteenResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

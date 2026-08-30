from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.segment import Segment
from data_science_arcade.lessons.l18_randomization_control_room.assignment_data import relative_imbalance
from data_science_arcade.lessons.l18_randomization_control_room.definition import LESSON_18
from data_science_arcade.lessons.l18_randomization_control_room.requests import ASSIGNMENT_REQUESTS
from data_science_arcade.lessons.l18_randomization_control_room.scoring import LessonEighteenResult
from data_science_arcade.lessons.l18_randomization_control_room.twist_data import generate_platform_split_data, ios_share
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l18_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l18_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l18_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l18_investigation.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l18_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l18_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l18_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l18_debrief.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l18_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l18_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="experiment_verdict",
        prompt_key="lesson.l18.field.experiment_verdict.prompt",
        hint_key="lesson.l18.field.experiment_verdict.hint",
        options=(
            BriefOption("approve", "lesson.l18.option.experiment_verdict.approve"),
            BriefOption("repair_and_rerun", "lesson.l18.option.experiment_verdict.repair_and_rerun"),
            BriefOption("invalidate", "lesson.l18.option.experiment_verdict.invalidate"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l18.field.general_lesson.prompt",
        hint_key="lesson.l18.field.general_lesson.hint",
        options=(
            BriefOption("any_split_is_fine_if_sizes_match", "lesson.l18.option.general_lesson.any_split_is_fine_if_sizes_match"),
            BriefOption("deterministic_rules_are_always_safer", "lesson.l18.option.general_lesson.deterministic_rules_are_always_safer"),
            BriefOption("srm_passing_isnt_enough", "lesson.l18.option.general_lesson.srm_passing_isnt_enough"),
        ),
    ),
)


def _format_balance_value(segment: Segment, value: float) -> str:
    if segment.key == "covariate":
        return f"{value:.0%}"
    if segment.key == "tenure":
        return f"{value:.0f}"
    return f"{value:,.0f}"


def build_lesson_eighteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 18's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonEighteenResult once both diagnostic
    stages and the decision brief have completed."""
    collected: dict = {}
    platform_data = generate_platform_split_data()

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(choices):
            collected["guided_choices"] = choices
            advance()

        return SegmentSlicerScene(
            app,
            "lesson.l18.simulator_title",
            ASSIGNMENT_REQUESTS,
            on_complete,
            guided=True,
            row_column_label_key="lesson.l18.row_column_label",
            before_column_label_key="lesson.l18.treatment_column_label",
            after_column_label_key="lesson.l18.control_column_label",
            pick_hint_key="lesson.l18.pick_a_rule_hint",
            value_format=_format_balance_value,
            flag_check=relative_imbalance,
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(choices):
            collected["independent_choices"] = choices
            advance()

        return SegmentSlicerScene(
            app,
            "lesson.l18.simulator_title",
            ASSIGNMENT_REQUESTS,
            on_complete,
            guided=False,
            row_column_label_key="lesson.l18.row_column_label",
            before_column_label_key="lesson.l18.treatment_column_label",
            after_column_label_key="lesson.l18.control_column_label",
            pick_hint_key="lesson.l18.pick_a_rule_hint",
            value_format=_format_balance_value,
            flag_check=relative_imbalance,
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l18.twist_title",
            narrative_keys=("dialogue.l18_twist.line1", "dialogue.l18_twist.line2"),
            dataset=platform_data,
            comparisons=(
                ("lesson.l18.twist_treatment_ios_label", ios_share(platform_data, "treatment")),
                ("lesson.l18.twist_control_ios_label", ios_share(platform_data, "control")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l18.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonEighteenResult(
            guided_choices=collected.get("guided_choices", {}),
            independent_choices=collected.get("independent_choices", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(
        app, stages, on_finished=finished, lesson_number=18, collected=collected, definition=LESSON_18
    )
    return runner, collected

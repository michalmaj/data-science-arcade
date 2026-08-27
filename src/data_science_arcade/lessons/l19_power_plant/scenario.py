from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.framework.sampling import SamplingGroup
from data_science_arcade.lessons.l19_power_plant.experiments import EXPERIMENTS, SAMPLING_GROUPS, STEP, TOTAL_WEEKS, detectable_effect_for
from data_science_arcade.lessons.l19_power_plant.scoring import LessonNineteenResult
from data_science_arcade.lessons.l19_power_plant.twist_data import conversion_rate, generate_banner_experiment_data
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import FINANCE_LEAD, MENTOR
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene
from data_science_arcade.ui.twist_reveal_scene import TwistRevealScene

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l19_briefing.line1"),
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l19_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_briefing.line3"),
    )
)

INVESTIGATION_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_investigation.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_investigation.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_investigation.line3"),
    )
)

INDEPENDENT_INTRO_DIALOGUE = Dialogue(
    lines=(DialogueLine(speaker=MENTOR, text_key="dialogue.l19_independent_intro.line1"),)
)

DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=FINANCE_LEAD, text_key="dialogue.l19_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l19_debrief.line3"),
    )
)

DECISION_FIELDS: tuple[BriefField, ...] = (
    BriefField(
        key="banner_result_response",
        prompt_key="lesson.l19.field.banner_result_response.prompt",
        hint_key="lesson.l19.field.banner_result_response.hint",
        options=(
            BriefOption("ship_it_because_its_real", "lesson.l19.option.banner_result_response.ship_it_because_its_real"),
            BriefOption("treat_as_not_worth_shipping", "lesson.l19.option.banner_result_response.treat_as_not_worth_shipping"),
            BriefOption("run_it_longer_to_grow_the_effect", "lesson.l19.option.banner_result_response.run_it_longer_to_grow_the_effect"),
        ),
    ),
    BriefField(
        key="general_lesson",
        prompt_key="lesson.l19.field.general_lesson.prompt",
        hint_key="lesson.l19.field.general_lesson.hint",
        options=(
            BriefOption("bigger_sample_always_worth_it", "lesson.l19.option.general_lesson.bigger_sample_always_worth_it"),
            BriefOption("undetected_effects_dont_exist", "lesson.l19.option.general_lesson.undetected_effects_dont_exist"),
            BriefOption(
                "statistical_and_practical_significance_differ", "lesson.l19.option.general_lesson.statistical_and_practical_significance_differ"
            ),
        ),
    ),
)

_PLANS_BY_KEY = {plan.key: plan for plan in EXPERIMENTS}
DIAGNOSTIC_ROW_SPACING = 92


def _make_diagnostic(app):
    def diagnostic(group: SamplingGroup, weeks: int) -> tuple[str, bool] | None:
        if weeks == 0:
            return None
        plan = _PLANS_BY_KEY[group.key]
        mde_pts = detectable_effect_for(group.key, weeks) * 100
        threshold_pts = plan.minimum_useful_effect * 100
        enough = mde_pts <= threshold_pts
        loc = app.localization
        status = loc.t("lesson.l19.status_enough" if enough else "lesson.l19.status_not_enough")
        text = f"{loc.t('lesson.l19.detectable_label')} {mde_pts:.1f}pt ({loc.t('lesson.l19.need_label')} {threshold_pts:.1f}pt) - {status}"
        return text, not enough

    return diagnostic


def build_lesson_nineteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 19's 8-stage sequence. Returns the runner plus a
    dict that fills in with the player's results as they progress -
    `result` holds the final LessonNineteenResult once both allocator
    stages and the decision brief have completed."""
    collected: dict = {}
    banner_data = generate_banner_experiment_data()
    diagnostic = _make_diagnostic(app)

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def investigation(advance):
        return DialogueScene(app, INVESTIGATION_DIALOGUE, on_complete=advance)

    def guided_work(advance):
        def on_complete(allocation):
            collected["guided_allocation"] = allocation
            advance()

        return SamplingAllocatorScene(
            app,
            "lesson.l19.allocator_title",
            "lesson.l19.allocator_prompt",
            SAMPLING_GROUPS,
            TOTAL_WEEKS,
            STEP,
            on_complete,
            guided=True,
            hint_key="lesson.l19.allocator_hint",
            diagnostic=diagnostic,
            row_spacing=DIAGNOSTIC_ROW_SPACING,
        )

    def independent_intro(advance):
        return DialogueScene(app, INDEPENDENT_INTRO_DIALOGUE, on_complete=advance)

    def independent_challenge(advance):
        def on_complete(allocation):
            collected["independent_allocation"] = allocation
            advance()

        return SamplingAllocatorScene(
            app,
            "lesson.l19.allocator_title",
            "lesson.l19.allocator_prompt",
            SAMPLING_GROUPS,
            TOTAL_WEEKS,
            STEP,
            on_complete,
            guided=False,
            diagnostic=diagnostic,
            row_spacing=DIAGNOSTIC_ROW_SPACING,
        )

    def twist(advance):
        return TwistRevealScene(
            app,
            title_key="lesson.l19.twist_title",
            narrative_keys=("dialogue.l19_twist.line1", "dialogue.l19_twist.line2"),
            dataset=banner_data,
            comparisons=(
                ("lesson.l19.twist_control_label", conversion_rate(banner_data, "control")),
                ("lesson.l19.twist_treatment_label", conversion_rate(banner_data, "treatment")),
            ),
            on_complete=advance,
        )

    def decision(advance):
        def on_complete(brief):
            collected["decision_brief"] = brief
            advance()

        return BriefBuilderScene(app, "lesson.l19.decision_title", DECISION_FIELDS, on_complete, guided=True)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        collected["result"] = LessonNineteenResult(
            guided_allocation=collected.get("guided_allocation", {}),
            independent_allocation=collected.get("independent_allocation", {}),
            decision_brief=collected.get("decision_brief", {}),
        )
        on_finished(collected["result"])

    stages = [briefing, investigation, guided_work, independent_intro, independent_challenge, twist, decision, debrief]
    runner = LessonRunner(app, stages, on_finished=finished)
    return runner, collected

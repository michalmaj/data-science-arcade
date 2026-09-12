from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.inspection import InspectionOption, InspectionPrompt
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l18_randomization_control_room import data as d
from data_science_arcade.lessons.l18_randomization_control_room.definition import LESSON_18
from data_science_arcade.lessons.l18_randomization_control_room.scoring import (
    ASSIGNMENT_BALANCE_EVIDENCE_KEY,
    ASSIGNMENT_MECHANISM_EVIDENCE_KEY,
    CRITICAL_EVIDENCE_KEYS,
    MECHANISM_CONTRAST_EVIDENCE_KEY,
    LessonEighteenResult,
    score_lesson_eighteen,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.assignment_audit_scene import AssignmentAuditScene, AuditRow
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.workbench_scene import WorkbenchScene, WorkbenchTab
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -----------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l18_briefing.line1"),
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l18_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l18_briefing.line3"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l18_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l18_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l18_debrief.line3"),
    )
)
REVISION_OFFER_LINE_KEYS = ("lesson.l18.revision_offer.line1",)
MASTERY_DIALOGUE_KEYS = ("dialogue.l18_mastery.line1", "dialogue.l18_mastery.line2", "dialogue.l18_mastery.line3")

# --- Ground truth, precomputed once (real, hand-verified via a real
# pandas script - see data.py's own module docstring) ----------------------

ROSTER = d.generate_roster().frame

MECHANISM_LABEL_KEYS = {
    d.ID_PARITY: "lesson.l18.mechanism.id_parity.label",
    d.SIMPLE_RANDOM: "lesson.l18.mechanism.simple_random.label",
    d.STRATIFIED_RANDOM: "lesson.l18.mechanism.stratified_random.label",
}
MECHANISM_DESCRIPTION_KEYS = {
    d.ID_PARITY: "lesson.l18.mechanism.id_parity.description",
    d.SIMPLE_RANDOM: "lesson.l18.mechanism.simple_random.description",
    d.STRATIFIED_RANDOM: "lesson.l18.mechanism.stratified_random.description",
}
AUDIT_NARRATIVE_KEYS = {
    d.ID_PARITY: "dialogue.l18_audit_parity.line1",
    d.SIMPLE_RANDOM: "dialogue.l18_audit_simple.line1",
    d.STRATIFIED_RANDOM: "dialogue.l18_audit_stratified.line1",
}

# The counterexample every final design must see, per the mandatory
# mechanism-contrast beat: parity's own trap payoff is contrasted against
# a genuinely random design; a genuinely random final design (simple or
# stratified) is contrasted against parity's own deterministic-but-
# balanced-looking split. Never a re-pick - the final design is already
# locked by the time this runs.
COUNTEREXAMPLE_DESIGN = {
    d.ID_PARITY: d.SIMPLE_RANDOM,
    d.SIMPLE_RANDOM: d.ID_PARITY,
    d.STRATIFIED_RANDOM: d.ID_PARITY,
}
CONTRAST_NARRATIVE_KEYS = {
    d.ID_PARITY: "dialogue.l18_contrast_from_parity.line1",
    d.SIMPLE_RANDOM: "dialogue.l18_contrast_from_random.line1",
    d.STRATIFIED_RANDOM: "dialogue.l18_contrast_from_random.line1",
}
FINAL_DESIGN_ANNOUNCEMENT_KEY = {
    d.ID_PARITY: "dialogue.l18_final_design_parity.line1",
    d.SIMPLE_RANDOM: "dialogue.l18_final_design_simple.line1",
    d.STRATIFIED_RANDOM: "dialogue.l18_final_design_stratified.line1",
}

# --- Roster inspection - grain, before any design is picked -----------------

INSPECTION_PROMPT = InspectionPrompt(
    prompt_key="lesson.l18.inspection.prompt",
    hint_key="lesson.l18.inspection.hint",
    options=(
        InspectionOption("one_row_per_customer", "lesson.l18.inspection.option.one_row_per_customer"),
        InspectionOption("one_row_per_platform", "lesson.l18.inspection.option.one_row_per_platform"),
        InspectionOption("one_row_per_signup_week", "lesson.l18.inspection.option.one_row_per_signup_week"),
    ),
)

# --- The blind design pick - one real field, 3 options, no numbers shown ---

DESIGN_CHOICE_FIELD = BriefField(
    key="assignment_design",
    prompt_key="lesson.l18.design_choice.prompt",
    hint_key="lesson.l18.design_choice.hint",
    options=(
        BriefOption(d.ID_PARITY, "lesson.l18.design_choice.option.id_parity"),
        BriefOption(d.SIMPLE_RANDOM, "lesson.l18.design_choice.option.simple_random"),
        BriefOption(d.STRATIFIED_RANDOM, "lesson.l18.design_choice.option.stratified_random"),
    ),
)


def _pct(value: float) -> str:
    return f"{value:.1f}%"


def _days(value: float) -> str:
    return f"{value:.1f}d"


def _count(value: float) -> str:
    return f"{value:.0f}"


def _pct_gap(value: float) -> str:
    return f"{value:+.1f}pp"


def _days_gap(value: float) -> str:
    return f"{value:+.1f}d"


def _count_gap(value: float) -> str:
    return f"{value:+.0f}"


def _build_audit_rows(audit: dict) -> tuple[AuditRow, ...]:
    return (
        AuditRow("n", "lesson.l18.audit.row_n", audit["n_treatment"], audit["n_control"], _count, _count_gap),
        AuditRow(
            "ios_share",
            "lesson.l18.audit.row_ios_share",
            audit["ios_share_treatment"] * 100,
            audit["ios_share_control"] * 100,
            _pct,
            _pct_gap,
        ),
        AuditRow(
            "avg_tenure",
            "lesson.l18.audit.row_avg_tenure",
            audit["avg_tenure_treatment"],
            audit["avg_tenure_control"],
            _days,
            _days_gap,
        ),
    )


# --- Optional mastery: NovaMart Logistics packaging experiment, a
# different domain - given, not chosen; real row-level generator. --------

PACKAGING_FRAME = d.generate_packaging_experiment()
PACKAGING_AUDIT = d.packaging_audit_values(PACKAGING_FRAME)

MASTERY_MECHANISM_JUDGMENT_FIELD = BriefField(
    key="mastery_mechanism_judgment",
    prompt_key="lesson.l18.mastery.field.mechanism_judgment.prompt",
    options=(
        BriefOption("genuinely_randomly_assigned_per_provenance", "lesson.l18.mastery.option.mechanism_judgment.genuinely_randomly_assigned_per_provenance"),
        BriefOption("not_really_random_just_looks_assigned", "lesson.l18.mastery.option.mechanism_judgment.not_really_random_just_looks_assigned"),
        BriefOption("cant_tell_without_more_info", "lesson.l18.mastery.option.mechanism_judgment.cant_tell_without_more_info"),
    ),
)
MASTERY_IMBALANCE_MEANING_FIELD = BriefField(
    key="mastery_imbalance_meaning",
    prompt_key="lesson.l18.mastery.field.imbalance_meaning.prompt",
    options=(
        BriefOption("real_diagnostic_fact_not_invalidating", "lesson.l18.mastery.option.imbalance_meaning.real_diagnostic_fact_not_invalidating"),
        BriefOption("invalidates_the_randomization", "lesson.l18.mastery.option.imbalance_meaning.invalidates_the_randomization"),
        BriefOption("means_nothing_at_all", "lesson.l18.mastery.option.imbalance_meaning.means_nothing_at_all"),
    ),
)
MASTERY_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l18.mastery.field.evidence.prompt",
    options=(
        BriefOption(
            "provenance_log_confirms_seeded_random_assignment", "lesson.l18.mastery.option.evidence.provenance_log_confirms_seeded_random_assignment"
        ),
        BriefOption("distance_gap_is_a_real_but_modest_imbalance", "lesson.l18.mastery.option.evidence.distance_gap_is_a_real_but_modest_imbalance"),
        BriefOption("group_sizes_being_equal_proves_randomization", "lesson.l18.mastery.option.evidence.group_sizes_being_equal_proves_randomization"),
        BriefOption("outcome_data_confirms_it_worked", "lesson.l18.mastery.option.evidence.outcome_data_confirms_it_worked"),
    ),
    min_count=1,
    max_count=2,
)

# --- Final Randomization Brief - 6 fields + Evidence ------------------------

MECHANISM_CLASSIFICATION_FIELD = BriefField(
    key="mechanism_classification",
    prompt_key="lesson.l18.decision.mechanism_classification.prompt",
    options=(
        BriefOption("deterministic_not_randomized", "lesson.l18.decision.mechanism_classification.option.deterministic_not_randomized"),
        BriefOption("valid_random_fixed_size", "lesson.l18.decision.mechanism_classification.option.valid_random_fixed_size"),
        BriefOption("valid_random_within_strata", "lesson.l18.decision.mechanism_classification.option.valid_random_within_strata"),
    ),
)
WHAT_MAKES_RANDOMIZED_FIELD = BriefField(
    key="what_makes_assignment_randomized",
    prompt_key="lesson.l18.decision.what_makes_randomized.prompt",
    options=(
        BriefOption("decided_by_random_mechanism_before_outcome", "lesson.l18.decision.what_makes_randomized.option.decided_by_random_mechanism_before_outcome"),
        BriefOption("group_sizes_came_out_even", "lesson.l18.decision.what_makes_randomized.option.group_sizes_came_out_even"),
        BriefOption("customer_ids_were_sorted_consistently", "lesson.l18.decision.what_makes_randomized.option.customer_ids_were_sorted_consistently"),
    ),
)
EQUAL_GROUP_SIZES_FIELD = BriefField(
    key="what_equal_group_sizes_establish",
    prompt_key="lesson.l18.decision.equal_group_sizes.prompt",
    options=(
        BriefOption("establishes_nothing_about_mechanism_alone", "lesson.l18.decision.equal_group_sizes.option.establishes_nothing_about_mechanism_alone"),
        BriefOption("proves_the_assignment_was_random", "lesson.l18.decision.equal_group_sizes.option.proves_the_assignment_was_random"),
        BriefOption("proves_covariates_are_balanced_too", "lesson.l18.decision.equal_group_sizes.option.proves_covariates_are_balanced_too"),
    ),
)
SMALL_IMBALANCE_FIELD = BriefField(
    key="how_to_interpret_small_realized_imbalance",
    prompt_key="lesson.l18.decision.small_imbalance.prompt",
    options=(
        BriefOption("does_not_invalidate_valid_randomization", "lesson.l18.decision.small_imbalance.option.does_not_invalidate_valid_randomization"),
        BriefOption("proves_the_randomization_failed", "lesson.l18.decision.small_imbalance.option.proves_the_randomization_failed"),
        BriefOption("means_nothing_and_can_be_ignored", "lesson.l18.decision.small_imbalance.option.means_nothing_and_can_be_ignored"),
    ),
)
WHY_STRATIFY_FIELD = BriefField(
    key="why_stratify_on_platform",
    prompt_key="lesson.l18.decision.why_stratify.prompt",
    options=(
        BriefOption(
            "guarantees_balance_on_a_known_covariate_randomness_within_strata",
            "lesson.l18.decision.why_stratify.option.guarantees_balance_on_a_known_covariate_randomness_within_strata",
        ),
        BriefOption("platform_decides_which_group_a_customer_joins", "lesson.l18.decision.why_stratify.option.platform_decides_which_group_a_customer_joins"),
        BriefOption("removes_the_need_for_randomization_entirely", "lesson.l18.decision.why_stratify.option.removes_the_need_for_randomization_entirely"),
    ),
)
WHAT_MUST_STAY_SEALED_FIELD = BriefField(
    key="what_must_stay_sealed_during_assignment",
    prompt_key="lesson.l18.decision.what_must_stay_sealed.prompt",
    options=(
        BriefOption(
            "determined_without_outcomes_or_post_treatment_info", "lesson.l18.decision.what_must_stay_sealed.option.determined_without_outcomes_or_post_treatment_info"
        ),
        BriefOption(
            "just_the_outcome_column_needs_to_be_hidden_from_view", "lesson.l18.decision.what_must_stay_sealed.option.just_the_outcome_column_needs_to_be_hidden_from_view"
        ),
        BriefOption("nothing_needs_to_stay_sealed_if_the_seed_is_fixed", "lesson.l18.decision.what_must_stay_sealed.option.nothing_needs_to_stay_sealed_if_the_seed_is_fixed"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l18.decision.evidence.prompt", min_count=2, max_count=3)
DECISION_FIELDS: tuple[BriefField, ...] = (
    MECHANISM_CLASSIFICATION_FIELD,
    WHAT_MAKES_RANDOMIZED_FIELD,
    EQUAL_GROUP_SIZES_FIELD,
    SMALL_IMBALANCE_FIELD,
    WHY_STRATIFY_FIELD,
    WHAT_MUST_STAY_SEALED_FIELD,
)


def build_lesson_eighteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 18's real investigation: one real 1200-customer
    NovaMart Go eligible roster (data.py). No outcome column exists
    anywhere in this lesson - the pilot's own outcome stays fully sealed
    from start to finish; L19/L20 are where it finally gets touched.

    The student picks one of 3 assignment designs blind (no numbers
    visible), the pick is really executed, and a real AssignmentAuditScene
    shows the consequence - never a live candidate-switcher. One real
    revision is offered; whichever design is final gets a second real
    audit. A mandatory mechanism-contrast beat then shows the *other*
    kind of design's own real consequence (parity's trap for a random
    final design, or a genuinely random design's own small imbalance for
    a parity final design) - every student sees both of this lesson's
    load-bearing counterexamples, regardless of path. METHOD reads only
    `collected["final_design"]`, never anything the Final Brief claims."""
    collected: dict = {}
    context = LessonContext()

    def _restore_context_if_present() -> None:
        data_ = collected.get("analytical_context")
        if data_ is not None:
            context.restore_from_dict(data_)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    def roster_inspection(advance):
        def on_complete(_resolution):
            advance()

        return WorkbenchScene(
            app,
            d.generate_roster(),
            issues=(),
            on_complete=on_complete,
            inspection_prompt=INSPECTION_PROMPT,
            visible_tabs=(WorkbenchTab.DATA, WorkbenchTab.PYTHON),
        )

    # --- Blind pick -> real execution -> real audit -> one real revision ---

    def design_pick_and_audit(advance):
        def _build_audit_scene(design_key: str, on_complete):
            group = d.execute_design(design_key, ROSTER)
            audit = d.audit_values(ROSTER, group)
            return AssignmentAuditScene(
                app,
                title_key="lesson.l18.audit.title",
                narrative_keys=(AUDIT_NARRATIVE_KEYS[design_key],),
                mechanism_label_key=MECHANISM_LABEL_KEYS[design_key],
                mechanism_description_key=MECHANISM_DESCRIPTION_KEYS[design_key],
                rows=_build_audit_rows(audit),
                mirror_action_label_key="lesson.l18.audit.action_label",
                mirror_python_code=d.DESIGN_MIRROR[design_key],
                context=context,
                record_key="assignment_audit",
                on_complete=on_complete,
                mechanism_evidence_key=ASSIGNMENT_MECHANISM_EVIDENCE_KEY,
                balance_evidence_key=ASSIGNMENT_BALANCE_EVIDENCE_KEY,
            )

        def on_initial_pick_complete(choices):
            design_key = choices["assignment_design"]
            collected["initial_design"] = design_key
            collected["final_design"] = design_key
            outer.advance_to_second()

        def build_after_initial_pick():
            design_key = collected["initial_design"]

            def on_initial_audit_complete():
                _sync_context_into_collected()
                inner.advance_to_second()

            initial_audit_scene = _build_audit_scene(design_key, on_initial_audit_complete)
            inner = SequenceScene(app, first=initial_audit_scene, build_second=build_revision_offer)
            return inner

        def build_revision_offer():
            def build_revision_task(on_task_complete):
                def on_revised(choices):
                    revised_key = choices["assignment_design"]
                    collected["final_design"] = revised_key
                    revision_composite.advance_to_second()

                def build_second_audit():
                    def on_second_audit_complete():
                        _sync_context_into_collected()
                        on_task_complete(collected["final_design"])

                    return _build_audit_scene(collected["final_design"], on_second_audit_complete)

                revision_pick_scene = BriefBuilderScene(
                    app,
                    "lesson.l18.design_choice.revision_title",
                    (DESIGN_CHOICE_FIELD,),
                    on_revised,
                    guided=False,
                    initial_choices={"assignment_design": collected["final_design"]},
                )
                revision_composite = SequenceScene(app, first=revision_pick_scene, build_second=build_second_audit)
                return revision_composite

            def on_offer_complete(_engaged, _result):
                _sync_context_into_collected()
                advance()

            return OfferThenTaskScene(
                app,
                build_revision_task,
                on_offer_complete,
                title_key="lesson.l18.revision_offer.title",
                line_keys=REVISION_OFFER_LINE_KEYS,
                engage_label_key="lesson.l18.revision_offer.revise",
                skip_label_key="lesson.l18.revision_offer.keep",
            )

        initial_pick_scene = BriefBuilderScene(app, "lesson.l18.design_choice.title", (DESIGN_CHOICE_FIELD,), on_initial_pick_complete, guided=True)
        outer = SequenceScene(app, first=initial_pick_scene, build_second=build_after_initial_pick)
        return outer

    # --- Mandatory mechanism contrast - the missing counterexample,
    # never a re-pick, final design already stands. -------------------------

    def mechanism_contrast(advance):
        final_key = collected["final_design"]
        counterexample_key = COUNTEREXAMPLE_DESIGN[final_key]
        group = d.execute_design(counterexample_key, ROSTER)
        audit = d.audit_values(ROSTER, group)

        def on_complete():
            _sync_context_into_collected()
            advance()

        return AssignmentAuditScene(
            app,
            title_key="lesson.l18.contrast.title",
            narrative_keys=(CONTRAST_NARRATIVE_KEYS[final_key],),
            mechanism_label_key=MECHANISM_LABEL_KEYS[counterexample_key],
            mechanism_description_key=MECHANISM_DESCRIPTION_KEYS[counterexample_key],
            rows=_build_audit_rows(audit),
            mirror_action_label_key="lesson.l18.contrast.action_label",
            mirror_python_code=d.DESIGN_MIRROR[counterexample_key],
            context=context,
            record_key="mechanism_contrast",
            on_complete=on_complete,
            contrast_evidence_key=MECHANISM_CONTRAST_EVIDENCE_KEY,
        )

    def final_design_announcement(advance):
        final_key = collected["final_design"]
        dialogue = Dialogue(lines=(DialogueLine(speaker=MENTOR, text_key=FINAL_DESIGN_ANNOUNCEMENT_KEY[final_key]),))
        return DialogueScene(app, dialogue, on_complete=advance)

    # --- Final Randomization Brief ---

    def final_randomization_brief(advance):
        def on_complete(choices):
            collected["decision"] = choices
            context.set_decision(
                DecisionState(
                    choices={k: v for k, v in choices.items() if isinstance(v, str)},
                    supporting_evidence_ids=tuple(choices["evidence"]),
                )
            )
            _sync_context_into_collected()
            advance()

        return DecisionBuilderScene(
            app,
            "lesson.l18.decision_title",
            steps=(*DECISION_FIELDS, DECISION_EVIDENCE_FIELD),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l18.mastery.title",
                (MASTERY_MECHANISM_JUDGMENT_FIELD, MASTERY_IMBALANCE_MEANING_FIELD, MASTERY_EVIDENCE_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(app, build_task, on_complete, title_key="lesson.l18.mastery.title", line_keys=MASTERY_DIALOGUE_KEYS)

    # --- Feedback / Debrief ---

    def _critical_evidence_present(selected_evidence_ids: set[str]) -> tuple[str, ...]:
        present: set[str] = set()
        for item in context.evidence:
            if item.id not in selected_evidence_ids:
                continue
            for critical_key in CRITICAL_EVIDENCE_KEYS:
                if critical_key in item.label_key:
                    present.add(critical_key)
        return tuple(sorted(present))

    def _build_result() -> LessonEighteenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonEighteenResult(
            initial_design=collected.get("initial_design", ""),
            final_design=collected.get("final_design", ""),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_18.number, 0)
        evaluation = score_lesson_eighteen(result, LESSON_18, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        roster_inspection,
        design_pick_and_audit,
        mechanism_contrast,
        final_design_announcement,
        final_randomization_brief,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=18,
        collected=collected,
        definition=LESSON_18,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

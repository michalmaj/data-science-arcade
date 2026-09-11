from data_science_arcade.lessons.framework.brief import BriefField, BriefOption, MultiChoiceField
from data_science_arcade.lessons.framework.runner import LessonRunner
from data_science_arcade.lessons.l15_segment_detective.definition import LESSON_15
from data_science_arcade.lessons.l15_segment_detective.scoring import CRITICAL_EVIDENCE_KEYS, LessonFifteenResult, score_lesson_fifteen
from data_science_arcade.lessons.l15_segment_detective.sessions import (
    DEVICE_RATE_PCT,
    DEVICE_SHARE_PCT,
    OVERALL_RATE_PCT,
    Q2_AT_Q1_MIX_PCT,
    REGION_RATE_PCT,
    REGION_SHARE_PCT,
)
from data_science_arcade.narrative.dialogue import Dialogue, DialogueLine
from data_science_arcade.narrative.npc import DATA_ENGINEER, MENTOR, PRODUCT_MANAGER
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.comparison_reveal_scene import ComparisonRevealScene, ComparisonValue, InterpretOption
from data_science_arcade.ui.composite_scene import OfferThenTaskScene, SequenceScene
from data_science_arcade.ui.decision_builder_scene import DecisionBuilderScene, EvidenceField
from data_science_arcade.ui.dialogue_scene import DialogueScene
from data_science_arcade.ui.lesson_feedback_scene import LessonFeedbackScene
from data_science_arcade.ui.segment_mix_scene import DimensionOption, SegmentMixScene, SegmentRow
from data_science_arcade.workbench.context import DecisionState, LessonContext

# --- The Ask -------------------------------------------------------------

BRIEFING_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l15_briefing.line1"),
        DialogueLine(speaker=PRODUCT_MANAGER, text_key="dialogue.l15_briefing.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l15_briefing.line3"),
    )
)
DEBRIEF_DIALOGUE = Dialogue(
    lines=(
        DialogueLine(speaker=DATA_ENGINEER, text_key="dialogue.l15_debrief.line1"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l15_debrief.line2"),
        DialogueLine(speaker=MENTOR, text_key="dialogue.l15_debrief.line3"),
    )
)
MASTERY_DIALOGUE_KEYS = ("dialogue.l15_mastery.line1", "dialogue.l15_mastery.line2", "dialogue.l15_mastery.line3")


def _pct(value: float) -> str:
    return f"{value:.1f}%"


def _pp(value: float) -> str:
    return f"{value:+.1f}pp"


# --- Segment mix dimensions - each fully self-contained (real
# share/rate values for both real periods), same discipline as L13's
# JoinTypeOption/L14's ChartFormOption. -----------------------------

DEVICE_ROWS = (
    SegmentRow(
        "mobile",
        "lesson.l15.segment_mix.device.mobile",
        DEVICE_SHARE_PCT["Q1"]["mobile"],
        DEVICE_RATE_PCT["Q1"]["mobile"],
        DEVICE_SHARE_PCT["Q2"]["mobile"],
        DEVICE_RATE_PCT["Q2"]["mobile"],
    ),
    SegmentRow(
        "desktop",
        "lesson.l15.segment_mix.device.desktop",
        DEVICE_SHARE_PCT["Q1"]["desktop"],
        DEVICE_RATE_PCT["Q1"]["desktop"],
        DEVICE_SHARE_PCT["Q2"]["desktop"],
        DEVICE_RATE_PCT["Q2"]["desktop"],
    ),
)
DEVICE_OPTION = DimensionOption(
    key="device",
    label_key="lesson.l15.segment_mix.dimension.device",
    rows=DEVICE_ROWS,
    mirror_code=(
        "device_rates = (\n"
        "    sessions.groupby(['period', 'device'])['converted']\n"
        "    .mean()\n"
        "    .unstack()\n"
        ")\n"
        "device_mix = pd.crosstab(sessions['period'], sessions['device'], normalize='index')"
    ),
    evidence_keys=("lesson.l15.evidence.device_rates", "lesson.l15.evidence.device_share"),
)

REGION_ROWS = (
    SegmentRow(
        "EU",
        "lesson.l15.segment_mix.region.eu",
        REGION_SHARE_PCT["Q1"]["EU"],
        REGION_RATE_PCT["Q1"]["EU"],
        REGION_SHARE_PCT["Q2"]["EU"],
        REGION_RATE_PCT["Q2"]["EU"],
    ),
    SegmentRow(
        "US",
        "lesson.l15.segment_mix.region.us",
        REGION_SHARE_PCT["Q1"]["US"],
        REGION_RATE_PCT["Q1"]["US"],
        REGION_SHARE_PCT["Q2"]["US"],
        REGION_RATE_PCT["Q2"]["US"],
    ),
)
REGION_OPTION = DimensionOption(
    key="region",
    label_key="lesson.l15.segment_mix.dimension.region",
    rows=REGION_ROWS,
    mirror_code=(
        "region_rates = (\n    sessions.groupby(['period', 'region'])['converted']\n    .mean()\n    .unstack()\n)"
    ),
    evidence_keys=("lesson.l15.evidence.region_null",),
)

# --- Prior headline / revision options - shared keys between the
# ComparisonRevealScene interpret step (stage 2) and the plain BriefField
# re-ask (stage 6), so the same 3 real choices are asked twice with full
# context the second time. The correct option's own label is worded
# neutrally - it never names "mix," "composition," or "weights" before
# investigation, matching the user's own explicit instruction not to
# leak the central mechanism through this option's own text. ----------

_HEADLINE_OPTION_KEYS = ("conversion_improved", "conversion_worsened", "need_to_check_composition_first")

OVERALL_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l15.overall_reveal.interpret.option.{key}", evidence_key="lesson.l15.evidence.overall_change")
    for key in _HEADLINE_OPTION_KEYS
)
HEADLINE_REVISION_FIELD = BriefField(
    key="revised_headline",
    prompt_key="lesson.l15.headline_revision.prompt",
    options=tuple(BriefOption(key, f"lesson.l15.overall_reveal.interpret.option.{key}") for key in _HEADLINE_OPTION_KEYS),
)

# --- Stage-3 sub-reveal interpret options - no evidence_key on any of
# these: SegmentMixScene's own Finish already recorded the real facts
# unconditionally (fact seen != correct first interpretation), so these
# reveals are pure framing/consequence checks. ------------------------

REGION_NULL_INTERPRET_OPTIONS = (
    InterpretOption("region_tracks_aggregate_doesnt_explain", "lesson.l15.region_reveal.interpret.option.region_tracks_aggregate_doesnt_explain"),
    InterpretOption("region_explains_the_reversal", "lesson.l15.region_reveal.interpret.option.region_explains_the_reversal"),
    InterpretOption("cant_tell_from_this_table", "lesson.l15.region_reveal.interpret.option.cant_tell_from_this_table"),
)

DEVICE_REVEAL_INTERPRET_OPTIONS = (
    InterpretOption("device_explains_the_reversal", "lesson.l15.device_reveal.interpret.option.device_explains_the_reversal"),
    InterpretOption("device_doesnt_explain_anything", "lesson.l15.device_reveal.interpret.option.device_doesnt_explain_anything"),
    InterpretOption("only_share_matters_not_rates", "lesson.l15.device_reveal.interpret.option.only_share_matters_not_rates"),
)

WEIGHTED_RECONSTRUCTION_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l15.weighted_reveal.interpret.option.{key}", evidence_key="lesson.l15.evidence.weighted_reconstruction")
    for key in ("aggregate_is_weighted_blend", "aggregate_is_a_separate_number", "reconstruction_is_a_coincidence")
)

STANDARDIZED_INTERPRET_OPTIONS = tuple(
    InterpretOption(key, f"lesson.l15.standardized_reveal.interpret.option.{key}", evidence_key="lesson.l15.evidence.standardized_comparison")
    for key in ("q2_rates_at_q1_mix_no_gain", "proves_product_regressed", "number_is_meaningless")
)

# --- Final Segment Brief -----------------------------------------------

OBSERVED_OVERALL_RESULT_FIELD = BriefField(
    key="observed_overall_result",
    prompt_key="lesson.l15.decision.observed_overall_result.prompt",
    options=(
        BriefOption("rose_28_4_to_33_2", "lesson.l15.decision.observed_overall_result.option.rose_28_4_to_33_2"),
        BriefOption("fell_28_4_to_33_2", "lesson.l15.decision.observed_overall_result.option.fell_28_4_to_33_2"),
        BriefOption("stayed_roughly_flat", "lesson.l15.decision.observed_overall_result.option.stayed_roughly_flat"),
    ),
)
WITHIN_DEVICE_RESULT_FIELD = BriefField(
    key="within_device_result",
    prompt_key="lesson.l15.decision.within_device_result.prompt",
    options=(
        BriefOption("both_declined", "lesson.l15.decision.within_device_result.option.both_declined"),
        BriefOption("both_improved", "lesson.l15.decision.within_device_result.option.both_improved"),
        BriefOption("mobile_up_desktop_down", "lesson.l15.decision.within_device_result.option.mobile_up_desktop_down"),
    ),
)
STATEMENTS_RELATIONSHIP_FIELD = BriefField(
    key="statements_relationship",
    prompt_key="lesson.l15.decision.statements_relationship.prompt",
    options=(
        BriefOption("both_true_different_comparisons", "lesson.l15.decision.statements_relationship.option.both_true_different_comparisons"),
        BriefOption(
            "aggregate_misleading_within_device_real", "lesson.l15.decision.statements_relationship.option.aggregate_misleading_within_device_real"
        ),
        BriefOption(
            "aggregate_real_within_device_doesnt_matter",
            "lesson.l15.decision.statements_relationship.option.aggregate_real_within_device_doesnt_matter",
        ),
    ),
)
WHAT_EXPLAINS_THE_REVERSAL_FIELD = BriefField(
    key="what_explains_the_reversal",
    prompt_key="lesson.l15.decision.what_explains_the_reversal.prompt",
    options=(
        BriefOption(
            "mix_shifted_toward_higher_converting_group", "lesson.l15.decision.what_explains_the_reversal.option.mix_shifted_toward_higher_converting_group"
        ),
        BriefOption("desktop_simply_declined", "lesson.l15.decision.what_explains_the_reversal.option.desktop_simply_declined"),
        BriefOption(
            "mobile_users_more_valuable", "lesson.l15.decision.what_explains_the_reversal.option.mobile_users_more_valuable"
        ),
    ),
)
STANDARDIZED_INTERPRETATION_FIELD = BriefField(
    key="standardized_interpretation",
    prompt_key="lesson.l15.decision.standardized_interpretation.prompt",
    options=(
        BriefOption(
            "no_within_device_gain_at_fixed_mix", "lesson.l15.decision.standardized_interpretation.option.no_within_device_gain_at_fixed_mix"
        ),
        BriefOption("proves_product_regressed", "lesson.l15.decision.standardized_interpretation.option.proves_product_regressed"),
        BriefOption("number_is_meaningless", "lesson.l15.decision.standardized_interpretation.option.number_is_meaningless"),
    ),
)
STRONGEST_DEFENSIBLE_CLAIM_FIELD = BriefField(
    key="strongest_defensible_claim",
    prompt_key="lesson.l15.decision.strongest_defensible_claim.prompt",
    options=(
        BriefOption(
            "names_both_facts_respects_causal_boundary", "lesson.l15.decision.strongest_defensible_claim.option.names_both_facts_respects_causal_boundary"
        ),
        BriefOption("mobile_traffic_caused_deterioration", "lesson.l15.decision.strongest_defensible_claim.option.mobile_traffic_caused_deterioration"),
        BriefOption("aggregate_number_is_wrong", "lesson.l15.decision.strongest_defensible_claim.option.aggregate_number_is_wrong"),
    ),
)
DECISION_EVIDENCE_FIELD = EvidenceField(key="evidence", prompt_key="lesson.l15.decision.evidence.prompt", min_count=3, max_count=6)
DECISION_FIELDS: tuple[BriefField, ...] = (
    OBSERVED_OVERALL_RESULT_FIELD,
    WITHIN_DEVICE_RESULT_FIELD,
    STATEMENTS_RELATIONSHIP_FIELD,
    WHAT_EXPLAINS_THE_REVERSAL_FIELD,
    STANDARDIZED_INTERPRETATION_FIELD,
    STRONGEST_DEFENSIBLE_CLAIM_FIELD,
)

# --- Optional mastery: fulfillment on-time delivery, a real non-reversal

MASTERY_SUPPORTING_EVIDENCE_FIELD = MultiChoiceField(
    key="mastery_supporting_evidence",
    prompt_key="lesson.l15.mastery.field.supporting_evidence.prompt",
    options=(
        BriefOption("both_carriers_improved", "lesson.l15.mastery.option.supporting_evidence.both_carriers_improved"),
        BriefOption("mix_shifted_toward_third_party", "lesson.l15.mastery.option.supporting_evidence.mix_shifted_toward_third_party"),
        BriefOption("overall_improved", "lesson.l15.mastery.option.supporting_evidence.overall_improved"),
        BriefOption("third_party_grew_a_lot", "lesson.l15.mastery.option.supporting_evidence.third_party_grew_a_lot"),
    ),
    min_count=1,
    max_count=2,
)
MASTERY_REVERSAL_JUDGMENT_FIELD = BriefField(
    key="mastery_reversal_judgment",
    prompt_key="lesson.l15.mastery.field.reversal_judgment.prompt",
    options=(
        BriefOption("no_reversal_real_improvement", "lesson.l15.mastery.option.reversal_judgment.no_reversal_real_improvement"),
        BriefOption("reversal_aggregate_misleading", "lesson.l15.mastery.option.reversal_judgment.reversal_aggregate_misleading"),
        BriefOption("cant_tell_without_more_data", "lesson.l15.mastery.option.reversal_judgment.cant_tell_without_more_data"),
    ),
)


def build_lesson_fifteen_runner(app, on_finished) -> tuple[LessonRunner, dict]:
    """Assembles Lesson 15's real investigation: one 2000-session NovaMart
    Go feed, a genuine Simpson reversal (device explains it, a real
    neutral region slice doesn't), explored via a real rate+share table
    (`SegmentMixScene`) rather than a before/after-only slicer. LessonContext
    is threaded through every analytical stage exactly like L06-L14.

    The dimension-investigation stage (region-first vs. device-first) is
    the one genuinely path-dependent composite - its own chain length
    differs by which dimension the student picks first, built via nested
    `SequenceScene`/`OfferThenTaskScene` closures that inspect `collected`
    state at build time, the same technique L14's own 3-deep nested
    revision already proved out."""
    collected: dict = {}
    context = LessonContext()

    def _restore_context_if_present() -> None:
        data = collected.get("analytical_context")
        if data is not None:
            context.restore_from_dict(data)

    def _sync_context_into_collected() -> None:
        collected["analytical_context"] = context.to_dict()

    # --- The Ask ---

    def briefing(advance):
        return DialogueScene(app, BRIEFING_DIALOGUE, on_complete=advance)

    # --- Overall reveal + prior headline (unscored, trajectory only) ---

    def overall_reveal(advance):
        def on_complete(interpretation):
            collected["prior_headline"] = interpretation
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l15.overall_reveal.title",
            narrative_keys=("dialogue.l15_overall_reveal.line1", "dialogue.l15_overall_reveal.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l15.overall_reveal.q1_label",
                    OVERALL_RATE_PCT["Q1"],
                    python_code="overall = sessions.groupby('period')['converted'].mean()\noverall.loc['Q1']",
                    value_format=_pct,
                ),
                ComparisonValue(
                    "lesson.l15.overall_reveal.q2_label", OVERALL_RATE_PCT["Q2"], python_code="overall.loc['Q2']", value_format=_pct
                ),
            ),
            interpret_prompt_key="lesson.l15.overall_reveal.interpret_prompt",
            interpret_options=OVERALL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Stage-3 shared sub-reveal builders ---

    def _region_null_reveal(on_complete):
        return ComparisonRevealScene(
            app,
            title_key="lesson.l15.region_reveal.title",
            narrative_keys=("dialogue.l15_region_reveal.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l15.region_reveal.eu_change_label",
                    REGION_RATE_PCT["Q2"]["EU"] - REGION_RATE_PCT["Q1"]["EU"],
                    python_code="region_rates.loc['Q2', 'EU'] - region_rates.loc['Q1', 'EU']",
                    value_format=_pp,
                ),
                ComparisonValue(
                    "lesson.l15.region_reveal.us_change_label",
                    REGION_RATE_PCT["Q2"]["US"] - REGION_RATE_PCT["Q1"]["US"],
                    python_code="region_rates.loc['Q2', 'US'] - region_rates.loc['Q1', 'US']",
                    value_format=_pp,
                ),
            ),
            interpret_prompt_key="lesson.l15.region_reveal.interpret_prompt",
            interpret_options=REGION_NULL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def _device_reveal(on_complete):
        return ComparisonRevealScene(
            app,
            title_key="lesson.l15.device_reveal.title",
            narrative_keys=("dialogue.l15_device_reveal.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l15.device_reveal.mobile_change_label",
                    DEVICE_RATE_PCT["Q2"]["mobile"] - DEVICE_RATE_PCT["Q1"]["mobile"],
                    python_code="device_rates.loc['Q2', 'mobile'] - device_rates.loc['Q1', 'mobile']",
                    value_format=_pp,
                ),
                ComparisonValue(
                    "lesson.l15.device_reveal.desktop_change_label",
                    DEVICE_RATE_PCT["Q2"]["desktop"] - DEVICE_RATE_PCT["Q1"]["desktop"],
                    python_code="device_rates.loc['Q2', 'desktop'] - device_rates.loc['Q1', 'desktop']",
                    value_format=_pp,
                ),
            ),
            interpret_prompt_key="lesson.l15.device_reveal.interpret_prompt",
            interpret_options=DEVICE_REVEAL_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    def _build_segment_mix(dimension_options, on_complete):
        return SegmentMixScene(
            app,
            "lesson.l15.dimension_investigation.title",
            "lesson.l15.dimension_investigation.ask",
            dimension_options,
            on_complete,
            context,
            hint_key="lesson.l15.dimension_investigation.hint",
            guided=True,
        )

    # --- Dimension investigation (path-dependent composite) ---

    def dimension_investigation(advance):
        def _build_region_first_chain():
            def on_region_reveal_complete(_interpretation):
                collected["region_inspected"] = True
                _sync_context_into_collected()
                region_first_sequence.advance_to_second()

            def on_device_mix_complete(_choice):
                _sync_context_into_collected()
                inner_sequence.advance_to_second()

            def on_device_reveal_complete(_interpretation):
                _sync_context_into_collected()
                advance()

            inner_sequence = SequenceScene(
                app,
                first=_build_segment_mix((DEVICE_OPTION,), on_device_mix_complete),
                build_second=lambda: _device_reveal(on_device_reveal_complete),
            )
            region_first_sequence = SequenceScene(
                app,
                first=_region_null_reveal(on_region_reveal_complete),
                build_second=lambda: inner_sequence,
            )
            return region_first_sequence

        def _build_device_first_chain():
            def build_region_task(on_task_complete):
                def on_region_mix_complete(_choice):
                    _sync_context_into_collected()
                    region_sequence.advance_to_second()

                def on_region_reveal_complete(_interpretation):
                    collected["region_inspected"] = True
                    _sync_context_into_collected()
                    on_task_complete(None)

                region_sequence = SequenceScene(
                    app,
                    first=_build_segment_mix((REGION_OPTION,), on_region_mix_complete),
                    build_second=lambda: _region_null_reveal(on_region_reveal_complete),
                )
                return region_sequence

            def on_offer_complete(_engaged, _result):
                _sync_context_into_collected()
                advance()

            def build_offer():
                return OfferThenTaskScene(
                    app,
                    build_region_task,
                    on_offer_complete,
                    title_key="lesson.l15.region_offer.title",
                    line_keys=("lesson.l15.region_offer.line1",),
                    engage_label_key="lesson.l15.region_offer.engage",
                    skip_label_key="lesson.l15.region_offer.skip",
                )

            def on_device_reveal_complete(_interpretation):
                _sync_context_into_collected()
                device_first_sequence.advance_to_second()

            device_first_sequence = SequenceScene(app, first=_device_reveal(on_device_reveal_complete), build_second=build_offer)
            return device_first_sequence

        def on_picker_complete(dimension_key):
            collected["first_dimension"] = dimension_key
            _sync_context_into_collected()
            composite.advance_to_second()

        def build_second():
            if collected["first_dimension"] == "region":
                return _build_region_first_chain()
            return _build_device_first_chain()

        picker = _build_segment_mix((REGION_OPTION, DEVICE_OPTION), on_picker_complete)
        composite = SequenceScene(app, first=picker, build_second=build_second)
        return composite

    # --- Weighted reconstruction (unconditional) ---

    def weighted_reconstruction_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l15.weighted_reveal.title",
            narrative_keys=("dialogue.l15_weighted_reveal.line1",),
            comparisons=(
                ComparisonValue(
                    "lesson.l15.weighted_reveal.q1_label",
                    OVERALL_RATE_PCT["Q1"],
                    python_code="reconstructed = (device_rates * device_mix).sum(axis=1)\nreconstructed.loc['Q1']",
                    value_format=_pct,
                ),
                ComparisonValue(
                    "lesson.l15.weighted_reveal.q2_label", OVERALL_RATE_PCT["Q2"], python_code="reconstructed.loc['Q2']", value_format=_pct
                ),
            ),
            interpret_prompt_key="lesson.l15.weighted_reveal.interpret_prompt",
            interpret_options=WEIGHTED_RECONSTRUCTION_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Standardized (common-mix) comparison (unconditional) ---

    def standardized_comparison_reveal(advance):
        def on_complete(_interpretation):
            _sync_context_into_collected()
            advance()

        return ComparisonRevealScene(
            app,
            title_key="lesson.l15.standardized_reveal.title",
            narrative_keys=("dialogue.l15_standardized_reveal.line1", "dialogue.l15_standardized_reveal.line2"),
            comparisons=(
                ComparisonValue(
                    "lesson.l15.standardized_reveal.q1_observed_label",
                    OVERALL_RATE_PCT["Q1"],
                    python_code="overall.loc['Q1']",
                    value_format=_pct,
                ),
                ComparisonValue(
                    "lesson.l15.standardized_reveal.q2_at_q1_mix_label",
                    Q2_AT_Q1_MIX_PCT,
                    python_code="q2_at_q1_mix = (device_rates.loc['Q2'] * device_mix.loc['Q1']).sum()\nq2_at_q1_mix",
                    value_format=_pct,
                ),
            ),
            interpret_prompt_key="lesson.l15.standardized_reveal.interpret_prompt",
            interpret_options=STANDARDIZED_INTERPRET_OPTIONS,
            on_complete=on_complete,
            context=context,
            comparisons_are_evidence=False,
        )

    # --- Headline revision (real, separate re-ask) ---

    def headline_revision(advance):
        def on_complete(choices):
            collected["revised_headline"] = choices["revised_headline"]
            advance()

        return BriefBuilderScene(app, "lesson.l15.headline_revision.title", (HEADLINE_REVISION_FIELD,), on_complete, guided=False)

    # --- Final Decision ---

    def final_decision(advance):
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
            "lesson.l15.decision_title",
            steps=(
                OBSERVED_OVERALL_RESULT_FIELD,
                WITHIN_DEVICE_RESULT_FIELD,
                STATEMENTS_RELATIONSHIP_FIELD,
                WHAT_EXPLAINS_THE_REVERSAL_FIELD,
                STANDARDIZED_INTERPRETATION_FIELD,
                STRONGEST_DEFENSIBLE_CLAIM_FIELD,
                DECISION_EVIDENCE_FIELD,
            ),
            context=context,
            on_complete=on_complete,
        )

    # --- Optional Mastery ---

    def mastery_challenge(advance):
        def build_task(on_task_complete):
            return BriefBuilderScene(
                app,
                "lesson.l15.mastery.title",
                (MASTERY_SUPPORTING_EVIDENCE_FIELD, MASTERY_REVERSAL_JUDGMENT_FIELD),
                on_task_complete,
                guided=False,
            )

        def on_complete(engaged, result):
            collected["mastery_engaged"] = engaged
            collected["mastery_result"] = dict(result) if result else {}
            advance()

        return OfferThenTaskScene(
            app,
            build_task,
            on_complete,
            title_key="lesson.l15.mastery.title",
            line_keys=MASTERY_DIALOGUE_KEYS,
        )

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

    def _build_result() -> LessonFifteenResult:
        decision = collected.get("decision", {})
        selected_evidence_ids = set(decision.get("evidence", ()))

        return LessonFifteenResult(
            prior_headline=collected.get("prior_headline"),
            first_dimension=collected.get("first_dimension"),
            region_inspected=collected.get("region_inspected", False),
            revised_headline=collected.get("revised_headline"),
            decision=decision,
            critical_evidence_present=_critical_evidence_present(selected_evidence_ids),
            mastery_engaged=collected.get("mastery_engaged", False),
            mastery_result=collected.get("mastery_result", {}),
        )

    def feedback(advance):
        result = _build_result()
        hints_used = app.progress.hints_used.get(LESSON_15.number, 0)
        evaluation = score_lesson_fifteen(result, LESSON_15, hints_used=hints_used)
        return LessonFeedbackScene(app, evaluation, on_complete=advance)

    def debrief(advance):
        return DialogueScene(app, DEBRIEF_DIALOGUE, on_complete=advance)

    def finished():
        on_finished(_build_result())

    stages = [
        briefing,
        overall_reveal,
        dimension_investigation,
        weighted_reconstruction_reveal,
        standardized_comparison_reveal,
        headline_revision,
        final_decision,
        mastery_challenge,
        feedback,
        debrief,
    ]
    runner = LessonRunner(
        app,
        stages,
        on_finished=finished,
        lesson_number=15,
        collected=collected,
        definition=LESSON_15,
        on_resume=_restore_context_if_present,
    )
    return runner, collected

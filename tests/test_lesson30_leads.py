import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.core.fonts import get_font
from data_science_arcade.localization.service import Localization
from data_science_arcade.lessons.l30_the_data_incident.leads import (
    BASELINE_CHECK_REQUEST,
    CHECKOUT_HEALTH_REQUEST,
    CORRECT_BASELINE_CHECK,
    CORRECT_CHART_OPTION,
    CORRECT_CHECKOUT_HEALTH_OPTION,
    CORRECT_DEDUP_CHOICE,
    CORRECT_PROMO_VERDICT,
    CORRECT_REDESIGN_VERDICT,
    CORRECT_REGIONAL_CUT,
    DASHBOARD_CHART_REQUEST,
    MINIMUM_LEADS_REQUIRED,
    MONITORING_REQUEST,
    RAW_EVENT_COUNT,
    REDESIGN_CORRELATION_REQUEST,
    REGIONAL_CUT_REQUEST,
    TRUE_UNIQUE_REDEMPTIONS,
    build_investigation_leads,
    flags_a_meaningful_decline,
    monitoring_choice_is_sound,
    promo_correlation_request_for,
)
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.button import BUTTON_TEXT_SIZE
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.composite_scene import SequenceScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.decision_builder_scene import EVIDENCE_OPTION_SIZE
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.workbench.context import LessonContext


def _sync_noop() -> None:
    pass


def test_there_are_six_leads_with_unique_keys():
    app = App()
    app.init()
    try:
        leads = build_investigation_leads(app, LessonContext(), {}, _sync_noop)
        assert len(leads) == 6
        assert len({lead.key for lead in leads}) == 6
    finally:
        pygame.quit()


def test_minimum_required_is_fewer_than_the_total_leads():
    assert 0 < MINIMUM_LEADS_REQUIRED < 6


def test_each_lead_builds_its_expected_reused_scene_type():
    app = App()
    app.init()
    try:
        leads = {lead.key: lead for lead in build_investigation_leads(app, LessonContext(), {}, _sync_noop)}
        expected = {
            "regional_breakdown": SegmentSlicerScene,
            "promo_correlation": SequenceScene,
            "redesign_correlation": CorrelationScene,
            "checkout_health_check": SegmentSlicerScene,
            "monitoring_review": AlertConfigScene,
            "dashboard_chart": ChartDesignerScene,
        }
        assert set(leads) == set(expected)
        for key, scene_type in expected.items():
            scene = leads[key].build_scene(lambda *_choices: None)
            assert isinstance(scene, scene_type)
        # The promo_correlation lead starts on its own dedup micro-decision,
        # not the correlation view directly.
        promo_scene = leads["promo_correlation"].build_scene(lambda *_choices: None)
        assert isinstance(promo_scene._active, BriefBuilderScene)
    finally:
        pygame.quit()


def test_correct_verdicts_are_real_options_on_their_own_requests():
    assert CORRECT_REDESIGN_VERDICT in {option.key for option in REDESIGN_CORRELATION_REQUEST.options}
    assert CORRECT_PROMO_VERDICT in {option.key for option in promo_correlation_request_for(dedupe=True).options}
    assert CORRECT_CHART_OPTION in {option.key for option in DASHBOARD_CHART_REQUEST.options}
    assert CORRECT_REGIONAL_CUT in {option.key for option in REGIONAL_CUT_REQUEST.options}
    assert CORRECT_BASELINE_CHECK in {option.key for option in BASELINE_CHECK_REQUEST.options}
    assert CORRECT_CHECKOUT_HEALTH_OPTION in {option.key for option in CHECKOUT_HEALTH_REQUEST.options}


def test_the_correlation_requests_use_real_computed_correlations_not_placeholders():
    assert -1.0 <= REDESIGN_CORRELATION_REQUEST.correlation <= 1.0
    assert REDESIGN_CORRELATION_REQUEST.correlation not in (0.0, 1.0, -1.0)
    promo_request = promo_correlation_request_for(dedupe=True)
    assert -1.0 <= promo_request.correlation <= 1.0
    assert promo_request.correlation != 0.0


def test_regional_cut_only_flags_the_region_with_a_meaningful_decline():
    by_region = next(option for option in REGIONAL_CUT_REQUEST.options if option.key == "by_region")
    flagged = {segment.key for segment in by_region.segments if flags_a_meaningful_decline(segment.before_rate, segment.after_rate)}
    assert flagged == {"east"}


def test_baseline_check_shows_a_flat_move_for_the_correct_option():
    vs_baseline = next(option for option in BASELINE_CHECK_REQUEST.options if option.key == CORRECT_BASELINE_CHECK)
    segment = vs_baseline.segments[0]
    assert abs((segment.after_rate - segment.before_rate) / segment.before_rate) < 0.02


def test_monitoring_request_targets_the_real_promo_week():
    assert MONITORING_REQUEST.target_incident_day == 7
    assert len(MONITORING_REQUEST.metric_options) == 3
    assert len(MONITORING_REQUEST.threshold_options) == 3


def test_monitoring_choice_soundness_matches_real_recomputed_outcomes():
    # east_revenue: sound at every threshold (no real discrimination to
    # score between them). company_total_revenue: sound only when not
    # loose. east_support_tickets: never sound (noisy or blind).
    assert monitoring_choice_is_sound("east_revenue", 0.05) is True
    assert monitoring_choice_is_sound("east_revenue", 0.15) is True
    assert monitoring_choice_is_sound("east_revenue", 0.30) is True
    assert monitoring_choice_is_sound("company_total_revenue", 0.05) is True
    assert monitoring_choice_is_sound("company_total_revenue", 0.15) is True
    assert monitoring_choice_is_sound("company_total_revenue", 0.30) is False
    assert monitoring_choice_is_sound("east_support_tickets", 0.05) is False
    assert monitoring_choice_is_sound("east_support_tickets", 0.15) is False
    assert monitoring_choice_is_sound("east_support_tickets", 0.30) is False


def test_dedup_choice_constants_match_the_real_promo_log_counts():
    assert TRUE_UNIQUE_REDEMPTIONS == 3000
    assert RAW_EVENT_COUNT == 3450
    assert CORRECT_DEDUP_CHOICE == "dedupe_by_redemption_id"


def test_regional_breakdown_records_concentration_and_reversion_evidence_on_the_correct_path():
    app = App()
    app.init()
    try:
        context = LessonContext()
        collected: dict = {}
        leads = {lead.key: lead for lead in build_investigation_leads(app, context, collected, _sync_noop)}

        closed = []
        scene = leads["regional_breakdown"].build_scene(lambda *choices: closed.append(choices))
        # Pick by_region then vs_own_baseline (both first-and-only correct options).
        scene._make_choose("by_region")()
        scene._next()
        scene._make_choose("vs_own_baseline")()
        scene._next()

        assert closed  # on_complete fired
        assert collected["regional_cut_choice"] == "by_region"
        assert collected["baseline_check_choice"] == "vs_own_baseline"
        # Both slots are STABLE per-lead keys (correction #26) - correctness
        # is read from the *_choice fields above, not the key itself.
        evidence_keys = {item.key for item in context.evidence}
        assert "regional_cut" in evidence_keys
        assert "baseline_check" in evidence_keys
    finally:
        pygame.quit()


def test_checkout_health_cherry_picked_choice_records_the_decoy_content_under_the_same_slot():
    app = App()
    app.init()
    try:
        context = LessonContext()
        collected: dict = {}
        leads = {lead.key: lead for lead in build_investigation_leads(app, context, collected, _sync_noop)}

        scene = leads["checkout_health_check"].build_scene(lambda *choices: None)
        scene._make_choose("cherry_picked_low_week")()
        scene._next()

        assert collected["checkout_health_choice"] == "cherry_picked_low_week"
        checkout_items = [item for item in context.evidence if item.key == "checkout_health"]
        assert len(checkout_items) == 1
        assert checkout_items[0].label_key == "lesson.l30.evidence.checkout_cherry_picked"
    finally:
        pygame.quit()


def _all_evidence_label_detail_pairs() -> list[tuple[str, str | None]]:
    """Drives every real choice (correct and decoy, where one exists) for
    every lead into its own fresh LessonContext, and collects the exact
    (label_key, detail) pairs DecisionBuilderScene's own EvidenceField
    would render for each - the same composition it uses:
    `label` if detail is None else `f"{label} {detail}"`. A fresh context
    per run is required since evidence keys are STABLE per-lead slots
    (correction #26) - recording a second variant into the same context
    would just overwrite the first rather than let both be captured."""

    def run(pick_fn) -> list:
        app = App()
        app.init()
        try:
            context = LessonContext()
            collected: dict = {}
            leads = {lead.key: lead for lead in build_investigation_leads(app, context, collected, _sync_noop)}
            pick_fn(leads)
            return list(context.evidence)
        finally:
            pygame.quit()

    def pick_regional(region_cut: str, baseline_check: str):
        def _pick(leads):
            scene = leads["regional_breakdown"].build_scene(lambda *choices: None)
            scene._make_choose(region_cut)()
            scene._next()
            scene._make_choose(baseline_check)()
            scene._next()

        return _pick

    def pick_checkout(choice: str):
        def _pick(leads):
            scene = leads["checkout_health_check"].build_scene(lambda *choices: None)
            scene._make_choose(choice)()
            scene._next()

        return _pick

    def pick_promo(dedup_choice: str):
        def _pick(leads):
            scene = leads["promo_correlation"].build_scene(lambda *choices: None)
            scene.buttons.buttons[0 if dedup_choice == CORRECT_DEDUP_CHOICE else 1].on_activate()
            scene.next_button.on_activate()
            scene._active.buttons.buttons[0].on_activate()
            scene._active.next_button.on_activate()

        return _pick

    def pick_redesign():
        def _pick(leads):
            scene = leads["redesign_correlation"].build_scene(lambda *choices: None)
            scene.buttons.buttons[0].on_activate()
            scene.next_button.on_activate()

        return _pick

    def pick_dashboard(choice_index: int):
        def _pick(leads):
            scene = leads["dashboard_chart"].build_scene(lambda *choices: None)
            scene.buttons.buttons[choice_index].on_activate()
            scene.next_button.on_activate()

        return _pick

    def pick_monitoring(metric_index: int, threshold_index: int):
        def _pick(leads):
            scene = leads["monitoring_review"].build_scene(lambda *choices: None)
            scene.buttons.buttons[metric_index].on_activate()
            scene.buttons.buttons[len(scene._current_request().metric_options) + threshold_index].on_activate()
            scene.next_button.on_activate()

        return _pick

    pairs: list[tuple[str, str | None]] = []
    for evidence in (
        run(pick_regional("by_region", "vs_own_baseline")),
        run(pick_regional("by_device", "vs_prior_week_only")),
        run(pick_checkout("full_window_avg")),
        run(pick_checkout("cherry_picked_low_week")),
        run(pick_promo(CORRECT_DEDUP_CHOICE)),
        run(pick_promo("count_every_log_row")),
        run(pick_redesign()),
        run(pick_dashboard(0)),  # zoomed_bar (wrong)
        run(pick_dashboard(1)),  # zero_based_bar (correct)
        run(pick_monitoring(0, 0)),  # east_revenue/tight - sound
        run(pick_monitoring(2, 0)),  # east_support_tickets/tight - unsound
    ):
        for item in evidence:
            pairs.append((item.label_key, item.detail))
    return pairs


@pytest.mark.parametrize("locale", ["en", "pl"])
def test_every_real_evidence_text_fits_the_evidence_field_button(locale):
    # EvidenceField's own button draws centered text with no wrapping,
    # same as every other button in this codebase - a label+detail
    # combination longer than the button silently spills past its edges,
    # exactly the class of bug a real screenshot (not this width test)
    # first caught for lesson 30's own evidence pool during review.
    pairs = _all_evidence_label_detail_pairs()  # each drives its own full App() init/quit cycle

    pygame.init()
    try:
        loc = Localization(locale=locale)
        font = get_font(BUTTON_TEXT_SIZE)
        max_width = EVIDENCE_OPTION_SIZE[0] - 40

        for label_key, detail in pairs:
            text = loc.t(label_key) if detail is None else f"{loc.t(label_key)} {detail}"
            width, _height = font.size(text)
            assert width <= max_width, f"{locale}/{label_key} is {width}px wide, evidence button only fits {max_width}px: {text!r}"
    finally:
        pygame.quit()

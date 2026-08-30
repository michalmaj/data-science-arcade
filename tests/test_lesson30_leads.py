import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l30_the_data_incident.leads import (
    CORRECT_CHART_OPTION,
    CORRECT_PROMO_VERDICT,
    CORRECT_REDESIGN_VERDICT,
    DASHBOARD_CHART_REQUEST,
    MINIMUM_LEADS_REQUIRED,
    MONITORING_REQUEST,
    PROMO_CORRELATION_REQUEST,
    REDESIGN_CORRELATION_REQUEST,
    REGIONAL_BREAKDOWN_REQUEST,
    build_investigation_leads,
    flags_a_meaningful_decline,
)
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene


def test_there_are_five_leads_with_unique_keys():
    app = App()
    app.init()
    try:
        leads = build_investigation_leads(app)
        assert len(leads) == 5
        assert len({lead.key for lead in leads}) == 5
    finally:
        pygame.quit()


def test_minimum_required_is_fewer_than_the_total_leads():
    assert 0 < MINIMUM_LEADS_REQUIRED < 5


def test_each_lead_builds_its_expected_reused_scene_type():
    app = App()
    app.init()
    try:
        leads = {lead.key: lead for lead in build_investigation_leads(app)}
        expected = {
            "redesign_correlation": CorrelationScene,
            "regional_breakdown": SegmentSlicerScene,
            "dashboard_chart": ChartDesignerScene,
            "promo_correlation": CorrelationScene,
            "monitoring_review": AlertConfigScene,
        }
        assert set(leads) == set(expected)
        for key, scene_type in expected.items():
            scene = leads[key].build_scene(lambda *_choices: None)
            assert isinstance(scene, scene_type)
    finally:
        pygame.quit()


def test_correct_verdicts_are_real_options_on_their_own_requests():
    assert CORRECT_REDESIGN_VERDICT in {option.key for option in REDESIGN_CORRELATION_REQUEST.options}
    assert CORRECT_PROMO_VERDICT in {option.key for option in PROMO_CORRELATION_REQUEST.options}
    assert CORRECT_CHART_OPTION in {option.key for option in DASHBOARD_CHART_REQUEST.options}


def test_the_two_correlation_requests_use_real_computed_correlations_not_placeholders():
    assert -1.0 <= REDESIGN_CORRELATION_REQUEST.correlation <= 1.0
    assert -1.0 <= PROMO_CORRELATION_REQUEST.correlation <= 1.0
    # A hand-picked placeholder would be suspiciously round - these aren't.
    assert REDESIGN_CORRELATION_REQUEST.correlation not in (0.0, 1.0, -1.0)
    assert PROMO_CORRELATION_REQUEST.correlation != 0.0


def test_regional_breakdown_only_flags_the_region_with_a_meaningful_decline():
    by_region = next(option for option in REGIONAL_BREAKDOWN_REQUEST.options if option.key == "by_region")
    flagged = {segment.key for segment in by_region.segments if flags_a_meaningful_decline(segment.before_rate, segment.after_rate)}
    assert flagged == {"east"}


def test_monitoring_request_targets_the_real_promo_week():
    assert MONITORING_REQUEST.target_incident_day == 7
    assert len(MONITORING_REQUEST.metric_options) == 3
    assert len(MONITORING_REQUEST.threshold_options) == 3

from data_science_arcade.lessons.framework.alerting import MetricOption, MonitoringRequest, ThresholdOption
from data_science_arcade.lessons.framework.chart import ChartOption, ChartRequest
from data_science_arcade.lessons.framework.correlation import CorrelationRequest, VerdictOption
from data_science_arcade.lessons.framework.investigation import InvestigationLead
from data_science_arcade.lessons.framework.segment import Segment, SegmentRequest, SliceOption
from data_science_arcade.lessons.l30_the_data_incident.incident_data import (
    correlation_promo_redemptions_vs_revenue,
    correlation_ticket_change_vs_revenue_change,
    generate_incident_data,
    percent_change,
    simulate_monitoring,
    weekly_company_revenue,
)
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene

INCIDENT_DATASET = generate_incident_data()

# Five leads, one shared dataset, four reused scene types - the whole
# point is that none of this needed a new "investigation engine" (spec
# §54 Phase 13: "Lesson 30 should reuse systems from the entire course").
# Each lead is a single request (not a multi-request sequence like every
# prior lesson's own stages) - a quick, focused look at one angle, since
# the *lesson's* length comes from choosing among five of these plus the
# hub navigation itself, not from repetition inside any one of them.

REDESIGN_CORRELATION = correlation_ticket_change_vs_revenue_change(INCIDENT_DATASET)

REDESIGN_CORRELATION_REQUEST = CorrelationRequest(
    key="redesign_correlation",
    prompt_key="lesson.l30.lead.redesign_correlation.prompt",
    hint_key="lesson.l30.lead.redesign_correlation.hint",
    metric_a_label_key="lesson.l30.metric.support_ticket_change",
    metric_b_label_key="lesson.l30.metric.revenue_change",
    evidence_key="lesson.l30.evidence.redesign_correlation",
    correlation=REDESIGN_CORRELATION,
    sample_size=4,
    options=(
        VerdictOption("redesign_confirmed", "lesson.l30.option.redesign_correlation.redesign_confirmed", "lesson.l30.explanation.redesign_correlation.redesign_confirmed"),
        VerdictOption("not_the_redesign_negative_correlation", "lesson.l30.option.redesign_correlation.not_the_redesign_negative_correlation", "lesson.l30.explanation.redesign_correlation.not_the_redesign_negative_correlation"),
        VerdictOption("not_the_redesign_too_weak", "lesson.l30.option.redesign_correlation.not_the_redesign_too_weak", "lesson.l30.explanation.redesign_correlation.not_the_redesign_too_weak"),
    ),
)

CORRECT_REDESIGN_VERDICT = "not_the_redesign_too_weak"


PROMO_CORRELATION = correlation_promo_redemptions_vs_revenue(INCIDENT_DATASET, "east")

PROMO_CORRELATION_REQUEST = CorrelationRequest(
    key="promo_correlation",
    prompt_key="lesson.l30.lead.promo_correlation.prompt",
    hint_key="lesson.l30.lead.promo_correlation.hint",
    metric_a_label_key="lesson.l30.metric.promo_redemptions",
    metric_b_label_key="lesson.l30.metric.east_revenue",
    evidence_key="lesson.l30.evidence.promo_correlation",
    correlation=PROMO_CORRELATION,
    sample_size=8,
    options=(
        VerdictOption("promo_explains_it", "lesson.l30.option.promo_correlation.promo_explains_it", "lesson.l30.explanation.promo_correlation.promo_explains_it"),
        VerdictOption("not_a_drop_seasonal", "lesson.l30.option.promo_correlation.not_a_drop_seasonal", "lesson.l30.explanation.promo_correlation.not_a_drop_seasonal"),
        VerdictOption("run_promo_permanently", "lesson.l30.option.promo_correlation.run_promo_permanently", "lesson.l30.explanation.promo_correlation.run_promo_permanently"),
    ),
)

CORRECT_PROMO_VERDICT = "promo_explains_it"


REGIONAL_BREAKDOWN_REQUEST = SegmentRequest(
    key="regional_breakdown",
    prompt_key="lesson.l30.lead.regional_breakdown.prompt",
    hint_key="lesson.l30.lead.regional_breakdown.hint",
    options=(
        SliceOption(
            "by_region",
            "lesson.l30.option.regional_breakdown.by_region",
            segments=(
                Segment("east", "lesson.l30.region.east", 150000.0, 74000.0),
                Segment("north", "lesson.l30.region.north", 90000.0, 90200.0),
                Segment("south", "lesson.l30.region.south", 95000.0, 95100.0),
                Segment("west", "lesson.l30.region.west", 85000.0, 84800.0),
            ),
        ),
        SliceOption(
            "by_device",
            "lesson.l30.option.regional_breakdown.by_device",
            segments=(
                Segment("mobile", "lesson.l30.device.mobile", 246000.0, 201000.0),
                Segment("desktop", "lesson.l30.device.desktop", 174000.0, 143100.0),
            ),
        ),
    ),
)


_WEEK_LABELS = ("W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8")  # locale-invariant, like L28's own "Q1".."Q4"
_COMPANY_WEEKLY_REVENUE = weekly_company_revenue(INCIDENT_DATASET)

DASHBOARD_CHART_REQUEST = ChartRequest(
    key="dashboard_chart",
    prompt_key="lesson.l30.lead.dashboard_chart.prompt",
    hint_key="lesson.l30.lead.dashboard_chart.hint",
    categories=_WEEK_LABELS,
    values=_COMPANY_WEEKLY_REVENUE,
    options=(
        ChartOption("zoomed_bar", "lesson.l30.option.dashboard_chart.zoomed_bar", chart_type="bar", scale="zoomed"),
        ChartOption("zero_based_bar", "lesson.l30.option.dashboard_chart.zero_based_bar", chart_type="bar", scale="zero_based"),
        ChartOption(
            "cherry_picked_two_weeks",
            "lesson.l30.option.dashboard_chart.cherry_picked_two_weeks",
            chart_type="bar",
            scale="zero_based",
            categories=(_WEEK_LABELS[6], _WEEK_LABELS[7]),
            values=(_COMPANY_WEEKLY_REVENUE[6], _COMPANY_WEEKLY_REVENUE[7]),
        ),
    ),
)

CORRECT_CHART_OPTION = "zero_based_bar"


def flags_a_meaningful_decline(before: float, after: float) -> bool:
    # Every region has some ordinary week-to-week noise (a fraction of a
    # percent either way) - SegmentSlicerScene's default "any decline"
    # flag_check would flag West's own trivial -0.2% dip right alongside
    # East's real -50.7% one, muddying the "concentrated in one region"
    # point this lead exists to make. Reuses L18's own "flag only a
    # relative gap past a real threshold" idea (`relative_imbalance()`)
    # rather than reintroducing the noise-sensitive default.
    return percent_change(before, after) < -0.05


MONITORING_REQUEST = MonitoringRequest(
    key="review_monitoring",
    prompt_key="lesson.l30.lead.monitoring_review.prompt",
    hint_key="lesson.l30.lead.monitoring_review.hint",
    target_incident_day=7,
    metric_options=(
        MetricOption("east_revenue", "lesson.l30.option.monitoring_review.east_revenue", metric_key="east_revenue"),
        MetricOption("company_total_revenue", "lesson.l30.option.monitoring_review.company_total_revenue", metric_key="company_total_revenue"),
        MetricOption("east_support_tickets", "lesson.l30.option.monitoring_review.east_support_tickets", metric_key="east_support_tickets"),
    ),
    threshold_options=(
        ThresholdOption("tight", "lesson.l30.option.monitoring_review.tight", multiplier=0.05),
        ThresholdOption("balanced", "lesson.l30.option.monitoring_review.balanced", multiplier=0.15),
        ThresholdOption("loose", "lesson.l30.option.monitoring_review.loose", multiplier=0.30),
    ),
)


def build_investigation_leads(app) -> tuple[InvestigationLead, ...]:
    def redesign_correlation(on_complete):
        return CorrelationScene(app, "lesson.l30.lead_title.redesign_correlation", (REDESIGN_CORRELATION_REQUEST,), on_complete, guided=True)

    def promo_correlation(on_complete):
        return CorrelationScene(app, "lesson.l30.lead_title.promo_correlation", (PROMO_CORRELATION_REQUEST,), on_complete, guided=True)

    def regional_breakdown(on_complete):
        return SegmentSlicerScene(
            app,
            "lesson.l30.lead_title.regional_breakdown",
            (REGIONAL_BREAKDOWN_REQUEST,),
            on_complete,
            guided=True,
            row_column_label_key="lesson.l30.segment_column_label",
            before_column_label_key="lesson.l30.before_column_label",
            after_column_label_key="lesson.l30.after_column_label",
            pick_hint_key="lesson.l30.pick_a_slice_hint",
            value_format=lambda segment, value: f"${value:,.0f}",
            flag_check=flags_a_meaningful_decline,
        )

    def dashboard_chart(on_complete):
        return ChartDesignerScene(app, "lesson.l30.lead_title.dashboard_chart", (DASHBOARD_CHART_REQUEST,), on_complete, guided=True)

    def monitoring_review(on_complete):
        return AlertConfigScene(
            app,
            "lesson.l30.lead_title.monitoring_review",
            INCIDENT_DATASET,
            (MONITORING_REQUEST,),
            simulate_monitoring,
            on_complete,
            guided=True,
            false_alarm_count_label_key="lesson.l30.false_alarm_count_label",
        )

    return (
        InvestigationLead("redesign_correlation", "lesson.l30.lead_label.redesign_correlation", redesign_correlation),
        InvestigationLead("regional_breakdown", "lesson.l30.lead_label.regional_breakdown", regional_breakdown),
        InvestigationLead("dashboard_chart", "lesson.l30.lead_label.dashboard_chart", dashboard_chart),
        InvestigationLead("promo_correlation", "lesson.l30.lead_label.promo_correlation", promo_correlation),
        InvestigationLead("monitoring_review", "lesson.l30.lead_label.monitoring_review", monitoring_review),
    )


MINIMUM_LEADS_REQUIRED = 3

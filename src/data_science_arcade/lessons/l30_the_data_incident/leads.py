from collections.abc import Callable

from data_science_arcade.lessons.framework.alerting import MetricOption, MonitoringRequest, ThresholdOption
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.lessons.framework.chart import ChartOption, ChartRequest
from data_science_arcade.lessons.framework.correlation import CorrelationRequest, VerdictOption
from data_science_arcade.lessons.framework.investigation import InvestigationLead
from data_science_arcade.lessons.framework.segment import Segment, SegmentRequest, SliceOption
from data_science_arcade.lessons.l30_the_data_incident.device_dashboard_data import device_revenue_at, generate_device_dashboard
from data_science_arcade.lessons.l30_the_data_incident.incident_data import (
    checkout_completion_window_average,
    correlation_ticket_change_vs_revenue_change,
    generate_incident_data,
    percent_change,
    region_baseline_average,
    region_series,
    simulate_monitoring,
    value_at,
    weekly_company_revenue,
)
from data_science_arcade.lessons.l30_the_data_incident.promo_log_data import (
    generate_promo_log,
    raw_event_count,
    unique_redemption_count,
    weekly_redemption_counts,
)
from data_science_arcade.ui.alert_config_scene import AlertConfigScene
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene
from data_science_arcade.ui.chart_designer_scene import ChartDesignerScene
from data_science_arcade.ui.composite_scene import SequenceScene
from data_science_arcade.ui.correlation_scene import CorrelationScene
from data_science_arcade.ui.segment_slicer_scene import SegmentSlicerScene
from data_science_arcade.workbench.context import LessonContext

INCIDENT_DATASET = generate_incident_data()
PROMO_LOG_DATASET = generate_promo_log()
DEVICE_DASHBOARD_DATASET = generate_device_dashboard()

WEEKS = tuple(range(1, 9))

# Six leads over three real sources (Finance's weekly table, Marketing's
# own device dashboard, the promo-redemption webhook log) plus two
# analyses of Finance's own data (monitoring, the exec chart) - all on
# reused scene types (spec §54 Phase 13: "Lesson 30 should reuse systems
# from the entire course"). Unlike the pre-deepening version, which one
# was investigated does matter now: scoring.py reads real choices/evidence
# recorded through `context`, not just "was this lead visited." Which
# leads to open, and in what order, is the player's own call - see
# scenario.py's own `build_investigation_leads(app, context, sync_context)`
# call site for how each lead's own wrapper records into `context` before
# handing control back to the hub.

# --- regional_breakdown ---

REGIONAL_CUT_REQUEST = SegmentRequest(
    key="regional_cut",
    prompt_key="lesson.l30.lead.regional_cut.prompt",
    hint_key="lesson.l30.lead.regional_cut.hint",
    options=(
        SliceOption(
            "by_region",
            "lesson.l30.option.regional_cut.by_region",
            segments=(
                Segment("east", "lesson.l30.region.east", 150000.0, 74000.0),
                Segment("north", "lesson.l30.region.north", 90000.0, 90200.0),
                Segment("south", "lesson.l30.region.south", 95000.0, 95100.0),
                Segment("west", "lesson.l30.region.west", 85000.0, 84800.0),
            ),
        ),
        SliceOption(
            "by_device",
            "lesson.l30.option.regional_cut.by_device",
            segments=(
                Segment(
                    "mobile",
                    "lesson.l30.device.mobile",
                    device_revenue_at(DEVICE_DASHBOARD_DATASET, "mobile", 7),
                    device_revenue_at(DEVICE_DASHBOARD_DATASET, "mobile", 8),
                ),
                Segment(
                    "desktop",
                    "lesson.l30.device.desktop",
                    device_revenue_at(DEVICE_DASHBOARD_DATASET, "desktop", 7),
                    device_revenue_at(DEVICE_DASHBOARD_DATASET, "desktop", 8),
                ),
            ),
        ),
    ),
)

_EAST_BASELINE = region_baseline_average(INCIDENT_DATASET, "east")
_EAST_WEEK_7 = value_at(INCIDENT_DATASET, "east", 7, "revenue")
_EAST_WEEK_8 = value_at(INCIDENT_DATASET, "east", 8, "revenue")

BASELINE_CHECK_REQUEST = SegmentRequest(
    key="baseline_check",
    prompt_key="lesson.l30.lead.baseline_check.prompt",
    hint_key="lesson.l30.lead.baseline_check.hint",
    options=(
        SliceOption(
            "vs_own_baseline",
            "lesson.l30.option.baseline_check.vs_own_baseline",
            segments=(Segment("east", "lesson.l30.region.east", _EAST_BASELINE, _EAST_WEEK_8),),
        ),
        SliceOption(
            "vs_prior_week_only",
            "lesson.l30.option.baseline_check.vs_prior_week_only",
            segments=(Segment("east", "lesson.l30.region.east", _EAST_WEEK_7, _EAST_WEEK_8),),
        ),
    ),
)

CORRECT_REGIONAL_CUT = "by_region"
CORRECT_BASELINE_CHECK = "vs_own_baseline"


def flags_a_meaningful_decline(before: float, after: float) -> bool:
    # Every region has some ordinary week-to-week noise (a fraction of a
    # percent either way) - the default "any decline" flag_check would
    # flag West's own trivial -0.2% dip right alongside East's real
    # -50.7% one, muddying the "concentrated in one region" point this
    # lead exists to make. Reuses L18's own "flag only a relative gap past
    # a real threshold" idea (`relative_imbalance()`-style discipline)
    # rather than the noise-sensitive default.
    return percent_change(before, after) < -0.05


# --- checkout_health_check ---

CHECKOUT_HEALTH_REQUEST = SegmentRequest(
    key="checkout_health",
    prompt_key="lesson.l30.lead.checkout_health.prompt",
    hint_key="lesson.l30.lead.checkout_health.hint",
    options=(
        SliceOption(
            "full_window_avg",
            "lesson.l30.option.checkout_health.full_window_avg",
            segments=(
                Segment(
                    "checkout_completion_rate",
                    "lesson.l30.metric.checkout_completion_rate",
                    checkout_completion_window_average(INCIDENT_DATASET, (1, 2, 3, 4, 5, 6)),
                    checkout_completion_window_average(INCIDENT_DATASET, (7, 8)),
                ),
            ),
        ),
        SliceOption(
            "cherry_picked_low_week",
            "lesson.l30.option.checkout_health.cherry_picked_low_week",
            segments=(
                Segment(
                    "checkout_completion_rate",
                    "lesson.l30.metric.checkout_completion_rate",
                    checkout_completion_window_average(INCIDENT_DATASET, (1, 2, 3, 4, 5, 6, 7, 8)),
                    checkout_completion_window_average(INCIDENT_DATASET, (5,)),
                ),
            ),
        ),
    ),
)

CORRECT_CHECKOUT_HEALTH_OPTION = "full_window_avg"


def _checkout_health_flag(before: float, after: float) -> bool:
    return percent_change(before, after) < -0.002


# --- redesign_correlation ---

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


# --- promo_correlation (dedup + join micro-decision, then correlation) ---

DEDUP_FIELD = BriefField(
    key="promo_count_method",
    prompt_key="lesson.l30.field.promo_count_method.prompt",
    hint_key="lesson.l30.field.promo_count_method.hint",
    options=(
        BriefOption("dedupe_by_redemption_id", "lesson.l30.option.promo_count_method.dedupe_by_redemption_id"),
        BriefOption("count_every_log_row", "lesson.l30.option.promo_count_method.count_every_log_row"),
    ),
)

CORRECT_DEDUP_CHOICE = "dedupe_by_redemption_id"

TRUE_UNIQUE_REDEMPTIONS = unique_redemption_count(PROMO_LOG_DATASET)
RAW_EVENT_COUNT = raw_event_count(PROMO_LOG_DATASET)

_DEDUPED_WEEKLY_REDEMPTIONS = weekly_redemption_counts(PROMO_LOG_DATASET, "east", WEEKS, dedupe=True)
_RAW_WEEKLY_REDEMPTIONS = weekly_redemption_counts(PROMO_LOG_DATASET, "east", WEEKS, dedupe=False)
assert len(_DEDUPED_WEEKLY_REDEMPTIONS) == len(WEEKS)  # the real cardinality check: still one row per week, no fan-out
assert len(_RAW_WEEKLY_REDEMPTIONS) == len(WEEKS)


def promo_correlation_for(dedupe: bool) -> float:
    import pandas as pd

    redemptions = pd.Series(_DEDUPED_WEEKLY_REDEMPTIONS if dedupe else _RAW_WEEKLY_REDEMPTIONS, dtype=float)
    revenue = pd.Series(region_series(INCIDENT_DATASET, "east", "revenue"))
    return float(redemptions.corr(revenue))


def promo_correlation_request_for(dedupe: bool) -> CorrelationRequest:
    return CorrelationRequest(
        key="promo_correlation",
        prompt_key="lesson.l30.lead.promo_correlation.prompt",
        hint_key="lesson.l30.lead.promo_correlation.hint",
        metric_a_label_key="lesson.l30.metric.promo_redemptions",
        metric_b_label_key="lesson.l30.metric.east_revenue",
        evidence_key="lesson.l30.evidence.promo_correlation",
        correlation=promo_correlation_for(dedupe),
        sample_size=8,
        options=(
            VerdictOption("promo_context_confirmed", "lesson.l30.option.promo_correlation.promo_context_confirmed", "lesson.l30.explanation.promo_correlation.promo_context_confirmed"),
            VerdictOption("not_a_drop_seasonal", "lesson.l30.option.promo_correlation.not_a_drop_seasonal", "lesson.l30.explanation.promo_correlation.not_a_drop_seasonal"),
            VerdictOption("run_promo_permanently", "lesson.l30.option.promo_correlation.run_promo_permanently", "lesson.l30.explanation.promo_correlation.run_promo_permanently"),
        ),
    )


CORRECT_PROMO_VERDICT = "promo_context_confirmed"


# --- dashboard_chart ---

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


# --- monitoring_review ---
# `ThresholdOption.multiplier` here is a plain percent-of-6-week-baseline
# check (incident_data.py's own `simulate_monitoring`), NOT the
# stdev-of-spread statistic `framework/alerting.py`'s own docstring
# describes for L25 - same dataclass field, deliberately different
# statistic (8 weekly points don't support a meaningful stdev baseline
# the way L25's real daily series does). Framed as "would this have
# flagged a large deviation", never "would this have caught the
# incident" - a flagged deviation is a prompt to look closer, not an
# explanation (L25's own alert != explanation discipline, applied here).

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


def monitoring_choice_is_sound(metric_key: str, multiplier: float) -> bool:
    """A real recomputation, not a fixed answer key: a metric/threshold
    combo is sound only if it would have flagged week 7's real deviation
    with zero false alarms elsewhere. Deliberately does NOT prefer one
    threshold over another when both give the identical outcome for a
    metric (east_revenue: all three thresholds already agree) - scoring
    a choice between equivalent options would grade a distinction the
    data doesn't support."""

    class _Metric:
        metric_key = None

    class _Threshold:
        multiplier = None

    metric = _Metric()
    metric.metric_key = metric_key
    threshold = _Threshold()
    threshold.multiplier = multiplier
    false_alarms, caught = simulate_monitoring(INCIDENT_DATASET, metric, threshold, target_anomaly_week=MONITORING_REQUEST.target_incident_day)
    return caught and false_alarms == 0


def build_investigation_leads(
    app, context: LessonContext, collected: dict, sync_context: Callable[[], None]
) -> tuple[InvestigationLead, ...]:
    def _record(label_key: str, evidence_label_key: str, slot_key: str, python_code: str | None = None, detail: str | None = None) -> None:
        # `slot_key` is stable per LEAD (not per choice within it): reopening
        # an already-investigated lead with a different choice updates this
        # same slot in place (LessonContext.record_action/record_evidence's
        # own keyed-replace behavior), rather than leaving both the old and
        # new facts separately citable - correction #26's own regression.
        # Which content is currently correct is looked up from `collected`'s
        # own raw choice fields at scoring time (scoring.py's own
        # _SLOT_CORRECT_CHOICE), not from the evidence key itself.
        action = context.record_action(label_key=label_key, python_code=python_code, key=slot_key)
        context.record_evidence(label_key=evidence_label_key, source_action=action, key=slot_key, detail=detail)
        sync_context()

    def regional_breakdown(hub_close):
        def on_complete(choices: dict) -> None:
            regional_cut = choices["regional_cut"]
            baseline_check = choices["baseline_check"]
            collected["regional_cut_choice"] = regional_cut
            collected["baseline_check_choice"] = baseline_check

            if regional_cut == "by_region":
                _record(
                    "lesson.l30.action.regional_cut_by_region",
                    "lesson.l30.evidence.concentration",
                    "regional_cut",
                    python_code="by_region = incident.groupby('region')['revenue'].agg(['first', 'last'])",
                )
            else:
                _record(
                    "lesson.l30.action.regional_cut_by_device",
                    "lesson.l30.evidence.by_device_seen",
                    "regional_cut",
                    python_code="by_device = device_dashboard.groupby('device')['revenue'].sum()",
                )

            if baseline_check == "vs_own_baseline":
                detail = f"{_EAST_BASELINE:,.0f} -> {_EAST_WEEK_8:,.0f} ({percent_change(_EAST_BASELINE, _EAST_WEEK_8):+.1%})"
                _record(
                    "lesson.l30.action.baseline_check_vs_own_baseline",
                    "lesson.l30.evidence.reversion",
                    "baseline_check",
                    python_code="east_baseline = incident[(incident.region == 'east') & (incident.week <= 6)]['revenue'].mean()",
                    detail=detail,
                )
            else:
                _record(
                    "lesson.l30.action.baseline_check_vs_prior_week_only",
                    "lesson.l30.evidence.vs_prior_week_only_seen",
                    "baseline_check",
                    python_code="east_week7 = incident[(incident.region == 'east') & (incident.week == 7)]['revenue'].iloc[0]",
                )
            hub_close(choices)

        return SegmentSlicerScene(
            app,
            "lesson.l30.lead_title.regional_breakdown",
            (REGIONAL_CUT_REQUEST, BASELINE_CHECK_REQUEST),
            on_complete,
            guided=True,
            row_column_label_key="lesson.l30.segment_column_label",
            # Generic "Before"/"After" (the scene's own default labels),
            # not literal "Week 7"/"Week 8" - the baseline_check request's
            # own correct option shows the 6-week baseline average as
            # "before", not week 7 itself, so a literal week-number label
            # would misstate what the column actually holds.
            pick_hint_key="lesson.l30.pick_a_slice_hint",
            value_format=lambda segment, value: f"${value:,.0f}",
            flag_check=flags_a_meaningful_decline,
        )

    def checkout_health_check(hub_close):
        def on_complete(choices: dict) -> None:
            choice = choices["checkout_health"]
            collected["checkout_health_choice"] = choice
            if choice == "full_window_avg":
                before = checkout_completion_window_average(INCIDENT_DATASET, (1, 2, 3, 4, 5, 6))
                after = checkout_completion_window_average(INCIDENT_DATASET, (7, 8))
                detail = f"{before:.1%} -> {after:.1%}"
                _record(
                    "lesson.l30.action.checkout_health_full_window",
                    "lesson.l30.evidence.checkout_flat",
                    "checkout_health",
                    python_code="checkout_rate = incident[incident.region == 'east']['checkout_completion_rate']",
                    detail=detail,
                )
            else:
                _record(
                    "lesson.l30.action.checkout_health_cherry_picked",
                    "lesson.l30.evidence.checkout_cherry_picked",
                    "checkout_health",
                )
            hub_close(choices)

        return SegmentSlicerScene(
            app,
            "lesson.l30.lead_title.checkout_health_check",
            (CHECKOUT_HEALTH_REQUEST,),
            on_complete,
            guided=True,
            row_column_label_key="lesson.l30.checkout_metric_column_label",
            # Generic "Before"/"After" defaults here too - the two options'
            # own windows ("weeks 1-6 avg" vs "weeks 7-8 avg", or "full
            # 8-week avg" vs "one cherry-picked week") are neither of them
            # literally "Week 7"/"Week 8".
            pick_hint_key="lesson.l30.pick_a_slice_hint",
            value_format=lambda segment, value: f"{value:.1%}",
            flag_check=_checkout_health_flag,
        )

    def redesign_correlation(hub_close):
        def on_complete(choices: dict) -> None:
            collected["redesign_verdict_choice"] = choices["redesign_correlation"]
            _record(
                "lesson.l30.action.redesign_correlation",
                "lesson.l30.evidence.redesign_weak_correlation",
                "redesign_weak_correlation",
                python_code="redesign_corr = ticket_change.corr(revenue_change)  # n=4",
                detail=f"r={REDESIGN_CORRELATION:.2f}, n=4",
            )
            hub_close(choices)

        return CorrelationScene(app, "lesson.l30.lead_title.redesign_correlation", (REDESIGN_CORRELATION_REQUEST,), on_complete, guided=True)

    def promo_correlation(hub_close):
        dedup_choice_holder: dict[str, str] = {}

        def on_correlation_complete(choices: dict) -> None:
            collected["promo_verdict_choice"] = choices["promo_correlation"]
            dedupe = dedup_choice_holder["choice"] == CORRECT_DEDUP_CHOICE
            count = TRUE_UNIQUE_REDEMPTIONS if dedupe else RAW_EVENT_COUNT
            _record(
                "lesson.l30.action.promo_correlation",
                "lesson.l30.evidence.promo_context",
                "promo_context",
                python_code=(
                    "promo_by_week = promo_log.drop_duplicates(subset='redemption_id').groupby('week').size()\n"
                    "weekly = incident[incident.region == 'east'].merge(promo_by_week, on='week', how='left').fillna(0)"
                    if dedupe
                    else "promo_by_week = promo_log.groupby('week').size()  # not deduped - inflates the count\n"
                    "weekly = incident[incident.region == 'east'].merge(promo_by_week, on='week', how='left').fillna(0)"
                ),
                # Pure count, no English words baked in - `detail` is never
                # localized (only the label is), so any hardcoded phrase
                # here would silently leak into the PL locale too.
                detail=f"~{count:,}",
            )
            hub_close(choices)

        def build_second():
            dedupe = dedup_choice_holder["choice"] == CORRECT_DEDUP_CHOICE
            request = promo_correlation_request_for(dedupe)
            return CorrelationScene(app, "lesson.l30.lead_title.promo_correlation", (request,), on_correlation_complete, guided=True)

        def on_dedup_choice(brief: dict) -> None:
            dedup_choice_holder["choice"] = brief["promo_count_method"]
            collected["dedup_choice"] = brief["promo_count_method"]
            sequence.advance_to_second()

        sequence = SequenceScene(
            app,
            BriefBuilderScene(app, "lesson.l30.lead_title.promo_count_method", (DEDUP_FIELD,), on_dedup_choice, guided=True),
            build_second,
        )
        return sequence

    def dashboard_chart(hub_close):
        def on_complete(choices: dict) -> None:
            chart_choice = choices["dashboard_chart"]
            collected["dashboard_choice"] = chart_choice
            if chart_choice == CORRECT_CHART_OPTION:
                _record(
                    "lesson.l30.action.dashboard_chart_honest",
                    "lesson.l30.evidence.dashboard_trend",
                    "dashboard_review",
                    python_code="company_weekly = incident.groupby('week')['revenue'].sum()",
                )
            else:
                _record(
                    "lesson.l30.action.dashboard_chart_misleading",
                    "lesson.l30.evidence.dashboard_misleading",
                    "dashboard_review",
                )
            hub_close(choices)

        return ChartDesignerScene(app, "lesson.l30.lead_title.dashboard_chart", (DASHBOARD_CHART_REQUEST,), on_complete, guided=True)

    def monitoring_review(hub_close):
        def on_complete(choices: dict) -> None:
            metric_key, threshold_key = choices["review_monitoring"]
            threshold_multiplier = next(t.multiplier for t in MONITORING_REQUEST.threshold_options if t.key == threshold_key)
            collected["monitoring_choice"] = (metric_key, threshold_multiplier)
            sound = monitoring_choice_is_sound(metric_key, threshold_multiplier)
            _record(
                "lesson.l30.action.monitoring_review",
                "lesson.l30.evidence.monitoring_sound" if sound else "lesson.l30.evidence.monitoring_unsound",
                "monitoring_review",
                python_code="flagged = [w for w in weeks if abs(pct_change(baseline, value_at(w))) >= threshold]",
            )
            hub_close(choices)

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
        InvestigationLead("regional_breakdown", "lesson.l30.lead_label.regional_breakdown", regional_breakdown),
        InvestigationLead("promo_correlation", "lesson.l30.lead_label.promo_correlation", promo_correlation),
        InvestigationLead("redesign_correlation", "lesson.l30.lead_label.redesign_correlation", redesign_correlation),
        InvestigationLead("checkout_health_check", "lesson.l30.lead_label.checkout_health_check", checkout_health_check),
        InvestigationLead("monitoring_review", "lesson.l30.lead_label.monitoring_review", monitoring_review),
        InvestigationLead("dashboard_chart", "lesson.l30.lead_label.dashboard_chart", dashboard_chart),
    )


MINIMUM_LEADS_REQUIRED = 4

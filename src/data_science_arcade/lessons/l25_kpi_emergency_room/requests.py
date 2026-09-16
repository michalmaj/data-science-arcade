from data_science_arcade.lessons.framework.alerting import MetricOption, MonitoringRequest, ThresholdOption

CHECKOUT_ERROR_RATE = MetricOption("checkout_error_rate", "lesson.l25.option.metric.checkout_error_rate", metric_key="checkout_error_rate")
ON_TIME_DELIVERY_RATE = MetricOption("on_time_delivery_rate", "lesson.l25.option.metric.on_time_delivery_rate", metric_key="on_time_delivery_rate")
SOCIAL_MENTIONS = MetricOption("social_mentions", "lesson.l25.option.metric.social_mentions", metric_key="social_mentions")
PAGE_LOAD_TIME = MetricOption("page_load_time", "lesson.l25.option.metric.page_load_time", metric_key="page_load_time")

TIGHT_THRESHOLD = ThresholdOption("tight", "lesson.l25.option.threshold.tight", multiplier=1.0)
BALANCED_THRESHOLD = ThresholdOption("balanced", "lesson.l25.option.threshold.balanced", multiplier=3.0)

# Two real incidents this quarter (day 5's checkout spike, day 11's
# delivery dip), each requiring a different metric to catch - no single
# metric+threshold combo catches both (checkout_error_rate never flags
# day 11; on_time_delivery_rate never flags day 5, verified directly
# against incident_log.py's own simulate_monitoring). A third request
# offering the same checkout incident with a different wrong-metric
# distractor existed before this pass and was dropped as genuinely
# redundant with checkout_incident_focus (same correct answer, same real
# incident) - its own wrong-metric distractor (page_load_time) is still
# fully exercised, as Reveal A's own subject.
#
# Tight and balanced thresholds are BYTE-IDENTICAL for both real metrics
# on their own real incident day (0 false alarms, incident caught,
# verified directly) - so CORRECT_METRIC_BY_REQUEST intentionally scores
# metric selection only, never threshold. The interactive scene still
# offers both threshold options (needed to explore the WRONG-metric case,
# where threshold genuinely does matter) and still records the full
# (metric, threshold) pick for state/Mirror purposes.
MONITORING_REQUESTS: tuple[MonitoringRequest, ...] = (
    MonitoringRequest(
        key="checkout_incident_focus",
        prompt_key="lesson.l25.request.checkout_incident_focus.prompt",
        target_incident_day=5,
        metric_options=(CHECKOUT_ERROR_RATE, SOCIAL_MENTIONS),
        threshold_options=(TIGHT_THRESHOLD, BALANCED_THRESHOLD),
    ),
    MonitoringRequest(
        key="delivery_incident_focus",
        prompt_key="lesson.l25.request.delivery_incident_focus.prompt",
        target_incident_day=11,
        metric_options=(PAGE_LOAD_TIME, ON_TIME_DELIVERY_RATE),
        threshold_options=(BALANCED_THRESHOLD, TIGHT_THRESHOLD),
    ),
)

CORRECT_METRIC_BY_REQUEST: dict[str, str] = {
    "checkout_incident_focus": "checkout_error_rate",
    "delivery_incident_focus": "on_time_delivery_rate",
}

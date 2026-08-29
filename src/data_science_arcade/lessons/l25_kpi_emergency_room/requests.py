from data_science_arcade.lessons.framework.alerting import MetricOption, MonitoringRequest, ThresholdOption

CHECKOUT_ERROR_RATE = MetricOption("checkout_error_rate", "lesson.l25.option.metric.checkout_error_rate", metric_key="checkout_error_rate")
ON_TIME_DELIVERY_RATE = MetricOption("on_time_delivery_rate", "lesson.l25.option.metric.on_time_delivery_rate", metric_key="on_time_delivery_rate")
SOCIAL_MENTIONS = MetricOption("social_mentions", "lesson.l25.option.metric.social_mentions", metric_key="social_mentions")
PAGE_LOAD_TIME = MetricOption("page_load_time", "lesson.l25.option.metric.page_load_time", metric_key="page_load_time")

TIGHT_THRESHOLD = ThresholdOption("tight", "lesson.l25.option.threshold.tight", multiplier=1.0)
BALANCED_THRESHOLD = ThresholdOption("balanced", "lesson.l25.option.threshold.balanced", multiplier=3.0)

# Three scenarios, each built around one of the quarter's two real
# incidents (day 5's checkout spike, day 11's delivery dip) or the
# temptation to just watch everything as tightly as possible. The flawed
# metric offered never reflects that scenario's real incident, regardless
# of threshold - a vanity or merely-noisy metric doesn't become useful by
# watching it harder. The defensible combo (the metric that actually
# moves, a balanced threshold) never changes, but its position varies
# across both option columns.
MONITORING_REQUESTS: tuple[MonitoringRequest, ...] = (
    MonitoringRequest(
        key="checkout_incident_focus",
        prompt_key="lesson.l25.request.checkout_incident_focus.prompt",
        hint_key="lesson.l25.request.checkout_incident_focus.hint",
        target_incident_day=5,
        metric_options=(CHECKOUT_ERROR_RATE, SOCIAL_MENTIONS),
        threshold_options=(TIGHT_THRESHOLD, BALANCED_THRESHOLD),
    ),
    MonitoringRequest(
        key="delivery_incident_focus",
        prompt_key="lesson.l25.request.delivery_incident_focus.prompt",
        hint_key="lesson.l25.request.delivery_incident_focus.hint",
        target_incident_day=11,
        metric_options=(PAGE_LOAD_TIME, ON_TIME_DELIVERY_RATE),
        threshold_options=(BALANCED_THRESHOLD, TIGHT_THRESHOLD),
    ),
    MonitoringRequest(
        key="monitor_everything_temptation",
        prompt_key="lesson.l25.request.monitor_everything_temptation.prompt",
        hint_key="lesson.l25.request.monitor_everything_temptation.hint",
        target_incident_day=5,
        metric_options=(CHECKOUT_ERROR_RATE, PAGE_LOAD_TIME),
        threshold_options=(TIGHT_THRESHOLD, BALANCED_THRESHOLD),
    ),
)

CORRECT_COMBO_BY_REQUEST: dict[str, tuple[str, str]] = {
    "checkout_incident_focus": ("checkout_error_rate", "balanced"),
    "delivery_incident_focus": ("on_time_delivery_rate", "balanced"),
    "monitor_everything_temptation": ("checkout_error_rate", "balanced"),
}

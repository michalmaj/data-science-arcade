from data_science_arcade.lessons.framework.segment import Segment, SegmentRequest, SliceOption
from data_science_arcade.lessons.l16_metric_forge.incentive_data import (
    generate_app_data,
    generate_sales_data,
    generate_support_data,
    guardrail_mean,
    metric_mean,
)


def _metric_option(key: str, label_key: str, dataset, primary_label_key: str, guardrail_label_key: str) -> SliceOption:
    segments = (
        Segment("primary", primary_label_key, before_rate=metric_mean(dataset, key, "before"), after_rate=metric_mean(dataset, key, "after")),
        Segment("guardrail", guardrail_label_key, before_rate=guardrail_mean(dataset, key, "before"), after_rate=guardrail_mean(dataset, key, "after")),
    )
    return SliceOption(key, label_key, segments)


_SUPPORT_DATA = generate_support_data()
_SALES_DATA = generate_sales_data()
_APP_DATA = generate_app_data()

QUICK_CLOSE_SHARE = _metric_option(
    "quick_close_share", "lesson.l16.metric.quick_close_share", _SUPPORT_DATA,
    "lesson.l16.row.primary_quick_close_share", "lesson.l16.row.guardrail_csat",
)
FIRST_CONTACT_RESOLUTION_RATE = _metric_option(
    "first_contact_resolution_rate", "lesson.l16.metric.first_contact_resolution_rate", _SUPPORT_DATA,
    "lesson.l16.row.primary_first_contact_resolution_rate", "lesson.l16.row.guardrail_csat",
)
TICKETS_CLOSED_RATE = _metric_option(
    "tickets_closed_rate", "lesson.l16.metric.tickets_closed_rate", _SUPPORT_DATA,
    "lesson.l16.row.primary_tickets_closed_rate", "lesson.l16.row.guardrail_csat",
)
SIGNUP_CONVERSION_RATE = _metric_option(
    "signup_conversion_rate", "lesson.l16.metric.signup_conversion_rate", _SALES_DATA,
    "lesson.l16.row.primary_signup_conversion_rate", "lesson.l16.row.guardrail_retention_30d",
)
ACTIVATED_CUSTOMER_RATE = _metric_option(
    "activated_customer_rate", "lesson.l16.metric.activated_customer_rate", _SALES_DATA,
    "lesson.l16.row.primary_activated_customer_rate", "lesson.l16.row.guardrail_retention_30d",
)
LEADS_CONTACTED_RATE = _metric_option(
    "leads_contacted_rate", "lesson.l16.metric.leads_contacted_rate", _SALES_DATA,
    "lesson.l16.row.primary_leads_contacted_rate", "lesson.l16.row.guardrail_retention_30d",
)
DAILY_OPEN_RATE = _metric_option(
    "daily_open_rate", "lesson.l16.metric.daily_open_rate", _APP_DATA,
    "lesson.l16.row.primary_daily_open_rate", "lesson.l16.row.guardrail_retention_90d",
)
TASK_COMPLETION_RATE = _metric_option(
    "task_completion_rate", "lesson.l16.metric.task_completion_rate", _APP_DATA,
    "lesson.l16.row.primary_task_completion_rate", "lesson.l16.row.guardrail_retention_90d",
)
NOTIFICATION_CLICK_RATE = _metric_option(
    "notification_click_rate", "lesson.l16.metric.notification_click_rate", _APP_DATA,
    "lesson.l16.row.primary_notification_click_rate", "lesson.l16.row.guardrail_retention_90d",
)

# Hand-crafted, no trap outside the twist (matching every prior lesson's
# discipline): each request has one metric resistant to gaming plus two
# genuinely gameable decoys - every candidate's own number improves once
# targeted, but only the correct one's guardrail holds up, per real
# computed data (see incentive_data.py). Correct-option index varies
# across all three requests so no single index reveals the answer.
METRIC_REQUESTS: tuple[SegmentRequest, ...] = (
    SegmentRequest(
        key="support_speed_initiative",
        prompt_key="lesson.l16.request.support_speed_initiative.prompt",
        hint_key="lesson.l16.request.support_speed_initiative.hint",
        options=(TICKETS_CLOSED_RATE, FIRST_CONTACT_RESOLUTION_RATE, QUICK_CLOSE_SHARE),
    ),
    SegmentRequest(
        key="sales_growth_initiative",
        prompt_key="lesson.l16.request.sales_growth_initiative.prompt",
        hint_key="lesson.l16.request.sales_growth_initiative.hint",
        options=(ACTIVATED_CUSTOMER_RATE, LEADS_CONTACTED_RATE, SIGNUP_CONVERSION_RATE),
    ),
    SegmentRequest(
        key="app_engagement_initiative",
        prompt_key="lesson.l16.request.app_engagement_initiative.prompt",
        hint_key="lesson.l16.request.app_engagement_initiative.hint",
        options=(NOTIFICATION_CLICK_RATE, DAILY_OPEN_RATE, TASK_COMPLETION_RATE),
    ),
)

CORRECT_OPTION_BY_REQUEST: dict[str, str] = {
    "support_speed_initiative": "first_contact_resolution_rate",
    "sales_growth_initiative": "activated_customer_rate",
    "app_engagement_initiative": "task_completion_rate",
}

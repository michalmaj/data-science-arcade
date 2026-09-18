from data_science_arcade.lessons.framework.findings import Finding
from data_science_arcade.lessons.l29_the_executive_brief.findings_data import (
    percent_change_mirror_code,
    point_change_mirror_code,
)

# Eight real findings from the same checkout-redesign quarter, backed by
# lessons/l29_the_executive_brief/findings_data.py's real computed
# numbers, for one stated decision: should NovaMart keep the checkout
# redesign in production, and what should leadership monitor next? See
# findings_data.py's own header for the full three-tier breakdown this
# pool is built around - headline-candidate / real-but-lower-priority /
# not connected to this decision.
CHECKOUT_COMPLETION = Finding(
    "checkout_completion",
    "lesson.l29.finding.checkout_completion",
    python_code=point_change_mirror_code("checkout_completion", "checkout_completion_change"),
)
PAYMENT_STEP_ABANDONMENT = Finding(
    "payment_step_abandonment",
    "lesson.l29.finding.payment_step_abandonment",
    python_code=point_change_mirror_code("payment_step_abandonment", "payment_step_abandonment_change"),
)
ORDER_VALUE_AND_RETURNS_STEADY = Finding(
    "order_value_and_returns_steady",
    "lesson.l29.finding.order_value_and_returns_steady",
    python_code=(
        point_change_mirror_code("average_order_value", "order_value_change")
        + "\n"
        + point_change_mirror_code("return_rate", "return_rate_change")
    ),
)
SOCIAL_MENTIONS = Finding(
    "social_mentions", "lesson.l29.finding.social_mentions", python_code=percent_change_mirror_code("social_mentions", "social_mentions_change")
)
STOCK_PRICE = Finding("stock_price", "lesson.l29.finding.stock_price", python_code=percent_change_mirror_code("stock_price", "stock_price_change"))
EMPLOYEE_SATISFACTION = Finding(
    "employee_satisfaction",
    "lesson.l29.finding.employee_satisfaction",
    python_code=point_change_mirror_code("employee_satisfaction", "employee_satisfaction_change"),
)
SUPPORT_TICKETS = Finding(
    "support_tickets_confusing_checkout",
    "lesson.l29.finding.support_tickets_confusing_checkout",
    python_code=percent_change_mirror_code("support_tickets_confusing_checkout", "support_tickets_change"),
)
COMPETITOR_COMPLETION_RATE = Finding(
    "competitor_completion_rate",
    "lesson.l29.finding.competitor_completion_rate",
    python_code=point_change_mirror_code("competitor_completion_rate", "competitor_completion_rate_change"),
)

FINDINGS_POOL: tuple[Finding, ...] = (
    CHECKOUT_COMPLETION,
    PAYMENT_STEP_ABANDONMENT,
    ORDER_VALUE_AND_RETURNS_STEADY,
    SOCIAL_MENTIONS,
    STOCK_PRICE,
    EMPLOYEE_SATISFACTION,
    SUPPORT_TICKETS,
    COMPETITOR_COMPLETION_RATE,
)

SHORTLIST_TARGET_COUNT = 5
"""Cut 1's own target_count: from the full 8-finding pool, keep the 5
that bear on the stated decision at all - excluding the 3 with no given
connection to it (social_mentions, stock_price, employee_satisfaction)."""

ON_TOPIC_FINDING_KEYS: frozenset[str] = frozenset(
    {
        CHECKOUT_COMPLETION.key,
        PAYMENT_STEP_ABANDONMENT.key,
        ORDER_VALUE_AND_RETURNS_STEADY.key,
        SUPPORT_TICKETS.key,
        COMPETITOR_COMPLETION_RATE.key,
    }
)
"""Cut 1's own correct 5-set."""

HEADLINE_TARGET_COUNT = 3
"""Cut 2's own EvidenceField target_count: of the 5 on-topic findings,
the 3 that each add a genuinely distinct facet of the stated decision
under a short brief's own budget - not the 2 real, on-topic findings
that don't (support_tickets, real but redundant with the payment-step
mechanism already covered; competitor_completion_rate, real but
caveat-tier, not supporting evidence for the headline claim)."""

CORRECT_FINDING_KEYS: frozenset[str] = frozenset(
    {CHECKOUT_COMPLETION.key, PAYMENT_STEP_ABANDONMENT.key, ORDER_VALUE_AND_RETURNS_STEADY.key}
)
"""Cut 2's own correct 3-set - the direct outcome, the process/friction
mechanism behind it, and the guardrail check for a hidden cost."""

LEAD_FINDING_KEY = CHECKOUT_COMPLETION.key
"""The one finding, among the 3 headline candidates, that directly
answers the stated decision's own outcome question - correct answer for
the `lead_finding` field. `payment_step_abandonment` and
`order_value_and_returns_steady` are real, correctly-cited support and
guardrail evidence, not the lead."""

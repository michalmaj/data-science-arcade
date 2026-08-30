from data_science_arcade.lessons.framework.findings import Finding

# Eight real findings from the same checkout-redesign quarter - hand-
# crafted, not random, backed by lessons/l29_the_executive_brief/
# findings_data.py's real computed numbers. Only three are actually
# decision-relevant to "is the redesign working, and should we keep it":
# the direct completion-rate lift, the diagnostic payment-step detail
# that shows *where* the lift comes from, and the pair of numbers that
# rule out the two most obvious costs (bigger carts, more returns).
# The rest are real, but either moved for unrelated reasons (a viral
# post, a market-wide rally, a routine survey) or are secondary/
# redundant with a stronger finding already in the three.
CHECKOUT_COMPLETION = Finding(
    "checkout_completion", "lesson.l29.finding.checkout_completion", python_code="point_change(dataset, 'checkout_completion')  # = +4.0 pts"
)
PAYMENT_STEP_ABANDONMENT = Finding(
    "payment_step_abandonment",
    "lesson.l29.finding.payment_step_abandonment",
    python_code="point_change(dataset, 'payment_step_abandonment')  # = -5.0 pts",
)
ORDER_VALUE_AND_RETURNS_STEADY = Finding(
    "order_value_and_returns_steady",
    "lesson.l29.finding.order_value_and_returns_steady",
    python_code=(
        "point_change(dataset, 'average_order_value')  # = +0.20\n"
        "point_change(dataset, 'return_rate')  # = +0.1 pts"
    ),
)
SOCIAL_MENTIONS = Finding(
    "social_mentions", "lesson.l29.finding.social_mentions", python_code="percent_change(dataset, 'social_mentions')  # = +3.00 (+300%)"
)
STOCK_PRICE = Finding("stock_price", "lesson.l29.finding.stock_price", python_code="percent_change(dataset, 'stock_price')  # = +0.09 (+9%)")
EMPLOYEE_SATISFACTION = Finding(
    "employee_satisfaction", "lesson.l29.finding.employee_satisfaction", python_code="point_change(dataset, 'employee_satisfaction')  # = +5.0 pts"
)
SUPPORT_TICKETS = Finding(
    "support_tickets_confusing_checkout",
    "lesson.l29.finding.support_tickets_confusing_checkout",
    python_code="percent_change(dataset, 'support_tickets_confusing_checkout')  # = -0.60 (-60%)",
)
COMPETITOR_COMPLETION_RATE = Finding(
    "competitor_completion_rate",
    "lesson.l29.finding.competitor_completion_rate",
    python_code="point_change(dataset, 'competitor_completion_rate')  # = +1.0 pt",
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

TARGET_FINDING_COUNT = 3

CORRECT_FINDING_KEYS: frozenset[str] = frozenset(
    {CHECKOUT_COMPLETION.key, PAYMENT_STEP_ABANDONMENT.key, ORDER_VALUE_AND_RETURNS_STEADY.key}
)

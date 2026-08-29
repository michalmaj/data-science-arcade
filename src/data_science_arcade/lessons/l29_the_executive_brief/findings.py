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
CHECKOUT_COMPLETION = Finding("checkout_completion", "lesson.l29.finding.checkout_completion")
PAYMENT_STEP_ABANDONMENT = Finding("payment_step_abandonment", "lesson.l29.finding.payment_step_abandonment")
ORDER_VALUE_AND_RETURNS_STEADY = Finding("order_value_and_returns_steady", "lesson.l29.finding.order_value_and_returns_steady")
SOCIAL_MENTIONS = Finding("social_mentions", "lesson.l29.finding.social_mentions")
STOCK_PRICE = Finding("stock_price", "lesson.l29.finding.stock_price")
EMPLOYEE_SATISFACTION = Finding("employee_satisfaction", "lesson.l29.finding.employee_satisfaction")
SUPPORT_TICKETS = Finding("support_tickets_confusing_checkout", "lesson.l29.finding.support_tickets_confusing_checkout")
COMPETITOR_COMPLETION_RATE = Finding("competitor_completion_rate", "lesson.l29.finding.competitor_completion_rate")

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

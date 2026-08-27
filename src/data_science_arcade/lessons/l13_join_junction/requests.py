from data_science_arcade.lessons.framework.join import JoinOption, JoinRequest

# Hand-crafted, no trap outside the twist (matching every prior lesson's
# discipline): each request has one genuinely correct join type given
# what it actually asks for. Correct-option position varies across all
# three requests so no single index reveals the answer.
JOIN_REQUESTS: tuple[JoinRequest, ...] = (
    JoinRequest(
        key="orders_missing_customers",
        prompt_key="lesson.l13.request.orders_missing_customers.prompt",
        hint_key="lesson.l13.request.orders_missing_customers.hint",
        options=(
            JoinOption("inner", "lesson.l13.join.inner", "inner"),
            JoinOption("left", "lesson.l13.join.left", "left"),
            JoinOption("right", "lesson.l13.join.right", "right"),
        ),
    ),
    JoinRequest(
        key="confident_customer_match",
        prompt_key="lesson.l13.request.confident_customer_match.prompt",
        hint_key="lesson.l13.request.confident_customer_match.hint",
        options=(
            JoinOption("left", "lesson.l13.join.left", "left"),
            JoinOption("inner", "lesson.l13.join.inner", "inner"),
            JoinOption("right", "lesson.l13.join.right", "right"),
        ),
    ),
    JoinRequest(
        key="full_customer_outreach_list",
        prompt_key="lesson.l13.request.full_customer_outreach_list.prompt",
        hint_key="lesson.l13.request.full_customer_outreach_list.hint",
        options=(
            JoinOption("left", "lesson.l13.join.left", "left"),
            JoinOption("inner", "lesson.l13.join.inner", "inner"),
            JoinOption("right", "lesson.l13.join.right", "right"),
        ),
    ),
)

CORRECT_HOW_BY_REQUEST: dict[str, str] = {
    "orders_missing_customers": "left",
    "confident_customer_match": "inner",
    "full_customer_outreach_list": "right",
}

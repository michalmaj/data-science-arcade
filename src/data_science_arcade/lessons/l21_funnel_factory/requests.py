from data_science_arcade.lessons.framework.funnel import FunnelRequest
from data_science_arcade.lessons.l21_funnel_factory.checkout_events import build_funnel_definition, generate_checkout_events

_CHECKOUT_EVENTS = generate_checkout_events()

_LEGACY_CART_TRACKING = build_funnel_definition(
    _CHECKOUT_EVENTS,
    "legacy_cart_tracking",
    "legacy_cart_tracking",
    "lesson.l21.definition.legacy_cart_tracking",
    step_label_overrides={"add_to_cart": "lesson.l21.step.add_to_cart_legacy"},
)
_COMPLETE_CART_TRACKING = build_funnel_definition(
    _CHECKOUT_EVENTS,
    "complete_cart_tracking",
    "complete_cart_tracking",
    "lesson.l21.definition.complete_cart_tracking",
)
_PERCENT_OF_TOTAL_VISITS = build_funnel_definition(
    _CHECKOUT_EVENTS,
    "complete_cart_tracking",
    "percent_of_total_visits",
    "lesson.l21.definition.percent_of_total_visits",
    percent_basis="top",
)
_PERCENT_OF_PREVIOUS_STEP = build_funnel_definition(
    _CHECKOUT_EVENTS,
    "complete_cart_tracking",
    "percent_of_previous_step",
    "lesson.l21.definition.percent_of_previous_step",
    percent_basis="previous",
)
_RAW_CART_EVENTS = build_funnel_definition(
    _CHECKOUT_EVENTS,
    "raw_cart_events",
    "raw_cart_events",
    "lesson.l21.definition.raw_cart_events",
    step_label_overrides={"add_to_cart": "lesson.l21.step.add_to_cart_raw"},
)
_UNIQUE_SESSION_CART = build_funnel_definition(
    _CHECKOUT_EVENTS,
    "complete_cart_tracking",
    "unique_session_cart",
    "lesson.l21.definition.unique_session_cart",
)

MOBILE_DROPOUT_COMPLAINT = FunnelRequest(
    key="mobile_dropout_complaint",
    prompt_key="lesson.l21.request.mobile_dropout_complaint.prompt",
    hint_key="lesson.l21.request.mobile_dropout_complaint.hint",
    definitions=(_LEGACY_CART_TRACKING, _COMPLETE_CART_TRACKING),
)
PAYMENT_STEP_COMPLAINT = FunnelRequest(
    key="payment_step_complaint",
    prompt_key="lesson.l21.request.payment_step_complaint.prompt",
    hint_key="lesson.l21.request.payment_step_complaint.hint",
    definitions=(_PERCENT_OF_PREVIOUS_STEP, _PERCENT_OF_TOTAL_VISITS),
)
CART_ABANDONMENT_COMPLAINT = FunnelRequest(
    key="cart_abandonment_complaint",
    prompt_key="lesson.l21.request.cart_abandonment_complaint.prompt",
    hint_key="lesson.l21.request.cart_abandonment_complaint.hint",
    definitions=(_RAW_CART_EVENTS, _UNIQUE_SESSION_CART),
)

FUNNEL_REQUESTS: tuple[FunnelRequest, ...] = (MOBILE_DROPOUT_COMPLAINT, PAYMENT_STEP_COMPLAINT, CART_ABANDONMENT_COMPLAINT)

CORRECT_DEFINITION_BY_REQUEST: dict[str, str] = {
    "mobile_dropout_complaint": "complete_cart_tracking",
    "payment_step_complaint": "percent_of_previous_step",
    "cart_abandonment_complaint": "unique_session_cart",
}

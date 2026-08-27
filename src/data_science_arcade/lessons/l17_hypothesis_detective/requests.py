from data_science_arcade.lessons.framework.prediction import HypothesisRequest
from data_science_arcade.lessons.l17_hypothesis_detective.launch_data import generate_launch_data, metric_mean

_LAUNCH_DATA = generate_launch_data()


def _dollars(value: float) -> str:
    return f"${value:,.2f}"


REPEAT_PURCHASE_RATE = HypothesisRequest(
    key="repeat_purchase_rate",
    prompt_key="lesson.l17.request.repeat_purchase_rate.prompt",
    metric_label_key="lesson.l17.metric.repeat_purchase_rate",
    hint_key="lesson.l17.request.repeat_purchase_rate.hint",
    before_value=metric_mean(_LAUNCH_DATA, "repeat_purchase_rate", "before"),
    after_value=metric_mean(_LAUNCH_DATA, "repeat_purchase_rate", "after"),
)
AVERAGE_ORDER_VALUE = HypothesisRequest(
    key="average_order_value",
    prompt_key="lesson.l17.request.average_order_value.prompt",
    metric_label_key="lesson.l17.metric.average_order_value",
    hint_key="lesson.l17.request.average_order_value.hint",
    before_value=metric_mean(_LAUNCH_DATA, "average_order_value", "before"),
    after_value=metric_mean(_LAUNCH_DATA, "average_order_value", "after"),
    value_format=_dollars,
)
SUPPORT_CONTACT_RATE = HypothesisRequest(
    key="support_contact_rate",
    prompt_key="lesson.l17.request.support_contact_rate.prompt",
    metric_label_key="lesson.l17.metric.support_contact_rate",
    hint_key="lesson.l17.request.support_contact_rate.hint",
    before_value=metric_mean(_LAUNCH_DATA, "support_contact_rate", "before"),
    after_value=metric_mean(_LAUNCH_DATA, "support_contact_rate", "after"),
)

# The three direction buttons always render in the same Increase/Decrease/
# No-real-change order (a stable response scale, not per-request decoys),
# so whichever request's real answer is "increase" unavoidably sits at the
# keyboard-focus default (button index 0) no matter how these requests are
# ordered - only one of the three ever does, though, so the Lesson 04
# always-index-0 exploit (an answer a player could learn to pick blindly)
# doesn't apply: two of three requests still need an actual prediction.
HYPOTHESIS_REQUESTS: tuple[HypothesisRequest, ...] = (
    REPEAT_PURCHASE_RATE,
    AVERAGE_ORDER_VALUE,
    SUPPORT_CONTACT_RATE,
)

CORRECT_DIRECTION_BY_REQUEST: dict[str, str] = {request.key: request.correct_direction for request in HYPOTHESIS_REQUESTS}

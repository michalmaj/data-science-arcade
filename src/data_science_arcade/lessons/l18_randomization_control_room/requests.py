from data_science_arcade.lessons.framework.segment import Segment, SegmentRequest, SliceOption
from data_science_arcade.lessons.l18_randomization_control_room.assignment_data import (
    average_tenure,
    covariate_rate,
    generate_assignment_data,
    group_size,
)

_ASSIGNMENT_DATA = generate_assignment_data()


def _rule_option(experiment_key: str, rule_key: str, label_key: str, covariate_label_key: str) -> SliceOption:
    segments = (
        Segment(
            "group_size",
            "lesson.l18.row.group_size",
            before_rate=group_size(_ASSIGNMENT_DATA, experiment_key, rule_key, "treatment"),
            after_rate=group_size(_ASSIGNMENT_DATA, experiment_key, rule_key, "control"),
        ),
        Segment(
            "covariate",
            covariate_label_key,
            before_rate=covariate_rate(_ASSIGNMENT_DATA, experiment_key, rule_key, "treatment"),
            after_rate=covariate_rate(_ASSIGNMENT_DATA, experiment_key, rule_key, "control"),
        ),
        Segment(
            "tenure",
            "lesson.l18.row.avg_tenure",
            before_rate=average_tenure(_ASSIGNMENT_DATA, experiment_key, rule_key, "treatment"),
            after_rate=average_tenure(_ASSIGNMENT_DATA, experiment_key, rule_key, "control"),
        ),
    )
    return SliceOption(rule_key, label_key, segments)


def _experiment_request(key: str, prompt_key: str, hint_key: str, covariate_label_key: str, rule_order: tuple[str, ...]) -> SegmentRequest:
    rule_label_keys = {
        "order_alternation": "lesson.l18.rule.order_alternation",
        "id_parity": "lesson.l18.rule.id_parity",
        "signup_week": "lesson.l18.rule.signup_week",
    }
    options = tuple(_rule_option(key, rule_key, rule_label_keys[rule_key], covariate_label_key) for rule_key in rule_order)
    return SegmentRequest(key=key, prompt_key=prompt_key, hint_key=hint_key, options=options)


# Rule order varies per request so the correct rule never sits at button
# index 0 - the default keyboard focus (Lesson 04 regression guard) - even
# though no single request repeats the pattern on its own.
CHECKOUT_REDESIGN = _experiment_request(
    "checkout_redesign",
    "lesson.l18.request.checkout_redesign.prompt",
    "lesson.l18.request.checkout_redesign.hint",
    "lesson.l18.row.mobile_share",
    rule_order=("id_parity", "signup_week", "order_alternation"),
)
LOYALTY_DISCOUNT_TEST = _experiment_request(
    "loyalty_discount_test",
    "lesson.l18.request.loyalty_discount_test.prompt",
    "lesson.l18.request.loyalty_discount_test.hint",
    "lesson.l18.row.referral_share",
    rule_order=("signup_week", "id_parity", "order_alternation"),
)
NOTIFICATION_FREQUENCY_TEST = _experiment_request(
    "notification_frequency_test",
    "lesson.l18.request.notification_frequency_test.prompt",
    "lesson.l18.request.notification_frequency_test.hint",
    "lesson.l18.row.high_spend_share",
    rule_order=("order_alternation", "signup_week", "id_parity"),
)

ASSIGNMENT_REQUESTS: tuple[SegmentRequest, ...] = (CHECKOUT_REDESIGN, LOYALTY_DISCOUNT_TEST, NOTIFICATION_FREQUENCY_TEST)

CORRECT_RULE_BY_REQUEST: dict[str, str] = {
    "checkout_redesign": "order_alternation",
    "loyalty_discount_test": "id_parity",
    "notification_frequency_test": "signup_week",
}

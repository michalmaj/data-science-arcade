from data_science_arcade.lessons.framework.flow import FlowEventOption, FlowStep

# Hand-crafted (not random): the 6 spec-listed check types, each calibrated
# against real context from this specific daily feed rather than applied
# as a generic checklist - a check that's too strict blocks good data, too
# loose misses real problems. Each has one genuinely correct calibration
# plus two targeted decoys (one too strict, one too loose), no trap - the
# trap is reserved for the twist, matching every prior lesson's discipline.
VALIDATION_CHECKS: tuple[FlowStep, ...] = (
    FlowStep(
        key="uniqueness",
        short_label_key="lesson.l10.check.uniqueness.label",
        prompt_key="lesson.l10.check.uniqueness.prompt",
        hint_key="lesson.l10.check.uniqueness.hint",
        options=(
            FlowEventOption("no_check", "lesson.l10.rule.uniqueness.no_check"),
            FlowEventOption("flag_any_duplicate", "lesson.l10.rule.uniqueness.flag_any_duplicate"),
            FlowEventOption("flag_over_100", "lesson.l10.rule.uniqueness.flag_over_100"),
        ),
    ),
    FlowStep(
        key="allowed_range",
        short_label_key="lesson.l10.check.allowed_range.label",
        prompt_key="lesson.l10.check.allowed_range.prompt",
        hint_key="lesson.l10.check.allowed_range.hint",
        options=(
            FlowEventOption("flag_over_1000", "lesson.l10.rule.allowed_range.flag_over_1000"),
            FlowEventOption("flag_outside_0_100k", "lesson.l10.rule.allowed_range.flag_outside_0_100k"),
            FlowEventOption("no_check", "lesson.l10.rule.allowed_range.no_check"),
        ),
    ),
    FlowStep(
        key="null_limit",
        short_label_key="lesson.l10.check.null_limit.label",
        prompt_key="lesson.l10.check.null_limit.prompt",
        hint_key="lesson.l10.check.null_limit.hint",
        options=(
            FlowEventOption("zero_tolerance", "lesson.l10.rule.null_limit.zero_tolerance"),
            FlowEventOption("no_check", "lesson.l10.rule.null_limit.no_check"),
            FlowEventOption("flag_over_5_percent", "lesson.l10.rule.null_limit.flag_over_5_percent"),
        ),
    ),
    FlowStep(
        key="referential_integrity",
        short_label_key="lesson.l10.check.referential_integrity.label",
        prompt_key="lesson.l10.check.referential_integrity.prompt",
        hint_key="lesson.l10.check.referential_integrity.hint",
        options=(
            FlowEventOption("sample_last_10", "lesson.l10.rule.referential_integrity.sample_last_10"),
            FlowEventOption("no_check", "lesson.l10.rule.referential_integrity.no_check"),
            FlowEventOption("check_every_row", "lesson.l10.rule.referential_integrity.check_every_row"),
        ),
    ),
    FlowStep(
        key="freshness",
        short_label_key="lesson.l10.check.freshness.label",
        prompt_key="lesson.l10.check.freshness.prompt",
        hint_key="lesson.l10.check.freshness.hint",
        options=(
            FlowEventOption("flag_over_1_hour", "lesson.l10.rule.freshness.flag_over_1_hour"),
            FlowEventOption("no_check", "lesson.l10.rule.freshness.no_check"),
            FlowEventOption("flag_over_48_hours", "lesson.l10.rule.freshness.flag_over_48_hours"),
        ),
    ),
    FlowStep(
        key="category_validity",
        short_label_key="lesson.l10.check.category_validity.label",
        prompt_key="lesson.l10.check.category_validity.prompt",
        hint_key="lesson.l10.check.category_validity.hint",
        options=(
            FlowEventOption("null_only", "lesson.l10.rule.category_validity.null_only"),
            FlowEventOption("accept_anything", "lesson.l10.rule.category_validity.accept_anything"),
            FlowEventOption("flag_unknown_values", "lesson.l10.rule.category_validity.flag_unknown_values"),
        ),
    ),
)

CORRECT_RULE_BY_CHECK: dict[str, str] = {
    "uniqueness": "flag_any_duplicate",
    "allowed_range": "flag_outside_0_100k",
    "null_limit": "flag_over_5_percent",
    "referential_integrity": "check_every_row",
    "freshness": "flag_over_48_hours",
    "category_validity": "flag_unknown_values",
}

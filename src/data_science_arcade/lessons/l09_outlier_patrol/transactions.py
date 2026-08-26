from data_science_arcade.lessons.framework.flow import FlowEventOption, FlowStep

# Hand-crafted (not random): 5 extreme NovaPay transactions, one per
# spec-listed action (retain/flag/exclude/cap/investigate) - each has one
# genuinely correct action given its context, plus two decoys (an
# over-cautious one and an under-cautious one), no trap. The trap - that a
# single global rule can't tell these apart - is reserved for the twist.
OUTLIER_CASES: tuple[FlowStep, ...] = (
    FlowStep(
        key="consistent_enterprise_order",
        short_label_key="lesson.l09.case.consistent_enterprise_order.label",
        prompt_key="lesson.l09.case.consistent_enterprise_order.prompt",
        hint_key="lesson.l09.case.consistent_enterprise_order.hint",
        options=(
            FlowEventOption("exclude", "lesson.l09.action.exclude"),
            FlowEventOption("retain", "lesson.l09.action.retain"),
            FlowEventOption("flag", "lesson.l09.action.flag"),
        ),
    ),
    FlowStep(
        key="new_account_spike",
        short_label_key="lesson.l09.case.new_account_spike.label",
        prompt_key="lesson.l09.case.new_account_spike.prompt",
        hint_key="lesson.l09.case.new_account_spike.hint",
        options=(
            FlowEventOption("retain", "lesson.l09.action.retain"),
            FlowEventOption("flag", "lesson.l09.action.flag"),
            FlowEventOption("exclude", "lesson.l09.action.exclude"),
        ),
    ),
    FlowStep(
        key="test_artifact",
        short_label_key="lesson.l09.case.test_artifact.label",
        prompt_key="lesson.l09.case.test_artifact.prompt",
        hint_key="lesson.l09.case.test_artifact.hint",
        options=(
            FlowEventOption("retain", "lesson.l09.action.retain"),
            FlowEventOption("cap", "lesson.l09.action.cap"),
            FlowEventOption("exclude", "lesson.l09.action.exclude"),
        ),
    ),
    FlowStep(
        key="decimal_slip",
        short_label_key="lesson.l09.case.decimal_slip.label",
        prompt_key="lesson.l09.case.decimal_slip.prompt",
        hint_key="lesson.l09.case.decimal_slip.hint",
        options=(
            FlowEventOption("retain", "lesson.l09.action.retain"),
            FlowEventOption("exclude", "lesson.l09.action.exclude"),
            FlowEventOption("cap", "lesson.l09.action.cap"),
        ),
    ),
    FlowStep(
        key="fraud_signals",
        short_label_key="lesson.l09.case.fraud_signals.label",
        prompt_key="lesson.l09.case.fraud_signals.prompt",
        hint_key="lesson.l09.case.fraud_signals.hint",
        options=(
            FlowEventOption("retain", "lesson.l09.action.retain"),
            FlowEventOption("exclude", "lesson.l09.action.exclude"),
            FlowEventOption("investigate", "lesson.l09.action.investigate"),
        ),
    ),
)

CORRECT_ACTION_BY_CASE: dict[str, str] = {
    "consistent_enterprise_order": "retain",
    "new_account_spike": "flag",
    "test_artifact": "exclude",
    "decimal_slip": "cap",
    "fraud_signals": "investigate",
}

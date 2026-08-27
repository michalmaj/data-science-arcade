from data_science_arcade.lessons.framework.monitoring import MetricRow, MonitoringCheckpoint
from data_science_arcade.lessons.l20_ab_test_commander.experiment_data import (
    CHECKPOINT_DAYS,
    TOTAL_RUNTIME_DAYS,
    generate_checkout_experiment_data,
    rate_at_checkpoint,
)

_EXPERIMENT_DATA = generate_checkout_experiment_data()

_ROW_LABEL_KEYS = (
    ("primary_conversion", "lesson.l20.row.primary_conversion"),
    ("guardrail_refund", "lesson.l20.row.guardrail_refund"),
    ("guardrail_support", "lesson.l20.row.guardrail_support"),
    ("segment_mobile", "lesson.l20.row.segment_mobile"),
)


def _build_checkpoint(checkpoint_number: int) -> MonitoringCheckpoint:
    rows = tuple(
        MetricRow(
            key=metric_key,
            label_key=label_key,
            treatment_value=rate_at_checkpoint(_EXPERIMENT_DATA, checkpoint_number, metric_key, "treatment"),
            control_value=rate_at_checkpoint(_EXPERIMENT_DATA, checkpoint_number, metric_key, "control"),
            # Every row here stays essentially flat or narrows toward
            # parity by design (see experiment_data.py) - this experiment's
            # problem is a statistical illusion, not a guardrail breach, so
            # nothing is ever flagged.
            flagged=False,
        )
        for metric_key, label_key in _ROW_LABEL_KEYS
    )
    return MonitoringCheckpoint(day=CHECKPOINT_DAYS[checkpoint_number], rows=rows)


CHECKOUT_CHECKPOINTS: tuple[MonitoringCheckpoint, ...] = tuple(_build_checkpoint(n) for n in sorted(CHECKPOINT_DAYS))

# The correct play is to keep running to the final, planned checkpoint
# rather than act on an early, still-noisy read - see experiment_data.py
# for why the early lift is real-looking but doesn't hold.
CORRECT_FINAL_CHECKPOINT = len(CHECKOUT_CHECKPOINTS)

import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

PROMO_LOG_SCHEMA = Schema(
    columns=(
        ColumnSchema("event_id", "object"),
        ColumnSchema("redemption_id", "object"),
        ColumnSchema("region", "object"),
        ColumnSchema("week", "int64"),
    )
)

# Marketing's own promo-redemption webhook log for the week-7 East flash
# promo - a real event-level feed, not a pre-aggregated count, so joining
# it to Finance's weekly revenue table requires the same real
# dedupe-then-aggregate-then-join pipeline L08/L13 already taught, applied
# once here rather than re-taught. 3,000 real, distinct redemptions
# happened (`redemption_id` is the real identity key); the first 450 of
# them were double-logged when the checkout confirmation webhook retried
# after a slow response during the promo traffic spike - a real transport
# replay, the same mechanism class as L08's own payment-webhook double-fire,
# giving 3,450 raw rows for 3,000 real redemptions.
TRUE_UNIQUE_REDEMPTIONS = 3000
DUPLICATED_REDEMPTIONS = 450
PROMO_REGION = "east"
PROMO_WEEK = 7


def _build_rows() -> list[tuple[str, str, str, int]]:
    rows = []
    for index in range(TRUE_UNIQUE_REDEMPTIONS):
        redemption_id = f"redeem_{index:04d}"
        rows.append((f"evt_{index:04d}_a", redemption_id, PROMO_REGION, PROMO_WEEK))
        if index < DUPLICATED_REDEMPTIONS:
            rows.append((f"evt_{index:04d}_b", redemption_id, PROMO_REGION, PROMO_WEEK))
    return rows


def generate_promo_log() -> Dataset:
    frame = pd.DataFrame(_build_rows(), columns=["event_id", "redemption_id", "region", "week"])
    step = PipelineStep("collected", python_code="promo_log = pd.read_csv('novamart_promo_redemption_log.csv')")
    return Dataset(name="novamart_promo_redemption_log", frame=frame, schema=PROMO_LOG_SCHEMA, history=(step,))


def raw_event_count(dataset: Dataset) -> int:
    return int(len(dataset.frame))


def unique_redemption_count(dataset: Dataset) -> int:
    return int(dataset.frame["redemption_id"].nunique())


def weekly_redemption_counts(dataset: Dataset, region: str, weeks: tuple[int, ...], dedupe: bool) -> tuple[int, ...]:
    """The real pipeline this lead exercises: (1) optionally dedupe by the
    real identity key `redemption_id` - skipping this is exactly the wrong
    choice the lead's own micro-decision offers; (2) aggregate to one row
    per week; (3) left-join that onto every week Finance's own revenue
    table has for this region, filling weeks with no log rows at all as 0
    - never fan-out, since the log is already unique-per-week after step
    2; (4) the caller (leads.py) validates the resulting length still
    equals `len(weeks)`, the real cardinality check this step is for."""
    region_events = dataset.frame[dataset.frame["region"] == region]
    if dedupe:
        region_events = region_events.drop_duplicates(subset="redemption_id")
    weekly_counts = region_events.groupby("week").size()
    aligned = weekly_counts.reindex(list(weeks), fill_value=0)
    return tuple(int(value) for value in aligned)

import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

INCIDENT_SCHEMA = Schema(
    columns=(
        ColumnSchema("region", "object"),
        ColumnSchema("week", "int64"),
        ColumnSchema("revenue", "float64"),
        ColumnSchema("support_tickets", "int64"),
        ColumnSchema("promo_redemptions", "int64"),
    )
)

# One real incident, one shared table every investigation lead reads from -
# unlike every prior lesson's separate guided/independent/twist datasets,
# Lesson 30's whole point is drawing the right conclusion from ONE body of
# evidence, so there is deliberately no separate twist_data.py here.
#
# Weeks 1-6: ordinary weeks, small realistic noise, no real signal anywhere.
# Week 7: a one-week 20%-off flash promo ran in the East region only,
# driving a real, large but temporary revenue spike there (and nowhere
# else) - real promo-code redemptions back it up.
# Week 8 ("this week"): the promo ended and East reverted to its own
# ordinary baseline. Company-wide revenue looks like an 18% "drop" versus
# week 7, but every region's week-8 number is unremarkable on its own.
REGION_WEEKLY_REVENUE = {
    "east": (74800.0, 75200.0, 74900.0, 75100.0, 75300.0, 74700.0, 150000.0, 74000.0),
    "north": (89800.0, 90200.0, 89900.0, 90100.0, 90300.0, 89700.0, 90000.0, 90200.0),
    "south": (94900.0, 95100.0, 94800.0, 95200.0, 95000.0, 94900.0, 95000.0, 95100.0),
    "west": (84900.0, 85100.0, 84800.0, 85200.0, 85000.0, 84900.0, 85000.0, 84800.0),
}

REGION_WEEKLY_TICKETS = {
    "east": (10, 11, 9, 10, 9, 11, 11, 10),
    "north": (8, 9, 8, 9, 8, 9, 8, 9),
    "south": (10, 9, 11, 10, 9, 10, 10, 9),
    "west": (7, 8, 7, 8, 7, 8, 8, 7),
}

REGION_WEEKLY_PROMO_REDEMPTIONS = {
    "east": (0, 0, 0, 0, 0, 0, 3000, 0),
    "north": (0, 0, 0, 0, 0, 0, 0, 0),
    "south": (0, 0, 0, 0, 0, 0, 0, 0),
    "west": (0, 0, 0, 0, 0, 0, 0, 0),
}

WEEKS = tuple(range(1, 9))
PROMO_WEEK = 7
INCIDENT_WEEK = 8


def _build_rows() -> list[tuple[str, int, float, int, int]]:
    rows = []
    for region in REGION_WEEKLY_REVENUE:
        for index, week in enumerate(WEEKS):
            rows.append(
                (
                    region,
                    week,
                    REGION_WEEKLY_REVENUE[region][index],
                    REGION_WEEKLY_TICKETS[region][index],
                    REGION_WEEKLY_PROMO_REDEMPTIONS[region][index],
                )
            )
    return rows


def generate_incident_data() -> Dataset:
    frame = pd.DataFrame(
        _build_rows(), columns=["region", "week", "revenue", "support_tickets", "promo_redemptions"]
    )
    step = PipelineStep("collected", python_code="incident = pd.read_csv('novamart_weekly_regional_revenue.csv')")
    return Dataset(name="novamart_weekly_regional_revenue", frame=frame, schema=INCIDENT_SCHEMA, history=(step,))


def region_series(dataset: Dataset, region: str, column: str) -> tuple[float, ...]:
    subset = dataset.frame[dataset.frame["region"] == region].sort_values("week")
    return tuple(subset[column].astype(float))


def value_at(dataset: Dataset, region: str, week: int, column: str) -> float:
    row = dataset.frame[(dataset.frame["region"] == region) & (dataset.frame["week"] == week)]
    return float(row[column].iloc[0])


def weekly_company_revenue(dataset: Dataset) -> tuple[float, ...]:
    totals = dataset.frame.groupby("week")["revenue"].sum().sort_index()
    return tuple(float(value) for value in totals)


def percent_change(before: float, after: float) -> float:
    return (after - before) / before


def correlation_ticket_change_vs_revenue_change(dataset: Dataset) -> float:
    # Per region, week 7 -> week 8: if the checkout redesign had broken
    # something, regions with a bigger revenue drop should also show more
    # (not fewer) checkout-related support tickets.
    regions = list(REGION_WEEKLY_REVENUE)
    ticket_changes = [
        float(value_at(dataset, region, INCIDENT_WEEK, "support_tickets") - value_at(dataset, region, PROMO_WEEK, "support_tickets"))
        for region in regions
    ]
    revenue_changes = [
        percent_change(value_at(dataset, region, PROMO_WEEK, "revenue"), value_at(dataset, region, INCIDENT_WEEK, "revenue"))
        for region in regions
    ]
    return float(pd.Series(ticket_changes).corr(pd.Series(revenue_changes)))


def correlation_promo_redemptions_vs_revenue(dataset: Dataset, region: str) -> float:
    redemptions = pd.Series(region_series(dataset, region, "promo_redemptions"))
    revenue = pd.Series(region_series(dataset, region, "revenue"))
    return float(redemptions.corr(revenue))


def region_week_over_week_change(dataset: Dataset, region: str) -> tuple[float, float]:
    before = value_at(dataset, region, PROMO_WEEK, "revenue")
    after = value_at(dataset, region, INCIDENT_WEEK, "revenue")
    return before, after


def region_baseline_average(dataset: Dataset, region: str, through_week: int = 6) -> float:
    subset = dataset.frame[(dataset.frame["region"] == region) & (dataset.frame["week"] <= through_week)]
    return float(subset["revenue"].mean())


def metric_series(dataset: Dataset, metric_key: str) -> tuple[float, ...]:
    if metric_key == "east_revenue":
        return region_series(dataset, "east", "revenue")
    if metric_key == "company_total_revenue":
        return weekly_company_revenue(dataset)
    if metric_key == "east_support_tickets":
        return region_series(dataset, "east", "support_tickets")
    raise ValueError(f"unknown metric_key: {metric_key}")


def simulate_monitoring(
    dataset: Dataset, metric, threshold, target_incident_day: int
) -> tuple[int, bool]:
    """Flags any week whose value strays from the first 6 weeks' own
    baseline average by at least `threshold.multiplier` - real computed
    anomaly detection over `metric.metric_key`'s series, not a scripted
    result. A false alarm is any flagged week other than the real
    incident week; `incident_caught` is whether that week itself got
    flagged."""
    series = metric_series(dataset, metric.metric_key)
    baseline = sum(series[:6]) / 6
    flagged_weeks = [index + 1 for index, value in enumerate(series) if abs(percent_change(baseline, value)) >= threshold.multiplier]
    false_alarm_count = sum(1 for week in flagged_weeks if week != target_incident_day)
    incident_caught = target_incident_day in flagged_weeks
    return false_alarm_count, incident_caught

import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Hidden population: 960 NovaMart deliveries this quarter --------------
#
# Region -> (population, real problem count, partner). Rural is the one
# small, high-failure segment doing double duty: it's why the best
# available frame still has a gap, and why plain random sampling under-
# represents it. Hand-picked, not derived from a formula, and independently
# re-verifiable by summing the tables below.

REGION_POPULATION: dict[str, tuple[int, int, str]] = {
    "metro": (400, 40, "carrierco"),
    "suburban": (300, 36, "carrierco"),
    "coastal": (180, 27, "carrierco"),
    "rural": (80, 28, "quickship"),
}
TOTAL_POPULATION = sum(population for population, _, _ in REGION_POPULATION.values())  # 960
TOTAL_PROBLEMS = sum(problem_count for _, problem_count, _ in REGION_POPULATION.values())  # 131
TRUE_PROBLEM_RATE = TOTAL_PROBLEMS / TOTAL_POPULATION  # 13.65% - never shown to the student

# Of Rural's 80 deliveries (handled by the smaller partner, QuickShip),
# only these have synced from QuickShip's own separate manual log into the
# fulfillment tracking export so far - the other 65 aren't in that frame
# at any sample size, at any strategy.
RURAL_SYNCED_PROBLEM = 5
RURAL_SYNCED_OK = 10

# region -> (tickets filed by real-problem deliveries, tickets filed by
# otherwise-fine deliveries) - free, already-compiled, self-selects toward
# real problems.
SUPPORT_TICKETS: dict[str, tuple[int, int]] = {
    "metro": (36, 20),
    "suburban": (32, 16),
    "coastal": (25, 12),
    "rural": (26, 5),
}

# region -> (raters among problem deliveries, raters among ok deliveries) -
# free, already-compiled, self-selects the other direction (toward Metro
# and toward people who bother rating a normal delivery).
LOYALTY_RATERS: dict[str, tuple[int, int]] = {
    "metro": (6, 194),
    "suburban": (4, 46),
    "coastal": (2, 18),
    "rural": (1, 4),
}

# region -> (express deliveries among problem rows, express deliveries
# among ok rows) - mastery-only, never touches the core 4 rounds. ~12% of
# every region, with a modestly higher problem rate than that region's own
# overall rate (e.g. Metro: 8/48 = 16.7% vs Metro's overall 10%).
EXPRESS_DELIVERIES: dict[str, tuple[int, int]] = {
    "metro": (8, 40),
    "suburban": (6, 30),
    "coastal": (5, 17),
    "rural": (4, 6),
}

POPULATION_SCHEMA = Schema(
    columns=(
        ColumnSchema("delivery_id", "int64"),
        ColumnSchema("region", "object"),
        ColumnSchema("partner", "object"),
        ColumnSchema("had_problem", "bool"),
        ColumnSchema("in_tracking_export", "bool"),
        ColumnSchema("filed_support_ticket", "bool"),
        ColumnSchema("rated_in_loyalty_app", "bool"),
        ColumnSchema("is_express", "bool"),
    )
)

FRAME_COLUMNS: dict[str, str] = {
    "tracking_export": "in_tracking_export",
    "support_tickets": "filed_support_ticket",
    "loyalty_app": "rated_in_loyalty_app",
}
# Only the tracking export costs real per-row audit budget - a support
# ticket or an app rating already states its own outcome, so reading one
# is free. This is what makes "convenience" mean two different things
# depending on frame: use everything (free), or take the first `budget`
# rows as exported (each one still costs an audit).
COSTED_FRAMES = {"tracking_export"}


def _interleaved_outcomes(problem_count: int, ok_count: int) -> list[bool]:
    """Evenly distributes `problem_count` True values across `problem_count
    + ok_count` slots (a standard Bresenham-style spread) instead of
    grouping every problem row before every ok row. Every *count* this
    module hand-verifies (895 tracking_export rows, 108 problems, 172
    tickets, ...) is order-independent and unaffected by this - but the
    tracking_export "convenience" strategy deliberately takes the frame's
    own *first* `budget` rows (see draw_sample), and a region's own rows
    being outcome-grouped would make that slice wildly unrepresentative of
    the region for a reason with no real-world analogue (a problem-first
    export ordering isn't a real list-order bias mechanism worth
    teaching), rather than the intended, real one (landing entirely in the
    single region that happens to sort first)."""
    total = problem_count + ok_count
    outcomes: list[bool] = []
    accumulated = 0
    for _ in range(total):
        accumulated += problem_count
        if accumulated >= total:
            accumulated -= total
            outcomes.append(True)
        else:
            outcomes.append(False)
    return outcomes


def _region_rows(region: str, partner: str, problem_count: int, ok_count: int) -> list[dict]:
    ticket_problem, ticket_ok = SUPPORT_TICKETS[region]
    rating_problem, rating_ok = LOYALTY_RATERS[region]
    express_problem, express_ok = EXPRESS_DELIVERIES[region]
    rural_synced = region == "rural"

    rows: list[dict] = []
    problem_offset = 0
    ok_offset = 0
    for had_problem in _interleaved_outcomes(problem_count, ok_count):
        if had_problem:
            offset, problem_offset = problem_offset, problem_offset + 1
            rows.append(
                {
                    "region": region,
                    "partner": partner,
                    "had_problem": True,
                    "in_tracking_export": (not rural_synced) or offset < RURAL_SYNCED_PROBLEM,
                    "filed_support_ticket": offset < ticket_problem,
                    "rated_in_loyalty_app": offset < rating_problem,
                    "is_express": offset < express_problem,
                }
            )
        else:
            offset, ok_offset = ok_offset, ok_offset + 1
            rows.append(
                {
                    "region": region,
                    "partner": partner,
                    "had_problem": False,
                    "in_tracking_export": (not rural_synced) or offset < RURAL_SYNCED_OK,
                    "filed_support_ticket": offset < ticket_ok,
                    "rated_in_loyalty_app": offset < rating_ok,
                    "is_express": offset < express_ok,
                }
            )
    return rows


def generate_population() -> Dataset:
    rows: list[dict] = []
    for region, (population, problem_count, partner) in REGION_POPULATION.items():
        rows.extend(_region_rows(region, partner, problem_count, population - problem_count))

    frame = pd.DataFrame(rows)
    frame.insert(0, "delivery_id", range(1, len(frame) + 1))
    step = PipelineStep(
        "deliveries",
        python_code="deliveries = pd.read_csv('novamart_deliveries_q.csv')  # one row per delivery",
    )
    return Dataset(name="deliveries", frame=frame, schema=POPULATION_SCHEMA, history=(step,))


def frame_for(population: pd.DataFrame, frame_key: str) -> pd.DataFrame:
    """The real, independently re-derivable filter behind one candidate
    sampling frame - not a separate dataset, the same hidden population
    table seen through one boolean column."""
    column = FRAME_COLUMNS[frame_key]
    return population[population[column]].reset_index(drop=True)


def region_availability(frame: pd.DataFrame) -> dict[str, int]:
    """How many real rows of each region are actually in this frame - the
    real per-stratum ceiling a stratified allocation can't allocate past,
    regardless of total budget (see SamplingGroup.available)."""
    return {region: int(count) for region, count in frame["region"].value_counts().items()}


def draw_sample(
    frame: pd.DataFrame,
    strategy: str,
    budget: int,
    costed: bool,
    seed: int = 0,
    allocation: dict[str, int] | None = None,
) -> pd.DataFrame:
    """The one real mechanism behind every draw in this lesson - real,
    seeded pandas sampling, not a scripted composition. `costed` (True only
    for the tracking export) is what makes "convenience" mean two
    different things: use the whole frame for free, or take the first
    `budget` rows as exported (order preserved, no shuffle) because every
    row still costs a real audit."""
    if strategy == "convenience":
        if not costed:
            return frame.reset_index(drop=True)
        return frame.head(budget).reset_index(drop=True)
    if strategy == "simple_random":
        n = min(budget, len(frame))
        return frame.sample(n=n, random_state=seed).reset_index(drop=True)
    if strategy == "stratified":
        if allocation is None:
            raise ValueError("stratified sampling requires an allocation")
        parts = [
            frame[frame["region"] == region].sample(n=min(count, (frame["region"] == region).sum()), random_state=seed)
            for region, count in allocation.items()
            if count > 0
        ]
        if not parts:
            return frame.iloc[0:0].reset_index(drop=True)
        return pd.concat(parts, ignore_index=True)
    raise ValueError(f"unknown strategy: {strategy}")


def rural_share(sample: pd.DataFrame) -> float:
    if len(sample) == 0:
        return 0.0
    return float((sample["region"] == "rural").mean())


def _weighted_rate(sample_subset: pd.DataFrame, frame_subset: pd.DataFrame) -> float:
    """The real stratified-sampling estimator: each region's own sample
    rate weighted by that region's real share of the frame it was drawn
    from - renormalized over whichever regions actually ended up in the
    sample, not the raw sample count. A plain `sample.mean()` (what this
    lesson shipped with initially) is only correct when every row had an
    equal chance of being drawn (convenience/simple_random); a student who
    deliberately over-samples one region under stratified sampling - the
    whole reason to stratify - would otherwise see that region's own
    *sample* share distort the headline number, not its real frame share."""
    if len(sample_subset) == 0:
        return 0.0
    frame_counts = frame_subset["region"].value_counts()
    total = frame_counts.sum()
    if total == 0:
        return float(sample_subset["had_problem"].mean())
    weighted_sum = 0.0
    weight_covered = 0.0
    for region, region_sample in sample_subset.groupby("region"):
        weight = frame_counts.get(region, 0) / total
        weighted_sum += weight * region_sample["had_problem"].mean()
        weight_covered += weight
    if weight_covered == 0:
        return 0.0
    return weighted_sum / weight_covered


def estimated_problem_rate(sample: pd.DataFrame, frame: pd.DataFrame | None = None) -> float:
    """The reportable headline estimate - deliberately scoped to
    CarrierCo-served regions only (metro/suburban/coastal), never blending
    Rural/QuickShip's own thin, unreliable coverage into one combined
    number. Rural's own presence is a separate, explicitly surfaced fact
    (see rural_share) - this is what keeps "the reported estimate" and "a
    rate for CarrierCo regions, Rural flagged open" the same real
    quantity, not two different things that happen to share a sentence.

    Pass `frame` (the same frame the sample was drawn from) for a
    stratified draw specifically, so a deliberately uneven allocation
    across CarrierCo's own three regions gets properly reweighted by their
    real frame shares rather than by however much of each the student
    happened to draw. Convenience/simple-random draws don't need it - every
    CarrierCo row already had an equal chance of being drawn, so a plain
    mean is already the correct estimator."""
    carrierco_sample = sample[sample["region"] != "rural"]
    if len(carrierco_sample) == 0:
        return 0.0
    if frame is None:
        return float(carrierco_sample["had_problem"].mean())
    carrierco_frame = frame[frame["region"] != "rural"]
    return _weighted_rate(carrierco_sample, carrierco_frame)


def express_rate(sample: pd.DataFrame) -> float:
    express = sample[sample["is_express"]]
    if len(express) == 0:
        return 0.0
    return float(express["had_problem"].mean())


def round1_mechanism(frame_key: str, strategy_key: str) -> str:
    """The one real bias mechanism behind a given Frame+Strategy pick -
    three real states, not two: tracking_export+convenience is a
    genuinely different mechanism (list order) than
    tracking_export+{simple_random,stratified} (frame coverage), which is
    itself different from either self-selected frame. Used to score
    Prediction 1/Reveal 1/Reveal 4's interpret correctness - Prediction 2
    is a separate, constant-answer question (see scoring.py), not derived
    from this."""
    if frame_key in ("support_tickets", "loyalty_app"):
        return "self_selection"
    if strategy_key == "convenience":
        return "draw_order_bias"
    return "frame_coverage_gap"


_FRAME_EXPRESSIONS: dict[str, str] = {
    "tracking_export": "deliveries[deliveries['in_tracking_export']]",
    "support_tickets": "deliveries[deliveries['filed_support_ticket']]",
    "loyalty_app": "deliveries[deliveries['rated_in_loyalty_app']]",
}


def sample_python_code(frame_key: str, strategy_key: str, budget: int, seed: int, allocation: dict[str, int] | None) -> str:
    """A self-contained, real pandas equivalent of exactly how one draw
    was produced *and estimated* - shown in the Python Mirror once
    recorded onto a ComparisonValue/PipelineStep. The stratified branch
    shows the real weighted estimator (see _weighted_rate) rather than a
    plain .mean(), since that plain mean is exactly the wrong number for a
    deliberately uneven allocation."""
    frame_expr = _FRAME_EXPRESSIONS[frame_key]
    if strategy_key == "convenience":
        if frame_key == "tracking_export":
            return f"frame = {frame_expr}\nsample = frame.head({budget})  # audited in export order, no shuffle"
        return f"sample = {frame_expr}  # already self-reported, no audit needed"
    if strategy_key == "simple_random":
        return (
            f"frame = {frame_expr}\n"
            f"sample = frame.sample(n={budget}, random_state={seed})\n"
            "carrierco_sample = sample[sample['region'] != 'rural']\n"
            "rate = carrierco_sample['had_problem'].mean()  # every row had an equal chance, plain mean is correct"
        )
    lines = [f"frame = {frame_expr}", "parts = []"]
    for region, count in (allocation or {}).items():
        if count > 0:
            lines.append(f"parts.append(frame[frame['region'] == '{region}'].sample(n={count}, random_state={seed}))")
    lines.append("sample = pd.concat(parts, ignore_index=True)")
    lines.append("carrierco_sample, carrierco_frame = sample[sample['region'] != 'rural'], frame[frame['region'] != 'rural']")
    lines.append("frame_share = carrierco_frame['region'].value_counts(normalize=True)")
    lines.append("sample_rates = carrierco_sample.groupby('region')['had_problem'].mean()")
    lines.append("rate = (sample_rates * frame_share[sample_rates.index]).sum() / frame_share[sample_rates.index].sum()")
    return "\n".join(lines)


def sample_dataset(sample: pd.DataFrame, name: str, python_code: str) -> Dataset:
    return Dataset(name=name, frame=sample, schema=POPULATION_SCHEMA, history=(PipelineStep(name, python_code),))

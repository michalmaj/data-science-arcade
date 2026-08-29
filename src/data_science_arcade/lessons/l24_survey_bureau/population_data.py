import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.survey import ChannelOption, WordingOption

CUSTOMER_POPULATION_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "int64"),
        ColumnSchema("segment", "object"),
        ColumnSchema("true_satisfaction", "float64", description="Hidden ground truth - never shown to the player directly"),
        ColumnSchema("still_active", "bool", description="False if this customer already quit the app over the price change"),
        ColumnSchema("is_power_user", "bool", description="Eligible for the incentivized advisory panel"),
    )
)

# Three real customer segments reacting to NovaMart's price change -
# hand-crafted, not random. Vocal critics are far more likely to respond
# to any survey than the quiet majority, and over half of them have
# already quit the app entirely - so a channel that can only reach
# still-active users can never hear from them at all. Vocal fans are, by
# definition here, part of the power-user advisory panel; a slice of the
# quiet majority is too.
TRUE_SATISFACTION_BY_SEGMENT = {"vocal_critic": 0.20, "vocal_fan": 0.90, "quiet_majority": 0.62}
RESPONSE_RATE_BY_SEGMENT = {"vocal_critic": 0.80, "vocal_fan": 0.70, "quiet_majority": 0.20}


def _rows() -> list[tuple[int, str, float, bool, bool]]:
    rows: list[tuple[int, str, float, bool, bool]] = []
    customer_id = 1

    def add(count: int, segment: str, still_active: bool, is_power_user: bool) -> None:
        nonlocal customer_id
        for _ in range(count):
            rows.append((customer_id, segment, TRUE_SATISFACTION_BY_SEGMENT[segment], still_active, is_power_user))
            customer_id += 1

    add(18, "vocal_critic", still_active=True, is_power_user=False)
    add(27, "vocal_critic", still_active=False, is_power_user=False)  # already quit over the change
    add(30, "vocal_fan", still_active=True, is_power_user=True)
    add(30, "quiet_majority", still_active=True, is_power_user=True)
    add(195, "quiet_majority", still_active=True, is_power_user=False)
    return rows


def generate_population_data() -> Dataset:
    frame = pd.DataFrame(_rows(), columns=["customer_id", "segment", "true_satisfaction", "still_active", "is_power_user"])
    step = PipelineStep("collected", python_code="customers = pd.read_csv('novamart_price_change_population.csv')")
    return Dataset(name="novamart_price_change_population", frame=frame, schema=CUSTOMER_POPULATION_SCHEMA, history=(step,))


def true_population_mean(dataset: Dataset) -> float:
    return float(dataset.frame["true_satisfaction"].mean())


def simulate_survey(dataset: Dataset, channel: ChannelOption, wording: WordingOption) -> tuple[int, float]:
    """Runs a real (if small) simulation: filters the population down to
    whoever the channel can even reach, then applies each segment's own
    response rate to however many of them are left - a segment a channel
    can't reach at all contributes zero respondents no matter how likely
    its members would otherwise be to answer."""
    frame = dataset.frame
    reached = frame.query(channel.reach_query) if channel.reach_query else frame

    total_respondents = 0
    weighted_sum = 0.0
    for segment, rate in RESPONSE_RATE_BY_SEGMENT.items():
        segment_reached = reached[reached["segment"] == segment]
        respondent_count = round(len(segment_reached) * rate)
        if respondent_count == 0:
            continue
        recorded_value = min(1.0, float(segment_reached["true_satisfaction"].mean()) + wording.bias)
        total_respondents += respondent_count
        weighted_sum += respondent_count * recorded_value

    mean_satisfaction = weighted_sum / total_respondents if total_respondents else 0.0
    return total_respondents, mean_satisfaction

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


def survey_mean_mirror_code(channel: ChannelOption, wording: WordingOption, var_name: str) -> str:
    """Real per-segment filter -> response-rate -> wording-biased-mean
    logic, matching simulate_survey's own for-loop shape exactly (not a
    force-vectorized reimplementation that could silently diverge on the
    zero-respondent-segment edge case). FINAL {var_name} is always
    mean_satisfaction - the same quantity the live result preview and any
    ComparisonValue built from this call actually display.
    RESPONSE_RATE_BY_SEGMENT is embedded as a literal dict (a fixed
    business constant, never a customers.csv column)."""
    reach_line = (
        f'{var_name}_reached = customers.query("{channel.reach_query}")'
        if channel.reach_query is not None
        else f"{var_name}_reached = customers"
    )
    return "\n".join(
        (
            reach_line,
            f"{var_name}_response_rate_by_segment = {RESPONSE_RATE_BY_SEGMENT!r}",
            f"{var_name}_respondent_count = 0",
            f"{var_name}_weighted_sum = 0.0",
            f"for segment, rate in {var_name}_response_rate_by_segment.items():",
            f'    {var_name}_segment_reached = {var_name}_reached[{var_name}_reached["segment"] == segment]',
            f"    {var_name}_segment_respondents = round(len({var_name}_segment_reached) * rate)",
            f"    if {var_name}_segment_respondents == 0:",
            f"        continue",
            f'    {var_name}_segment_value = min(1.0, float({var_name}_segment_reached["true_satisfaction"].mean()) + {wording.bias})',
            f"    {var_name}_respondent_count += {var_name}_segment_respondents",
            f"    {var_name}_weighted_sum += {var_name}_segment_respondents * {var_name}_segment_value",
            f"{var_name} = {var_name}_weighted_sum / {var_name}_respondent_count if {var_name}_respondent_count else 0.0",
        )
    )


def survey_reach_count_mirror_code(segment: str, condition_query: str, var_name: str) -> str:
    """A real count of one segment's own rows matching condition_query -
    e.g. "still_active == False" for in_app_popup's own 27 unreachable
    already-churned critics, or "is_power_user == True" for the 0
    critics the power-user panel can reach. A plain count, never a mean -
    kept as its own function rather than folded into
    survey_mean_mirror_code, matching every other lesson's own
    multiple-small-mirror-functions style."""
    return "\n".join(
        (
            f'{var_name}_segment = customers[customers["segment"] == "{segment}"]',
            f'{var_name} = int(len({var_name}_segment.query("{condition_query}")))',
        )
    )


def response_rate_mirror_code(segment: str, var_name: str) -> str:
    """The real, fixed response-rate business constant for one segment -
    what Reveal C's own response-rate ComparisonValues actually display."""
    return "\n".join(
        (
            f"{var_name}_response_rate_by_segment = {RESPONSE_RATE_BY_SEGMENT!r}",
            f'{var_name} = float({var_name}_response_rate_by_segment["{segment}"])',
        )
    )

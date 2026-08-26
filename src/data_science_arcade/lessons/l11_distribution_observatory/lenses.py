from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.lessons.framework.distribution import DistributionLens, LensOption

# Hand-crafted decoys, no trap outside the twist (matching every prior
# lesson's discipline): each lens has one genuinely correct pick for the
# specific question it asks, plus targeted wrong answers grounded in real,
# common misreadings of a summary statistic. Correct-option position
# varies across all three lenses (never index 0), same discipline as
# every per-item mechanic since Lesson 04.
CORRECT_OPTION_BY_LENS: dict[str, str] = {
    "single_number_pick": "median",
    "spread_pick": "std_dev_above_mean",
    "shape_pick": "inspect_the_histogram",
}


def build_distribution_lenses(dataset: Dataset) -> tuple[DistributionLens, ...]:
    values = dataset.frame["order_value"]
    mean = float(values.mean())
    median = float(values.median())
    highest_order = float(values.max())
    spread_marker = float(values.mean() + values.std())

    return (
        DistributionLens(
            key="single_number_pick",
            prompt_key="lesson.l11.lens.single_number_pick.prompt",
            hint_key="lesson.l11.lens.single_number_pick.hint",
            options=(
                LensOption("mean", "lesson.l11.option.single_number_pick.mean", mean),
                LensOption("median", "lesson.l11.option.single_number_pick.median", median),
                LensOption("highest_order", "lesson.l11.option.single_number_pick.highest_order", highest_order),
            ),
        ),
        DistributionLens(
            key="spread_pick",
            prompt_key="lesson.l11.lens.spread_pick.prompt",
            hint_key="lesson.l11.lens.spread_pick.hint",
            options=(
                LensOption("highest_order_again", "lesson.l11.option.spread_pick.highest_order_again", highest_order),
                LensOption("assume_consistent", "lesson.l11.option.spread_pick.assume_consistent", None),
                LensOption("std_dev_above_mean", "lesson.l11.option.spread_pick.std_dev_above_mean", spread_marker),
            ),
        ),
        DistributionLens(
            key="shape_pick",
            prompt_key="lesson.l11.lens.shape_pick.prompt",
            hint_key="lesson.l11.lens.shape_pick.hint",
            options=(
                LensOption("trust_the_mean", "lesson.l11.option.shape_pick.trust_the_mean", mean),
                LensOption("inspect_the_histogram", "lesson.l11.option.shape_pick.inspect_the_histogram", None),
                LensOption("assume_more_data_helps", "lesson.l11.option.shape_pick.assume_more_data_helps", None),
            ),
        ),
    )

from dataclasses import dataclass

from data_science_arcade.lessons.framework.power import minimum_detectable_effect
from data_science_arcade.lessons.framework.sampling import SamplingGroup


@dataclass(frozen=True)
class ExperimentPlan:
    key: str
    label_key: str
    weekly_traffic_per_group: int
    baseline_rate: float
    minimum_useful_effect: float


# Three experiments competing for the same quarter, each with a real
# traffic level and its own "minimum effect actually worth shipping" -
# high-traffic surfaces (checkout) reach a given detectable effect in
# fewer weeks per point of traffic, but a strict minimum-useful-effect
# threshold can still make them the most expensive to satisfy overall.
# Fully satisfying all three at once needs more weeks than the budget
# allows (verified via a manual script) - a real, not scripted, trade-off.
EXPERIMENTS: tuple[ExperimentPlan, ...] = (
    ExperimentPlan("checkout_redesign", "lesson.l19.experiment.checkout_redesign", 2000, 0.24, 0.015),
    ExperimentPlan("pricing_page_test", "lesson.l19.experiment.pricing_page_test", 600, 0.10, 0.020),
    ExperimentPlan("loyalty_settings_test", "lesson.l19.experiment.loyalty_settings_test", 150, 0.05, 0.030),
)
TOTAL_WEEKS = 12
STEP = 1

SAMPLING_GROUPS: tuple[SamplingGroup, ...] = tuple(SamplingGroup(plan.key, plan.label_key) for plan in EXPERIMENTS)

_PLANS_BY_KEY = {plan.key: plan for plan in EXPERIMENTS}


def weeks_needed_for_threshold(experiment_key: str) -> int:
    """The fewest whole weeks that bring this experiment's own detectable
    effect at or below its stated minimum useful effect."""
    plan = _PLANS_BY_KEY[experiment_key]
    weeks = 1
    while detectable_effect_for(experiment_key, weeks) > plan.minimum_useful_effect:
        weeks += 1
    return weeks


def detectable_effect_for(experiment_key: str, weeks: int) -> float:
    plan = _PLANS_BY_KEY[experiment_key]
    return minimum_detectable_effect(plan.baseline_rate, weeks * plan.weekly_traffic_per_group)

import math

# Standard normal critical values for the field's default significance and
# power (95% significance, two-sided; 80% power) - the same defaults every
# real experimentation platform uses unless told otherwise. Not exposed as
# parameters: a caller passing a non-default alpha/power without also
# supplying the matching z-value would silently get a wrong answer, so
# this only ever computes the one, standard version.
Z_ALPHA_2 = 1.959964
Z_BETA = 0.841621


def minimum_detectable_effect(baseline_rate: float, sample_size_per_group: int) -> float:
    """The effect size that corresponds *approximately* to the field's
    default power (80%) at the field's default test level (95%,
    two-sided) for this many observations per group and this baseline -
    the standard normal-approximation sample-size formula for a
    two-proportion test, solved for effect size instead of sample size.
    Smaller sample -> larger (worse) MDE.

    This is a design-stage planning quantity, not a deterministic cutoff
    on any later observed result: an effect smaller than the MDE can
    still be detected in a given experiment, and an effect larger than
    the MDE can still be missed. MDE is the effect SIZE the plan is
    sized to detect at that target power - power itself is the
    probability; MDE is never a probability, it's an effect magnitude
    that corresponds to one. Never read a real observed effect against
    this number after the fact (see L19's own Handbook entry) - it only
    ever describes a plan, before any result exists."""
    if sample_size_per_group <= 0:
        return math.inf
    variance_term = 2 * baseline_rate * (1 - baseline_rate)
    return math.sqrt(variance_term * (Z_ALPHA_2 + Z_BETA) ** 2 / sample_size_per_group)


def proportion_difference_ci(
    control_conversions: int,
    control_n: int,
    treatment_conversions: int,
    treatment_n: int,
    z: float = Z_ALPHA_2,
) -> tuple[float, float]:
    """Normal-approximation (unpooled/Wald) interval for treatment -
    control - the default `z` (Z_ALPHA_2) corresponds to a 95% interval;
    a caller passing a different `z` gets whatever interval that
    z-value actually corresponds to, not automatically "95%" again."""
    p_control = control_conversions / control_n
    p_treatment = treatment_conversions / treatment_n
    diff = p_treatment - p_control
    standard_error = math.sqrt(
        p_control * (1 - p_control) / control_n + p_treatment * (1 - p_treatment) / treatment_n
    )
    return diff - z * standard_error, diff + z * standard_error


def two_proportion_z_statistic(
    control_conversions: int,
    control_n: int,
    treatment_conversions: int,
    treatment_n: int,
) -> float:
    """The z-statistic for a real two-sided two-proportion test against
    the null of no difference (treatment == control) - a pooled standard
    error under that null, the standard hypothesis-testing convention
    (distinct from proportion_difference_ci's own unpooled/Wald SE, which
    estimates a real interval around the observed difference rather than
    testing a null - the two functions deliberately use different SEs for
    their different real jobs, both standard, neither an ad hoc choice)."""
    p_control = control_conversions / control_n
    p_treatment = treatment_conversions / treatment_n
    p_pooled = (control_conversions + treatment_conversions) / (control_n + treatment_n)
    pooled_standard_error = math.sqrt(p_pooled * (1 - p_pooled) * (1 / control_n + 1 / treatment_n))
    if pooled_standard_error == 0:
        return 0.0
    return (p_treatment - p_control) / pooled_standard_error

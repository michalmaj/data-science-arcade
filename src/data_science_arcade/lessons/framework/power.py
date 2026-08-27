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
    """The smallest true difference in rate a two-proportion test could
    reliably detect (95% significance, 80% power) given this many
    observations per group - the standard normal-approximation sample-size
    formula for a two-proportion test, solved for effect size instead of
    sample size. Smaller sample -> larger (worse) detectable effect."""
    if sample_size_per_group <= 0:
        return math.inf
    variance_term = 2 * baseline_rate * (1 - baseline_rate)
    return math.sqrt(variance_term * (Z_ALPHA_2 + Z_BETA) ** 2 / sample_size_per_group)

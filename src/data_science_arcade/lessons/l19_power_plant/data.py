import numpy as np
import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.power import Z_ALPHA_2, minimum_detectable_effect, two_proportion_z_statistic

# --- Ground truth (hand-verified via a real pandas/numpy script this
# session, against the real framework/power.py helpers - never
# hand-typed headline numbers). NovaMart Go / Quick Pay, continued from
# L18 - L18's own outcome stays fully sealed here too; this lesson never
# touches it. -------------------------------------------------------

BASELINE_RATE = 0.24
BUSINESS_MINIMUM_EFFECT = 0.015
WEEKLY_N_PER_ARM = 2000
MIN_WEEKS = 1
MAX_WEEKS = 12
COLD_PICK_WEEK_OPTIONS = (2, 4, 7, 12)

# Real MDE table, weeks -> n/arm -> MDE, verified this session:
#   2wk  n=4,000   MDE=2.675pp
#   4wk  n=8,000   MDE=1.892pp
#   6wk  n=12,000  MDE=1.545pp - close, still above the +1.5pp target
#   7wk  n=14,000  MDE=1.430pp - first full week meeting the target
#   8wk  n=16,000  MDE=1.338pp
#   12wk n=24,000  MDE=1.092pp - adequate, costs more than needed


def n_per_arm_for_weeks(weeks: int) -> int:
    return weeks * WEEKLY_N_PER_ARM


def mde_for_weeks(weeks: int) -> float:
    return minimum_detectable_effect(BASELINE_RATE, n_per_arm_for_weeks(weeks))


def meets_sensitivity_target(weeks: int) -> bool:
    return mde_for_weeks(weeks) <= BUSINESS_MINIMUM_EFFECT


def plan_mirror_code(weeks: int) -> str:
    """The only code in the whole lesson that ever assigns weeks/n_per_arm/
    mde - reflects whatever the student's own final weeks pick actually
    was, never a canonical substitute. Every other reveal's own mirror
    code below uses deliberately different variable names."""
    return (
        f"weeks = {weeks}\n"
        f"n_per_arm = weeks * {WEEKLY_N_PER_ARM}\n"
        f"mde = minimum_detectable_effect(baseline_rate={BASELINE_RATE}, sample_size_per_group=n_per_arm)"
    )


# --- "What 80% power means" - a real, seeded Monte Carlo illustration,
# never the definition of power itself. Two FIXED reference designs
# (never the student's own final pick): 4 weeks (n=8,000/arm) vs 7 weeks
# (n=14,000/arm), assuming a true effect of exactly the business's own
# +1.5pp (control ~ Binomial(n, 0.24), treatment ~ Binomial(n, 0.255)),
# real two-proportion z-test (two-sided, pooled SE under the null,
# two_proportion_z_statistic - see framework/power.py's own docstring for
# why this differs from proportion_difference_ci's own unpooled SE),
# empirical fraction of simulated runs where |z| > Z_ALPHA_2. Seed 7,
# 2000 sims, computed once at import - real, reproducible, verified this
# session: 4wk ~60.25% empirical detection (well below 80%), 7wk ~81.8%
# (close to 80%, consistent with 7 weeks' own MDE of 1.43pp already being
# below the assumed 1.5pp true effect). Displayed rounded to the nearest
# whole percent with a "~" prefix - n_sims=2000 has a real Monte Carlo
# standard error of roughly 1pp near 80%, so a bare "81.8%" would claim
# more precision than a 2000-run illustration actually supports. -------

REFERENCE_DESIGN_A_WEEKS = 4
REFERENCE_DESIGN_B_WEEKS = 7
SIMULATION_TRUE_EFFECT = BUSINESS_MINIMUM_EFFECT
SIMULATION_SEED = 7
SIMULATION_N_SIMS = 2000


def simulate_detection_rate(
    n_per_arm: int,
    baseline: float = BASELINE_RATE,
    true_effect: float = SIMULATION_TRUE_EFFECT,
    seed: int = SIMULATION_SEED,
    n_sims: int = SIMULATION_N_SIMS,
) -> float:
    rng = np.random.default_rng(seed)
    p_control = baseline
    p_treatment = baseline + true_effect
    detections = 0
    for _ in range(n_sims):
        control = rng.binomial(n_per_arm, p_control)
        treatment = rng.binomial(n_per_arm, p_treatment)
        z = two_proportion_z_statistic(control, n_per_arm, treatment, n_per_arm)
        if abs(z) > Z_ALPHA_2:
            detections += 1
    return detections / n_sims


REFERENCE_DESIGN_A_N = n_per_arm_for_weeks(REFERENCE_DESIGN_A_WEEKS)
REFERENCE_DESIGN_B_N = n_per_arm_for_weeks(REFERENCE_DESIGN_B_WEEKS)
REFERENCE_DESIGN_A_DETECTION_RATE = simulate_detection_rate(REFERENCE_DESIGN_A_N)
REFERENCE_DESIGN_B_DETECTION_RATE = simulate_detection_rate(REFERENCE_DESIGN_B_N)

REFERENCE_DESIGN_A_MIRROR = (
    "reference_design_a_rng = np.random.default_rng(7)\n"
    "reference_design_a_detections = 0\n"
    "for _ in range(2000):\n"
    "    control = reference_design_a_rng.binomial(8000, 0.24)\n"
    "    treatment = reference_design_a_rng.binomial(8000, 0.255)\n"
    "    z = two_proportion_z_statistic(control, 8000, treatment, 8000)\n"
    "    if abs(z) > Z_ALPHA_2:\n"
    "        reference_design_a_detections += 1\n"
    "empirical_detection_rate_a = reference_design_a_detections / 2000"
)
REFERENCE_DESIGN_B_MIRROR = (
    "reference_design_b_rng = np.random.default_rng(7)\n"
    "reference_design_b_detections = 0\n"
    "for _ in range(2000):\n"
    "    control = reference_design_b_rng.binomial(14000, 0.24)\n"
    "    treatment = reference_design_b_rng.binomial(14000, 0.255)\n"
    "    z = two_proportion_z_statistic(control, 14000, treatment, 14000)\n"
    "    if abs(z) > Z_ALPHA_2:\n"
    "        reference_design_b_detections += 1\n"
    "empirical_detection_rate_b = reference_design_b_detections / 2000"
)


# --- Two mandatory calibration reveals - real aggregate-count Datasets
# (group/n/conversions), matching the established precedent in this exact
# codebase (old L19's own twist_data.py, L20's experiment_data.py) for a
# "given, already-run result" - never per-customer rows (nothing ever
# browses these as a raw table), never bare ints (keeps a real
# pandas-shaped Python Mirror). Both real, verified this session, both
# unconditional (shown to every student regardless of path). -----------

CALIBRATION_SCHEMA = Schema(
    columns=(
        ColumnSchema("group", "object", description="'control' or 'treatment'"),
        ColumnSchema("n", "int64"),
        ColumnSchema("conversions", "int64"),
    )
)

# Underpowered / wide CI (n=4,000/arm - a 2-week-equivalent inadequate
# design): control 960/4,000=24.0%, treatment 1,008/4,000=25.2%, observed
# +1.2pp, 95% CI [-0.69pp, +3.09pp] - crosses zero AND spans well above
# the +1.5pp threshold. Never "not significant = no effect."
UNDERPOWERED_ROWS = [("control", 4000, 960), ("treatment", 4000, 1008)]

# High-N, tiny-but-precise (n=100,000/arm): control 24,000/100,000=24.0%,
# treatment 24,400/100,000=24.4%, observed +0.4pp, 95% CI [+0.02pp,
# +0.78pp] - narrow, excludes zero, but the ENTIRE interval sits below
# the +1.5pp threshold. Never "significant, so ship it."
HIGH_N_ROWS = [("control", 100000, 24000), ("treatment", 100000, 24400)]


def _calibration_dataset(name: str, rows: list, mirror_step_name: str, mirror_python_code: str) -> Dataset:
    frame = pd.DataFrame(rows, columns=["group", "n", "conversions"])
    step = PipelineStep(mirror_step_name, python_code=mirror_python_code)
    return Dataset(name=name, frame=frame, schema=CALIBRATION_SCHEMA, history=(step,))


def generate_underpowered_calibration() -> Dataset:
    return _calibration_dataset(
        "underpowered_calibration",
        UNDERPOWERED_ROWS,
        "collected",
        "underpowered_calibration = pd.read_csv('novamart_go_underpowered_calibration.csv')",
    )


def _calibration_comparison_mirror_codes(frame_var: str, csv_name: str) -> tuple[str, str, str]:
    """3 real mirror snippets for a calibration reveal's own 4 comparison
    values - control rate, treatment rate, and the CI (both bounds
    computed together; the 4th comparison, the upper bound, needs no
    separate code since ci_upper is already in scope from this same
    snippet). `frame_var` is treated as a legitimate external dependency
    already loaded (see the Dataset's own PipelineStep for its real
    provenance comment) - matching L17/L18's own established discipline
    that a lesson's base dataset is never re-derived mid-mirror, only
    ever referenced."""
    control_code = (
        f"# {frame_var} = pd.read_csv('{csv_name}')\n"
        f"control_row = {frame_var}[{frame_var}['group'] == 'control'].iloc[0]\n"
        "control_rate = control_row['conversions'] / control_row['n']"
    )
    treatment_code = (
        f"treatment_row = {frame_var}[{frame_var}['group'] == 'treatment'].iloc[0]\n"
        "treatment_rate = treatment_row['conversions'] / treatment_row['n']"
    )
    ci_code = (
        "ci_lower, ci_upper = proportion_difference_ci(\n"
        "    control_row['conversions'], control_row['n'],\n"
        "    treatment_row['conversions'], treatment_row['n'],\n"
        ")"
    )
    return control_code, treatment_code, ci_code


UNDERPOWERED_CALIBRATION_MIRROR = _calibration_comparison_mirror_codes(
    "underpowered_calibration", "novamart_go_underpowered_calibration.csv"
)
HIGH_N_CALIBRATION_MIRROR = _calibration_comparison_mirror_codes("high_n_calibration", "novamart_go_high_n_calibration.csv")


def generate_high_n_calibration() -> Dataset:
    return _calibration_dataset(
        "high_n_calibration",
        HIGH_N_ROWS,
        "collected",
        "high_n_calibration = pd.read_csv('novamart_go_high_n_calibration.csv')",
    )


def calibration_counts(dataset: Dataset, group: str) -> tuple[int, int]:
    """(conversions, n) for one group of a calibration Dataset."""
    row = dataset.frame[dataset.frame["group"] == group].iloc[0]
    return int(row["conversions"]), int(row["n"])


def calibration_rate(dataset: Dataset, group: str) -> float:
    conversions, n = calibration_counts(dataset, group)
    return conversions / n


# --- Optional mastery: NovaMart Logistics late-delivery reduction, a
# different domain. Business minimum useful improvement: a 2.0pp
# REDUCTION in late-delivery rate (lower is better here - the opposite
# direction from Quick Pay's own checkout completion). The shared
# proportion_difference_ci/two_proportion_z_statistic helpers always
# compute treatment - control, the same convention as the main lesson;
# for this bad-outcome metric a NEGATIVE treatment-control difference is
# the improvement direction - stated explicitly in this lesson's own
# copy, never silently flipped in code. Real, verified via script this
# session: 4-week design (n=2,000/arm) MDE=2.879pp (inadequate for the
# 2.0pp target); 10-week design (n=5,000/arm) MDE=1.821pp (adequate). The
# study is presented as already run, using the too-small 4-week design:
# control 240/2,000=12.0%, treatment 220/2,000=11.0%, treatment-control=
# -1.0pp, 95% CI [-2.98pp, +0.98pp] - crosses zero AND still comfortably
# contains the business-useful -2.0pp reduction, genuinely inconclusive
# on both fronts. ---------------------------------------------------

MASTERY_BASELINE = 0.12
MASTERY_MINIMUM_EFFECT = 0.02
MASTERY_WEEKLY_N_PER_ARM = 500
MASTERY_INADEQUATE_WEEKS = 4
MASTERY_ADEQUATE_WEEKS = 10

MASTERY_RESULT_ROWS = [("control", 2000, 240), ("treatment", 2000, 220)]


def mastery_mde_for_weeks(weeks: int) -> float:
    return minimum_detectable_effect(MASTERY_BASELINE, weeks * MASTERY_WEEKLY_N_PER_ARM)


def generate_mastery_result() -> Dataset:
    return _calibration_dataset(
        "mastery_late_delivery_result",
        MASTERY_RESULT_ROWS,
        "collected",
        "mastery_result = pd.read_csv('novamart_logistics_late_delivery_result.csv')",
    )

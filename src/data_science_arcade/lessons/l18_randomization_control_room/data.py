import numpy as np
import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

# --- Ground truth (hand-verified via a real pandas script this session -
# no outcome column exists anywhere in this module; the NovaMart Go Quick
# Pay pilot's own outcome is fully sealed for the whole lesson). ----------
#
# 1200 eligible customers - 480 iOS, 720 Android. A real historical
# ID-allocation structure ties platform to customer_id parity: even IDs
# split 360 iOS / 240 Android (600 total); odd IDs split 120 iOS / 480
# Android (600 total). So `customer_id_num % 2 == 0 -> treatment` gives an
# exact 600/600 split by construction, with severe platform imbalance
# (treatment 60.0% iOS, control 20.0% iOS) - "perfect sample ratio,
# terrible assignment mechanism," this lesson's own central trap.
#
# Within each parity class, platform is spread evenly across the ID
# sequence (_evenly_distributed_flags, not "first k IDs are iOS") so a
# raw preview is never a systematically biased sample - same discipline
# L17's own data.py already applies to its own row order.
#
# tenure_days is a real background covariate, generated once via a
# seeded RNG independent of platform/parity (seed 7, distinct from the
# assignment seed) - not a hidden alias of either.
#
# Three real, executed assignment designs, all verified via the same
# script:
#   - id_parity: N 600/600, iOS 60.0% vs 20.0%, tenure 471.2 vs 473.4
#     (deterministic - not a random mechanism at all).
#   - simple_random (seed 42): N 600/600 by construction, iOS 39.8% vs
#     40.2% (a real, small realized imbalance - compatible with valid
#     randomization), tenure 461.2 vs 483.5 (a real, more noticeable but
#     still plausible tenure gap under a genuinely valid mechanism).
#   - stratified_random (seed 42, same seed as simple_random so the
#     Python Mirror diff between them is clean): N 600/600, iOS exactly
#     40.0%/40.0% by construction, tenure 472.0 vs 472.7 (stratification
#     protects platform specifically - it does not zero every covariate's
#     own realized gap).

N_CUSTOMERS = 1200
EVEN_COUNT = 600
ODD_COUNT = 600
EVEN_IOS = 360
EVEN_ANDROID = 240
ODD_IOS = 120
ODD_ANDROID = 480
assert EVEN_IOS + EVEN_ANDROID == EVEN_COUNT
assert ODD_IOS + ODD_ANDROID == ODD_COUNT
assert EVEN_IOS + ODD_IOS == 480  # total iOS
assert EVEN_ANDROID + ODD_ANDROID == 720  # total Android

TREATMENT_SIZE = 600
SIMPLE_RANDOM_SEED = 42
STRATIFIED_RANDOM_SEED = 42
TENURE_SEED = 7
TENURE_MIN_DAYS = 30
TENURE_MAX_DAYS = 900

ID_PARITY = "id_parity"
SIMPLE_RANDOM = "simple_random"
STRATIFIED_RANDOM = "stratified_random"

ROSTER_SCHEMA = Schema(
    columns=(
        ColumnSchema("customer_id", "object"),
        ColumnSchema("customer_id_num", "int64", description="the same identifier as customer_id, as a real integer"),
        ColumnSchema("platform", "object", description="'ios' or 'android'"),
        ColumnSchema("tenure_days", "int64"),
    )
)


def _evenly_distributed_flags(n: int, k: int) -> list[bool]:
    """k True values spread as evenly as possible across n slots (see
    L17's own data.py for the same helper and its own docstring) - used
    here so platform is never front-loaded within a parity class, which
    would make even a raw roster preview a biased sample."""
    return [((i + 1) * k) // n != (i * k) // n for i in range(n)]


def _roster_rows() -> list[dict]:
    even_ids = list(range(2, N_CUSTOMERS + 1, 2))
    odd_ids = list(range(1, N_CUSTOMERS, 2))
    even_ios_flags = _evenly_distributed_flags(EVEN_COUNT, EVEN_IOS)
    odd_ios_flags = _evenly_distributed_flags(ODD_COUNT, ODD_IOS)
    rows = [
        {"customer_id_num": cid, "platform": "ios" if is_ios else "android"}
        for cid, is_ios in zip(even_ids, even_ios_flags)
    ]
    rows += [
        {"customer_id_num": cid, "platform": "ios" if is_ios else "android"}
        for cid, is_ios in zip(odd_ids, odd_ios_flags)
    ]
    return rows


def _roster_frame() -> pd.DataFrame:
    frame = pd.DataFrame(_roster_rows()).sort_values("customer_id_num").reset_index(drop=True)
    frame["customer_id"] = frame["customer_id_num"].apply(lambda n: f"CUST-{n:04d}")
    rng = np.random.default_rng(TENURE_SEED)
    frame["tenure_days"] = rng.integers(TENURE_MIN_DAYS, TENURE_MAX_DAYS + 1, size=len(frame))
    return frame[["customer_id", "customer_id_num", "platform", "tenure_days"]]


def generate_roster() -> Dataset:
    """The real, full pre-treatment roster - no outcome column exists
    anywhere in this module, since NovaMart Go's own outcome is sealed
    for this whole lesson (L19/L20's own future territory)."""
    frame = _roster_frame()
    step = PipelineStep("collected", python_code="roster = pd.read_csv('novamart_go_eligible_roster.csv')")
    return Dataset(name="roster", frame=frame, schema=ROSTER_SCHEMA, history=(step,))


# --- Three real, executed assignment designs -------------------------------


def assign_by_id_parity(roster: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.where(roster["customer_id_num"] % 2 == 0, "treatment", "control"),
        index=roster.index,
    )


ID_PARITY_MIRROR = (
    "roster[\"group\"] = np.where(\n"
    "    roster[\"customer_id_num\"] % 2 == 0,\n"
    "    \"treatment\",\n"
    "    \"control\",\n"
    ")"
)


def assign_simple_random(roster: pd.DataFrame, seed: int = SIMPLE_RANDOM_SEED) -> pd.Series:
    rng = np.random.default_rng(seed)
    order = rng.permutation(roster.index.to_numpy())
    group = pd.Series("control", index=roster.index)
    group.loc[order[:TREATMENT_SIZE]] = "treatment"
    return group


SIMPLE_RANDOM_MIRROR = (
    "rng = np.random.default_rng(42)\n"
    "order = rng.permutation(roster.index.to_numpy())\n"
    "roster[\"group\"] = \"control\"\n"
    "roster.loc[order[:600], \"group\"] = \"treatment\""
)


def assign_stratified_random(roster: pd.DataFrame, seed: int = STRATIFIED_RANDOM_SEED) -> pd.Series:
    rng = np.random.default_rng(seed)
    group = pd.Series("control", index=roster.index)
    for platform in ("ios", "android"):
        pool = roster.index[roster["platform"] == platform].to_numpy()
        order = rng.permutation(pool)
        half = len(order) // 2
        group.loc[order[:half]] = "treatment"
    return group


STRATIFIED_RANDOM_MIRROR = (
    "rng = np.random.default_rng(42)\n"
    "roster[\"group\"] = \"control\"\n"
    "for platform in [\"ios\", \"android\"]:\n"
    "    pool = roster.index[roster[\"platform\"] == platform].to_numpy()\n"
    "    order = rng.permutation(pool)\n"
    "    half = len(order) // 2\n"
    "    roster.loc[order[:half], \"group\"] = \"treatment\""
)

DESIGN_FUNCTIONS = {
    ID_PARITY: assign_by_id_parity,
    SIMPLE_RANDOM: assign_simple_random,
    STRATIFIED_RANDOM: assign_stratified_random,
}
DESIGN_MIRROR = {
    ID_PARITY: ID_PARITY_MIRROR,
    SIMPLE_RANDOM: SIMPLE_RANDOM_MIRROR,
    STRATIFIED_RANDOM: STRATIFIED_RANDOM_MIRROR,
}


def execute_design(design_key: str, roster: pd.DataFrame) -> pd.Series:
    return DESIGN_FUNCTIONS[design_key](roster)


def audit_values(roster: pd.DataFrame, group: pd.Series) -> dict:
    """The real 3-row diagnostic every AssignmentAuditScene shows: N
    split, iOS share, average tenure - treatment vs control."""
    treatment = group == "treatment"
    control = group == "control"
    return {
        "n_treatment": int(treatment.sum()),
        "n_control": int(control.sum()),
        "ios_share_treatment": float((roster.loc[treatment, "platform"] == "ios").mean()),
        "ios_share_control": float((roster.loc[control, "platform"] == "ios").mean()),
        "avg_tenure_treatment": float(roster.loc[treatment, "tenure_days"].mean()),
        "avg_tenure_control": float(roster.loc[control, "tenure_days"].mean()),
    }


# --- Optional mastery: NovaMart Logistics packaging experiment, a
# different domain. Given (not chosen by the student) - a real,
# genuinely-random-by-provenance assignment where one baseline covariate
# (warehouse distance) shows a real but plausible imbalance despite the
# mechanism truly being random. Real, hand-verified via the same script:
# 900 units, seeded simple random assignment (seed 99) over a seeded
# covariate (seed 11, uniform 5-95 km) - 450/450 exact split, average
# distance 47.3 km (treatment) vs 49.5 km (control), a real ~2.2 km /
# ~4.5% relative gap under a genuinely valid random mechanism. -----------

PACKAGING_N = 900
PACKAGING_TREATMENT_SIZE = 450
PACKAGING_COVARIATE_SEED = 11
PACKAGING_ASSIGNMENT_SEED = 99
PACKAGING_DISTANCE_MIN_KM = 5.0
PACKAGING_DISTANCE_MAX_KM = 95.0


def generate_packaging_experiment() -> pd.DataFrame:
    rng_covariate = np.random.default_rng(PACKAGING_COVARIATE_SEED)
    distance = rng_covariate.uniform(PACKAGING_DISTANCE_MIN_KM, PACKAGING_DISTANCE_MAX_KM, size=PACKAGING_N)
    frame = pd.DataFrame(
        {
            "unit_id": [f"PKG-{i + 1:04d}" for i in range(PACKAGING_N)],
            "warehouse_distance_km": distance,
        }
    )
    rng_assign = np.random.default_rng(PACKAGING_ASSIGNMENT_SEED)
    order = rng_assign.permutation(frame.index.to_numpy())
    frame["group"] = "control"
    frame.loc[order[:PACKAGING_TREATMENT_SIZE], "group"] = "treatment"
    return frame


def packaging_audit_values(frame: pd.DataFrame) -> dict:
    treatment = frame["group"] == "treatment"
    control = frame["group"] == "control"
    return {
        "n_treatment": int(treatment.sum()),
        "n_control": int(control.sum()),
        "avg_distance_treatment": float(frame.loc[treatment, "warehouse_distance_km"].mean()),
        "avg_distance_control": float(frame.loc[control, "warehouse_distance_km"].mean()),
    }

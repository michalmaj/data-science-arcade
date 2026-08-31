import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset, PipelineStep
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

BILLING_SCHEMA = Schema(columns=(ColumnSchema("customer_id", "int64"), ColumnSchema("status", "string")))
APP_LOG_SCHEMA = Schema(columns=(ColumnSchema("customer_id", "int64"), ColumnSchema("last_open", "datetime64[ns]")))
MARKETING_SCHEMA = Schema(columns=(ColumnSchema("customer_id", "int64"), ColumnSchema("payment_processor", "string")))
SUPPORT_SCHEMA = Schema(columns=(ColumnSchema("customer_id", "int64"), ColumnSchema("payment_processor", "string")))

REFERENCE_DATE = pd.Timestamp("2026-06-01")
ACTIVE_WINDOW_DAYS = 30

# Named, contiguous customer_id segments - hand-crafted, not randomly
# seeded, so every real number this lesson computes is guaranteed and
# hand-verifiable (same discipline as l01_question_first/twist_data.py).
#
# Ground truth, never shown to the student and never even encoded below -
# no available source resolves it, on purpose: of the 30 legacypay
# accounts, 18 are still actively paying and 12 have cancelled. That
# split simply isn't in any of the four datasets below. The lesson's own
# honest output is a confirmed floor (100), a named unresolved population
# (30), and a defensible range (100-130) - never a "corrected" 118.
NEWPAY_ACTIVE = range(1, 101)  # 100 - Billing: active
NEWPAY_CANCELLED = range(101, 131)  # 30 - Billing: cancelled
LEGACYPAY = range(131, 161)  # 30 - structurally absent from Billing
TRIAL_PENDING = range(161, 169)  # 8 - never billed, absent from Billing

_APP_ACCOUNT_NO_APP = range(81, 101)  # 20 of NEWPAY_ACTIVE never opened the Go app at all
_APP_RECENT_CANCELLED = range(101, 109)  # 8 - cancelled billing, still opens the app
_APP_RECENT_LEGACYPAY = range(131, 138)  # 7 - legacypay, recently active in-app

_SUPPORT_LEGACYPAY = range(131, 145)  # 14 unique legacypay customers on Support's list
_SUPPORT_OTHER = range(1, 7)  # 6 unique non-legacypay customers
_SUPPORT_DUPLICATES = (131, 132)  # 2 of the legacypay rows entered twice by accident


def generate_billing() -> Dataset:
    """Finance's warehouse export: customer_id + status, nothing else.
    Structurally cannot represent a legacypay account - there is no
    processor column and no row for one, not a filtered-out value. An ETL
    gap from the payment-processor migration 3 months ago, not random
    noise. 130 rows, 100 active."""
    rows = [(cid, "active") for cid in NEWPAY_ACTIVE] + [(cid, "cancelled") for cid in NEWPAY_CANCELLED]
    frame = pd.DataFrame(rows, columns=["customer_id", "status"])
    step = PipelineStep("prepared", python_code="billing = pd.read_sql('SELECT * FROM plus_subscriptions', warehouse)")
    return Dataset(name="billing", frame=frame, schema=BILLING_SCHEMA, history=(step,))


def generate_app_log() -> Dataset:
    """The Go app's own event log: one row per customer who has ever
    opened the app, with their most recent open. 20 of the 160 real
    customers never opened the Go app at all - a different population
    than "Plus member," not a data-quality flaw. 140 rows; 95 opened
    within the last 30 days, including 8 who cancelled billing but still
    poke the app occasionally, and 7 legacypay customers - activity isn't
    the same thing as paying, in either direction."""
    recent = REFERENCE_DATE - pd.Timedelta(days=5)
    dormant = REFERENCE_DATE - pd.Timedelta(days=90)
    recent_ids = set(range(1, 81)) | set(_APP_RECENT_CANCELLED) | set(_APP_RECENT_LEGACYPAY)
    has_account = (set(NEWPAY_ACTIVE) | set(NEWPAY_CANCELLED) | set(LEGACYPAY)) - set(_APP_ACCOUNT_NO_APP)
    rows = [(cid, recent if cid in recent_ids else dormant) for cid in sorted(has_account)]
    frame = pd.DataFrame(rows, columns=["customer_id", "last_open"])
    step = PipelineStep("prepared", python_code="app_log = pd.read_json('go_app_activity_snapshot.json')")
    return Dataset(name="app_log", frame=frame, schema=APP_LOG_SCHEMA, history=(step,))


def generate_marketing() -> Dataset:
    """Marketing's CRM export: every customer_id still "enrolled," across
    both payment processors, plus trial signups never billed at all. The
    one source with full population coverage - 168 rows (160 real
    customers + 8 trial-only leads) - which is exactly what makes it
    useful for finding who's missing from Billing, even though its own
    "enrolled" definition overcounts "actively paying"."""
    rows = (
        [(cid, "novapay") for cid in NEWPAY_ACTIVE]
        + [(cid, "novapay") for cid in NEWPAY_CANCELLED]
        + [(cid, "legacypay") for cid in LEGACYPAY]
        + [(cid, "trial_pending") for cid in TRIAL_PENDING]
    )
    frame = pd.DataFrame(rows, columns=["customer_id", "payment_processor"])
    step = PipelineStep("prepared", python_code="marketing = pd.read_csv('crm_plus_enrollment_export.csv')")
    return Dataset(name="marketing", frame=frame, schema=MARKETING_SCHEMA, history=(step,))


def generate_support() -> Dataset:
    """Customer Success's manually maintained VIP/escalation spreadsheet:
    22 rows, but only 20 unique customers - 2 legacypay entries were
    accidentally pasted in twice. Skews toward legacypay customers (they
    called in confused about the migration), which makes this list
    genuinely useful for corroborating that real legacypay accounts exist
    - and genuinely useless for population totals, since it was never a
    sample of anything, and rows here don't equal people even at this
    small scale."""
    rows = (
        [(cid, "legacypay") for cid in _SUPPORT_LEGACYPAY]
        + [(cid, "novapay") for cid in _SUPPORT_OTHER]
        + [(cid, "legacypay") for cid in _SUPPORT_DUPLICATES]
    )
    frame = pd.DataFrame(rows, columns=["customer_id", "payment_processor"])
    step = PipelineStep("prepared", python_code="support = pd.read_excel('customer_success_vip_list.xlsx')")
    return Dataset(name="support", frame=frame, schema=SUPPORT_SCHEMA, history=(step,))


def billing_active_count(billing: Dataset) -> int:
    return int((billing.frame["status"] == "active").sum())


def app_log_active_count(
    app_log: Dataset, reference_date: pd.Timestamp = REFERENCE_DATE, window_days: int = ACTIVE_WINDOW_DAYS
) -> int:
    cutoff = reference_date - pd.Timedelta(days=window_days)
    return int(app_log.frame[app_log.frame["last_open"] >= cutoff]["customer_id"].nunique())


def marketing_enrolled_count(marketing: Dataset) -> int:
    return int(marketing.frame["customer_id"].nunique())


def missing_from_billing_counts(marketing: Dataset, billing: Dataset) -> dict[str, int]:
    """Real customer_ids present in Marketing's full population with zero
    rows in Billing, split by payment_processor - {"legacypay": 30,
    "trial_pending": 8} by construction. The real, computed instance of
    Billing's systematic gap, not a narrated one."""
    billing_ids = set(billing.frame["customer_id"])
    missing = marketing.frame[~marketing.frame["customer_id"].isin(billing_ids)]
    return {str(processor): int(count) for processor, count in missing["payment_processor"].value_counts().items()}


def support_legacypay_counts(support: Dataset) -> tuple[int, int]:
    """(raw rows labeled legacypay, unique legacypay customers after
    dedup) - 16, 14 by construction. The gap between them is the real
    lesson: 22 rows is not 22 people, even in a source this small."""
    legacy_rows = support.frame[support.frame["payment_processor"] == "legacypay"]
    return len(legacy_rows), int(legacy_rows["customer_id"].nunique())


def support_legacypay_share(support: Dataset) -> float:
    """Unique legacypay customers as a share of Support's own unique
    customer count, deduped first - 14/20 = 0.70. Never the raw-row
    share; the dedup lesson from support_legacypay_counts is assumed
    already learned by the time this runs (the optional mastery
    challenge is about representativeness, not re-teaching dedup)."""
    deduped = support.frame.drop_duplicates(subset="customer_id")
    legacy = deduped[deduped["payment_processor"] == "legacypay"]
    return len(legacy) / len(deduped)


def population_legacypay_share(marketing: Dataset) -> float:
    """Real legacypay customers (excluding never-billed trial_pending
    leads) as a share of the full known customer population - 30/160 =
    0.1875. Marketing is the one source with every real customer_id, so
    it's the only honest source for this denominator."""
    real_customers = marketing.frame[marketing.frame["payment_processor"] != "trial_pending"]
    legacy = real_customers[real_customers["payment_processor"] == "legacypay"]
    return len(legacy) / len(real_customers)

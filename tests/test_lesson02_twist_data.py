from data_science_arcade.lessons.l02_source_scout.twist_data import (
    LEGACYPAY,
    app_log_active_count,
    billing_active_count,
    generate_app_log,
    generate_billing,
    generate_marketing,
    generate_support,
    marketing_enrolled_count,
    missing_from_billing_counts,
    population_legacypay_share,
    support_legacypay_counts,
    support_legacypay_share,
)


def test_billing_has_130_rows_100_active():
    billing = generate_billing()
    assert len(billing.frame) == 130
    assert billing_active_count(billing) == 100


def test_billing_never_contains_a_legacypay_customer_id():
    # The real twist: not a filtered value, a structurally absent row.
    billing = generate_billing()
    assert set(billing.frame["customer_id"]).isdisjoint(set(LEGACYPAY))


def test_app_log_has_140_rows_95_recently_active():
    app_log = generate_app_log()
    assert len(app_log.frame) == 140
    assert app_log_active_count(app_log) == 95


def test_app_log_active_count_respects_a_custom_window():
    import pandas as pd

    app_log = generate_app_log()
    # A window so wide it includes even the dormant rows (90 days back)
    assert app_log_active_count(app_log, window_days=120) == 140
    # A window so narrow it excludes even the recent rows (5 days back)
    assert app_log_active_count(app_log, window_days=1) == 0


def test_marketing_has_168_rows_covering_the_full_population():
    marketing = generate_marketing()
    assert len(marketing.frame) == 168
    assert marketing_enrolled_count(marketing) == 168
    processors = set(marketing.frame["payment_processor"])
    assert processors == {"novapay", "legacypay", "trial_pending"}


def test_missing_from_billing_splits_into_legacy_and_trial():
    billing = generate_billing()
    marketing = generate_marketing()
    counts = missing_from_billing_counts(marketing, billing)
    assert counts == {"legacypay": 30, "trial_pending": 8}


def test_support_has_22_rows_but_only_20_unique_customers():
    support = generate_support()
    assert len(support.frame) == 22
    assert support.frame["customer_id"].nunique() == 20


def test_support_legacypay_counts_distinguish_raw_rows_from_unique_customers():
    support = generate_support()
    raw, unique = support_legacypay_counts(support)
    assert raw == 16
    assert unique == 14


def test_support_legacypay_share_uses_the_deduped_denominator():
    support = generate_support()
    # 14 unique legacypay / 20 unique total, not 16/22 (the raw, undeduped
    # numbers) - the whole point of this function existing.
    assert support_legacypay_share(support) == 14 / 20


def test_population_legacypay_share_excludes_trial_pending():
    marketing = generate_marketing()
    # 30 real legacypay customers / 160 real customers (100 + 30 + 30),
    # not /168 - trial_pending was never a real member.
    assert population_legacypay_share(marketing) == 30 / 160


def test_support_massively_overrepresents_legacypay_relative_to_the_full_population():
    # The real point of the optional mastery challenge: a source can be
    # excellent for confirming a mechanism exists and terrible for
    # estimating how common it is.
    support = generate_support()
    marketing = generate_marketing()
    assert support_legacypay_share(support) > 3 * population_legacypay_share(marketing)

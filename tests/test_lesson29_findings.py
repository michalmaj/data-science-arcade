from data_science_arcade.lessons.l29_the_executive_brief.findings import (
    CORRECT_FINDING_KEYS,
    FINDINGS_POOL,
    TARGET_FINDING_COUNT,
)
from data_science_arcade.lessons.l29_the_executive_brief.findings_data import generate_findings_data


def test_the_pool_has_more_findings_than_the_target_count():
    assert len(FINDINGS_POOL) > TARGET_FINDING_COUNT


def test_every_finding_key_is_unique():
    keys = [finding.key for finding in FINDINGS_POOL]
    assert len(keys) == len(set(keys))


def test_exactly_three_findings_are_marked_correct():
    assert len(CORRECT_FINDING_KEYS) == TARGET_FINDING_COUNT


def test_every_correct_finding_key_is_actually_in_the_pool():
    pool_keys = {finding.key for finding in FINDINGS_POOL}
    assert CORRECT_FINDING_KEYS <= pool_keys


def test_every_finding_key_used_by_a_dataset_lookup_actually_exists_in_the_data():
    # The pool's "dramatic" and "secondary" findings reference real rows in
    # the shared dataset via their own key, same as the three correct ones -
    # every finding is backed by a real number, not just the right answers.
    dataset = generate_findings_data()
    real_keys = set(dataset.frame["finding_key"])
    for finding in FINDINGS_POOL:
        if finding.key == "order_value_and_returns_steady":
            continue  # this one is a combined finding over two dataset rows, not a single key
        assert finding.key in real_keys

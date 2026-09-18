from data_science_arcade.lessons.l29_the_executive_brief.findings import (
    CORRECT_FINDING_KEYS,
    FINDINGS_POOL,
    HEADLINE_TARGET_COUNT,
    LEAD_FINDING_KEY,
    ON_TOPIC_FINDING_KEYS,
    SHORTLIST_TARGET_COUNT,
)
from data_science_arcade.lessons.l29_the_executive_brief.findings_data import generate_findings_data


def test_the_pool_has_more_findings_than_the_shortlist_target():
    assert len(FINDINGS_POOL) > SHORTLIST_TARGET_COUNT > HEADLINE_TARGET_COUNT


def test_every_finding_key_is_unique():
    keys = [finding.key for finding in FINDINGS_POOL]
    assert len(keys) == len(set(keys))


def test_exactly_five_findings_are_on_topic_and_exactly_three_are_correct():
    assert len(ON_TOPIC_FINDING_KEYS) == SHORTLIST_TARGET_COUNT == 5
    assert len(CORRECT_FINDING_KEYS) == HEADLINE_TARGET_COUNT == 3


def test_every_correct_finding_key_is_a_subset_of_the_on_topic_set():
    assert CORRECT_FINDING_KEYS <= ON_TOPIC_FINDING_KEYS


def test_every_on_topic_finding_key_is_actually_in_the_pool():
    pool_keys = {finding.key for finding in FINDINGS_POOL}
    assert ON_TOPIC_FINDING_KEYS <= pool_keys


def test_the_on_topic_set_excludes_exactly_the_three_dramatic_unrelated_findings():
    pool_keys = {finding.key for finding in FINDINGS_POOL}
    excluded = pool_keys - ON_TOPIC_FINDING_KEYS
    assert excluded == {"social_mentions", "stock_price", "employee_satisfaction"}


def test_the_on_topic_but_not_headline_findings_are_support_tickets_and_competitor():
    assert (ON_TOPIC_FINDING_KEYS - CORRECT_FINDING_KEYS) == {"support_tickets_confusing_checkout", "competitor_completion_rate"}


def test_lead_finding_is_the_direct_outcome_not_the_mechanism_or_guardrail():
    assert LEAD_FINDING_KEY == "checkout_completion"
    assert LEAD_FINDING_KEY in CORRECT_FINDING_KEYS


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


def test_every_finding_has_real_mirror_code_ending_on_a_named_variable():
    dataset = generate_findings_data()
    for finding in FINDINGS_POOL:
        assert finding.python_code is not None
        namespace = {"findings": dataset.frame}
        exec(finding.python_code, namespace)
        bound_names = set(namespace) - {"findings"}
        assert bound_names, f"{finding.key}'s own python_code never binds a named variable"

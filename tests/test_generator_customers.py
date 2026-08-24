from data_science_arcade.data_engine.generators.customers import PLANS, REGIONS, generate_customers
from data_science_arcade.data_engine.testing import assert_matches_schema, assert_unique, assert_values_in


def test_same_seed_produces_identical_data():
    first = generate_customers(seed=42, count=50)
    second = generate_customers(seed=42, count=50)

    assert first.frame.equals(second.frame)


def test_different_seeds_produce_different_data():
    first = generate_customers(seed=1, count=50)
    second = generate_customers(seed=2, count=50)

    assert not first.frame.equals(second.frame)


def test_row_count_matches_the_requested_count():
    assert len(generate_customers(seed=1, count=123).frame) == 123


def test_matches_its_own_schema():
    assert_matches_schema(generate_customers(seed=1, count=100))


def test_customer_id_is_unique():
    assert_unique(generate_customers(seed=1, count=200), "customer_id")


def test_region_and_plan_only_take_documented_values():
    dataset = generate_customers(seed=1, count=200)
    assert_values_in(dataset, "region", set(REGIONS))
    assert_values_in(dataset, "plan", set(PLANS))


def test_history_records_that_it_was_generated():
    dataset = generate_customers(seed=1, count=10)
    assert [step.name for step in dataset.history] == ["generated"]
    assert dataset.python_mirror()  # has a Python Mirror entry, non-empty

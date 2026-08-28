from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l20_ab_test_commander.twist_data import click_through_rate, generate_reranking_data


def test_generated_data_matches_its_schema():
    dataset = generate_reranking_data()
    dtesting.assert_matches_schema(dataset)


def test_the_full_scale_rollout_actually_declined():
    dataset = generate_reranking_data()
    before = click_through_rate(dataset, "before_rollout")
    after = click_through_rate(dataset, "after_rollout")
    assert before == 0.072
    assert after == 0.061
    assert after < before  # the early peek pointed the wrong way entirely

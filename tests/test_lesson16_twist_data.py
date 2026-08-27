import pytest

from data_science_arcade.lessons.l16_metric_forge.twist_data import churn_mean, generate_churn_data


def test_churn_rate_more_than_triples_after_the_initiative():
    # Real computed values (verified via a manual script before writing
    # this assertion), not hand-picked.
    dataset = generate_churn_data()
    before = churn_mean(dataset, "before")
    after = churn_mean(dataset, "after")
    assert before == pytest.approx(0.05)
    assert after == pytest.approx(0.18)
    assert after > before * 3

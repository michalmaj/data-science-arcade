from data_science_arcade.lessons.l08_duplicate_detective.twist_data import (
    generate_match_results,
    precision,
    recall,
)


def test_aggressive_rule_has_perfect_recall_but_merges_real_people():
    dataset = generate_match_results()
    assert recall(dataset, "aggressive_merge") == 1.0
    assert precision(dataset, "aggressive_merge") == 0.8


def test_conservative_rule_has_perfect_precision_but_misses_some_duplicates():
    dataset = generate_match_results()
    assert precision(dataset, "conservative_merge") == 1.0
    assert recall(dataset, "conservative_merge") == 0.85


def test_fifty_candidate_pairs_with_forty_true_duplicates():
    dataset = generate_match_results()
    assert len(dataset.frame) == 50
    assert int(dataset.frame["is_true_duplicate"].sum()) == 40

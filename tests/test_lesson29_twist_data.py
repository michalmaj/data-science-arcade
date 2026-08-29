from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l29_the_executive_brief.twist_data import generate_app_update_data, percent_change


def test_generated_data_matches_its_schema():
    dataset = generate_app_update_data()
    dtesting.assert_matches_schema(dataset)


def test_app_downloads_spiked_dramatically():
    dataset = generate_app_update_data()
    assert round(percent_change(dataset, "app_downloads"), 2) == 5.0


def test_session_length_barely_moved_in_comparison():
    dataset = generate_app_update_data()
    downloads_change = percent_change(dataset, "app_downloads")
    session_change = percent_change(dataset, "session_length_minutes")
    assert session_change > 0
    assert downloads_change > session_change * 20

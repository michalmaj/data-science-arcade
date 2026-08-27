from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l17_hypothesis_detective.twist_data import device_repeat_rate, generate_device_split_data


def test_generated_data_matches_its_schema():
    dataset = generate_device_split_data()
    dtesting.assert_matches_schema(dataset)


def test_app_and_website_users_start_at_very_different_baselines():
    dataset = generate_device_split_data()
    app_before = device_repeat_rate(dataset, "app", "before")
    website_before = device_repeat_rate(dataset, "website", "before")
    assert app_before == 0.40
    assert website_before == 0.13
    assert app_before > website_before * 2


def test_both_devices_move_by_the_identical_amount_after_launch():
    dataset = generate_device_split_data()
    for device in ("app", "website"):
        before = device_repeat_rate(dataset, device, "before")
        after = device_repeat_rate(dataset, device, "after")
        assert round(after - before, 4) == 0.10

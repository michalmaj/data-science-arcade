from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l18_randomization_control_room.assignment_data import relative_imbalance
from data_science_arcade.lessons.l18_randomization_control_room.twist_data import generate_platform_split_data, ios_share


def test_generated_data_matches_its_schema():
    dataset = generate_platform_split_data()
    dtesting.assert_matches_schema(dataset)


def test_group_sizes_are_balanced_but_platform_is_not():
    dataset = generate_platform_split_data()
    frame = dataset.frame
    treatment_size = int(frame[frame["group"] == "treatment"]["customer_count"].iloc[0])
    control_size = int(frame[frame["group"] == "control"]["customer_count"].iloc[0])
    assert treatment_size == control_size == 500

    treatment_ios = ios_share(dataset, "treatment")
    control_ios = ios_share(dataset, "control")
    assert treatment_ios == 0.68
    assert control_ios == 0.24
    assert relative_imbalance(treatment_ios, control_ios) is True

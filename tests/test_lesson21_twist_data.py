from data_science_arcade.data_engine import testing as dtesting
from data_science_arcade.lessons.l21_funnel_factory.twist_data import generate_onboarding_data, profile_completion_rate, signup_rate


def test_generated_data_matches_its_schema():
    dataset = generate_onboarding_data()
    dtesting.assert_matches_schema(dataset)


def test_the_flawed_signup_count_looked_far_worse_than_reality():
    dataset = generate_onboarding_data()
    flawed = signup_rate(dataset, flawed=True)
    correct = signup_rate(dataset, flawed=False)
    assert flawed == 0.35
    assert correct == 0.81
    assert correct > flawed * 2  # not a small correction - the flawed read was badly wrong


def test_the_real_bottleneck_was_never_investigated():
    dataset = generate_onboarding_data()
    correct_signup = signup_rate(dataset, flawed=False)
    profile = profile_completion_rate(dataset)
    assert profile == 0.42
    assert profile < correct_signup  # worse than the step the team actually "fixed"

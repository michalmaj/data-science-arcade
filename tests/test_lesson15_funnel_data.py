import pytest

from data_science_arcade.lessons.l15_segment_detective.funnel_data import (
    generate_channel_funnel,
    generate_device_funnel,
    generate_region_funnel,
    overall_rate,
    segment_rate,
)

DIMENSIONS = (
    (generate_device_funnel, ("mobile", "desktop")),
    (generate_region_funnel, ("eu", "us")),
    (generate_channel_funnel, ("organic", "paid")),
)


@pytest.mark.parametrize("generate,segments", DIMENSIONS)
def test_every_individual_segment_rate_declines(generate, segments):
    dataset = generate()
    for segment in segments:
        assert segment_rate(dataset, "Q2", segment) < segment_rate(dataset, "Q1", segment)


@pytest.mark.parametrize("generate,segments", DIMENSIONS)
def test_the_overall_rate_improves_despite_every_segment_declining(generate, segments):
    # Real computed values (verified via a manual script before writing
    # this assertion), not hand-picked: Simpson's paradox by construction -
    # the higher-converting segment's share of traffic grows enough to
    # pull the blended rate up even though both segments' own rates fell.
    dataset = generate()
    assert overall_rate(dataset, "Q2") > overall_rate(dataset, "Q1")


def test_device_rates_match_the_verified_manual_computation():
    dataset = generate_device_funnel()
    assert segment_rate(dataset, "Q1", "mobile") == pytest.approx(0.42)
    assert segment_rate(dataset, "Q2", "mobile") == pytest.approx(0.38)
    assert segment_rate(dataset, "Q1", "desktop") == pytest.approx(0.25)
    assert segment_rate(dataset, "Q2", "desktop") == pytest.approx(0.22)
    assert overall_rate(dataset, "Q1") == pytest.approx(0.284)
    assert overall_rate(dataset, "Q2") == pytest.approx(0.332)

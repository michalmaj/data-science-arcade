from data_science_arcade.lessons.l03_api_courier.twist_data import (
    SHORTFALL_PAGE,
    generate_page_completeness,
    overall_completeness,
    page_completeness,
)


def test_overall_completeness_is_92_percent():
    dataset = generate_page_completeness()
    assert overall_completeness(dataset) == 0.92


def test_the_shortfall_page_is_60_percent_complete():
    dataset = generate_page_completeness()
    assert page_completeness(dataset, SHORTFALL_PAGE) == 0.60


def test_every_other_page_is_fully_complete():
    dataset = generate_page_completeness()
    for page_number in (1, 2, 3, 5):
        assert page_completeness(dataset, page_number) == 1.0


def test_the_aggregate_hides_the_shortfall_the_same_way_lesson_02_hides_the_skew():
    dataset = generate_page_completeness()
    overall = overall_completeness(dataset)
    shortfall = page_completeness(dataset, SHORTFALL_PAGE)
    assert overall > 0.85  # looks fine in aggregate
    assert shortfall < overall  # but one page is meaningfully worse

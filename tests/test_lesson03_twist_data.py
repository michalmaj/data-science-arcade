from data_science_arcade.lessons.l03_api_courier.twist_data import (
    BEST_ACHIEVABLE_TOTAL,
    MASTERY_PAGE_SIZE,
    MASTERY_RECEIVED_TOTAL,
    MASTERY_TOTAL_COUNT,
    PAGE_SIZE,
    RATE_LIMITED_PAGE,
    SHORTFALL_ACTUAL,
    SHORTFALL_PAGE,
    TOTAL_COUNT,
    generate_pages,
    page_shortfall,
)


def test_generated_pages_has_one_row_per_page_and_sums_to_the_best_achievable_total():
    dataset = generate_pages()
    assert len(dataset.frame) == 6
    assert int(dataset.frame["actual_count"].sum()) == BEST_ACHIEVABLE_TOTAL


def test_the_best_achievable_total_still_falls_short_of_the_declared_total_count():
    # Page 3's real shortfall is never recovered by anything this lesson's
    # console does - even a perfectly-executed pull (every rate limit
    # correctly backed off) stays 9 short of TOTAL_COUNT.
    assert BEST_ACHIEVABLE_TOTAL == TOTAL_COUNT - (PAGE_SIZE - SHORTFALL_ACTUAL)


def test_page_shortfall_is_nine_records_on_the_shortfall_page_and_zero_elsewhere():
    dataset = generate_pages()
    assert page_shortfall(dataset, SHORTFALL_PAGE) == PAGE_SIZE - SHORTFALL_ACTUAL == 9
    for page_number in (1, 2, 4, RATE_LIMITED_PAGE):
        assert page_shortfall(dataset, page_number) == 0


def test_the_last_page_is_naturally_smaller_and_has_more_correctly_reads_false():
    # page_shortfall() compares against the fixed page_size *parameter*
    # (25 records requested), not "what a natural last page should hold" -
    # a genuinely smaller last page is real API behavior, not a shortfall,
    # which is exactly why has_more (not page_shortfall) is the signal a
    # student should actually be reading here.
    dataset = generate_pages()
    last_page = dataset.frame[dataset.frame["page_number"] == 6].iloc[0]
    assert last_page["actual_count"] == TOTAL_COUNT - 5 * PAGE_SIZE == 12
    assert bool(last_page["has_more"]) is False


def test_only_the_shortfall_page_has_a_real_gap_every_other_page_reconciles():
    dataset = generate_pages()
    for _, row in dataset.frame.iterrows():
        if row["page_number"] == SHORTFALL_PAGE:
            continue
        assert row["actual_count"] == min(PAGE_SIZE, TOTAL_COUNT - (row["page_number"] - 1) * PAGE_SIZE)


def test_mastery_numbers_hide_a_shortfall_on_what_looks_like_a_normal_last_page():
    natural_last_page = MASTERY_TOTAL_COUNT - 2 * MASTERY_PAGE_SIZE
    real_last_page_received = MASTERY_RECEIVED_TOTAL - 2 * MASTERY_PAGE_SIZE
    assert natural_last_page == 8
    assert real_last_page_received == 3
    assert real_last_page_received < natural_last_page  # the trap: it looks like a normal small last page anyway
    assert MASTERY_RECEIVED_TOTAL < MASTERY_TOTAL_COUNT

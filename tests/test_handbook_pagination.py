import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.core import fonts
from data_science_arcade.core.fonts import get_font
from data_science_arcade.ui.handbook_pagination import paginate


@pytest.fixture(autouse=True)
def _pygame_session():
    pygame.init()
    fonts.clear_cache()
    pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def test_short_content_fits_on_one_page():
    font = get_font(16)
    pages = paginate(["A short paragraph."], font, max_width=500, max_lines_per_page=20)
    assert pages == [["A short paragraph."]]


def test_long_content_spans_multiple_pages():
    font = get_font(16)
    paragraph = " ".join(["word"] * 200)  # wraps to well more than 3 lines at this width
    pages = paginate([paragraph], font, max_width=200, max_lines_per_page=3)
    assert len(pages) > 1
    for page in pages:
        assert 1 <= len(page) <= 3


def test_two_paragraphs_produce_exactly_one_blank_line_separator():
    font = get_font(16)
    pages = paginate(["First.", "Second."], font, max_width=500, max_lines_per_page=20)
    assert pages == [["First.", "", "Second."]]  # one separator, not zero, not two


def test_a_page_never_starts_with_a_stripped_leading_blank_line():
    # Two one-line paragraphs, one line per page: without stripping, the
    # separator between them would land alone as its own page (a visible
    # gap). It must instead disappear entirely, leaving exactly 2 pages -
    # one per paragraph - not 3.
    font = get_font(16)
    pages = paginate(["First.", "Second."], font, max_width=500, max_lines_per_page=1)
    assert pages == [["First."], ["Second."]]
    assert all(page != [""] for page in pages)


def test_a_paragraph_longer_than_one_page_still_produces_valid_nonempty_pages():
    font = get_font(16)
    paragraph = " ".join(["word"] * 50)
    pages = paginate([paragraph, "Short second paragraph."], font, max_width=150, max_lines_per_page=2)
    assert len(pages) > 1
    for page in pages:
        assert len(page) > 0


def test_embedded_newline_is_normalized_not_rendered_as_a_broken_line():
    # pygame's own font rendering doesn't honor embedded newlines - it
    # fuses both fragments onto one visual line instead of breaking, a
    # real risk for hand-authored prose. Normalizing first means the
    # paragraph wraps by real pixel width like any other text, rather
    # than silently producing one fused, unmeasured line.
    font = get_font(16)
    pages = paginate(["Line one.\nLine two that keeps going and going and going."], font, max_width=100, max_lines_per_page=20)
    for page in pages:
        for line in page:
            assert "\n" not in line
            assert font.size(line)[0] <= 100


def test_empty_paragraphs_list_returns_one_empty_page():
    font = get_font(16)
    assert paginate([], font, max_width=500, max_lines_per_page=10) == [[]]


def test_max_lines_per_page_below_one_raises():
    font = get_font(16)
    with pytest.raises(ValueError):
        paginate(["Some text."], font, max_width=500, max_lines_per_page=0)

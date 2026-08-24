import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.core import fonts
from data_science_arcade.core.fonts import get_font
from data_science_arcade.ui.text import wrap_text


@pytest.fixture(autouse=True)
def _pygame_session():
    pygame.init()
    fonts.clear_cache()
    pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def test_short_text_stays_on_one_line():
    font = get_font(20)
    assert wrap_text("hello world", font, max_width=500) == ["hello world"]


def test_long_text_wraps_across_multiple_lines_that_each_fit():
    font = get_font(20)
    text = " ".join(["word"] * 40)

    lines = wrap_text(text, font, max_width=200)

    assert len(lines) > 1
    for line in lines:
        assert font.size(line)[0] <= 200


def test_wrapping_preserves_every_word_in_order():
    font = get_font(20)
    text = "the quick brown fox jumps over the lazy dog"

    lines = wrap_text(text, font, max_width=80)

    assert " ".join(lines).split(" ") == text.split(" ")


def test_a_single_word_wider_than_max_width_gets_its_own_line_instead_of_vanishing():
    font = get_font(20)
    long_word = "x" * 200

    lines = wrap_text(long_word, font, max_width=10)

    assert lines == [long_word]

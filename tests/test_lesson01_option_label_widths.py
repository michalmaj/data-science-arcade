import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.core import fonts
from data_science_arcade.core.fonts import get_font
from data_science_arcade.lessons.l01_question_first.scenario import BRIEF_FIELDS, DECISION_FIELDS
from data_science_arcade.localization.service import SUPPORTED_LOCALES, Localization
from data_science_arcade.ui.brief_builder_scene import OPTION_SIZE
from data_science_arcade.ui.button import BUTTON_TEXT_SIZE

# Button.draw() centers text with no wrapping/truncation (unlike table cells
# or dialogue text), so any option label wider than the button silently
# spills past its edges - this test is what should have caught the
# window_choice/limitation overflow found by hand via screenshots.
MAX_LABEL_WIDTH = OPTION_SIZE[0] - 40  # matches the padding used elsewhere for button text


@pytest.fixture(autouse=True)
def _pygame_session():
    pygame.init()
    fonts.clear_cache()
    yield
    pygame.quit()


ALL_OPTIONS = [
    (field.key, option.key, option.label_key) for field in (*BRIEF_FIELDS, *DECISION_FIELDS) for option in field.options
]


@pytest.mark.parametrize("field_key,option_key,label_key", ALL_OPTIONS)
@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_option_label_fits_within_the_button(locale, field_key, option_key, label_key):
    loc = Localization(locale=locale)
    text = loc.t(label_key)
    font = get_font(BUTTON_TEXT_SIZE)

    width, _height = font.size(text)

    assert width <= MAX_LABEL_WIDTH, (
        f"{locale}/{label_key} ({field_key}.{option_key}) is {width}px wide, "
        f"button only fits {MAX_LABEL_WIDTH}px: {text!r}"
    )

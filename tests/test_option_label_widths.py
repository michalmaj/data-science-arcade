import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.core import fonts
from data_science_arcade.core.fonts import get_font
from data_science_arcade.lessons.l01_question_first.scenario import BRIEF_FIELDS as L01_BRIEF_FIELDS
from data_science_arcade.lessons.l01_question_first.scenario import DECISION_FIELDS as L01_DECISION_FIELDS
from data_science_arcade.lessons.l02_source_scout.scenario import DECISION_FIELDS as L02_DECISION_FIELDS
from data_science_arcade.lessons.l02_source_scout.scenario import SOURCES as L02_SOURCES
from data_science_arcade.lessons.l03_api_courier.scenario import DECISION_FIELDS as L03_DECISION_FIELDS
from data_science_arcade.lessons.l04_event_log_factory.scenario import DECISION_FIELDS as L04_DECISION_FIELDS
from data_science_arcade.lessons.l04_event_log_factory.scenario import FLOW_STEPS as L04_FLOW_STEPS
from data_science_arcade.localization.service import SUPPORTED_LOCALES, Localization
from data_science_arcade.ui.brief_builder_scene import OPTION_SIZE
from data_science_arcade.ui.button import BUTTON_TEXT_SIZE
from data_science_arcade.ui.flow_builder_scene import OPTION_SIZE as FLOW_OPTION_SIZE
from data_science_arcade.ui.source_board_scene import HEADER_SIZE

# Button.draw() centers text with no wrapping/truncation (unlike table cells
# or dialogue text), so any label wider than its button silently spills past
# its edges - this is what should have caught the Lesson 01 window_choice/
# limitation overflow that was originally found by hand via screenshots.
# Every lesson's BriefField options and SourceBoardScene source names get
# checked here, in both languages, rather than one test file per lesson.
BUTTON_PADDING = 40


def _collect_checks() -> list[tuple[str, str, int]]:
    checks: list[tuple[str, str, int]] = []

    option_button_width = OPTION_SIZE[0] - BUTTON_PADDING
    brief_fields = (
        *L01_BRIEF_FIELDS,
        *L01_DECISION_FIELDS,
        *L02_DECISION_FIELDS,
        *L03_DECISION_FIELDS,
        *L04_DECISION_FIELDS,
    )
    for field in brief_fields:
        for option in field.options:
            checks.append((f"{field.key}.{option.key}", option.label_key, option_button_width))

    header_button_width = HEADER_SIZE[0] - BUTTON_PADDING
    for source in L02_SOURCES:
        checks.append((f"source.{source.key}", source.name_key, header_button_width))

    flow_option_button_width = FLOW_OPTION_SIZE[0] - BUTTON_PADDING
    for step in L04_FLOW_STEPS:
        for option in step.options:
            checks.append((f"{step.key}.{option.key}", option.label_key, flow_option_button_width))

    return checks


ALL_CHECKS = _collect_checks()


@pytest.fixture(autouse=True)
def _pygame_session():
    pygame.init()
    fonts.clear_cache()
    yield
    pygame.quit()


@pytest.mark.parametrize("owner,label_key,max_width", ALL_CHECKS)
@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_button_label_fits_within_its_button(locale, owner, label_key, max_width):
    loc = Localization(locale=locale)
    text = loc.t(label_key)
    font = get_font(BUTTON_TEXT_SIZE)

    width, _height = font.size(text)

    assert width <= max_width, f"{locale}/{label_key} ({owner}) is {width}px wide, button only fits {max_width}px: {text!r}"

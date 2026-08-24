import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.brief import BriefField, BriefOption
from data_science_arcade.ui.brief_builder_scene import BriefBuilderScene

FIELDS = (
    BriefField(
        key="color",
        prompt_key="common.back",  # any real key works - content isn't under test here
        hint_key="common.back",
        options=(BriefOption("red", "common.back"), BriefOption("blue", "common.back")),
    ),
    BriefField(
        key="size",
        prompt_key="common.back",
        options=(BriefOption("small", "common.back"), BriefOption("large", "common.back")),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_starts_on_the_first_field_with_next_disabled():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        assert scene.field_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_selecting_an_option_enables_next():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_does_nothing_if_nothing_is_selected():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        scene._next()
        assert scene.field_index == 0
    finally:
        pygame.quit()


def test_next_advances_to_the_second_field_once_selected():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        assert scene.field_index == 1
        assert scene.back_button.enabled is True
    finally:
        pygame.quit()


def test_back_returns_to_the_previous_field_and_keeps_its_earlier_choice():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        scene.buttons.buttons[0].on_activate()  # color=red
        scene.next_button.on_activate()

        scene.back_button.on_activate()

        assert scene.field_index == 0
        assert scene.choices["color"] == "red"
    finally:
        pygame.quit()


def test_finishing_the_last_field_calls_on_complete_with_every_choice():
    app = _init_app()
    try:
        collected = []
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: collected.append(brief))

        scene.buttons.buttons[0].on_activate()  # color=red
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # size=large
        scene.next_button.on_activate()

        assert collected == [{"color": "red", "size": "large"}]
    finally:
        pygame.quit()


def test_the_next_button_says_finish_only_on_the_last_field():
    app = _init_app()
    try:
        scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None)
        assert scene.next_button.label == app.localization.t("brief.next")

        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.next_button.label == app.localization.t("brief.finish")
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = BriefBuilderScene(app, "app.title", FIELDS, on_complete=lambda brief: None, guided=guided)
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.api import APIRequestAttempt
from data_science_arcade.ui.api_console_scene import APIConsoleScene

ATTEMPTS = (
    APIRequestAttempt(page_number=1, status_key="common.on", records_returned=20, is_success=True),
    APIRequestAttempt(page_number=2, status_key="common.off", records_returned=0, is_success=False),
    APIRequestAttempt(page_number=2, status_key="common.on", records_returned=15, is_success=True),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda total: None, **kwargs):
    return APIConsoleScene(app, "app.title", "app.title", ATTEMPTS, on_complete, **kwargs)


def test_starts_with_an_empty_log_and_zero_records():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.log == []
        assert scene.total_records() == 0
    finally:
        pygame.quit()


def test_sending_a_request_appends_the_next_scripted_attempt():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._send_request()
        assert scene.log == [ATTEMPTS[0]]
        assert scene.total_records() == 20
    finally:
        pygame.quit()


def test_a_failed_attempt_does_not_add_to_the_record_count():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._send_request()  # page 1: success, 20
        scene._send_request()  # page 2: failure, 0

        assert scene.total_records() == 20
    finally:
        pygame.quit()


def test_the_action_button_becomes_finish_only_once_every_attempt_has_played():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.action_button.label == app.localization.t("api_console.send_request")

        for _ in ATTEMPTS:
            scene._send_request()

        assert scene.action_button.label == app.localization.t("api_console.finish")
    finally:
        pygame.quit()


def test_finish_does_nothing_before_every_attempt_has_played():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda total: collected.append(total))
        scene._send_request()

        scene._finish()

        assert collected == []
    finally:
        pygame.quit()


def test_finish_calls_on_complete_with_the_total_once_everything_has_played():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda total: collected.append(total))
        for _ in ATTEMPTS:
            scene._send_request()

        scene.action_button.on_activate()  # the button itself, not the private method

        assert collected == [35]  # 20 + 0 + 15
    finally:
        pygame.quit()


def test_sending_past_the_end_of_the_script_is_a_no_op():
    app = _init_app()
    try:
        scene = _make_scene(app)
        for _ in range(len(ATTEMPTS) + 3):
            scene._send_request()

        assert scene.log == list(ATTEMPTS)
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_at_any_point_in_the_sequence():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided, hint_key="common.back")
            for _ in range(len(ATTEMPTS) + 1):
                scene.draw(app.logical_surface)
                scene._send_request()
    finally:
        pygame.quit()

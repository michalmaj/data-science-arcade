import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.api import APIRequestAttempt, RetryOption
from data_science_arcade.ui.api_console_scene import APIConsoleScene
from data_science_arcade.workbench.context import LessonContext

_RATE_LIMITED_STATUS = "common.off"
_SKIPPED_STATUS = "dialogue.continue_hint"

_WAIT_SUCCESS = APIRequestAttempt(2, "common.on", 15, True, has_more=True, total_count=35)
_SKIP = APIRequestAttempt(2, _SKIPPED_STATUS, 0, False, has_more=True, total_count=None)
_SECOND_RATE_LIMIT = APIRequestAttempt(
    2,
    _RATE_LIMITED_STATUS,
    0,
    False,
    has_more=True,
    total_count=None,
    retry_options=(
        RetryOption("wait_and_retry", "common.back", _WAIT_SUCCESS),
        RetryOption("skip", "common.back", _SKIP),
    ),
)
_INITIAL_RATE_LIMIT = APIRequestAttempt(
    2,
    _RATE_LIMITED_STATUS,
    0,
    False,
    has_more=True,
    total_count=None,
    retry_options=(
        RetryOption("retry_immediately", "common.back", _SECOND_RATE_LIMIT),
        RetryOption("wait_and_retry", "common.back", _WAIT_SUCCESS),
        RetryOption("skip", "common.back", _SKIP),
    ),
)

ATTEMPTS = (
    APIRequestAttempt(1, "common.on", 20, True, has_more=True, total_count=35),
    _INITIAL_RATE_LIMIT,
    APIRequestAttempt(3, "common.on", 12, True, has_more=False, total_count=35),
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


def test_a_rate_limited_attempt_replaces_the_single_button_with_real_choices():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._send_request()  # page 1
        scene._send_request()  # page 2, rate-limited

        assert scene._pending is ATTEMPTS[1]
        assert len(scene.buttons.buttons) == 3
        labels = {button.label for button in scene.buttons.buttons}
        assert app.localization.t("common.back") in labels
    finally:
        pygame.quit()


def test_retrying_immediately_fails_again_and_narrows_to_two_choices():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._send_request()
        scene._send_request()
        retry_immediately = next(o for o in scene._pending.retry_options if o.key == "retry_immediately")

        scene._make_choose_retry(retry_immediately)()

        assert scene._pending is _SECOND_RATE_LIMIT
        assert len(scene.buttons.buttons) == 2
        assert scene.total_records() == 20  # the second failure adds nothing
    finally:
        pygame.quit()


def test_waiting_and_retrying_resolves_the_page_and_advances():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._send_request()
        scene._send_request()
        wait_and_retry = next(o for o in scene._pending.retry_options if o.key == "wait_and_retry")

        scene._make_choose_retry(wait_and_retry)()

        assert scene._pending is None
        assert scene.total_records() == 20 + 15
        scene._send_request()  # page 3 is now reachable
        assert scene.total_records() == 20 + 15 + 12
    finally:
        pygame.quit()


def test_skipping_resolves_the_page_with_zero_records_but_still_advances():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._send_request()
        scene._send_request()
        skip = next(o for o in scene._pending.retry_options if o.key == "skip")

        scene._make_choose_retry(skip)()

        assert scene._pending is None
        assert scene.total_records() == 20
        scene._send_request()  # page 3 is still reachable after a skip
        assert scene.total_records() == 20 + 12
    finally:
        pygame.quit()


def test_finish_does_nothing_while_a_choice_is_still_pending():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda total: collected.append(total))
        scene._send_request()
        scene._send_request()

        scene._finish()

        assert collected == []
    finally:
        pygame.quit()


def test_finish_calls_on_complete_with_the_total_once_every_page_resolves():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda total: collected.append(total))
        scene._send_request()
        scene._send_request()
        wait_and_retry = next(o for o in scene._pending.retry_options if o.key == "wait_and_retry")
        scene._make_choose_retry(wait_and_retry)()
        scene._send_request()

        scene.buttons.buttons[0].on_activate()  # the button itself, not the private method

        assert collected == [20 + 15 + 12]
    finally:
        pygame.quit()


def test_context_records_one_action_and_one_evidence_item_on_finish():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(
            app,
            context=context,
            python_code="real_code_here",
            evidence_label_key="app.title",
        )
        scene._send_request()
        scene._send_request()
        wait_and_retry = next(o for o in scene._pending.retry_options if o.key == "wait_and_retry")
        scene._make_choose_retry(wait_and_retry)()
        scene._send_request()
        scene._finish()

        assert len(context.actions) == 1
        assert context.actions[0].python_code == "real_code_here"
        assert len(context.evidence) == 1
        assert context.evidence[0].detail == str(20 + 15 + 12)
    finally:
        pygame.quit()


def test_record_evidence_false_keeps_the_action_but_skips_the_evidence_item():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context, python_code="real_code_here", evidence_label_key="app.title", record_evidence=False)
        scene._send_request()
        scene._send_request()
        wait_and_retry = next(o for o in scene._pending.retry_options if o.key == "wait_and_retry")
        scene._make_choose_retry(wait_and_retry)()
        scene._send_request()
        scene._finish()

        assert len(context.actions) == 1
        assert context.evidence == ()
    finally:
        pygame.quit()


def test_skipped_status_key_adds_a_second_evidence_item_only_when_actually_skipped():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(
            app,
            context=context,
            evidence_label_key="app.title",
            skipped_status_key=_SKIPPED_STATUS,
            skipped_evidence_label_key="dialogue.continue_hint",
        )
        scene._send_request()
        scene._send_request()
        skip = next(o for o in scene._pending.retry_options if o.key == "skip")
        scene._make_choose_retry(skip)()
        scene._send_request()
        scene._finish()

        assert {e.label_key for e in context.evidence} == {"app.title", "dialogue.continue_hint"}
    finally:
        pygame.quit()


def test_no_skipped_evidence_when_the_page_was_actually_recovered():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(
            app,
            context=context,
            evidence_label_key="app.title",
            skipped_status_key=_SKIPPED_STATUS,
            skipped_evidence_label_key="dialogue.continue_hint",
        )
        scene._send_request()
        scene._send_request()
        wait_and_retry = next(o for o in scene._pending.retry_options if o.key == "wait_and_retry")
        scene._make_choose_retry(wait_and_retry)()
        scene._send_request()
        scene._finish()

        assert {e.label_key for e in context.evidence} == {"app.title"}
    finally:
        pygame.quit()


def test_sending_past_the_end_of_the_script_is_a_no_op():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._send_request()
        scene._send_request()
        wait_and_retry = next(o for o in scene._pending.retry_options if o.key == "wait_and_retry")
        scene._make_choose_retry(wait_and_retry)()
        scene._send_request()
        for _ in range(3):
            scene._send_request()  # exhausted - every extra call is a no-op

        assert len(scene.log) == 4  # page 1, the initial rate limit, the wait-and-retry resolution, page 3
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_at_any_point_in_the_sequence():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided, hint_key="common.back")
            scene.draw(app.logical_surface)
            scene._send_request()
            scene.draw(app.logical_surface)
            scene._send_request()  # now pending with 3 real choices
            scene.draw(app.logical_surface)
            retry_immediately = next(o for o in scene._pending.retry_options if o.key == "retry_immediately")
            scene._make_choose_retry(retry_immediately)()
            scene.draw(app.logical_surface)  # now pending with 2 real choices
            wait_and_retry = next(o for o in scene._pending.retry_options if o.key == "wait_and_retry")
            scene._make_choose_retry(wait_and_retry)()
            scene.draw(app.logical_surface)
            scene._send_request()
            scene.draw(app.logical_surface)  # exhausted - Finish
    finally:
        pygame.quit()

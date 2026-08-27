import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pandas as pd
import pygame

from data_science_arcade.app.game import App
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.join import JoinOption, JoinRequest
from data_science_arcade.ui.junction_scene import JunctionScene

LEFT_SCHEMA = Schema(columns=(ColumnSchema("key", "object"), ColumnSchema("amount", "float64")))
RIGHT_SCHEMA = Schema(columns=(ColumnSchema("key", "object"), ColumnSchema("label", "object")))

# "a" matches on both sides; "orphan_left" only exists on the left;
# "orphan_right" only exists on the right - exactly the shape needed to
# tell inner/left/right apart by row count.
LEFT_FRAME = pd.DataFrame([("a", 10.0), ("orphan_left", 5.0)], columns=["key", "amount"])
RIGHT_FRAME = pd.DataFrame([("a", "A"), ("orphan_right", "B")], columns=["key", "label"])

LEFT_DATASET = Dataset(name="left_table", frame=LEFT_FRAME, schema=LEFT_SCHEMA, history=())
RIGHT_DATASET = Dataset(name="right_table", frame=RIGHT_FRAME, schema=RIGHT_SCHEMA, history=())

REQUESTS = (
    JoinRequest(
        key="request_a",
        prompt_key="app.title",
        hint_key="common.back",
        options=(
            JoinOption("inner", "common.on", "inner"),
            JoinOption("left", "common.off", "left"),
        ),
    ),
    JoinRequest(
        key="request_b",
        prompt_key="app.title",
        hint_key="common.back",
        options=(
            JoinOption("inner", "common.on", "inner"),
            JoinOption("left", "common.off", "left"),
        ),
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda choices: None, **kwargs):
    return JunctionScene(app, "app.title", LEFT_DATASET, RIGHT_DATASET, "key", REQUESTS, on_complete, **kwargs)


def test_starts_on_the_first_request_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.request_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_computes_exactly_the_real_matching_pairs():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene._matches == [(0, 0)]
    finally:
        pygame.quit()


def test_choosing_an_option_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()

        assert scene.choices == {"request_a": "inner"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_inner_join_drops_both_orphans_left_join_keeps_the_left_orphan():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # inner
        assert scene._left_dropped(1, "inner") is True  # orphan_left dropped
        assert scene._right_dropped(1, "inner") is True  # orphan_right dropped
        assert scene._left_dropped(0, "inner") is False  # matched row never dropped

        scene.buttons.buttons[1].on_activate()  # left
        assert scene._left_dropped(1, "left") is False  # left orphan survives a left join
        assert scene._right_dropped(1, "left") is True  # right orphan still dropped
    finally:
        pygame.quit()


def test_next_advances_to_the_next_request_and_back_returns():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert scene.request_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()

        assert scene.request_index == 0
        assert scene.choices["request_a"] == "inner"
    finally:
        pygame.quit()


def test_finishing_the_last_request_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda choices: collected.append(choices))
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()

        scene.next_button.on_activate()

        assert collected == [{"request_a": "inner", "request_b": "left"}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_before_or_after_a_choice():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)  # before any choice - the "pick a join type" placeholder path
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)  # after a choice - the live result path
    finally:
        pygame.quit()

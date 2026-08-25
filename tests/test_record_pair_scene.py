import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.record_pair import RecordField, RecordPair
from data_science_arcade.ui.record_pair_scene import RecordPairScene

PAIRS = (
    RecordPair(
        key="pair_a",
        id_a="C-1",
        id_b="C-2",
        fields=(RecordField("app.title", "Jon Kowalski", "Jonathan Kowalski", matches=False),),
        hint_key="common.back",
    ),
    RecordPair(
        key="pair_b",
        id_a="C-3",
        id_b="C-4",
        fields=(RecordField("app.title", "Anna Nowak", "Piotr Nowak", matches=False),),
        hint_key="common.back",
    ),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda decisions: None, **kwargs):
    return RecordPairScene(app, "app.title", "app.title", PAIRS, on_complete, **kwargs)


def test_starts_on_the_first_pair_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.pair_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_merge_records_the_decision_and_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.merge_button.on_activate()

        assert scene.decisions == {"pair_a": "merge"}
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_advances_and_back_returns_with_the_decision_preserved():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.keep_separate_button.on_activate()
        scene.next_button.on_activate()

        assert scene.pair_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()

        assert scene.pair_index == 0
        assert scene.decisions["pair_a"] == "keep_separate"
    finally:
        pygame.quit()


def test_next_relabels_to_finish_on_the_last_pair():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.merge_button.on_activate()
        scene.next_button.on_activate()

        assert scene.next_button.label == app.localization.t("brief.finish")
    finally:
        pygame.quit()


def test_finishing_the_last_pair_calls_on_complete_with_every_decision():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda decisions: collected.append(decisions))
        scene.merge_button.on_activate()
        scene.next_button.on_activate()
        scene.keep_separate_button.on_activate()

        scene.next_button.on_activate()

        assert collected == [{"pair_a": "merge", "pair_b": "keep_separate"}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_at_either_pair():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            for index in range(len(PAIRS)):
                scene.pair_index = index
                scene._rebuild_buttons()
                scene.draw(app.logical_surface)
    finally:
        pygame.quit()

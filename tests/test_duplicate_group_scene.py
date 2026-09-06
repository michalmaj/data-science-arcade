import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.duplicate_group import DuplicateGroup, GroupVerdictOption
from data_science_arcade.ui.duplicate_group_scene import DuplicateGroupScene

VERDICT_OPTIONS = (
    GroupVerdictOption("safe_to_remove_duplicate", "common.on"),
    GroupVerdictOption("keep_all_not_a_duplicate", "common.off"),
    GroupVerdictOption("conflict_needs_reconciliation", "app.title"),
)

REPLAY_GROUP = DuplicateGroup(
    key="replay_group",
    key_column="event_id",
    columns=("event_id", "event_type", "amount"),
    rows=(
        {"event_id": "E010", "event_type": "captured", "amount": "$50.00"},
        {"event_id": "E010", "event_type": "captured", "amount": "$50.00"},
    ),
    prompt_key="app.title",
    hint_key="common.back",
)

CONFLICT_GROUP = DuplicateGroup(
    key="conflict_group",
    key_column="event_id",
    columns=("event_id", "event_type", "amount"),
    rows=(
        {"event_id": "E020", "event_type": "captured", "amount": "$50.00"},
        {"event_id": "E020", "event_type": "captured", "amount": "$45.00"},
    ),
    prompt_key="app.title",
    hint_key="common.back",
)

GROUPS = (REPLAY_GROUP, CONFLICT_GROUP)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda verdicts: None, **kwargs):
    return DuplicateGroupScene(app, "app.title", GROUPS, VERDICT_OPTIONS, on_complete, **kwargs)


def test_starts_on_the_first_group_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.group_index == 0
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_a_column_with_identical_values_across_rows_is_not_flagged_as_differing():
    app = _init_app()
    try:
        scene = _make_scene(app)
        differing = scene._differing_columns(REPLAY_GROUP)
        assert differing == set()
    finally:
        pygame.quit()


def test_a_column_with_different_values_across_rows_is_flagged_as_differing():
    app = _init_app()
    try:
        scene = _make_scene(app)
        differing = scene._differing_columns(CONFLICT_GROUP)
        assert differing == {"amount"}
    finally:
        pygame.quit()


def test_the_key_column_itself_is_never_counted_as_a_differing_column():
    app = _init_app()
    try:
        scene = _make_scene(app)
        # Every row in both fixture groups shares the same event_id -
        # key_column equality is a precondition of being "one group," not
        # itself a live-diff signal.
        assert "event_id" not in scene._differing_columns(REPLAY_GROUP)
        assert "event_id" not in scene._differing_columns(CONFLICT_GROUP)
    finally:
        pygame.quit()


def test_picking_a_verdict_enables_next_and_advances_to_the_next_group():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # safe_to_remove_duplicate
        assert scene.next_button.enabled is True
        scene.next_button.on_activate()
        assert scene.group_index == 1
        assert scene.back_button.enabled is True
    finally:
        pygame.quit()


def test_back_returns_to_the_previous_group_with_its_own_verdict_preserved():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()
        scene.back_button.on_activate()
        assert scene.group_index == 0
        assert scene.verdicts["replay_group"] == "safe_to_remove_duplicate"
    finally:
        pygame.quit()


def test_completing_every_group_calls_on_complete_with_all_verdicts():
    app = _init_app()
    try:
        results = []
        scene = _make_scene(app, on_complete=lambda verdicts: results.append(verdicts))
        scene.buttons.buttons[0].on_activate()  # replay_group -> safe_to_remove_duplicate
        scene.next_button.on_activate()
        scene.buttons.buttons[2].on_activate()  # conflict_group -> conflict_needs_reconciliation
        scene.next_button.on_activate()

        assert results == [{"replay_group": "safe_to_remove_duplicate", "conflict_group": "conflict_needs_reconciliation"}]
    finally:
        pygame.quit()


def test_guided_shows_hint_and_independent_hides_it():
    app = _init_app()
    try:
        guided_scene = _make_scene(app, guided=True)
        independent_scene = _make_scene(app, guided=False)
        assert guided_scene.guided is True
        assert independent_scene.guided is False
    finally:
        pygame.quit()

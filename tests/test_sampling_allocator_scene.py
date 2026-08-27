import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.lessons.framework.sampling import SamplingGroup
from data_science_arcade.ui.sampling_allocator_scene import SamplingAllocatorScene

GROUPS = (
    SamplingGroup(key="group_a", label_key="app.title"),
    SamplingGroup(key="group_b", label_key="app.title"),
)
TOTAL_BUDGET = 20
STEP = 10


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda allocation: None, **kwargs):
    return SamplingAllocatorScene(app, "app.title", "app.title", GROUPS, TOTAL_BUDGET, STEP, on_complete, **kwargs)


def test_starts_with_every_group_at_zero_and_confirm_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.allocation == {"group_a": 0, "group_b": 0}
        assert scene.confirm_button.enabled is False
        assert scene.minus_buttons["group_a"].enabled is False
        assert scene.plus_buttons["group_a"].enabled is True
    finally:
        pygame.quit()


def test_incrementing_a_group_reduces_the_remaining_budget():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.plus_buttons["group_a"].on_activate()

        assert scene.allocation["group_a"] == STEP
        assert scene._remaining() == TOTAL_BUDGET - STEP
        assert scene.minus_buttons["group_a"].enabled is True
    finally:
        pygame.quit()


def test_decrementing_at_zero_is_a_no_op():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene._make_decrement("group_a")()

        assert scene.allocation["group_a"] == 0
    finally:
        pygame.quit()


def test_plus_buttons_disable_everywhere_once_the_budget_is_fully_spent():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.plus_buttons["group_a"].on_activate()
        scene.plus_buttons["group_a"].on_activate()  # group_a now holds the whole budget

        assert scene._remaining() == 0
        assert scene.plus_buttons["group_a"].enabled is False
        assert scene.plus_buttons["group_b"].enabled is False
    finally:
        pygame.quit()


def test_confirm_does_nothing_before_the_full_budget_is_allocated():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda allocation: collected.append(allocation))
        scene.plus_buttons["group_a"].on_activate()

        scene._confirm()

        assert collected == []
    finally:
        pygame.quit()


def test_confirm_calls_on_complete_with_the_full_allocation_once_budget_is_spent():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda allocation: collected.append(allocation))
        scene.plus_buttons["group_a"].on_activate()
        scene.plus_buttons["group_b"].on_activate()

        scene.confirm_button.on_activate()

        assert collected == [{"group_a": STEP, "group_b": STEP}]
    finally:
        pygame.quit()


def test_draw_does_not_crash_guided_or_not_at_any_allocation_level():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided, hint_key="common.back")
            scene.draw(app.logical_surface)
            scene.plus_buttons["group_a"].on_activate()
            scene.draw(app.logical_surface)
            scene.plus_buttons["group_b"].on_activate()
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_default_diagnostic_draws_nothing_extra():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.diagnostic(GROUPS[0], 0) is None
        assert scene.diagnostic(GROUPS[0], STEP) is None
    finally:
        pygame.quit()


def test_a_custom_diagnostic_is_called_with_the_groups_own_allocation():
    app = _init_app()
    try:
        calls = []

        def diagnostic(group, allocated):
            calls.append((group.key, allocated))
            return f"{allocated} units", allocated > STEP

        scene = _make_scene(app, diagnostic=diagnostic, row_spacing=90)
        scene.plus_buttons["group_a"].on_activate()
        scene.draw(app.logical_surface)

        assert ("group_a", STEP) in calls
        assert ("group_b", 0) in calls
    finally:
        pygame.quit()

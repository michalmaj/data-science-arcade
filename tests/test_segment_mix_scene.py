import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_science_arcade.app.game import App
from data_science_arcade.core.display import LOGICAL_SIZE
from data_science_arcade.ui.segment_mix_scene import DimensionOption, SegmentMixScene, SegmentRow
from data_science_arcade.workbench.context import LessonContext

DEVICE_OPTION = DimensionOption(
    "device",
    "lesson.l15.segment_mix.dimension.device",
    (
        SegmentRow("mobile", "lesson.l15.segment_mix.device.mobile", 20.0, 42.0, 70.0, 38.0),
        SegmentRow("desktop", "lesson.l15.segment_mix.device.desktop", 80.0, 25.0, 30.0, 22.0),
    ),
    mirror_code="device_rates = sessions.groupby(['period', 'device'])['converted'].mean().unstack()",
    evidence_keys=("lesson.l15.evidence.device_rates", "lesson.l15.evidence.device_share"),
)
REGION_OPTION = DimensionOption(
    "region",
    "lesson.l15.segment_mix.dimension.region",
    (
        SegmentRow("EU", "lesson.l15.segment_mix.region.eu", 50.0, 28.4, 50.0, 33.2),
        SegmentRow("US", "lesson.l15.segment_mix.region.us", 50.0, 28.4, 50.0, 33.2),
    ),
    mirror_code="region_rates = sessions.groupby(['period', 'region'])['converted'].mean().unstack()",
    evidence_keys=("lesson.l15.evidence.region_null",),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _surface() -> pygame.Surface:
    return pygame.Surface(LOGICAL_SIZE)


def test_picker_mode_shows_both_dimensions_and_picking_enables_finish():
    app = _init_app()
    try:
        context = LessonContext()
        scene = SegmentMixScene(
            app, "lesson.l15.dimension_investigation.title", "lesson.l15.dimension_investigation.ask",
            (REGION_OPTION, DEVICE_OPTION), lambda c: None, context,
        )
        assert scene.finish_button.enabled is False
        scene.buttons.buttons[1].on_activate()  # device
        assert scene.choice == "device"
        assert scene.finish_button.enabled is True
    finally:
        pygame.quit()


def test_finish_records_one_action_and_the_options_own_evidence_items():
    app = _init_app()
    try:
        context = LessonContext()
        completed = []
        scene = SegmentMixScene(
            app, "lesson.l15.dimension_investigation.title", "lesson.l15.dimension_investigation.ask",
            (REGION_OPTION, DEVICE_OPTION), completed.append, context,
        )
        scene.buttons.buttons[1].on_activate()  # device
        scene.finish_button.on_activate()

        assert completed == ["device"]
        assert len(context.actions) == 1
        assert context.actions[0].python_code == DEVICE_OPTION.mirror_code
        evidence_keys = {item.label_key for item in context.evidence}
        assert evidence_keys == {"lesson.l15.evidence.device_rates", "lesson.l15.evidence.device_share"}
    finally:
        pygame.quit()


def test_picking_both_dimensions_across_two_instances_keeps_both_mirror_definitions():
    # Regression: the Mirror action used to be keyed by a fixed,
    # scene-instance-level string - a second SegmentMixScene showing a
    # different dimension would silently overwrite the first one's own
    # real groupby definition in place. Both must now survive as two
    # separate, real actions.
    app = _init_app()
    try:
        context = LessonContext()
        region_scene = SegmentMixScene(
            app, "t", "a", (REGION_OPTION,), lambda c: None, context,
        )
        region_scene.finish_button.on_activate()

        device_scene = SegmentMixScene(
            app, "t", "a", (DEVICE_OPTION,), lambda c: None, context,
        )
        device_scene.finish_button.on_activate()

        codes = {action.python_code for action in context.actions}
        assert DEVICE_OPTION.mirror_code in codes
        assert REGION_OPTION.mirror_code in codes
        assert len(context.actions) == 2
    finally:
        pygame.quit()


def test_pinned_single_dimension_mode_has_no_picker_and_is_preselected():
    app = _init_app()
    try:
        context = LessonContext()
        scene = SegmentMixScene(
            app, "t", "a", (DEVICE_OPTION,), lambda c: None, context,
        )
        assert scene.choice == "device"
        assert scene.finish_button.enabled is True
        # Only the Finish button exists - no picker buttons for a single option.
        assert len(scene.buttons.buttons) == 1
    finally:
        pygame.quit()


def test_table_renders_without_error_for_both_dimensions():
    app = _init_app()
    try:
        context = LessonContext()
        scene = SegmentMixScene(
            app, "lesson.l15.dimension_investigation.title", "lesson.l15.dimension_investigation.ask",
            (REGION_OPTION, DEVICE_OPTION), lambda c: None, context,
        )
        surface = _surface()
        scene.draw(surface)  # no selection yet
        scene.buttons.buttons[0].on_activate()
        scene.draw(surface)
        scene.buttons.buttons[1].on_activate()
        scene.draw(surface)
    finally:
        pygame.quit()


def test_initial_choice_seeds_a_resumed_instance():
    app = _init_app()
    try:
        context = LessonContext()
        scene = SegmentMixScene(
            app, "t", "a", (REGION_OPTION, DEVICE_OPTION), lambda c: None, context, initial_choice="device",
        )
        assert scene.choice == "device"
        assert scene.finish_button.enabled is True
    finally:
        pygame.quit()

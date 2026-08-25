import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pandas as pd
import pygame

from data_science_arcade.app.game import App
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.framework.repair import RepairIssue, RepairOption
from data_science_arcade.ui.workbench_scene import DataView, WorkbenchScene, WorkbenchTab

SCHEMA = Schema(
    columns=(
        ColumnSchema("id", "int64", description="Row identifier"),
        ColumnSchema("code", "object"),
    )
)

CORRECT_OPTION = RepairOption(
    "upper", "app.title", lambda frame: frame.assign(code=frame["code"].str.upper()), python_code="x = x.upper()"
)
WRONG_OPTION = RepairOption("lower", "app.title", lambda frame: frame.assign(code=frame["code"].str.lower()))
ISSUES = (RepairIssue(column="code", prompt_key="app.title", options=(CORRECT_OPTION, WRONG_OPTION), hint_key="common.back"),)


def make_dataset() -> Dataset:
    frame = pd.DataFrame({"id": [1, 2, 3], "code": ["a1", "A1", "a1"]})
    return Dataset(name="things", frame=frame, schema=SCHEMA)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, on_complete=lambda resolution: None, **kwargs):
    return WorkbenchScene(app, make_dataset(), ISSUES, on_complete, **kwargs)


def test_starts_on_the_data_tab_showing_the_table_view():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.active_tab is WorkbenchTab.DATA
        assert scene.data_view is DataView.TABLE
    finally:
        pygame.quit()


def test_clicking_a_tab_button_switches_the_active_tab():
    app = _init_app()
    try:
        scene = _make_scene(app)
        pipeline_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("workbench.tab.pipeline"))

        pipeline_button.on_activate()

        assert scene.active_tab is WorkbenchTab.PIPELINE
    finally:
        pygame.quit()


def test_focus_stays_on_the_active_tab_after_switching_not_the_first_tab():
    app = _init_app()
    try:
        scene = _make_scene(app)
        pipeline_index = list(WorkbenchTab).index(WorkbenchTab.PIPELINE)
        pipeline_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("workbench.tab.pipeline"))

        pipeline_button.on_activate()

        assert scene.buttons.focus_index == pipeline_index
    finally:
        pygame.quit()


def test_data_view_buttons_only_exist_on_the_data_tab():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.table_view_button is not None
        assert scene.schema_view_button is not None

        scene.active_tab = WorkbenchTab.PIPELINE
        scene._rebuild_buttons()

        assert scene.table_view_button is None
        assert scene.schema_view_button is None
    finally:
        pygame.quit()


def test_switching_to_the_schema_view_and_back():
    app = _init_app()
    try:
        scene = _make_scene(app)
        schema_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("workbench.data.view_schema"))

        schema_button.on_activate()
        assert scene.data_view is DataView.SCHEMA

        table_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("workbench.data.view_table"))
        table_button.on_activate()
        assert scene.data_view is DataView.TABLE
    finally:
        pygame.quit()


def test_a_flagged_columns_cells_are_clickable_and_open_the_picker():
    app = _init_app()
    try:
        scene = _make_scene(app)
        flagged_cell = next(b for b in scene.buttons.buttons if b.label in ("a1", "A1"))

        flagged_cell.on_activate()

        assert scene.active_issue is ISSUES[0]
    finally:
        pygame.quit()


def test_choosing_a_picker_option_applies_it_and_resolves_the_issue():
    app = _init_app()
    try:
        scene = _make_scene(app)
        flagged_cell = next(b for b in scene.buttons.buttons if b.label in ("a1", "A1"))
        flagged_cell.on_activate()

        scene.picker_buttons["upper"].on_activate()

        assert scene.resolution == {"code": "upper"}
        assert scene.active_issue is None
        assert list(scene.dataset.frame["code"]) == ["A1", "A1", "A1"]
        assert scene.dataset.history[-1].name == "code_upper"
    finally:
        pygame.quit()


def test_a_wrong_choice_still_resolves_the_issue_non_punitively():
    app = _init_app()
    try:
        scene = _make_scene(app)
        flagged_cell = next(b for b in scene.buttons.buttons if b.label in ("a1", "A1"))
        flagged_cell.on_activate()

        scene.picker_buttons["lower"].on_activate()

        assert scene.resolution == {"code": "lower"}
        assert list(scene.dataset.frame["code"]) == ["a1", "a1", "a1"]
    finally:
        pygame.quit()


def test_resolved_columns_are_no_longer_clickable():
    app = _init_app()
    try:
        scene = _make_scene(app)
        flagged_cell = next(b for b in scene.buttons.buttons if b.label in ("a1", "A1"))
        flagged_cell.on_activate()
        scene.picker_buttons["upper"].on_activate()

        # every remaining button is chrome (tabs/view toggles/continue), not a cell button
        assert not any(b.label in ("a1", "A1") for b in scene.buttons.buttons)
    finally:
        pygame.quit()


def test_continue_is_disabled_until_every_issue_is_resolved_then_calls_on_complete():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda resolution: collected.append(resolution))
        assert scene.continue_button.enabled is False

        flagged_cell = next(b for b in scene.buttons.buttons if b.label in ("a1", "A1"))
        flagged_cell.on_activate()
        scene.picker_buttons["upper"].on_activate()

        assert scene.continue_button.enabled is True
        scene.continue_button.on_activate()

        assert collected == [{"code": "upper"}]
    finally:
        pygame.quit()


def test_escape_is_not_handled_here_pausable_intercepts_it_first():
    app = _init_app()
    try:
        scene = _make_scene(app)
        before = scene.active_tab

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        assert scene.active_tab is before  # no crash, no special handling - just ignored here
    finally:
        pygame.quit()


def test_draw_does_not_crash_for_any_tab_or_data_view():
    app = _init_app()
    try:
        scene = _make_scene(app)

        for tab in WorkbenchTab:
            scene.active_tab = tab
            scene._rebuild_buttons()
            scene.draw(app.logical_surface)

        scene.active_tab = WorkbenchTab.DATA
        for view in DataView:
            scene.data_view = view
            scene._rebuild_buttons()
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_draw_does_not_crash_while_the_picker_is_open():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            flagged_cell = next(b for b in scene.buttons.buttons if b.label in ("a1", "A1"))
            flagged_cell.on_activate()
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_more_rows_than_the_table_shows():
    app = _init_app()
    try:
        frame = pd.DataFrame({"id": range(1, 21), "code": [f"a{i}" for i in range(1, 21)]})
        big_dataset = Dataset(name="big", frame=frame, schema=SCHEMA)
        scene = WorkbenchScene(app, big_dataset, ISSUES, lambda resolution: None)

        scene.draw(app.logical_surface)
    finally:
        pygame.quit()

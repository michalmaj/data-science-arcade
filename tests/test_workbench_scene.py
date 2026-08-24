import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pandas as pd
import pygame

from data_science_arcade.app.game import App
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.ui.workbench_scene import DataView, WorkbenchScene, WorkbenchTab

SCHEMA = Schema(
    columns=(
        ColumnSchema("id", "int64", description="Row identifier"),
        ColumnSchema("value", "int64", nullable=True),
    )
)


def make_dataset() -> Dataset:
    frame = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
    return Dataset(name="things", frame=frame, schema=SCHEMA)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def test_starts_on_the_data_tab_showing_the_table_view():
    app = _init_app()
    try:
        scene = WorkbenchScene(app, make_dataset())
        assert scene.active_tab is WorkbenchTab.DATA
        assert scene.data_view is DataView.TABLE
    finally:
        pygame.quit()


def test_the_data_tab_has_extra_view_toggle_buttons_other_tabs_do_not():
    app = _init_app()
    try:
        scene = WorkbenchScene(app, make_dataset())
        data_tab_button_count = len(scene.buttons.buttons)

        scene.active_tab = WorkbenchTab.PIPELINE
        scene._rebuild_buttons()

        assert len(scene.buttons.buttons) == data_tab_button_count - 2
    finally:
        pygame.quit()


def test_clicking_a_tab_button_switches_the_active_tab():
    app = _init_app()
    try:
        scene = WorkbenchScene(app, make_dataset())
        pipeline_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("workbench.tab.pipeline"))

        pipeline_button.on_activate()

        assert scene.active_tab is WorkbenchTab.PIPELINE
    finally:
        pygame.quit()


def test_focus_stays_on_the_active_tab_after_switching_not_the_first_tab():
    app = _init_app()
    try:
        scene = WorkbenchScene(app, make_dataset())
        pipeline_index = list(WorkbenchTab).index(WorkbenchTab.PIPELINE)
        pipeline_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("workbench.tab.pipeline"))

        pipeline_button.on_activate()

        assert scene.buttons.focus_index == pipeline_index
        assert scene.buttons.buttons[scene.buttons.focus_index] is scene.buttons.buttons[pipeline_index]
    finally:
        pygame.quit()


def test_data_view_buttons_only_exist_on_the_data_tab():
    app = _init_app()
    try:
        scene = WorkbenchScene(app, make_dataset())
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
        scene = WorkbenchScene(app, make_dataset())
        schema_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("workbench.data.view_schema"))

        schema_button.on_activate()
        assert scene.data_view is DataView.SCHEMA

        table_button = next(b for b in scene.buttons.buttons if b.label == app.localization.t("workbench.data.view_table"))
        table_button.on_activate()
        assert scene.data_view is DataView.TABLE
    finally:
        pygame.quit()


def test_escape_pops_the_scene():
    app = _init_app()
    try:
        previous = app.scenes.current
        scene = WorkbenchScene(app, make_dataset())
        app.scenes.push(scene)

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        assert app.scenes.current is previous
    finally:
        pygame.quit()


def test_draw_does_not_crash_for_any_tab_or_data_view():
    app = _init_app()
    try:
        dataset = make_dataset().then("doubled", lambda f: f.assign(value=f["value"] * 2), python_code="x = x * 2")
        scene = WorkbenchScene(app, dataset)

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


def test_draw_does_not_crash_with_empty_history_or_python_mirror():
    app = _init_app()
    try:
        scene = WorkbenchScene(app, make_dataset())  # no .then() calls: empty history, empty python_mirror

        scene.active_tab = WorkbenchTab.PIPELINE
        scene._rebuild_buttons()
        scene.draw(app.logical_surface)

        scene.active_tab = WorkbenchTab.PYTHON
        scene._rebuild_buttons()
        scene.draw(app.logical_surface)
    finally:
        pygame.quit()


def test_draw_does_not_crash_with_more_rows_than_the_table_shows():
    app = _init_app()
    try:
        frame = pd.DataFrame({"id": range(1, 21), "value": range(1, 21)})
        big_dataset = Dataset(name="big", frame=frame, schema=SCHEMA)
        scene = WorkbenchScene(app, big_dataset)

        scene.draw(app.logical_surface)
    finally:
        pygame.quit()

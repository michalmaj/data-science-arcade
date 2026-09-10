import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.lessons.l13_join_junction.orders import (
    JOIN1_INNER_ROW_COUNT,
    JOIN1_LEFT_ROW_COUNT,
    JOIN1_OUTER_ROW_COUNT,
    generate_active_promotions,
    generate_customers,
    generate_orders,
)
from data_science_arcade.ui.join_builder_scene import JoinBuilderScene, JoinTypeOption
from data_science_arcade.workbench.context import LessonContext

ORDERS = generate_orders()
CUSTOMERS = generate_customers()
ACTIVE_PROMOTIONS = generate_active_promotions()

JOIN_TYPE_OPTIONS = (
    JoinTypeOption("inner", "app.title", "inner", right_dataset=CUSTOMERS),
    JoinTypeOption("left", "common.on", "left", right_dataset=CUSTOMERS),
    JoinTypeOption("outer", "common.off", "outer", right_dataset=CUSTOMERS),
)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, left=None, options=None, context=None, on_complete=lambda choice, ok: None, **kwargs):
    return JoinBuilderScene(
        app,
        "app.title",
        left if left is not None else ORDERS,
        "customer_id",
        options if options is not None else JOIN_TYPE_OPTIONS,
        on_complete,
        context or LessonContext(),
        **kwargs,
    )


def test_starts_with_no_choice_and_continue_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.choice is None
        assert scene.continue_button.enabled is False
    finally:
        pygame.quit()


def test_picking_a_join_type_enables_continue():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[1].on_activate()  # "left"
        assert scene.choice == "left"
        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


@pytest.mark.parametrize(
    "index,expected_total",
    [(0, JOIN1_INNER_ROW_COUNT), (1, JOIN1_LEFT_ROW_COUNT), (2, JOIN1_OUTER_ROW_COUNT)],
)
def test_each_join_type_computes_the_real_row_count_live(index, expected_total):
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[index].on_activate()
        merged, error = scene._attempt_merge()
        assert error is None
        assert len(merged) == expected_total
        assert "_merge" in merged.columns
    finally:
        pygame.quit()


def test_the_merge_indicator_breakdown_is_real_and_computed():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[1].on_activate()  # left
        merged, _error = scene._attempt_merge()
        counts = merged["_merge"].value_counts()
        assert int(counts.get("both", 0)) == 108
        assert int(counts.get("left_only", 0)) == 12
        assert int(counts.get("right_only", 0)) == 0
    finally:
        pygame.quit()


def test_finishing_records_a_real_assignable_python_mirror_line():
    app = _init_app()
    try:
        context = LessonContext()
        recorded = []
        scene = _make_scene(app, context=context, on_complete=lambda choice, ok: recorded.append((choice, ok)))
        scene.buttons.buttons[1].on_activate()  # left
        scene.continue_button.on_activate()

        assert recorded == [("left", True)]
        mirror = context.python_mirror()
        assert mirror == "result = orders.merge(customers, on='customer_id', how='left', indicator=True)"
    finally:
        pygame.quit()


def test_a_revision_seeded_with_initial_choice_starts_pre_selected():
    app = _init_app()
    try:
        scene = _make_scene(app, initial_choice="inner")
        assert scene.choice == "inner"
        assert scene.continue_button.enabled is True
    finally:
        pygame.quit()


def test_output_variable_name_and_mirror_action_key_are_threaded_through():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context, output_variable_name="join1_result", mirror_action_key="join1_pipeline")
        scene.buttons.buttons[1].on_activate()
        scene.continue_button.on_activate()
        assert context.python_mirror().startswith("join1_result = ")
        assert context._actions[0].key == "join1_pipeline"
    finally:
        pygame.quit()


def test_a_revision_updates_the_same_mirror_slot_in_place():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context, mirror_action_key="join1_pipeline")
        scene.buttons.buttons[0].on_activate()  # inner
        scene.continue_button.on_activate()
        assert len(context._actions) == 1

        revision = _make_scene(app, context=context, mirror_action_key="join1_pipeline", initial_choice="inner")
        revision.buttons.buttons[1].on_activate()  # left
        revision.continue_button.on_activate()

        assert len(context._actions) == 1  # updated in place, not appended
        assert "how='left'" in context.python_mirror()
    finally:
        pygame.quit()


# --- Per-option right_dataset - different real strategies against the
# same left table, not just a different `how` value ------------------


def test_sibling_options_can_target_genuinely_different_right_datasets():
    app = _init_app()
    try:
        promo_per_customer_frame = ACTIVE_PROMOTIONS.frame.groupby("customer_id", as_index=False).agg(
            active_promotion_count=("promotion_code", "size")
        )
        promo_per_customer = Dataset(
            name="promo_per_customer",
            frame=promo_per_customer_frame,
            schema=Schema(columns=(ColumnSchema("customer_id", "object"), ColumnSchema("active_promotion_count", "int64"))),
        )
        options = (
            JoinTypeOption("preaggregate_first", "app.title", "left", right_dataset=promo_per_customer, validate="many_to_one"),
            JoinTypeOption("join_raw_directly", "common.on", "left", right_dataset=ACTIVE_PROMOTIONS),
        )
        scene = _make_scene(app, options=options)

        scene.buttons.buttons[0].on_activate()  # preaggregate_first
        merged, error = scene._attempt_merge()
        assert error is None
        assert len(merged) == 120

        scene.buttons.buttons[1].on_activate()  # join_raw_directly
        merged, error = scene._attempt_merge()
        assert error is None
        assert len(merged) == 147
    finally:
        pygame.quit()


def test_preamble_python_code_is_prepended_to_the_recorded_mirror_action():
    app = _init_app()
    try:
        promo_per_customer_frame = ACTIVE_PROMOTIONS.frame.groupby("customer_id", as_index=False).agg(
            active_promotion_count=("promotion_code", "size")
        )
        promo_per_customer = Dataset(
            name="promo_per_customer",
            frame=promo_per_customer_frame,
            schema=Schema(columns=(ColumnSchema("customer_id", "object"), ColumnSchema("active_promotion_count", "int64"))),
        )
        options = (
            JoinTypeOption(
                "preaggregate_first",
                "app.title",
                "left",
                right_dataset=promo_per_customer,
                validate="many_to_one",
                preamble_python_code="promo_per_customer = active_promotions.groupby('customer_id', as_index=False).agg(active_promotion_count=('promotion_code', 'size'))",
            ),
        )
        context = LessonContext()
        scene = _make_scene(app, options=options, context=context, output_variable_name="final")
        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()

        mirror = context.python_mirror()
        assert mirror.startswith("promo_per_customer = active_promotions.groupby(")
        assert "final = orders.merge(promo_per_customer" in mirror

        namespace = {"orders": ORDERS.frame, "active_promotions": ACTIVE_PROMOTIONS.frame}
        exec(mirror, namespace)
        assert len(namespace["final"]) == 120
    finally:
        pygame.quit()


# --- validate= - a real, controlled failure, never a crash -----------------


def test_a_many_to_one_violation_is_caught_and_shown_as_a_distinct_state_not_a_crash():
    app = _init_app()
    try:
        raw_options = (JoinTypeOption("left_raw", "app.title", "left", right_dataset=ACTIVE_PROMOTIONS, validate="many_to_one"),)
        scene = JoinBuilderScene(app, "app.title", ORDERS, "customer_id", raw_options, lambda choice, ok: None, LessonContext())
        scene.buttons.buttons[0].on_activate()
        merged, error = scene._attempt_merge()
        assert merged is None
        assert error is not None
        assert "many-to-one" in error.lower() or "not unique" in error.lower()
    finally:
        pygame.quit()


def test_a_caught_validation_failure_still_lets_the_scene_finish():
    app = _init_app()
    try:
        raw_options = (JoinTypeOption("left_raw", "app.title", "left", right_dataset=ACTIVE_PROMOTIONS, validate="many_to_one"),)
        context = LessonContext()
        recorded = []
        scene = JoinBuilderScene(
            app, "app.title", ORDERS, "customer_id", raw_options, lambda choice, ok: recorded.append((choice, ok)), context
        )
        scene.buttons.buttons[0].on_activate()
        scene.continue_button.on_activate()  # must not raise

        assert recorded == [("left_raw", False)]
        mirror = context.python_mirror()
        assert "try:" in mirror
        assert "except pd.errors.MergeError as exc:" in mirror
        assert "=" not in mirror.split("try:")[0]  # no bare assignment before the try
    finally:
        pygame.quit()


def test_a_real_cardinality_that_satisfies_validate_succeeds_normally():
    app = _init_app()
    try:
        promo_per_customer_frame = ACTIVE_PROMOTIONS.frame.groupby("customer_id", as_index=False).agg(
            active_promotion_count=("promotion_code", "size")
        )
        right = Dataset(
            name="promo_per_customer",
            frame=promo_per_customer_frame,
            schema=Schema(columns=(ColumnSchema("customer_id", "object"), ColumnSchema("active_promotion_count", "int64"))),
        )
        raw_options = (JoinTypeOption("left_repaired", "app.title", "left", right_dataset=right, validate="many_to_one"),)
        scene = JoinBuilderScene(app, "app.title", ORDERS, "customer_id", raw_options, lambda choice, ok: None, LessonContext())
        scene.buttons.buttons[0].on_activate()
        merged, error = scene._attempt_merge()
        assert error is None
        assert len(merged) == 120
    finally:
        pygame.quit()


def test_the_scene_draws_safely_with_the_widest_real_result(headless_display=None):
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[2].on_activate()  # outer - the widest real result, 140 rows
        surface = pygame.Surface(app.size)
        scene.draw(surface)  # must not raise
    finally:
        pygame.quit()


def test_the_scene_draws_safely_with_an_explanation_and_a_validation_failure(headless_display=None):
    app = _init_app()
    try:
        raw_options = (
            JoinTypeOption(
                "left_raw",
                "app.title",
                "left",
                right_dataset=ACTIVE_PROMOTIONS,
                validate="many_to_one",
                validate_explanation_key="app.title",
            ),
        )
        scene = JoinBuilderScene(app, "app.title", ORDERS, "customer_id", raw_options, lambda choice, ok: None, LessonContext())
        scene.buttons.buttons[0].on_activate()
        surface = pygame.Surface(app.size)
        scene.draw(surface)  # must not raise, must not overlap illegibly
    finally:
        pygame.quit()

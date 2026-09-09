import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from data_science_arcade.app.game import App
from data_science_arcade.lessons.l12_groupby_kitchen.orders import generate_orders
from data_science_arcade.ui.aggregation_builder_scene import AggregationBuilderScene, GroupByOption, MetricOption, MetricSlot
from data_science_arcade.workbench.context import LessonContext

GROUP_BY_OPTIONS = (
    GroupByOption("by_customer", "app.title", "customer_id"),
    GroupByOption("by_store", "common.on", "store_id"),
)
ORDERS_SLOT = MetricSlot(
    key="orders",
    label_key="app.title",
    options=(
        MetricOption("wrong_sum_revenue", "common.off", "revenue", "sum"),
        MetricOption("count_order_id", "common.on", "order_id", "size"),
    ),
)
REVENUE_SLOT = MetricSlot(
    key="revenue",
    label_key="app.title",
    options=(
        MetricOption("sum_revenue", "common.on", "revenue", "sum"),
        MetricOption("wrong_mean_revenue", "common.off", "revenue", "mean"),
    ),
)
METRIC_SLOTS = (ORDERS_SLOT, REVENUE_SLOT)


def _init_app() -> App:
    app = App()
    app.init()
    return app


def _make_scene(app, context=None, on_complete=lambda g, m: None, **kwargs):
    return AggregationBuilderScene(
        app, "app.title", generate_orders(), GROUP_BY_OPTIONS, METRIC_SLOTS, on_complete, context or LessonContext(), **kwargs
    )


def test_starts_on_the_group_by_step_with_next_disabled():
    app = _init_app()
    try:
        scene = _make_scene(app)
        assert scene.step_index == 0
        assert scene._is_group_by_step() is True
        assert scene.next_button.enabled is False
        assert scene.back_button.enabled is False
    finally:
        pygame.quit()


def test_choosing_a_group_by_option_enables_next():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[1].on_activate()
        assert scene.group_by_choice == "by_store"
        assert scene.next_button.enabled is True
    finally:
        pygame.quit()


def test_next_advances_through_every_metric_slot_and_back_returns():
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[1].on_activate()
        scene.next_button.on_activate()
        assert scene.step_index == 1
        assert scene.back_button.enabled is True

        scene.back_button.on_activate()
        assert scene.step_index == 0
        assert scene.group_by_choice == "by_store"
    finally:
        pygame.quit()


def test_finishing_the_last_step_calls_on_complete_with_the_full_choices():
    app = _init_app()
    try:
        collected = []
        scene = _make_scene(app, on_complete=lambda g, m: collected.append((g, m)))
        scene.buttons.buttons[1].on_activate()  # group_by = by_store
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()  # orders slot: correct
        scene.next_button.on_activate()
        scene.buttons.buttons[0].on_activate()  # revenue slot: correct (index 0 here)
        scene.next_button.on_activate()

        assert collected == [("by_store", {"orders": "count_order_id", "revenue": "sum_revenue"})]
    finally:
        pygame.quit()


def test_finishing_records_exactly_one_real_python_mirror_action():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context)
        scene.buttons.buttons[1].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[1].on_activate()
        scene.next_button.on_activate()
        scene.buttons.buttons[0].on_activate()
        scene.next_button.on_activate()

        assert len(context.actions) == 1
        assert "groupby('store_id'" in context.actions[0].python_code
        assert "orders=('order_id', 'size')" in context.actions[0].python_code
        assert "revenue=('revenue', 'sum')" in context.actions[0].python_code
        assert context.evidence == ()
    finally:
        pygame.quit()


def test_toggling_options_never_records_an_action_or_evidence_on_its_own():
    app = _init_app()
    try:
        context = LessonContext()
        scene = _make_scene(app, context=context)
        scene.buttons.buttons[0].on_activate()
        scene.buttons.buttons[1].on_activate()
        assert context.actions == ()
        assert context.evidence == ()
    finally:
        pygame.quit()


def test_seeding_with_initial_choices_prefills_every_step_but_keeps_it_changeable():
    app = _init_app()
    try:
        scene = _make_scene(app, initial_group_by="by_store", initial_choices={"orders": "count_order_id", "revenue": "sum_revenue"})
        assert scene.group_by_choice == "by_store"
        assert scene.choices == {"orders": "count_order_id", "revenue": "sum_revenue"}
        assert scene.next_button.enabled is True

        # Still fully re-visitable: changing the pre-filled group key works.
        scene.buttons.buttons[0].on_activate()
        assert scene.group_by_choice == "by_customer"
    finally:
        pygame.quit()


def test_a_wrong_high_cardinality_group_by_does_not_overflow_and_reports_the_real_count():
    # P0: a wrong group key (customer_id here) must never crash or
    # silently substitute the canonical answer - the preview must show
    # the REAL group count for whatever was actually picked.
    app = _init_app()
    try:
        scene = _make_scene(app)
        scene.buttons.buttons[0].on_activate()  # by_customer
        frame, total, error = scene._compute_preview()
        assert error is None
        assert frame is not None
        assert total == generate_orders().frame["customer_id"].nunique()
        assert total > 5  # genuinely high cardinality relative to MAX_PREVIEW_ROWS
        scene.draw(app.logical_surface)  # must not raise
    finally:
        pygame.quit()


@pytest.mark.parametrize("group_by", GROUP_BY_OPTIONS)
@pytest.mark.parametrize("slot", METRIC_SLOTS)
def test_every_reachable_metric_option_computes_without_raising(group_by, slot):
    dataset = generate_orders()
    for option in slot.options:
        grouped = dataset.frame.groupby(group_by.column, as_index=False)
        grouped.agg(**{slot.key: (option.column, option.func)})  # must not raise


def test_draw_does_not_crash_at_any_step_guided_or_not():
    app = _init_app()
    try:
        for guided in (True, False):
            scene = _make_scene(app, guided=guided)
            scene.draw(app.logical_surface)
            scene.buttons.buttons[1].on_activate()
            scene.next_button.on_activate()
            scene.draw(app.logical_surface)
            scene.buttons.buttons[0].on_activate()
            scene.draw(app.logical_surface)
    finally:
        pygame.quit()

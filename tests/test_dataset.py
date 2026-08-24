import pandas as pd
import pytest

from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema

SIMPLE_SCHEMA = Schema(columns=(ColumnSchema("id", "int64"), ColumnSchema("value", "int64")))


def make_dataset() -> Dataset:
    frame = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
    return Dataset(name="things", frame=frame, schema=SIMPLE_SCHEMA)


def step_names(dataset: Dataset) -> tuple[str, ...]:
    return tuple(step.name for step in dataset.history)


def test_a_dataset_starts_with_empty_history():
    assert make_dataset().history == ()


def test_construction_rejects_a_frame_that_does_not_match_the_schema():
    frame = pd.DataFrame({"id": [1], "unexpected": [2]})
    with pytest.raises(ValueError):
        Dataset(name="things", frame=frame, schema=SIMPLE_SCHEMA)


def test_then_returns_a_new_dataset_and_records_the_step():
    original = make_dataset()

    doubled = original.then("doubled_value", lambda frame: frame.assign(value=frame["value"] * 2))

    assert step_names(doubled) == ("doubled_value",)
    assert doubled.frame["value"].tolist() == [20, 40, 60]


def test_then_does_not_mutate_the_original_dataset():
    original = make_dataset()

    original.then("doubled_value", lambda frame: frame.assign(value=frame["value"] * 2))

    assert original.frame["value"].tolist() == [10, 20, 30]
    assert original.history == ()


def test_then_chains_accumulate_history_in_order():
    result = (
        make_dataset()
        .then("doubled", lambda frame: frame.assign(value=frame["value"] * 2))
        .then("filtered", lambda frame: frame[frame["value"] > 20])
    )

    assert step_names(result) == ("doubled", "filtered")
    assert result.frame["id"].tolist() == [2, 3]


def test_then_rejects_a_column_changing_transform_without_an_explicit_schema():
    original = make_dataset()

    with pytest.raises(ValueError):
        original.then("dropped_value", lambda frame: frame[["id"]])


def test_then_accepts_a_column_changing_transform_when_given_the_new_schema():
    original = make_dataset()
    id_only_schema = Schema(columns=(ColumnSchema("id", "int64"),))

    result = original.then("dropped_value", lambda frame: frame[["id"]], schema=id_only_schema)

    assert result.schema is id_only_schema
    assert list(result.frame.columns) == ["id"]
    assert step_names(result) == ("dropped_value",)


def test_with_schema_replaces_the_schema_without_touching_history():
    original = make_dataset().then("doubled", lambda frame: frame.assign(value=frame["value"] * 2))
    new_schema = Schema(columns=(ColumnSchema("id", "int64"), ColumnSchema("value", "float64")))

    updated = original.with_schema(new_schema)

    assert updated.schema is new_schema
    assert step_names(updated) == ("doubled",)


def test_pipeline_summary_joins_the_dataset_name_and_history():
    result = make_dataset().then("doubled", lambda frame: frame).then("filtered", lambda frame: frame)

    assert result.pipeline_summary() == "things -> doubled -> filtered"


def test_python_mirror_concatenates_code_from_steps_that_have_it_in_order():
    result = (
        make_dataset()
        .then("doubled", lambda frame: frame, python_code="things['value'] *= 2")
        .then("filtered", lambda frame: frame)  # no python_code - skipped, not a blank line
        .then("sorted", lambda frame: frame, python_code="things = things.sort_values('value')")
    )

    assert result.python_mirror() == "things['value'] *= 2\nthings = things.sort_values('value')"


def test_python_mirror_is_empty_when_no_step_has_code():
    result = make_dataset().then("doubled", lambda frame: frame)

    assert result.python_mirror() == ""


def test_two_datasets_with_identical_data_are_not_spuriously_equal_or_unhashable():
    a, b = make_dataset(), make_dataset()
    assert a != b  # identity comparison (eq=False), not a DataFrame '==' crash
    {a, b}  # must not raise: frozen=True + eq=False keeps the default identity hash

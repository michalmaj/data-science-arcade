import pandas as pd
import pytest

from data_science_arcade.data_engine.dataset import Dataset
from data_science_arcade.data_engine.schema import ColumnSchema, Schema
from data_science_arcade.data_engine.testing import (
    assert_matches_schema,
    assert_row_count_between,
    assert_unique,
    assert_values_in,
)


def make_dataset(**columns) -> Dataset:
    frame = pd.DataFrame(columns)
    schema = Schema(columns=tuple(ColumnSchema(name, "object") for name in columns))
    return Dataset(name="t", frame=frame, schema=schema)


def test_assert_matches_schema_passes_when_non_nullable_columns_have_no_nulls():
    assert_matches_schema(make_dataset(id=[1, 2, 3]))  # must not raise


def test_assert_matches_schema_fails_on_nulls_in_a_non_nullable_column():
    dataset = make_dataset(id=[1, None, 3])
    with pytest.raises(AssertionError):
        assert_matches_schema(dataset)


def test_assert_matches_schema_allows_nulls_in_a_nullable_column():
    frame = pd.DataFrame({"id": [1, None, 3]})
    schema = Schema(columns=(ColumnSchema("id", "object", nullable=True),))
    assert_matches_schema(Dataset(name="t", frame=frame, schema=schema))  # must not raise


def test_assert_row_count_between_passes_inside_the_range():
    assert_row_count_between(make_dataset(id=[1, 2, 3]), 1, 5)


def test_assert_row_count_between_fails_outside_the_range():
    with pytest.raises(AssertionError):
        assert_row_count_between(make_dataset(id=[1, 2, 3]), 10, 20)


def test_assert_unique_passes_when_there_are_no_duplicates():
    assert_unique(make_dataset(id=[1, 2, 3]), "id")


def test_assert_unique_fails_on_a_duplicate():
    with pytest.raises(AssertionError):
        assert_unique(make_dataset(id=[1, 1, 3]), "id")


def test_assert_values_in_passes_when_every_value_is_allowed():
    assert_values_in(make_dataset(region=["North", "South"]), "region", {"North", "South", "East"})


def test_assert_values_in_fails_on_an_unexpected_value():
    with pytest.raises(AssertionError):
        assert_values_in(make_dataset(region=["North", "Mars"]), "region", {"North", "South"})

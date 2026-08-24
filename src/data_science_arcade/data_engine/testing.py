"""Reusable checks for dataset/generator/transformation tests. Lives in the
package (not tests/) so individual lessons' own test suites can import it
too, once lessons exist."""

from data_science_arcade.data_engine.dataset import Dataset


def assert_matches_schema(dataset: Dataset) -> None:
    """Dataset already validates column names match its schema on
    construction; this additionally checks the nullable=False columns
    actually have no nulls."""
    for column in dataset.schema.columns:
        if not column.nullable and dataset.frame[column.name].isna().any():
            raise AssertionError(f"{dataset.name}.{column.name} is non-nullable but contains nulls")


def assert_row_count_between(dataset: Dataset, minimum: int, maximum: int) -> None:
    count = len(dataset.frame)
    if not (minimum <= count <= maximum):
        raise AssertionError(f"{dataset.name} has {count} rows, expected between {minimum} and {maximum}")


def assert_unique(dataset: Dataset, column: str) -> None:
    if dataset.frame[column].duplicated().any():
        raise AssertionError(f"{dataset.name}.{column} has duplicate values")


def assert_values_in(dataset: Dataset, column: str, allowed: set) -> None:
    unexpected = set(dataset.frame[column].unique()) - allowed
    if unexpected:
        raise AssertionError(f"{dataset.name}.{column} has values outside {allowed}: {unexpected}")

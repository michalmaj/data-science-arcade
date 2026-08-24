from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from data_science_arcade.data_engine.schema import Schema


@dataclass(frozen=True, eq=False)
class Dataset:
    """A DataFrame plus schema metadata and its transformation history, so
    the eventual PIPELINE workbench tab can show provenance like:

        raw_orders -> parsed_timestamps -> filtered_valid_orders -> ...

    eq=False: dataclass's generated __eq__ would compare DataFrames with
    `==`, which raises ("truth value of a DataFrame is ambiguous") instead
    of returning a bool. frozen=True still blocks accidental reassignment
    of frame/schema - use .then()/.with_schema() to derive a new Dataset.
    """

    name: str
    frame: pd.DataFrame
    schema: Schema
    history: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        frame_columns = set(self.frame.columns)
        schema_columns = set(self.schema.column_names())
        if frame_columns != schema_columns:
            raise ValueError(
                f"{self.name}: frame columns {frame_columns} do not match schema columns {schema_columns}"
            )

    def then(
        self,
        step_name: str,
        transform: Callable[[pd.DataFrame], pd.DataFrame],
        schema: Schema | None = None,
    ) -> "Dataset":
        """Apply transform (must return a new DataFrame, not mutate the
        input in place - the standard pandas idiom) and record the step.

        Pass `schema` when transform changes the columns - a join or
        groupby, say. Omit it for column-preserving steps (filter, sort,
        dedupe, parse-in-place) to just carry the current schema forward.
        """
        return Dataset(
            name=self.name,
            frame=transform(self.frame),
            schema=schema if schema is not None else self.schema,
            history=(*self.history, step_name),
        )

    def with_schema(self, schema: Schema) -> "Dataset":
        return Dataset(name=self.name, frame=self.frame, schema=schema, history=self.history)

    def pipeline_summary(self) -> str:
        return " -> ".join((self.name, *self.history))

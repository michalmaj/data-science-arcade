from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSchema:
    name: str
    dtype: str
    nullable: bool = False
    description: str = ""


@dataclass(frozen=True)
class Schema:
    columns: tuple[ColumnSchema, ...]

    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

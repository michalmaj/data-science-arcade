from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ColumnSchema:
    name: str
    dtype: str
    nullable: bool = False
    description: str = ""
    """Legacy literal-English display text - never renamed, since this
    dataclass is frozen and `description=` is a real kwarg at ~45 call
    sites across most lessons' own data files, versus being *read* at
    exactly one (WorkbenchScene._draw_schema). Prefer description_key for
    any schema a player will actually see (today: only Lesson 06's)."""
    description_key: str | None = None
    """Localized alternative to `description` - preferred by
    WorkbenchScene._draw_schema when set, falling back to the raw
    `description` string otherwise. Additive, not a replacement, so the
    ~44 other ColumnSchema call sites (none of which are ever actually
    shown to a player today) don't need to change."""


@dataclass(frozen=True)
class Schema:
    columns: tuple[ColumnSchema, ...]

    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    def with_column(self, name: str, *, dtype: str | None = None, description_key: str | None = None) -> "Schema":
        """Returns a new Schema with only the named column's dtype and/or
        description_key replaced - every other column, resolved or not,
        passes through completely untouched. This is what lets a repair
        mechanic update one column's own schema metadata without ever
        silently rewriting another, still-unresolved column's own entry
        as a side effect (a real bug once one shared "fixed" Schema was
        swapped in wholesale for an issue with several columns). `dtype`/
        `description_key` left None keep that column's current value."""
        columns = tuple(
            replace(
                column,
                dtype=column.dtype if dtype is None else dtype,
                description_key=column.description_key if description_key is None else description_key,
            )
            if column.name == name
            else column
            for column in self.columns
        )
        return Schema(columns=columns)

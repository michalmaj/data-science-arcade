from dataclasses import dataclass


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

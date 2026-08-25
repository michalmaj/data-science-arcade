from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from data_science_arcade.data_engine.schema import Schema


@dataclass(frozen=True)
class RepairOption:
    key: str
    label_key: str
    apply: Callable[[pd.DataFrame], pd.DataFrame]
    """Takes the whole frame, returns a new frame with `column` repaired -
    same column-preserving contract as Dataset.then()'s transform."""
    python_code: str | None = None


@dataclass(frozen=True)
class RepairIssue:
    column: str
    prompt_key: str
    options: tuple[RepairOption, ...]
    hint_key: str | None = None
    """Shown only when the workbench runs in guided mode."""
    schema_after: Schema | None = None
    """Pass when every option for this issue changes the column's dtype
    (e.g. text -> float) - applied regardless of which option was chosen,
    since picking the *wrong* parsing rule still produces that dtype, just
    with wrong values. Omit when the fix only changes values, not type."""


RepairResolution = dict[str, str]
"""issue.column -> the chosen option.key for that column."""

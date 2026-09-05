from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from data_science_arcade.data_engine.dataset import Dataset


@dataclass(frozen=True)
class RepairOption:
    key: str
    label_key: str
    apply: Callable[[pd.DataFrame], pd.DataFrame]
    """Takes the whole frame, returns a new frame with `column` repaired -
    same column-preserving contract as Dataset.then()'s transform."""
    python_code: str | None = None
    result_dtype: str | None = None
    """This option's own real resulting dtype for the issue's column, if
    it changes - e.g. "string", "category", "datetime64[ns]". Deliberately
    per-option, not per-issue: different options on the same RepairIssue
    are free to produce genuinely different dtypes (an identifier can be
    validly kept as int64 or cast to text - a schema view that assumed
    one fixed dtype for the whole issue would misreport whichever real
    outcome the *other* option actually produced). None when this option
    only changes the column's *values*, not its physical type."""
    result_description_key: str | None = None
    """This option's own schema description once it's applied, if it
    should change (e.g. a migration note that stops being relevant once
    genuinely resolved - but not for an option that only pretends to
    resolve it, like a no-op recast). None keeps the column's current
    description_key unchanged."""
    result_nullable: bool | None = None
    """This option's own real nullable state for the issue's column, if
    it changes - e.g. False once a fill/recode option has genuinely
    removed every null, or explicitly True (unchanged) for an option that
    deliberately keeps real nulls in place. None keeps the column's
    current nullable flag unchanged."""


@dataclass(frozen=True)
class RepairIssue:
    column: str
    prompt_key: str
    options: tuple[RepairOption, ...]
    hint_key: str | None = None
    """Shown only when the workbench runs in guided mode."""
    evidence_key: str | None = None
    """The underlying finding this issue represents (e.g. "price had an
    inconsistent decimal separator"), true regardless of which option gets
    picked - recorded as an EvidenceItem in the WorkbenchScene's
    LessonContext once resolved. None if this issue shouldn't surface as
    evidence."""


RepairResolution = dict[str, str]
"""issue.column -> the chosen option.key for that column."""


def apply_resolution(dataset: Dataset, issues: tuple[RepairIssue, ...], resolution: RepairResolution) -> Dataset:
    """Deterministically replays a RepairResolution against `dataset` -
    the identical functional path WorkbenchScene._make_choose takes when
    a player actually clicks an option, just decoupled from any live
    scene. This is what lets a later stage (or a scorer) reconstruct
    exactly what the student's own choices really produced - right or
    wrong - without ever having to carry a live DataFrame across a
    checkpoint: a stage only ever needs the raw dataset plus the
    (already-checkpointed) resolution dict to rebuild the real result,
    which also makes resume trivially correct. An issue with no entry in
    `resolution` (not yet resolved) is left untouched."""
    for issue in issues:
        option_key = resolution.get(issue.column)
        if option_key is None:
            continue
        option = next(o for o in issue.options if o.key == option_key)
        schema = dataset.schema.with_column(
            issue.column,
            dtype=option.result_dtype,
            description_key=option.result_description_key,
            nullable=option.result_nullable,
        )
        dataset = dataset.then(
            f"{issue.column}_{option.key}", option.apply, schema=schema, python_code=option.python_code
        )
    return dataset

from dataclasses import dataclass


@dataclass(frozen=True)
class RecordField:
    label_key: str
    value_a: str
    value_b: str
    matches: bool
    """Precomputed, not derived in the UI - the scene renders this flag,
    it doesn't decide what counts as 'the same' (e.g. case-insensitive
    email, a nickname vs. a legal name) - that judgment lives in content."""


@dataclass(frozen=True)
class RecordPair:
    key: str
    id_a: str
    id_b: str
    fields: tuple[RecordField, ...]
    hint_key: str | None = None
    """Shown only when the scene runs in guided mode."""


PairDecisions = dict[str, str]
"""pair.key -> 'merge' or 'keep_separate'."""

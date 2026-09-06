from dataclasses import dataclass


@dataclass(frozen=True)
class GroupVerdictOption:
    key: str
    label_key: str


@dataclass(frozen=True)
class DuplicateGroup:
    """A real, representative cluster of rows sharing `key_column`, shown
    to the student one at a time by DuplicateGroupScene - `rows` are
    already-stringified real data. The scene itself has no notion of
    which verdict is "correct" for a group (mirrors SegmentSlicerScene's
    own no-evidence-awareness design) - the calling lesson's own
    on_complete handler decides that, and records evidence accordingly,
    from its own group-key -> correct-verdict mapping."""

    key: str
    key_column: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    prompt_key: str
    hint_key: str | None = None


DuplicateGroupVerdicts = dict[str, str]

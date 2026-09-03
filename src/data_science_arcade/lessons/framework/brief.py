from dataclasses import dataclass


@dataclass(frozen=True)
class BriefOption:
    key: str
    label_key: str


@dataclass(frozen=True)
class BriefField:
    key: str
    prompt_key: str
    options: tuple[BriefOption, ...]
    hint_key: str | None = None
    """Shown only when the builder runs in guided mode."""


@dataclass(frozen=True)
class MultiChoiceField:
    """A BriefField's multi-select sibling: pick min_count-max_count
    options from a fixed candidate list, not a single option. Distinct
    from ui/decision_builder_scene.py's own EvidenceField, which is a
    multi-select too but hard-wired to whatever real facts the student
    has gathered in LessonContext - this is for a fixed option list known
    up front (e.g. "which of these 5 properties should this event
    record"), the same relationship BriefField already has to a fixed
    single-select list."""

    key: str
    prompt_key: str
    options: tuple[BriefOption, ...]
    min_count: int = 1
    max_count: int = 3
    hint_key: str | None = None
    """Shown only when the builder runs in guided mode."""


BriefStep = BriefField | MultiChoiceField

AnalyticalBrief = dict[str, str | tuple[str, ...]]
"""field.key -> the chosen option.key for a BriefField, or a tuple of
chosen option.key values for a MultiChoiceField."""

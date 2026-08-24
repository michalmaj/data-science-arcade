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


AnalyticalBrief = dict[str, str]
"""field.key -> the chosen option.key for that field."""

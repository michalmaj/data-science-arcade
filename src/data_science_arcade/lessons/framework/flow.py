from dataclasses import dataclass


@dataclass(frozen=True)
class FlowEventOption:
    key: str
    label_key: str


@dataclass(frozen=True)
class FlowStep:
    key: str
    short_label_key: str
    """Shown in the persistent flow diagram box - keep this short, unlike
    prompt_key, since it has to fit a small fixed-width box alongside every
    other step at once."""
    prompt_key: str
    options: tuple[FlowEventOption, ...]
    hint_key: str | None = None
    """Shown only when the builder runs in guided mode."""


EventPlacement = dict[str, str]
"""step.key -> the chosen option.key for that step."""

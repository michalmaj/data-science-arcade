from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    key: str
    label_key: str
    before_rate: float
    after_rate: float


@dataclass(frozen=True)
class SliceOption:
    key: str
    label_key: str
    segments: tuple[Segment, ...]


@dataclass(frozen=True)
class SegmentRequest:
    key: str
    prompt_key: str
    options: tuple[SliceOption, ...]
    hint_key: str | None = None


SegmentChoices = dict[str, str]

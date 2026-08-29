from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    key: str
    label_key: str


FindingChoices = tuple[str, ...]  # exactly `target_count` finding keys, in pick order

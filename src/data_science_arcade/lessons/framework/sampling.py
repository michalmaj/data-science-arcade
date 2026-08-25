from dataclasses import dataclass


@dataclass(frozen=True)
class SamplingGroup:
    key: str
    label_key: str


SamplingAllocation = dict[str, int]
"""group.key -> how many contacts were allocated to that group."""

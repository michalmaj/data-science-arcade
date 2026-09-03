from dataclasses import dataclass


@dataclass(frozen=True)
class SamplingGroup:
    key: str
    label_key: str
    available: int | None = None
    """Real ceiling on how much of the total budget this one group can
    actually absorb - e.g. a stratum with only 15 real rows to draw from,
    no matter how much of the total budget points at it. None (default)
    means unbounded except by the total budget itself, exactly today's
    behavior - every existing caller passes 2 positional args, so this
    stays fully backward compatible."""


SamplingAllocation = dict[str, int]
"""group.key -> how many contacts were allocated to that group."""

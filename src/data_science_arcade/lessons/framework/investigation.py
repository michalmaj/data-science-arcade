from collections.abc import Callable
from dataclasses import dataclass

from data_science_arcade.core.scenes import Scene


@dataclass(frozen=True)
class InvestigationLead:
    key: str
    label_key: str
    build_scene: Callable[[Callable[..., None]], Scene]  # on_complete -> the lead's own reused scene


InvestigationResult = frozenset[str]  # keys of every lead the player actually investigated

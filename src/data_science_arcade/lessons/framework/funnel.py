from dataclasses import dataclass


@dataclass(frozen=True)
class FunnelStep:
    key: str
    label_key: str
    count: int


@dataclass(frozen=True)
class FunnelDefinition:
    key: str
    label_key: str
    steps: tuple[FunnelStep, ...]
    percent_basis: str = "previous"  # "previous" or "top" - which denominator each step's % is shown against


@dataclass(frozen=True)
class FunnelRequest:
    key: str
    prompt_key: str
    definitions: tuple[FunnelDefinition, ...]
    hint_key: str | None = None


FunnelChoices = dict[str, str]

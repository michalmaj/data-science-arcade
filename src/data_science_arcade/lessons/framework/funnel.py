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
    dataset_definition_key: str = ""
    """The real `definition_key` value this definition's own steps were
    filtered from (checkout_events.py's own generate_checkout_events()) -
    needed by funnel_mirror_code() to regenerate the real filter
    expression, since `key` alone can't distinguish two definitions built
    from the same underlying dataset_definition_key under different
    percent_basis values (e.g. percent_of_total_visits vs
    percent_of_previous_step). Defaults to "" so existing test fixtures
    that build a FunnelDefinition directly (never exercising the Python
    Mirror) stay unaffected."""


@dataclass(frozen=True)
class FunnelRequest:
    key: str
    prompt_key: str
    definitions: tuple[FunnelDefinition, ...]
    hint_key: str | None = None


FunnelChoices = dict[str, str]

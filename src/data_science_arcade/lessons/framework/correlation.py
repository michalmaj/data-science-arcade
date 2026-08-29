from dataclasses import dataclass


@dataclass(frozen=True)
class VerdictOption:
    key: str
    label_key: str
    explanation_key: str  # shown as the consequence once this verdict is picked


@dataclass(frozen=True)
class CorrelationRequest:
    key: str
    prompt_key: str
    metric_a_label_key: str
    metric_b_label_key: str
    evidence_key: str  # the additional fact that rules some explanations out
    correlation: float
    sample_size: int
    options: tuple[VerdictOption, ...]
    hint_key: str | None = None


CorrelationChoices = dict[str, str]

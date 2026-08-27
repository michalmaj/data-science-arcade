from dataclasses import dataclass


@dataclass(frozen=True)
class JoinOption:
    key: str
    label_key: str
    how: str  # a pandas merge() how value: "inner", "left", "right"


@dataclass(frozen=True)
class JoinRequest:
    key: str
    prompt_key: str
    options: tuple[JoinOption, ...]
    hint_key: str | None = None


JoinChoices = dict[str, str]  # request key -> chosen option key

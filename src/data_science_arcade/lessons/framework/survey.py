from dataclasses import dataclass


@dataclass(frozen=True)
class WordingOption:
    key: str
    label_key: str
    bias: float  # added to every respondent's recorded value, capped at 1.0; 0.0 = neutral


@dataclass(frozen=True)
class ChannelOption:
    key: str
    label_key: str
    reach_query: str | None  # a pandas .query() expression selecting who CAN be reached; None = everyone


@dataclass(frozen=True)
class SurveyRequest:
    key: str
    prompt_key: str
    wording_options: tuple[WordingOption, ...]
    channel_options: tuple[ChannelOption, ...]
    hint_key: str | None = None


SurveyChoice = tuple[str, str]  # (wording_key, channel_key)
SurveyChoices = dict[str, SurveyChoice]
